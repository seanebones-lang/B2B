"""REST API endpoints for programmatic access"""

from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uuid
from typing import Dict as TypingDict

from scraper import G2Scraper, CapterraScraper
from analyzer import PatternExtractor, XAIClient
from utils.database import get_db_manager
from utils.cache import CacheManager
from utils.async_helpers import scrape_tool_sync
from utils.security import SecurityManager, InputValidator
from utils.rate_limiter import RateLimiter
from utils.audit import get_audit_logger
from utils.health import check_health
import config

# Initialize FastAPI app
app = FastAPI(
    title="B2B Complaint Analyzer API",
    description="API for analyzing B2B SaaS tool complaints and generating product ideas",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize utilities
security_manager = SecurityManager()
cache_manager = CacheManager()
rate_limiter = RateLimiter()
db_manager = get_db_manager()
audit_logger = get_audit_logger()

# Simple in-memory task storage (for async processing)
_analysis_tasks: TypingDict[str, TypingDict[str, Any]] = {}


# Pydantic schemas
class AnalyzeRequest(BaseModel):
    """Request schema for analysis"""
    tools: List[str] = Field(..., description="List of tool names to analyze", min_items=1, max_items=3)
    use_semantic: bool = Field(True, description="Use semantic analysis")
    max_reviews_per_tool: int = Field(30, description="Maximum reviews per tool", ge=1, le=100)


class AnalyzeResponse(BaseModel):
    """Response schema for analysis"""
    analysis_id: str
    status: str
    message: str


class ResultResponse(BaseModel):
    """Response schema for results"""
    analysis_id: str
    tool_results: Dict[str, Any]
    top_opportunities: List[Dict[str, Any]]


class HealthResponse(BaseModel):
    """Response schema for health check"""
    status: str
    checks: Dict[str, Any]


# API key authentication
async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """Verify API key from header"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    # Validate API key format
    if not InputValidator.validate_api_key(x_api_key):
        audit_logger.log_authentication_attempt("api", False, "Invalid API key format")
        raise HTTPException(status_code=401, detail="Invalid API key format")
    
    # Log API key usage
    api_key_hash = security_manager.hash_api_key(x_api_key)
    audit_logger.log_api_key_usage(api_key_hash, "api_request", True)
    
    return x_api_key


# Rate limiting dependency
def check_rate_limit(api_key: str = Depends(verify_api_key)) -> str:
    """Check rate limit for API key"""
    if not rate_limiter.is_allowed(api_key):
        audit_logger.log_rate_limit_violation(api_key[:10] + "...", "api", 60)
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    return api_key


@app.post("/api/v1/analyze", response_model=AnalyzeResponse)
async def analyze_tools(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(check_rate_limit)
):
    """
    Run analysis on specified tools
    
    Args:
        request: Analysis request with tools and options
        api_key: API key for authentication
        
    Returns:
        Analysis response with analysis ID
    """
    try:
        # Validate tool names
        valid_tools = []
        for tool_name in request.tools:
            if InputValidator.validate_tool_name(tool_name):
                valid_tools.append(tool_name)
            else:
                audit_logger.log_input_validation_failure("tool_name", tool_name, "Invalid format")
        
        if not valid_tools:
            raise HTTPException(status_code=400, detail="No valid tools provided")
        
        # Generate analysis ID
        analysis_id = str(uuid.uuid4())
        
        # Store task as pending
        _analysis_tasks[analysis_id] = {
            "status": "pending",
            "tools": valid_tools
        }
        
        # Run analysis in background
        background_tasks.add_task(
            run_analysis_background,
            analysis_id=analysis_id,
            tools=valid_tools,
            use_semantic=request.use_semantic,
            api_key=api_key
        )
        
        return AnalyzeResponse(
            analysis_id=analysis_id,
            status="accepted",
            message=f"Analysis started for {len(valid_tools)} tool(s)"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        audit_logger.log_security_threat("api_error", {"error": str(e)})
        raise HTTPException(status_code=500, detail="Internal server error")


def run_analysis_background(
    analysis_id: str,
    tools: List[str],
    use_semantic: bool,
    api_key: str
) -> None:
    """Background task to run analysis"""
    try:
        xai_client = XAIClient(api_key)
        pattern_extractor = PatternExtractor()
        all_results: TypingDict[str, Any] = {}
        
        for tool_name in tools:
            tool_config = next(
                (t for t in config.B2B_TOOLS if t["name"] == tool_name),
                None
            )
            if not tool_config:
                continue
            
            # Scrape reviews (simplified - would use async scrapers)
            reviews: List[TypingDict[str, Any]] = []
            
            # Extract patterns
            pattern_results = pattern_extractor.extract_patterns(reviews)
            
            # AI analysis
            ai_analysis = xai_client.analyze_patterns(
                tool_name,
                pattern_results["patterns"],
                reviews
            )
            
            all_results[tool_name] = {
                "reviews": reviews,
                "pattern_results": pattern_results,
                "ai_analysis": ai_analysis
            }
        
        # Store results
        _analysis_tasks[analysis_id] = {
            "status": "completed",
            "results": all_results
        }
        
    except Exception as e:
        _analysis_tasks[analysis_id] = {
            "status": "failed",
            "error": str(e)
        }


@app.get("/api/v1/results/{analysis_id}", response_model=ResultResponse)
async def get_results(
    analysis_id: str,
    api_key: str = Depends(check_rate_limit)
):
    """
    Get analysis results by ID
    
    Args:
        analysis_id: Analysis ID from analyze endpoint
        api_key: API key for authentication
        
    Returns:
        Analysis results
    """
    if analysis_id not in _analysis_tasks:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    task = _analysis_tasks[analysis_id]
    
    if task["status"] == "failed":
        raise HTTPException(status_code=500, detail=f"Analysis failed: {task.get('error', 'Unknown error')}")
    
    if task["status"] != "completed":
        raise HTTPException(status_code=202, detail="Analysis still in progress")
    
    # Generate top opportunities (simplified)
    top_opportunities: List[TypingDict[str, Any]] = []
    
    return ResultResponse(
        analysis_id=analysis_id,
        tool_results=task["results"],
        top_opportunities=top_opportunities
    )


@app.get("/api/v1/tools", response_model=List[Dict[str, str]])
async def list_tools(api_key: str = Depends(check_rate_limit)):
    """
    List available tools for analysis
    
    Args:
        api_key: API key for authentication
        
    Returns:
        List of available tools
    """
    return [
        {"name": tool["name"], "category": tool["category"]}
        for tool in config.B2B_TOOLS
    ]


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    
    Returns:
        Health status and checks
    """
    health_status = check_health()
    
    return HealthResponse(
        status="healthy" if health_status["healthy"] else "unhealthy",
        checks=health_status
    )


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "B2B Complaint Analyzer API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    audit_logger.log_security_threat("api_error", {"error": str(exc), "path": str(request.url)})
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

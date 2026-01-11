"""Enhanced Streamlit application with improved error handling, logging, and utilities"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Optional
import json
import time
import os

from scraper import G2Scraper, CapterraScraper
from analyzer import PatternExtractor, PatternExtractorV2, XAIClient
from utils.security import SecurityManager, InputValidator
from utils.logging import get_logger
from utils.database import get_db_manager
from utils.cache import CacheManager
from utils.rate_limiter import RateLimiter
from utils.async_helpers import scrape_tool_sync
from utils.monitoring import monitor_performance
from utils.accessibility import get_aria_labels, get_accessibility_attributes
from utils.csrf import get_csrf_protection
from utils.performance_applications import get_perf_applications
from utils.bias_detection import get_bias_detector, get_explainability_provider
from utils.energy_efficiency import get_energy_tracker
import config

# Initialize logging
logger = get_logger(__name__)

# Initialize utilities
security_manager = SecurityManager()
cache_manager = CacheManager()
rate_limiter = RateLimiter()
db_manager = get_db_manager()

# Page config
st.set_page_config(
    page_title="B2B Complaint Analyzer",
    page_icon="🔍",
    layout="wide"
)

# Initialize session state
if "reviews_data" not in st.session_state:
    st.session_state.reviews_data = {}
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = {}
if "xai_client" not in st.session_state:
    st.session_state.xai_client = None
if "session_id" not in st.session_state:
    import uuid
    st.session_state.session_id = str(uuid.uuid4())

# Initialize CSRF protection
csrf_protection = get_csrf_protection()
csrf_token = csrf_protection.get_token_for_session(st.session_state.session_id)

# Apply performance optimizations on startup
if "perf_optimizations_applied" not in st.session_state:
    perf_applications = get_perf_applications()
    optimizations = perf_applications.apply_all_optimizations()
    st.session_state.perf_optimizations_applied = True
    logger.info("Performance optimizations applied", optimizations=optimizations)


def main():
    """Main application entry point"""
    st.title("🔍 B2B Complaint-Driven Product Ideation")
    st.markdown("Extract unmet needs from 1-2 star reviews and generate actionable product ideas")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # xAI API Key with security validation and accessibility
        aria_labels = get_aria_labels()
        api_key_input = st.text_input(
            "xAI API Key",
            type="password",
            help="Get your API key from https://x.ai/api",
            value=security_manager.get_api_key("streamlit") or "",
            key="api_key_input",
            label_visibility="visible"
        )
        
        if api_key_input:
            try:
                # Validate and sanitize API key
                if InputValidator.validate_api_key(api_key_input):
                    st.session_state.xai_client = XAIClient(api_key_input)
                    st.success("✅ API key configured")
                    logger.info("API key configured successfully")
                else:
                    st.error("❌ Invalid API key format")
            except Exception as e:
                st.error(f"Error initializing xAI client: {str(e)}")
                logger.error("Failed to initialize xAI client", error=str(e))
        else:
            # Try to get from environment
            api_key = security_manager.get_api_key()
            if api_key:
                try:
                    st.session_state.xai_client = XAIClient(api_key)
                    st.info("✅ Using API key from environment")
                except Exception as e:
                    logger.warning("Failed to use environment API key", error=str(e))
        
        st.divider()
        
        # Tool selection with validation and accessibility
        st.header("📊 Select Tools")
        tool_names = [tool["name"] for tool in config.B2B_TOOLS]
        selected_tools_raw = st.multiselect(
            "Choose B2B tools to analyze",
            tool_names,
            default=tool_names[:3] if len(tool_names) >= 3 else tool_names,
            help="Select 1-3 tools for best performance",
            key="tool_select",
            label_visibility="visible"
        )
        
        # Sanitize tool selection
        selected_tools = []
        for tool in selected_tools_raw:
            if InputValidator.validate_tool_name(tool):
                selected_tools.append(tool)
            else:
                st.warning(f"Invalid tool name: {tool}")
        
        st.divider()
        
        # Pattern extraction method selection
        st.header("🔬 Analysis Method")
        use_semantic = st.checkbox(
            "Use Semantic Analysis (Sentence Transformers)",
            value=True,
            help="Uses advanced NLP for better pattern detection. Falls back to TF-IDF if unavailable."
        )
        
        st.divider()
        
        # Run analysis button with rate limiting and accessibility
        run_analysis = st.button(
            "🚀 Run Analysis",
            type="primary",
            use_container_width=True,
            disabled=not st.session_state.xai_client or not selected_tools,
            key="run_analysis",
            help="Press Ctrl+Enter or Cmd+Enter to run analysis"
        )
        
        if not st.session_state.xai_client:
            st.warning("⚠️ Please enter xAI API key")
        if not selected_tools:
            st.warning("⚠️ Please select at least one tool")
        
        # Rate limiting check
        if run_analysis:
            if not rate_limiter.is_allowed(st.session_state.session_id):
                st.error("⏱️ Rate limit exceeded. Please wait a moment before trying again.")
                run_analysis = False
    
    # Main content area
    if run_analysis and st.session_state.xai_client and selected_tools:
        try:
            run_full_analysis(selected_tools, use_semantic=use_semantic)
        except Exception as e:
            logger.error("Analysis failed", error=str(e), exc_info=True)
            st.error(f"❌ Error during analysis: {str(e)}")
            st.exception(e)
    else:
        show_instructions()
    
    # Display results if available
    if st.session_state.analysis_results:
        display_results()
    
    # Footer with health check link
    st.divider()
    st.markdown("---")
    st.markdown(
        "<small>💡 Tip: Check system health at `/health` endpoint</small>",
        unsafe_allow_html=True
    )


def show_instructions():
    """Show usage instructions"""
    st.markdown("""
    ### How to Use
    
    1. **Enter xAI API Key**: Get your key from [x.ai/api](https://x.ai/api)
    2. **Select Tools**: Choose 1-3 B2B SaaS tools to analyze
    3. **Choose Analysis Method**: Select semantic analysis for better results
    4. **Run Analysis**: Click the button to scrape reviews and generate insights
    
    ### What This Tool Does
    
    - Scrapes 1-2 star reviews from G2.com and Capterra
    - Identifies complaint patterns using keyword matching and clustering
    - Uses xAI Grok to analyze patterns and generate product ideas
    - Creates actionable 4-week roadmaps for top opportunities
    
    ### Supported Tools
    
    The following B2B tools are pre-configured:
    """)
    
    tools_df = pd.DataFrame([
        {"Tool": tool["name"], "Category": tool["category"]}
        for tool in config.B2B_TOOLS
    ])
    st.dataframe(tools_df, use_container_width=True, hide_index=True)


def run_full_analysis(selected_tools: List[str], use_semantic: bool = True):
    """Run complete analysis pipeline with improved error handling"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    all_results = {}
    total_steps = len(selected_tools) * 3 + 2
    current_step = 0
    
    try:
        # Use semantic extractor if available and requested
        if use_semantic:
            try:
                pattern_extractor = PatternExtractorV2(use_semantic=True)
                logger.info("Using semantic pattern extractor")
            except Exception as e:
                logger.warning("Semantic extractor unavailable, falling back", error=str(e))
                pattern_extractor = PatternExtractor()
        else:
            pattern_extractor = PatternExtractor()
        
        # Process each tool (using async scrapers for better performance)
        for tool_name in selected_tools:
            tool_config = next((t for t in config.B2B_TOOLS if t["name"] == tool_name), None)
            if not tool_config:
                logger.warning("Tool config not found", tool_name=tool_name)
                continue
            
            status_text.text(f"📥 Scraping reviews for {tool_name}...")
            current_step += 1
            progress_bar.progress(current_step / total_steps)
            
            # Check cache first
            cache_key = f"reviews_{tool_name}"
            cached_reviews = cache_manager.get(cache_key)
            
            if cached_reviews:
                logger.info("Using cached reviews", tool_name=tool_name)
                reviews = cached_reviews
                st.info(f"  ✓ Using cached reviews for {tool_name}")
            else:
                # Scrape reviews using async scrapers (parallel G2 + Capterra)
                try:
                    status_text.text(f"  → Scraping G2.com and Capterra in parallel...")
                    reviews = scrape_tool_sync(
                        tool_name,
                        tool_config,
                        max_reviews=config.settings.max_reviews_per_tool
                    )
                    
                    g2_count = sum(1 for r in reviews if r.get("source") == "G2")
                    capterra_count = sum(1 for r in reviews if r.get("source") == "Capterra")
                    
                    logger.info(
                        "Async scraping complete",
                        tool_name=tool_name,
                        g2_count=g2_count,
                        capterra_count=capterra_count,
                        total=len(reviews)
                    )
                    
                    if g2_count > 0:
                        st.success(f"  ✓ Found {g2_count} reviews from G2")
                    if capterra_count > 0:
                        st.success(f"  ✓ Found {capterra_count} reviews from Capterra")
                    
                except Exception as e:
                    logger.error("Async scraping failed", tool_name=tool_name, error=str(e))
                    st.warning(f"  ⚠️ Scraping failed: {str(e)}")
                    reviews = []
                
                # Cache reviews
                if reviews:
                    cache_manager.set(cache_key, reviews)
            
            if not reviews:
                st.error(f"❌ No reviews found for {tool_name}. Skipping...")
                logger.warning("No reviews found", tool_name=tool_name)
                continue
            
            # Save reviews to database
            try:
                db_manager.save_reviews(tool_name, reviews)
                logger.info("Reviews saved to database", tool_name=tool_name, count=len(reviews))
            except Exception as e:
                logger.error("Failed to save reviews to database", error=str(e))
            
            # Extract patterns
            status_text.text(f"🔍 Analyzing patterns for {tool_name}...")
            current_step += 1
            progress_bar.progress(current_step / total_steps)
            
            pattern_results = pattern_extractor.extract_patterns(reviews)
            
            # AI analysis
            if st.session_state.xai_client:
                status_text.text(f"🤖 AI analysis for {tool_name}...")
                current_step += 1
                progress_bar.progress(current_step / total_steps)
                
                try:
                    ai_analysis = st.session_state.xai_client.analyze_patterns(
                        tool_name,
                        pattern_results["patterns"],
                        reviews
                    )
                    
                    # Generate product ideas
                    if ai_analysis.get("top_patterns"):
                        ideas = st.session_state.xai_client.generate_product_ideas(
                            tool_name,
                            ai_analysis["top_patterns"]
                        )
                        ai_analysis["product_ideas"] = ideas
                        
                        # Bias detection and explainability
                        bias_detector = get_bias_detector()
                        explainability = get_explainability_provider()
                        
                        # Check for bias in AI output
                        bias_analysis = bias_detector.analyze_ai_output(ai_analysis)
                        if bias_analysis["has_bias"]:
                            logger.warning("Bias detected in AI output", tool_name=tool_name, bias_analysis=bias_analysis)
                            ai_analysis["bias_warning"] = bias_analysis
                        
                        # Generate explainability report
                        explainability_report = explainability.generate_explainability_report({
                            "pattern_results": pattern_results,
                            "ai_analysis": ai_analysis
                        })
                        ai_analysis["explainability"] = explainability_report
                    
                    logger.info("AI analysis complete", tool_name=tool_name)
                except Exception as e:
                    logger.error("AI analysis failed", tool_name=tool_name, error=str(e))
                    st.error(f"Error in AI analysis: {str(e)}")
                    ai_analysis = {}
            else:
                ai_analysis = {}
            
            all_results[tool_name] = {
                "reviews": reviews,
                "pattern_results": pattern_results,
                "ai_analysis": ai_analysis
            }
        
        # Generate top 3 opportunities
        if st.session_state.xai_client and all_results:
            status_text.text("🎯 Generating top opportunities...")
            current_step += 1
            progress_bar.progress(current_step / total_steps)
            
            top_opportunities = generate_top_opportunities(all_results)
            
            # Save analysis results to database
            try:
                for tool_name, results in all_results.items():
                    db_manager.save_analysis_result(
                        tool_name=tool_name,
                        session_id=st.session_state.session_id,
                        patterns=results["pattern_results"],
                        ai_analysis=results["ai_analysis"],
                        product_ideas=results["ai_analysis"].get("product_ideas", [])
                    )
                logger.info("Analysis results saved to database")
            except Exception as e:
                logger.error("Failed to save analysis results", error=str(e))
            
            status_text.text("✅ Analysis complete!")
            current_step += 1
            progress_bar.progress(current_step / total_steps)
            
            st.session_state.analysis_results = {
                "tool_results": all_results,
                "top_opportunities": top_opportunities
            }
        else:
            st.session_state.analysis_results = {
                "tool_results": all_results,
                "top_opportunities": []
            }
        
        time.sleep(1)
        progress_bar.empty()
        status_text.empty()
        
    except Exception as e:
        logger.error("Analysis pipeline failed", error=str(e), exc_info=True)
        st.error(f"❌ Error during analysis: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def generate_top_opportunities(all_results: Dict) -> List[Dict]:
    """Generate top 3 opportunities across all tools"""
    opportunities = []
    
    for tool_name, results in all_results.items():
        ai_analysis = results.get("ai_analysis", {})
        ideas = ai_analysis.get("product_ideas", [])
        
        for idea_group in ideas:
            pattern_name = idea_group.get("pattern", "Unknown")
            for idea in idea_group.get("ideas", []):
                opportunities.append({
                    "tool": tool_name,
                    "pattern": pattern_name,
                    "idea": idea
                })
    
    # Sort by potential (prioritize standalone apps)
    opportunities.sort(key=lambda x: (
        0 if x["idea"].get("type") == "standalone" else 1,
        -len(x["idea"].get("name", ""))
    ))
    
    # Generate roadmaps for top 3
    top_3 = []
    for opp in opportunities[:3]:
        if st.session_state.xai_client:
            try:
                roadmap = st.session_state.xai_client.generate_roadmap(opp["idea"])
                opp["roadmap"] = roadmap
            except Exception as e:
                logger.warning("Failed to generate roadmap", error=str(e))
                st.warning(f"Could not generate roadmap: {str(e)}")
        top_3.append(opp)
    
    return top_3


def display_results():
    """Display analysis results (reuse from original app.py)"""
    results = st.session_state.analysis_results
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Summary", "🔍 Per-Tool Breakdown", "🚀 Top 3 Opportunities"])
    
    with tab1:
        display_summary(results)
    
    with tab2:
        display_per_tool(results)
    
    with tab3:
        display_top_opportunities(results)
    
    # Export buttons
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 Export as Markdown"):
            export_markdown(results)
    with col2:
        if st.button("📊 Export as JSON"):
            export_json(results)


def display_summary(results: Dict):
    """Display summary view"""
    tool_results = results.get("tool_results", {})
    top_opportunities = results.get("top_opportunities", [])
    
    st.header("Summary")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tools Analyzed", len(tool_results))
    with col2:
        total_reviews = sum(len(r["reviews"]) for r in tool_results.values())
        st.metric("Total Reviews", total_reviews)
    with col3:
        st.metric("Top Opportunities", len(top_opportunities))
    
    if top_opportunities:
        st.subheader("Top 3 Opportunities")
        for i, opp in enumerate(top_opportunities[:3], 1):
            with st.expander(f"{i}. {opp['idea'].get('name', 'Unknown')} - {opp['tool']}"):
                st.write(f"**Pattern:** {opp['pattern']}")
                st.write(f"**Value Prop:** {opp['idea'].get('value_prop', 'N/A')}")
                st.write(f"**Target:** {opp['idea'].get('target', 'N/A')}")
                st.write(f"**MVP Scope:** {opp['idea'].get('mvp_scope', 'N/A')}")
                st.write(f"**Monetization:** {opp['idea'].get('monetization', 'N/A')}")


def display_per_tool(results: Dict):
    """Display per-tool breakdown"""
    tool_results = results.get("tool_results", {})
    
    for tool_name, tool_data in tool_results.items():
        st.header(f"📦 {tool_name}")
        
        reviews = tool_data.get("reviews", [])
        pattern_results = tool_data.get("pattern_results", {})
        ai_analysis = tool_data.get("ai_analysis", {})
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Reviews Found", len(reviews))
        with col2:
            st.metric("Patterns Identified", len(pattern_results.get("patterns", [])))
        
        if pattern_results.get("patterns"):
            st.subheader("Complaint Patterns")
            patterns_df = pd.DataFrame([
                {
                    "Pattern": p["description"],
                    "Frequency": p["frequency"],
                    "Percentage": f"{p['frequency'] / len(reviews) * 100:.1f}%"
                }
                for p in pattern_results["patterns"][:5]
            ])
            st.dataframe(patterns_df, use_container_width=True, hide_index=True)
        
        if ai_analysis.get("top_patterns"):
            st.subheader("AI Analysis - Top Patterns")
            for pattern in ai_analysis["top_patterns"][:3]:
                with st.expander(f"{pattern.get('name', 'Unknown')} (Frequency: {pattern.get('frequency', 0)})"):
                    st.write(f"**Impact:** {pattern.get('impact_reason', 'N/A')}")
                    st.write(f"**Example:** {pattern.get('example', 'N/A')}")
        
        if ai_analysis.get("product_ideas"):
            st.subheader("Product Ideas")
            for idea_group in ai_analysis["product_ideas"]:
                st.write(f"**Pattern:** {idea_group.get('pattern', 'Unknown')}")
                for idea in idea_group.get("ideas", []):
                    with st.expander(idea.get("name", "Unknown Idea")):
                        st.write(f"**Type:** {idea.get('type', 'N/A')}")
                        st.write(f"**Value Prop:** {idea.get('value_prop', 'N/A')}")
                        st.write(f"**Target:** {idea.get('target', 'N/A')}")
                        st.write(f"**MVP Scope:** {idea.get('mvp_scope', 'N/A')}")
                        st.write(f"**Monetization:** {idea.get('monetization', 'N/A')}")
        
        st.divider()


def display_top_opportunities(results: Dict):
    """Display top 3 opportunities with roadmaps"""
    top_opportunities = results.get("top_opportunities", [])
    
    if not top_opportunities:
        st.info("No opportunities generated. Run analysis with xAI API key configured.")
        return
    
    for i, opp in enumerate(top_opportunities[:3], 1):
        st.header(f"Opportunity #{i}: {opp['idea'].get('name', 'Unknown')}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Tool:** {opp['tool']}")
            st.write(f"**Pattern:** {opp['pattern']}")
        with col2:
            st.write(f"**Type:** {opp['idea'].get('type', 'N/A')}")
            st.write(f"**Monetization:** {opp['idea'].get('monetization', 'N/A')}")
        
        st.write(f"**Value Proposition:** {opp['idea'].get('value_prop', 'N/A')}")
        st.write(f"**Target Audience:** {opp['idea'].get('target', 'N/A')}")
        st.write(f"**MVP Scope:** {opp['idea'].get('mvp_scope', 'N/A')}")
        
        if opp.get("roadmap"):
            st.subheader("4-Week Solo Founder Roadmap")
            roadmap = opp["roadmap"]
            
            for week_num in ["week1", "week2", "week3", "week4"]:
                week_data = roadmap.get(week_num, {})
                with st.expander(f"Week {week_num[-1]}: {week_data.get('goal', 'N/A')}"):
                    tasks = week_data.get("tasks", [])
                    if isinstance(tasks, list):
                        for task in tasks:
                            st.write(f"- {task}")
                    else:
                        st.write(tasks)
        
        st.divider()


def export_markdown(results: Dict):
    """Export results as Markdown"""
    md_content = "# B2B Complaint-Driven Product Ideas Report\n\n"
    
    tool_results = results.get("tool_results", {})
    top_opportunities = results.get("top_opportunities", [])
    
    md_content += "## Summary\n\n"
    md_content += f"- **Tools Analyzed:** {len(tool_results)}\n"
    md_content += f"- **Top Opportunities:** {len(top_opportunities)}\n\n"
    
    md_content += "## Top 3 Opportunities\n\n"
    for i, opp in enumerate(top_opportunities[:3], 1):
        md_content += f"### {i}. {opp['idea'].get('name', 'Unknown')}\n\n"
        md_content += f"**Pattern/Source:** {opp['pattern']} ({opp['tool']})\n\n"
        md_content += f"**Value Prop:** {opp['idea'].get('value_prop', 'N/A')}\n\n"
        md_content += f"**Target:** {opp['idea'].get('target', 'N/A')}\n\n"
        md_content += f"**MVP Scope:** {opp['idea'].get('mvp_scope', 'N/A')}\n\n"
        md_content += f"**Monetization:** {opp['idea'].get('monetization', 'N/A')}\n\n"
        
        if opp.get("roadmap"):
            md_content += "**Roadmap:**\n\n"
            roadmap = opp["roadmap"]
            for week_num in ["week1", "week2", "week3", "week4"]:
                week_data = roadmap.get(week_num, {})
                md_content += f"- **Week {week_num[-1]}:** {week_data.get('goal', 'N/A')}\n"
                tasks = week_data.get("tasks", [])
                if isinstance(tasks, list):
                    for task in tasks:
                        md_content += f"  - {task}\n"
            md_content += "\n"
    
    st.download_button(
        "Download Markdown",
        md_content,
        file_name="b2b_ideas_report.md",
        mime="text/markdown"
    )


def export_json(results: Dict):
    """Export results as JSON"""
    json_str = json.dumps(results, indent=2, default=str)
    st.download_button(
        "Download JSON",
        json_str,
        file_name="b2b_ideas_report.json",
        mime="application/json"
    )


if __name__ == "__main__":
    main()

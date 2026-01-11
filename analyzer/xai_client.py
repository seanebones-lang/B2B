"""xAI Grok API client for analysis and idea generation with improved error handling"""

from typing import List, Dict, Optional, Any
import json
import re

from openai import OpenAI
from openai import APIError, RateLimitError, APIConnectionError

from utils.logging import get_logger
from utils.retry import retry_api_call
from utils.security import InputValidator
from utils.cache import cached
from utils.circuit_breaker import get_circuit_breaker
from openai import APIError, RateLimitError, APIConnectionError
import config

logger = get_logger(__name__)


class XAIClient:
    """Client for xAI Grok API with retry logic and error handling"""
    
    def __init__(self, api_key: str):
        """
        Initialize xAI client
        
        Args:
            api_key: xAI API key
            
        Raises:
            ValueError: If API key is invalid
        """
        if not InputValidator.validate_api_key(api_key):
            raise ValueError("Invalid API key format")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=config.settings.xai_base_url
        )
        # Updated Jan 2026: Grok-3 as primary, with fallback
        self.model = config.settings.xai_model
        self.fallback_model = "grok-3"  # Stable fallback
        self.temperature = config.settings.xai_temperature
        self.max_tokens = config.settings.xai_max_tokens
        
        logger.info("xAI client initialized", model=self.model, fallback=self.fallback_model)
    
    @retry_api_call(max_attempts=3)
    def analyze_patterns(
        self,
        tool_name: str,
        patterns: List[Dict[str, Any]],
        reviews: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze complaint patterns and identify top pain points
        
        Args:
            tool_name: Name of the tool being analyzed
            patterns: List of extracted patterns
            reviews: List of review dictionaries
            
        Returns:
            Dictionary with top_patterns key containing analysis results
        """
        if not patterns:
            logger.warning("No patterns provided for analysis", tool_name=tool_name)
            return {"top_patterns": []}
        
        # Sanitize tool name
        tool_name = InputValidator.sanitize_string(tool_name, max_length=100)
        
        prompt = f"""You are analyzing 1-2 star reviews for {tool_name}, a B2B SaaS tool.

Found {len(patterns)} complaint patterns from {len(reviews)} reviews.

Patterns identified:
{self._format_patterns(patterns)}

Context: Current date is December 2025. Focus on B2B trends and market dynamics from 2025.

Task: Identify the TOP 3-5 pain patterns (highest frequency + highest impact on workflows/core use).

For each top pattern, provide:
1. Pattern name (1 sentence)
2. Frequency count
3. Why it's high-impact (affects workflows/core use)
4. Example complaint snippet
5. Feasibility score (1-10): How feasible is it to build a solution?
6. Market size score (1-10): How large is the addressable market?
7. Confidence score (1-10): How confident are you in this pattern?

Consider:
- Alignment with B2B SaaS trends from 2025
- Actionability for product development
- Market validation potential
- Technical feasibility

Format as JSON with idea scores (feasibility 1-10, market_size 1-10, confidence 1-10):
{{
    "top_patterns": [
        {{
            "name": "...",
            "frequency": X,
            "impact_reason": "...",
            "example": "...",
            "feasibility_score": 7,
            "market_size_score": 8,
            "confidence_score": 9
        }}
    ]
}}
"""
        
        # Get circuit breaker for xAI API (extended timeout to 30s as per plan)
        breaker = get_circuit_breaker(
            "xai_api",
            failure_threshold=5,
            timeout=30,  # Updated to 30s as per Phase 1 plan
            expected_exception=(APIError, RateLimitError, APIConnectionError)
        )
        
        def _make_api_call(use_fallback=False):
            """Make API call wrapped in circuit breaker with fallback"""
            model_to_use = self.fallback_model if use_fallback else self.model
            return self.client.chat.completions.create(
                model=model_to_use,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
        
        try:
            logger.info("Analyzing patterns", tool_name=tool_name, pattern_count=len(patterns))
            
            # Use circuit breaker to protect API call
            try:
                response = breaker.call(_make_api_call)
            except Exception as e:
                # If primary model fails, try fallback
                if "404" in str(e) or "not found" in str(e).lower():
                    logger.warning("Primary model not available, using fallback", model=self.model, fallback=self.fallback_model)
                    response = breaker.call(lambda: _make_api_call(use_fallback=True))
                else:
                    raise
            
            result_text = response.choices[0].message.content
            
            if not result_text:
                raise ValueError("Empty response from API")
            
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                logger.info("Pattern analysis complete", tool_name=tool_name)
                return result
            else:
                # Fallback: return structured text
                logger.warning("Could not parse JSON, using fallback", tool_name=tool_name)
                return {"top_patterns": self._parse_text_response(result_text)}
                
        except RateLimitError as e:
            logger.error("Rate limit exceeded", error=str(e))
            raise RuntimeError("API rate limit exceeded. Please try again later.") from e
        except APIConnectionError as e:
            logger.error("API connection error", error=str(e))
            raise RuntimeError("Failed to connect to API. Please check your internet connection.") from e
        except APIError as e:
            logger.error("API error", error=str(e), status_code=getattr(e, 'status_code', None))
            raise RuntimeError(f"API error: {str(e)}") from e
        except json.JSONDecodeError as e:
            logger.error("JSON decode error", error=str(e))
            # Fallback: return top patterns by frequency
            return self._fallback_analysis(patterns)
        except Exception as e:
            logger.error("Unexpected error in pattern analysis", error=str(e), exc_info=True)
            return self._fallback_analysis(patterns)
    
    @retry_api_call(max_attempts=3)
    def generate_product_ideas(
        self,
        tool_name: str,
        top_patterns: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate product ideas for each top pattern
        
        Args:
            tool_name: Name of the tool
            top_patterns: List of top pain patterns
            
        Returns:
            List of product idea dictionaries grouped by pattern
        """
        if not top_patterns:
            logger.warning("No patterns provided for idea generation", tool_name=tool_name)
            return []
        
        tool_name = InputValidator.sanitize_string(tool_name, max_length=100)
        
        prompt = f"""You are generating B2B SaaS product ideas based on complaints about {tool_name}.

Top pain patterns:
{self._format_top_patterns(top_patterns)}

Context: Current date is December 2025. Generate ideas aligned with B2B SaaS trends from 2025.
Consider market data, competitive landscape, and recent innovations in the space.

Task: For each pattern, generate 3 novel product ideas:
1. Standalone SaaS app
2. Browser plugin/extension
3. No-code integration (Zapier alternative)

For each idea, provide:
- App Name: [Catchy Name]
- Value Prop: [1-sentence fix]
- Target: [Complainers of {tool_name}]
- MVP Scope: [3 core features]
- Monetization: [$X/mo per user]
- Feasibility Score (1-10): Based on technical complexity and market readiness
- Market Size Score (1-10): Based on addressable market and demand
- Confidence Score (1-10): Your confidence in this idea's potential
- Estimated TAM: Market size estimate

Consider:
- Alignment with 2025 B2B trends (AI integration, automation, collaboration tools)
- Differentiation from existing solutions
- Technical feasibility for solo founder or small team
- Market validation potential

Format as JSON with idea scores (feasibility 1-10, market_size 1-10, confidence 1-10, estimated_tam):
{{
    "ideas": [
        {{
            "pattern": "...",
            "ideas": [
                {{
                    "name": "...",
                    "value_prop": "...",
                    "target": "...",
                    "mvp_scope": "...",
                    "monetization": "...",
                    "type": "standalone|plugin|integration",
                    "feasibility_score": 7,
                    "market_size_score": 8,
                    "confidence_score": 9,
                    "estimated_tam": "$10M+"
                }}
            ]
        }}
    ]
}}
"""
        
        try:
            logger.info("Generating product ideas", tool_name=tool_name, pattern_count=len(top_patterns))
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,  # Higher temperature for creativity
                max_tokens=self.max_tokens
            )
            
            result_text = response.choices[0].message.content
            
            if not result_text:
                raise ValueError("Empty response from API")
            
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                ideas = result.get("ideas", [])
                logger.info("Product ideas generated", tool_name=tool_name, idea_count=len(ideas))
                return ideas
            else:
                logger.warning("Could not parse JSON for ideas", tool_name=tool_name)
                return self._parse_ideas_text(result_text)
                
        except RateLimitError as e:
            logger.error("Rate limit exceeded", error=str(e))
            raise RuntimeError("API rate limit exceeded. Please try again later.") from e
        except APIConnectionError as e:
            logger.error("API connection error", error=str(e))
            raise RuntimeError("Failed to connect to API. Please check your internet connection.") from e
        except APIError as e:
            logger.error("API error", error=str(e))
            raise RuntimeError(f"API error: {str(e)}") from e
        except Exception as e:
            logger.error("Error generating ideas", error=str(e), exc_info=True)
            return []
    
    @retry_api_call(max_attempts=3)
    def generate_roadmap(self, top_idea: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate 4-week solo founder roadmap for top idea
        
        Args:
            top_idea: Product idea dictionary
            
        Returns:
            Dictionary with week1-week4 keys containing roadmap details
        """
        prompt = f"""Create a detailed 4-week solo founder roadmap for this product idea:

{self._format_idea(top_idea)}

Follow this template:
- Week 1: Validate (Goal: 7/10 say "Yes, I'd pay $X/mo")
- Week 2: Build MVP (Landing page + waitlist; 3 screens: Pain, Solution Demo, Signup)
- Week 3: Launch (100 visitors; 10 signups goal)
- Week 4: Iterate (Collect 5 feedbacks; implement top 2 changes)

Provide specific, actionable steps for each week.

Format as JSON:
{{
    "week1": {{
        "goal": "...",
        "tasks": ["...", "..."]
    }},
    "week2": {{...}},
    "week3": {{...}},
    "week4": {{...}}
}}
"""
        
        try:
            logger.info("Generating roadmap", idea_name=top_idea.get("name", "Unknown"))
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=self.max_tokens
            )
            
            result_text = response.choices[0].message.content
            
            if not result_text:
                raise ValueError("Empty response from API")
            
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                roadmap = json.loads(json_match.group())
                logger.info("Roadmap generated successfully")
                return roadmap
            else:
                logger.warning("Could not parse JSON for roadmap")
                return self._parse_roadmap_text(result_text)
                
        except RateLimitError as e:
            logger.error("Rate limit exceeded", error=str(e))
            raise RuntimeError("API rate limit exceeded. Please try again later.") from e
        except APIConnectionError as e:
            logger.error("API connection error", error=str(e))
            raise RuntimeError("Failed to connect to API. Please check your internet connection.") from e
        except APIError as e:
            logger.error("API error", error=str(e))
            raise RuntimeError(f"API error: {str(e)}") from e
        except Exception as e:
            logger.error("Error generating roadmap", error=str(e), exc_info=True)
            return self._default_roadmap()
    
    def _format_patterns(self, patterns: List[Dict[str, Any]]) -> str:
        """Format patterns for prompt"""
        return "\n".join([
            f"- {p.get('description', 'Unknown')} (Frequency: {p.get('frequency', 0)})"
            for p in patterns
        ])
    
    def _format_top_patterns(self, patterns: List[Dict[str, Any]]) -> str:
        """Format top patterns for prompt"""
        return "\n".join([
            f"{i+1}. {p.get('name', 'Unknown')} (Frequency: {p.get('frequency', 0)})\n"
            f"   Impact: {p.get('impact_reason', 'N/A')}\n"
            f"   Example: {(p.get('example', 'N/A') or 'N/A')[:150]}"
            for i, p in enumerate(patterns)
        ])
    
    def _format_idea(self, idea: Dict[str, Any]) -> str:
        """Format idea for prompt"""
        return f"""
Name: {idea.get('name', 'N/A')}
Value Prop: {idea.get('value_prop', 'N/A')}
Target: {idea.get('target', 'N/A')}
MVP Scope: {idea.get('mvp_scope', 'N/A')}
Monetization: {idea.get('monetization', 'N/A')}
"""
    
    def _fallback_analysis(self, patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback analysis when API fails"""
        return {
            "top_patterns": [
                {
                    "name": p.get("description", "Unknown pattern"),
                    "frequency": p.get("frequency", 0),
                    "impact_reason": "High frequency complaint",
                    "example": (
                        p.get("reviews", [{}])[0].get("text", "")[:200]
                        if p.get("reviews") and len(p.get("reviews", [])) > 0
                        else ""
                    )
                }
                for p in patterns[:5]
            ]
        }
    
    def _parse_text_response(self, text: str) -> List[Dict[str, Any]]:
        """Fallback parser for text responses"""
        # Simple parsing logic - could be enhanced
        return []
    
    def _parse_ideas_text(self, text: str) -> List[Dict[str, Any]]:
        """Fallback parser for ideas text"""
        return []
    
    def _parse_roadmap_text(self, text: str) -> Dict[str, Any]:
        """Fallback parser for roadmap text"""
        return self._default_roadmap()
    
    def _default_roadmap(self) -> Dict[str, Any]:
        """Default roadmap template"""
        return {
            "week1": {
                "goal": "Validate demand",
                "tasks": [
                    "Find 10 potential customers",
                    "Send survey",
                    "Analyze responses"
                ]
            },
            "week2": {
                "goal": "Build MVP",
                "tasks": [
                    "Create landing page",
                    "Set up waitlist",
                    "Build core features"
                ]
            },
            "week3": {
                "goal": "Launch",
                "tasks": [
                    "Post to Reddit/HN",
                    "Email leads",
                    "Monitor feedback"
                ]
            },
            "week4": {
                "goal": "Iterate",
                "tasks": [
                    "Collect feedback",
                    "Implement top changes",
                    "Plan next iteration"
                ]
            }
        }

"""xAI Grok API client for analysis and idea generation"""

from openai import OpenAI
from typing import List, Dict, Optional
import json
import re
import config


class XAIClient:
    """Client for xAI Grok API"""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url=config.XAI_BASE_URL
        )
        self.model = config.XAI_MODEL
    
    def analyze_patterns(self, tool_name: str, patterns: List[Dict], reviews: List[Dict]) -> Dict:
        """
        Analyze complaint patterns and identify top pain points
        Returns structured analysis
        """
        prompt = f"""You are analyzing 1-2 star reviews for {tool_name}, a B2B SaaS tool.

Found {len(patterns)} complaint patterns from {len(reviews)} reviews.

Patterns identified:
{self._format_patterns(patterns)}

Task: Identify the TOP 3-5 pain patterns (highest frequency + highest impact on workflows/core use).

For each top pattern, provide:
1. Pattern name (1 sentence)
2. Frequency count
3. Why it's high-impact (affects workflows/core use)
4. Example complaint snippet

Format as JSON:
{{
    "top_patterns": [
        {{
            "name": "...",
            "frequency": X,
            "impact_reason": "...",
            "example": "..."
        }}
    ]
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content
            # Try to extract JSON from response
            # Find JSON block
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback: return structured text
                return {"top_patterns": self._parse_text_response(result_text)}
                
        except Exception as e:
            print(f"Error in xAI analysis: {str(e)}")
            # Fallback: return top patterns by frequency
            return {
                "top_patterns": [
                    {
                        "name": p["description"],
                        "frequency": p["frequency"],
                        "impact_reason": "High frequency complaint",
                        "example": p["reviews"][0]["text"][:200] if p["reviews"] else ""
                    }
                    for p in patterns[:5]
                ]
            }
    
    def generate_product_ideas(self, tool_name: str, top_patterns: List[Dict]) -> List[Dict]:
        """
        Generate product ideas for each top pattern
        Returns list of product ideas
        """
        prompt = f"""You are generating B2B SaaS product ideas based on complaints about {tool_name}.

Top pain patterns:
{self._format_top_patterns(top_patterns)}

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

Format as JSON:
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
                    "type": "standalone|plugin|integration"
                }}
            ]
        }}
    ]
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            result_text = response.choices[0].message.content
            
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group()).get("ideas", [])
            else:
                return self._parse_ideas_text(result_text)
                
        except Exception as e:
            print(f"Error generating ideas: {str(e)}")
            return []
    
    def generate_roadmap(self, top_idea: Dict) -> Dict:
        """
        Generate 4-week solo founder roadmap for top idea
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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5
            )
            
            result_text = response.choices[0].message.content
            
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return self._parse_roadmap_text(result_text)
                
        except Exception as e:
            print(f"Error generating roadmap: {str(e)}")
            return {
                "week1": {"goal": "Validate demand", "tasks": ["Find 10 potential customers", "Send survey"]},
                "week2": {"goal": "Build MVP", "tasks": ["Create landing page", "Set up waitlist"]},
                "week3": {"goal": "Launch", "tasks": ["Post to Reddit/HN", "Email leads"]},
                "week4": {"goal": "Iterate", "tasks": ["Collect feedback", "Implement changes"]}
            }
    
    def _format_patterns(self, patterns: List[Dict]) -> str:
        """Format patterns for prompt"""
        return "\n".join([
            f"- {p['description']} (Frequency: {p['frequency']})"
            for p in patterns
        ])
    
    def _format_top_patterns(self, patterns: List[Dict]) -> str:
        """Format top patterns for prompt"""
        return "\n".join([
            f"{i+1}. {p['name']} (Frequency: {p['frequency']})\n   Impact: {p.get('impact_reason', 'N/A')}\n   Example: {p.get('example', 'N/A')[:150]}"
            for i, p in enumerate(patterns)
        ])
    
    def _format_idea(self, idea: Dict) -> str:
        """Format idea for prompt"""
        return f"""
Name: {idea.get('name', 'N/A')}
Value Prop: {idea.get('value_prop', 'N/A')}
Target: {idea.get('target', 'N/A')}
MVP Scope: {idea.get('mvp_scope', 'N/A')}
Monetization: {idea.get('monetization', 'N/A')}
"""
    
    def _parse_text_response(self, text: str) -> List[Dict]:
        """Fallback parser for text responses"""
        # Simple parsing logic
        return []
    
    def _parse_ideas_text(self, text: str) -> List[Dict]:
        """Fallback parser for ideas text"""
        return []
    
    def _parse_roadmap_text(self, text: str) -> Dict:
        """Fallback parser for roadmap text"""
        return {
            "week1": {"goal": "Validate", "tasks": []},
            "week2": {"goal": "Build MVP", "tasks": []},
            "week3": {"goal": "Launch", "tasks": []},
            "week4": {"goal": "Iterate", "tasks": []}
        }

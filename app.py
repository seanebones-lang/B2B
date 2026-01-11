"""Main Streamlit application for B2B Complaint Analyzer"""

import streamlit as st
import pandas as pd
from typing import List, Dict
import json
import time

from scraper import G2Scraper, CapterraScraper
from analyzer import PatternExtractor, XAIClient
import config

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
if "api_key_configured" not in st.session_state:
    st.session_state.api_key_configured = False


def main():
    st.title("🔍 B2B Complaint-Driven Product Ideation")
    st.markdown("Extract unmet needs from 1-2 star reviews and generate actionable product ideas")
    
    # Sidebar
    with st.sidebar:
        # API Key Section - Prominent and dedicated
        st.header("🔑 xAI API Key")
        st.markdown("""
        <div style='background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>
        <small>Enter your xAI API key to enable AI-powered analysis. 
        Get your key from <a href='https://x.ai/api' target='_blank'>x.ai/api</a></small>
        </div>
        """, unsafe_allow_html=True)
        
        api_key = st.text_input(
            "API Key",
            type="password",
            help="Enter your xAI API key (starts with 'xai-' or similar)",
            placeholder="xai-your-api-key-here",
            key="xai_api_key_input"
        )
        
        # API Key Status
        if api_key:
            try:
                st.session_state.xai_client = XAIClient(api_key)
                st.success("✅ API key configured and validated")
                st.session_state.api_key_configured = True
            except ValueError as e:
                st.error(f"❌ Invalid API key format: {str(e)}")
                st.session_state.api_key_configured = False
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.session_state.api_key_configured = False
        else:
            st.info("ℹ️ Please enter your xAI API key above")
            st.session_state.api_key_configured = False
        
        st.divider()
        
        st.header("⚙️ Configuration")
        
        # Tool selection
        st.header("📊 Select Tools")
        tool_names = [tool["name"] for tool in config.B2B_TOOLS]
        selected_tools = st.multiselect(
            "Choose B2B tools to analyze",
            tool_names,
            default=tool_names[:3] if len(tool_names) >= 3 else tool_names,
            help="Select 1-3 tools for best performance"
        )
        
        st.divider()
        
        # Run analysis button
        api_key_valid = st.session_state.get("api_key_configured", False)
        run_analysis = st.button(
            "🚀 Run Analysis",
            type="primary",
            use_container_width=True,
            disabled=not api_key_valid or not selected_tools
        )
        
        if not api_key_valid:
            st.warning("⚠️ API key required to run analysis")
        if not selected_tools:
            st.warning("⚠️ Please select at least one tool")
    
    # Main content area
    api_key_valid = st.session_state.get("api_key_configured", False)
    if run_analysis and api_key_valid and selected_tools:
        run_full_analysis(selected_tools)
    else:
        show_instructions()
    
    # Display results if available
    if st.session_state.analysis_results:
        display_results()


def show_instructions():
    """Show usage instructions"""
    st.markdown("""
    ### How to Use
    
    1. **Enter xAI API Key**: Use the sidebar (🔑 xAI API Key section) to enter your key from [x.ai/api](https://x.ai/api)
    2. **Select Tools**: Choose 1-3 B2B SaaS tools to analyze from the dropdown
    3. **Run Analysis**: Click the "🚀 Run Analysis" button to scrape reviews and generate insights
    
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


def run_full_analysis(selected_tools: List[str]):
    """Run complete analysis pipeline"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    all_results = {}
    total_steps = len(selected_tools) * 3 + 2  # 3 steps per tool + 2 final steps
    current_step = 0
    
    try:
        # Initialize multi-source scraper
        from scraper.multi_source_scraper import MultiSourceScraper
        multi_scraper = MultiSourceScraper()
        pattern_extractor = PatternExtractor()
        
        # Process each tool
        for tool_name in selected_tools:
            tool_config = next((t for t in config.B2B_TOOLS if t["name"] == tool_name), None)
            if not tool_config:
                continue
            
            status_text.text(f"📥 Scraping reviews for {tool_name} from multiple sources...")
            current_step += 1
            progress_bar.progress(current_step / total_steps)
            
            # Scrape from all sources with intelligent fallbacks
            try:
                reviews, sources_succeeded = multi_scraper.scrape_all_sources(
                    tool_name=tool_name,
                    tool_slug=tool_config.get("g2_slug"),
                    tool_id=tool_config.get("capterra_id"),
                    product_slug=tool_config.get("ph_slug"),
                    max_per_source=config.MAX_REVIEWS_PER_TOOL
                )
                
                if reviews:
                    st.success(f"✓ Found {len(reviews)} reviews from: {', '.join(sources_succeeded)}")
                else:
                    st.warning(f"⚠️ No reviews found from any source for {tool_name}")
            except Exception as e:
                st.error(f"❌ Error scraping {tool_name}: {str(e)}")
                reviews = []
            
            if not reviews:
                st.error(f"❌ No reviews found for {tool_name}. Skipping...")
                continue
            
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
                except Exception as e:
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
    
    # Sort by potential (simple heuristic: prioritize standalone apps)
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
                st.warning(f"Could not generate roadmap: {str(e)}")
        top_3.append(opp)
    
    return top_3


def display_results():
    """Display analysis results"""
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
    
    # Stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tools Analyzed", len(tool_results))
    with col2:
        total_reviews = sum(
            len(r["reviews"]) for r in tool_results.values()
        )
        st.metric("Total Reviews", total_reviews)
    with col3:
        st.metric("Top Opportunities", len(top_opportunities))
    
    # Top opportunities preview
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
        
        # Reviews count
        reviews = tool_data.get("reviews", [])
        pattern_results = tool_data.get("pattern_results", {})
        ai_analysis = tool_data.get("ai_analysis", {})
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Reviews Found", len(reviews))
        with col2:
            st.metric("Patterns Identified", len(pattern_results.get("patterns", [])))
        
        # Top patterns
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
        
        # AI analysis
        if ai_analysis.get("top_patterns"):
            st.subheader("AI Analysis - Top Patterns")
            for pattern in ai_analysis["top_patterns"][:3]:
                with st.expander(f"{pattern.get('name', 'Unknown')} (Frequency: {pattern.get('frequency', 0)})"):
                    st.write(f"**Impact:** {pattern.get('impact_reason', 'N/A')}")
                    st.write(f"**Example:** {pattern.get('example', 'N/A')}")
        
        # Product ideas
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
        
        # Roadmap
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

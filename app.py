"""Main Streamlit application for B2B Complaint Analyzer"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Optional
import json
import time

from scraper import G2Scraper, CapterraScraper
from analyzer import PatternExtractor, XAIClient
import config
from utils.logging import get_logger

logger = get_logger(__name__)

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
        
        # Date range filter (new 2025 feature)
        st.header("📅 Date Range Filter")
        date_from = st.date_input(
            "From Date",
            value=None,
            help="Filter reviews/complaints from this date onwards"
        )
        date_to = st.date_input(
            "To Date",
            value=None,
            help="Filter reviews/complaints up to this date"
        )
        
        st.divider()
        
        # User data upload (Phase 2 enhancement)
        st.header("📤 Upload Internal Data")
        uploaded_file = st.file_uploader(
            "Upload CSV/Excel with internal complaints",
            type=['csv', 'xlsx', 'xls'],
            help="Upload your internal complaint data to enhance analysis"
        )
        
        if uploaded_file is not None:
            try:
                # Clear old data first
                if "uploaded_data" in st.session_state:
                    del st.session_state.uploaded_data
                
                if uploaded_file.name.endswith('.csv'):
                    import pandas as pd
                    df = pd.read_csv(uploaded_file)
                    if len(df) > 0:
                        st.success(f"✅ Loaded {len(df)} rows from CSV")
                        st.session_state.uploaded_data = df.to_dict('records')
                    else:
                        st.warning("⚠️ CSV file is empty")
                elif uploaded_file.name.endswith(('.xlsx', '.xls')):
                    import pandas as pd
                    df = pd.read_excel(uploaded_file)
                    if len(df) > 0:
                        st.success(f"✅ Loaded {len(df)} rows from Excel")
                        st.session_state.uploaded_data = df.to_dict('records')
                    else:
                        st.warning("⚠️ Excel file is empty")
            except Exception as e:
                st.error(f"❌ Error loading file: {str(e)}")
                # Clear invalid data
                if "uploaded_data" in st.session_state:
                    del st.session_state.uploaded_data
        
        st.divider()
        
        # Run analysis button
        api_key_valid = st.session_state.get("api_key_configured", False)
        run_analysis = st.button(
            "🚀 Run Analysis",
            type="primary",
            disabled=not api_key_valid or not selected_tools
        )
        
        if not api_key_valid:
            st.warning("⚠️ API key required to run analysis")
        if not selected_tools:
            st.warning("⚠️ Please select at least one tool")
        
        # Store date filters in session state for access outside sidebar
        st.session_state.date_from = date_from
        st.session_state.date_to = date_to
    
    # Main content area
    api_key_valid = st.session_state.get("api_key_configured", False)
    date_from = st.session_state.get("date_from")
    date_to = st.session_state.get("date_to")
    
    if run_analysis and api_key_valid and selected_tools:
        date_from_str = date_from.isoformat() if date_from else None
        date_to_str = date_to.isoformat() if date_to else None
        run_full_analysis(selected_tools, date_from=date_from_str, date_to=date_to_str)
    else:
        show_instructions()
    
    # Auto-install Playwright browsers on first run
    if "playwright_installed" not in st.session_state:
        try:
            import subprocess
            result = subprocess.run(
                ['playwright', 'install', '--with-deps'],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                st.session_state.playwright_installed = True
                logger.info("Playwright browsers installed successfully")
        except Exception as e:
            logger.warning("Could not auto-install Playwright browsers", error=str(e))
            st.session_state.playwright_installed = False
    
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
    st.dataframe(tools_df, width='stretch', hide_index=True)


def run_full_analysis(selected_tools: List[str], date_from: Optional[str] = None, date_to: Optional[str] = None):
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
                    max_per_source=config.MAX_REVIEWS_PER_TOOL,
                    date_from=date_from,
                    date_to=date_to
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
            
            # Merge uploaded data if available (Phase 2 enhancement)
            uploaded_data = st.session_state.get("uploaded_data")
            if uploaded_data and isinstance(uploaded_data, list) and len(uploaded_data) > 0:
                uploaded_reviews = [
                    {
                        'text': row.get('text', row.get('complaint', row.get('review', ''))),
                        'rating': row.get('rating', 1),
                        'source': 'Internal Upload',
                        'date': row.get('date', ''),
                        'tool': tool_name
                    }
                    for row in uploaded_data
                    if isinstance(row, dict) and (row.get('text') or row.get('complaint') or row.get('review'))
                ]
                if uploaded_reviews:
                    reviews.extend(uploaded_reviews)
                    st.info(f"📤 Added {len(uploaded_reviews)} reviews from uploaded data")
            
            # Validate and filter reviews for quality (Phase 2 enhancement)
            if st.session_state.xai_client:
                status_text.text(f"✅ Validating review quality for {tool_name}...")
                from analyzer.data_validator import DataValidator
                validator = DataValidator(st.session_state.xai_client)
                
                # Filter by relevance
                reviews = validator.filter_reviews_by_relevance(reviews, tool_name, min_score=5)
                
                # Detect bias patterns
                bias_results = validator.detect_bias_patterns(reviews)
                if bias_results.get('bias_flags'):
                    st.warning(f"⚠️ Bias detected: {bias_results['recommendation']}")
            
            # Extract patterns with sentiment analysis
            status_text.text(f"🔍 Analyzing patterns for {tool_name}...")
            current_step += 1
            progress_bar.progress(current_step / total_steps)
            
            # Add sentiment analysis
            from analyzer.sentiment_analyzer import SentimentAnalyzer
            sentiment_analyzer = SentimentAnalyzer()
            reviews_with_sentiment = sentiment_analyzer.analyze_sentiment(reviews)
            
            pattern_results = pattern_extractor.extract_patterns(reviews_with_sentiment)
            
            # AI analysis with market validation
            if st.session_state.xai_client:
                status_text.text(f"🤖 AI analysis for {tool_name}...")
                current_step += 1
                progress_bar.progress(current_step / total_steps)
                
                try:
                    ai_analysis = st.session_state.xai_client.analyze_patterns(
                        tool_name,
                        pattern_results.get("patterns", []),
                        reviews
                    )
                    
                    # Generate product ideas
                    if ai_analysis.get("top_patterns"):
                        ideas = st.session_state.xai_client.generate_product_ideas(
                            tool_name,
                            ai_analysis["top_patterns"]
                        )
                        ai_analysis["product_ideas"] = ideas
                        
                        # Validate idea novelty (Phase 2 enhancement)
                        from analyzer.web_researcher import WebResearcher
                        researcher = WebResearcher()
                        
                        for idea_group in ideas:
                            for idea in idea_group.get("ideas", []):
                                idea_name = idea.get("name", "")
                                idea_desc = idea.get("value_prop", "")
                                
                                if idea_name:
                                    novelty = researcher.validate_idea_novelty(idea_name, idea_desc)
                                    idea["novelty_validation"] = novelty
                                    idea["novelty_score"] = novelty.get("novelty_score", 5)
                        
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
        0 if x.get("idea", {}).get("type") == "standalone" else 1,
        -len(x.get("idea", {}).get("name", ""))
    ))
    
    # Generate roadmaps for top 3
    top_3 = []
    for opp in opportunities[:3]:
        if st.session_state.xai_client and opp.get("idea"):
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
    
    # Export buttons (Phase 2: Added CSV/PDF)
    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("📥 Export as Markdown"):
            export_markdown(results)
    with col2:
        if st.button("📊 Export as JSON"):
            export_json(results)
    with col3:
        if st.button("📈 Export as CSV"):
            export_csv(results)
    with col4:
        if st.button("📄 Export as PDF"):
            export_pdf(results)


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
            idea = opp.get('idea', {})
            with st.expander(f"{i}. {idea.get('name', 'Unknown')} - {opp.get('tool', 'N/A')}"):
                st.write(f"**Pattern:** {opp.get('pattern', 'N/A')}")
                st.write(f"**Value Prop:** {idea.get('value_prop', 'N/A')}")
                st.write(f"**Target:** {idea.get('target', 'N/A')}")
                st.write(f"**MVP Scope:** {idea.get('mvp_scope', 'N/A')}")
                st.write(f"**Monetization:** {idea.get('monetization', 'N/A')}")


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
        patterns_list = pattern_results.get("patterns", [])
        if patterns_list:
            st.subheader("Complaint Patterns")
            patterns_df = pd.DataFrame([
                {
                    "Pattern": p.get("description", "Unknown"),
                    "Frequency": p.get("frequency", 0),
                    "Percentage": f"{p.get('frequency', 0) / len(reviews) * 100:.1f}%" if reviews else "0%"
                }
                for p in patterns_list[:5]
            ])
            st.dataframe(patterns_df, width='stretch', hide_index=True)
        
        # AI analysis
        if ai_analysis.get("top_patterns"):
            st.subheader("AI Analysis - Top Patterns")
            for pattern in ai_analysis["top_patterns"][:3]:
                with st.expander(f"{pattern.get('name', 'Unknown')} (Frequency: {pattern.get('frequency', 0)})"):
                    st.write(f"**Impact:** {pattern.get('impact_reason', 'N/A')}")
                    st.write(f"**Example:** {pattern.get('example', 'N/A')}")
        
        # Product ideas with quality scores
        if ai_analysis.get("product_ideas"):
            st.subheader("Product Ideas")
            for idea_group in ai_analysis["product_ideas"]:
                st.write(f"**Pattern:** {idea_group.get('pattern', 'Unknown')}")
                for idea in idea_group.get("ideas", []):
                    with st.expander(idea.get("name", "Unknown Idea")):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Feasibility", idea.get('feasibility_score', 'N/A'), help="1-10 score")
                        with col2:
                            st.metric("Market Size", idea.get('market_size_score', 'N/A'), help="1-10 score")
                        with col3:
                            st.metric("Confidence", idea.get('confidence_score', 'N/A'), help="1-10 score")
                        
                        # Novelty validation
                        if idea.get("novelty_validation"):
                            novelty = idea["novelty_validation"]
                            st.write(f"**Novelty Score:** {novelty.get('novelty_score', 'N/A')}/10")
                            st.write(f"**Novelty:** {novelty.get('recommendation', 'N/A')}")
                            if novelty.get('similar_products_found', 0) > 0:
                                st.info(f"Found {novelty['similar_products_found']} similar products in market")
                        
                        st.write(f"**Type:** {idea.get('type', 'N/A')}")
                        st.write(f"**Value Prop:** {idea.get('value_prop', 'N/A')}")
                        st.write(f"**Target:** {idea.get('target', 'N/A')}")
                        st.write(f"**MVP Scope:** {idea.get('mvp_scope', 'N/A')}")
                        st.write(f"**Monetization:** {idea.get('monetization', 'N/A')}")
                        st.write(f"**Estimated TAM:** {idea.get('estimated_tam', 'N/A')}")
                        
                        # Quality rubric scoring (Phase 2 enhancement)
                        quality_score = None
                        try:
                            from analyzer.quality_rubric import QualityRubric
                            rubric = QualityRubric()
                            quality_score = rubric.score_idea(
                                idea,
                                novelty_score=idea.get('novelty_score'),
                                feasibility_score=idea.get('feasibility_score'),
                                market_size_score=idea.get('market_size_score')
                            )
                        except Exception as e:
                            logger.warning("Quality scoring failed", error=str(e))
                            quality_score = {
                                'overall_score': 0.5,
                                'overall_rating': 'Unable to assess',
                                'breakdown': {}
                            }
                        
                        if quality_score:
                            st.divider()
                            st.write("**Quality Assessment:**")
                            overall_score = quality_score.get('overall_score', 0.5)
                            overall_rating = quality_score.get('overall_rating', 'N/A')
                            st.metric("Overall Score", f"{overall_score:.2f}", overall_rating)
                            
                            # Show breakdown
                            if quality_score.get('breakdown'):
                                with st.expander("Score Breakdown"):
                                    for dim, data in quality_score['breakdown'].items():
                                        st.write(f"**{dim.replace('_', ' ').title()}:** {data['score']:.2f} (weight: {data['weight']:.0%})")
                            
                            # Recommendations
                            try:
                                from analyzer.quality_rubric import QualityRubric
                                rubric = QualityRubric()
                                recommendations = rubric.get_recommendations(quality_score)
                                if recommendations:
                                    st.info("**Recommendations:** " + " | ".join(recommendations))
                            except Exception as e:
                                logger.debug("Could not get recommendations", error=str(e))
                                pass
                        
                        # Human review section (Phase 2 enhancement)
                        st.divider()
                        st.write("**Your Rating:**")
                        default_rating = int(overall_score * 10) if quality_score and overall_score else 5
                        user_rating = st.slider(
                            "Rate this idea (1-10)",
                            min_value=1,
                            max_value=10,
                            value=default_rating,
                            key=f"rating_{idea.get('name', 'unknown')}"
                        )
                        user_feedback = st.text_area(
                            "Feedback (optional)",
                            key=f"feedback_{idea.get('name', 'unknown')}",
                            placeholder="Add your thoughts on this idea..."
                        )
                        if st.button("Save Rating", key=f"save_{idea.get('name', 'unknown')}"):
                            # Store feedback (could save to database)
                            idea['user_rating'] = user_rating
                            idea['user_feedback'] = user_feedback
                            st.success("Rating saved!")
        
        st.divider()


def display_top_opportunities(results: Dict):
    """Display top 3 opportunities with roadmaps"""
    top_opportunities = results.get("top_opportunities", [])
    
    if not top_opportunities:
        st.info("No opportunities generated. Run analysis with xAI API key configured.")
        return
    
    for i, opp in enumerate(top_opportunities[:3], 1):
        idea = opp.get('idea', {})
        st.header(f"Opportunity #{i}: {idea.get('name', 'Unknown')}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Tool:** {opp.get('tool', 'N/A')}")
            st.write(f"**Pattern:** {opp.get('pattern', 'N/A')}")
        with col2:
            st.write(f"**Type:** {idea.get('type', 'N/A')}")
            st.write(f"**Monetization:** {idea.get('monetization', 'N/A')}")
        
        st.write(f"**Value Proposition:** {idea.get('value_prop', 'N/A')}")
        st.write(f"**Target Audience:** {idea.get('target', 'N/A')}")
        st.write(f"**MVP Scope:** {idea.get('mvp_scope', 'N/A')}")
        
        # Roadmap
        roadmap = opp.get("roadmap")
        if roadmap:
            st.subheader("4-Week Solo Founder Roadmap")
            
            for week_num in ["week1", "week2", "week3", "week4"]:
                week_data = roadmap.get(week_num, {})
                if week_data:
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
        idea = opp.get('idea', {})
        md_content += f"### {i}. {idea.get('name', 'Unknown')}\n\n"
        md_content += f"**Pattern/Source:** {opp.get('pattern', 'N/A')} ({opp.get('tool', 'N/A')})\n\n"
        md_content += f"**Value Prop:** {idea.get('value_prop', 'N/A')}\n\n"
        md_content += f"**Target:** {idea.get('target', 'N/A')}\n\n"
        md_content += f"**MVP Scope:** {idea.get('mvp_scope', 'N/A')}\n\n"
        md_content += f"**Monetization:** {idea.get('monetization', 'N/A')}\n\n"
        
        roadmap = opp.get("roadmap")
        if roadmap:
            md_content += "**Roadmap:**\n\n"
            for week_num in ["week1", "week2", "week3", "week4"]:
                week_data = roadmap.get(week_num, {})
                if week_data:
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


def export_csv(results: Dict):
    """Export results as CSV (Phase 2 enhancement)"""
    import io
    
    tool_results = results.get("tool_results", {})
    top_opportunities = results.get("top_opportunities", [])
    
    # Create CSV content
    output = io.StringIO()
    
    # Write opportunities to CSV
    output.write("Tool,Pattern,Idea Name,Value Prop,Target,MVP Scope,Monetization,Type,Feasibility Score,Market Size Score,Estimated TAM\n")
    
    for opp in top_opportunities:
        idea = opp.get('idea', {})
        output.write(f'"{opp.get("tool", "")}",')
        output.write(f'"{opp.get("pattern", "")}",')
        output.write(f'"{idea.get("name", "")}",')
        output.write(f'"{idea.get("value_prop", "")}",')
        output.write(f'"{idea.get("target", "")}",')
        output.write(f'"{idea.get("mvp_scope", "")}",')
        output.write(f'"{idea.get("monetization", "")}",')
        output.write(f'"{idea.get("type", "")}",')
        output.write(f'{idea.get("feasibility_score", "")},')
        output.write(f'{idea.get("market_size_score", "")},')
        output.write(f'"{idea.get("estimated_tam", "")}"\n')
    
    csv_content = output.getvalue()
    output.close()
    
    st.download_button(
        "Download CSV",
        csv_content,
        file_name="b2b_ideas_report.csv",
        mime="text/csv"
    )


def export_pdf(results: Dict):
    """Export results as PDF (Phase 2 enhancement)"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        import io
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        story.append(Paragraph("B2B Complaint-Driven Product Ideas Report", styles['Title']))
        story.append(Spacer(1, 12))
        
        tool_results = results.get("tool_results", {})
        top_opportunities = results.get("top_opportunities", [])
        
        # Summary
        story.append(Paragraph(f"Tools Analyzed: {len(tool_results)}", styles['Normal']))
        story.append(Paragraph(f"Top Opportunities: {len(top_opportunities)}", styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Top opportunities
        story.append(Paragraph("Top 3 Opportunities", styles['Heading2']))
        for i, opp in enumerate(top_opportunities[:3], 1):
            idea = opp.get('idea', {})
            story.append(Paragraph(f"{i}. {idea.get('name', 'Unknown')}", styles['Heading3']))
            story.append(Paragraph(f"Tool: {opp.get('tool', 'N/A')}", styles['Normal']))
            story.append(Paragraph(f"Pattern: {opp.get('pattern', 'N/A')}", styles['Normal']))
            story.append(Paragraph(f"Value Prop: {idea.get('value_prop', 'N/A')}", styles['Normal']))
            story.append(Spacer(1, 12))
        
        doc.build(story)
        pdf_content = buffer.getvalue()
        buffer.close()
        
        st.download_button(
            "Download PDF",
            pdf_content,
            file_name="b2b_ideas_report.pdf",
            mime="application/pdf"
        )
    except ImportError:
        st.error("PDF export requires reportlab. Install with: pip install reportlab")
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")


if __name__ == "__main__":
    main()

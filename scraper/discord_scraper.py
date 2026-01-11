"""Discord scraper for tech servers and B2B discussions"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from utils.logging import get_logger

logger = get_logger(__name__)

# Try to import discord.py
try:
    import discord
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False
    logger.warning("discord.py not available. Install with: pip install discord.py")


class DiscordScraper:
    """Scraper for Discord tech servers and B2B discussions"""
    
    def __init__(self):
        """Initialize Discord scraper"""
        self.client = None
        logger.info("Discord scraper initialized")
    
    async def scrape_tech_servers(
        self,
        tool_name: str,
        max_messages: int = 50,
        server_ids: Optional[List[int]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Scrape Discord tech servers for complaints
        
        Args:
            tool_name: Name of the tool/product
            max_messages: Maximum number of messages to collect
            server_ids: List of Discord server IDs to search
            date_from: Filter messages from this date (ISO format)
            date_to: Filter messages up to this date (ISO format)
            
        Returns:
            List of complaint dictionaries
            
        Note:
            Requires Discord bot token and proper permissions. Add to Streamlit secrets:
            discord_token: your_bot_token
        """
        if not DISCORD_AVAILABLE:
            logger.warning("discord.py not available, skipping Discord scraping")
            return []
        
        complaints = []
        
        try:
            import streamlit as st
            discord_token = st.secrets.get("discord", {}).get("token") or None
        except:
            discord_token = None
        
        if not discord_token:
            logger.warning("Discord token not found, skipping Discord scraping")
            return []
        
        try:
            intents = discord.Intents.default()
            intents.message_content = True
            self.client = discord.Client(intents=intents)
            
            @self.client.event
            async def on_ready():
                logger.info("Discord client ready")
            
            # Search for messages containing tool name and complaint keywords
            complaint_keywords = ['problem', 'issue', 'bug', 'broken', 'disappointed',
                                'frustrated', 'terrible', 'awful', 'worst', 'hate',
                                'switching', 'alternative']
            
            # Note: Discord API requires proper bot setup and permissions
            # This is a placeholder implementation
            # For production, use Discord's search API or webhooks
            
            await self.client.close()
            
        except Exception as e:
            logger.error("Error scraping Discord", error=str(e))
        
        logger.info("Discord scraping complete", tool_name=tool_name, complaints_found=len(complaints))
        return complaints

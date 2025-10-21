"""Chat agent for conversational scraping interface."""

import json
import logging
from typing import List, Dict, Any, Optional, AsyncIterator
from anthropic import Anthropic
from sqlalchemy.orm import Session
from app.core.config import settings
from app.services.scraping_agent import ScrapingAgent
from app.services.web_scraper import WebScraperTool
from app.db.base import SessionLocal
from app.models.agent_prompt import AgentPrompt

logger = logging.getLogger(__name__)


class ChatAgent:
    """Conversational agent for web scraping with streaming support."""

    def __init__(self, anthropic_api_key: str, db: Optional[Session] = None):
        """
        Initialize the chat agent.

        Args:
            anthropic_api_key: Anthropic API key for Claude
            db: Optional database session (creates new one if not provided)
        """
        self.client = Anthropic(api_key=anthropic_api_key)
        self.model = "claude-sonnet-4-20250514"
        self.db = db
        self.scraping_agent = ScrapingAgent(anthropic_api_key=anthropic_api_key, db=db)

    def get_system_prompt(self) -> str:
        """
        Get the system prompt from the database.
        Always fetches fresh from DB to ensure real-time updates.

        Returns:
            System prompt text
        """
        db = self.db or SessionLocal()

        try:
            prompt_record = db.query(AgentPrompt).filter(
                AgentPrompt.agent_name == "chat_agent",
                AgentPrompt.is_active == True
            ).first()

            if prompt_record:
                logger.info(f"Loaded chat_agent prompt (updated: {prompt_record.updated_at})")
                logger.debug(f"Prompt preview: {prompt_record.system_prompt[:100]}...")
                return prompt_record.system_prompt
            else:
                logger.warning("No active prompt found for chat_agent, using fallback")
                return "You are a helpful assistant for web scraping."

        finally:
            if not self.db:
                db.close()

    def parse_intent(self, message: str, conversation_history: List[Dict]) -> Dict[str, Any]:
        """
        Get a response from Claude and detect if scraping is requested.

        Args:
            message: User's message
            conversation_history: Previous conversation messages

        Returns:
            Dictionary with response text and optional scraping action
        """
        # Get system prompt from database
        system_prompt = self.get_system_prompt()

        # Build conversation context
        history_text = ""
        for msg in conversation_history[-4:]:  # Last 4 messages for context
            role = "User" if msg["sender"] == "user" else "Assistant"
            history_text += f"\n{role}: {msg['text']}"

        user_prompt = f"""Previous conversation:{history_text}

Current user message: {message}"""

        # Define scraping tool
        tools = [
            {
                "name": "scrape_website",
                "description": "Scrape a website to extract company names and addresses. Use this when the user asks to scrape a website or find companies on a website.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The URL to scrape (must include http:// or https://)"
                        },
                        "max_depth": {
                            "type": "integer",
                            "description": "Maximum crawl depth (default: 2)",
                            "default": 2
                        },
                        "max_pages": {
                            "type": "integer",
                            "description": "Maximum number of pages to scrape (default: 20)",
                            "default": 20
                        }
                    },
                    "required": ["url"]
                }
            }
        ]

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                temperature=0.7,
                system=system_prompt,
                tools=tools,
                messages=[{"role": "user", "content": user_prompt}]
            )

            # Check if Claude wants to use the scraping tool
            if response.stop_reason == "tool_use":
                for content in response.content:
                    if content.type == "tool_use" and content.name == "scrape_website":
                        tool_input = content.input
                        logger.info(f"Scraping requested: {tool_input}")

                        # Extract text response if any
                        text_response = ""
                        for c in response.content:
                            if hasattr(c, 'text'):
                                text_response = c.text

                        return {
                            "action": "scrape",
                            "url": tool_input.get("url"),
                            "max_depth": tool_input.get("max_depth", 2),
                            "max_pages": tool_input.get("max_pages", 20),
                            "response": text_response or f"I'll scrape {tool_input.get('url')} for companies..."
                        }

            # Regular text response
            response_text = ""
            for content in response.content:
                if hasattr(content, 'text'):
                    response_text += content.text

            print(response_text)
            logger.info(f"Agent response: {response_text[:100]}...")

            return {
                "action": "info",
                "response": response_text
            }

        except Exception as e:
            logger.error(f"Error getting response: {str(e)}")
            return {
                "action": "error",
                "response": "Something went wrong. Please try again."
            }

    async def stream_scraping(
        self,
        url: str,
        max_depth: int,
        max_pages: int
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream scraping progress and results.

        Args:
            url: URL to scrape
            max_depth: Maximum crawl depth
            max_pages: Maximum pages to scrape

        Yields:
            Progress updates and final results
        """
        try:
            # Initial progress
            yield {
                "type": "progress",
                "message": f"Starting scrape of {url}..."
            }

            # Initialize scraper
            scraper = WebScraperTool(max_depth=max_depth, max_pages=max_pages)

            # Start crawling
            yield {
                "type": "progress",
                "message": "Crawling pages and extracting content..."
            }

            pages = scraper.crawl(url)
            pages_crawled = len(pages)

            yield {
                "type": "progress",
                "message": f"Crawled {pages_crawled} pages. Analyzing with AI..."
            }

            # Extract companies from each page
            all_companies = []

            for idx, (page_url, text_content) in enumerate(pages, 1):
                yield {
                    "type": "progress",
                    "message": f"Analyzing page {idx}/{pages_crawled}..."
                }

                companies = self.scraping_agent.extract_companies_from_text(
                    text_content,
                    page_url
                )
                all_companies.extend(companies)

                if companies:
                    yield {
                        "type": "progress",
                        "message": f"Found {len(all_companies)} companies so far..."
                    }

            # Deduplicate
            unique_companies = []
            seen = set()

            for company in all_companies:
                key = (
                    company.get("company_name", "").lower(),
                    company.get("address", "").lower()
                )
                if key not in seen and key[0] and key[1]:
                    seen.add(key)
                    unique_companies.append(company)

            # Final result
            yield {
                "type": "complete",
                "message": f"✅ Complete! Found {len(unique_companies)} companies.",
                "data": {
                    "companies": unique_companies,
                    "pages_crawled": pages_crawled,
                    "total_found": len(unique_companies)
                }
            }

        except Exception as e:
            logger.error(f"Error during streaming scrape: {str(e)}")
            yield {
                "type": "error",
                "message": f"Error: {str(e)}"
            }


def create_chat_agent() -> ChatAgent:
    """Create a chat agent instance with the API key from settings."""
    anthropic_api_key = getattr(settings, 'anthropic_api_key', None)

    if not anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in settings")

    return ChatAgent(anthropic_api_key=anthropic_api_key)

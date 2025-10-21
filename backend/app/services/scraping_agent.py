"""Claude-powered agent for extracting company information from web pages."""

import json
import logging
from typing import List, Dict, Any, Optional
from anthropic import Anthropic
from sqlalchemy.orm import Session
from app.core.config import settings
from app.services.web_scraper import WebScraperTool
from app.db.base import SessionLocal
from app.models.agent_prompt import AgentPrompt

logger = logging.getLogger(__name__)


class ScrapingAgent:
    """Agent that uses Claude to extract structured company information from web content."""

    def __init__(self, anthropic_api_key: str, db: Optional[Session] = None):
        """
        Initialize the scraping agent.

        Args:
            anthropic_api_key: Anthropic API key for Claude
            db: Optional database session (creates new one if not provided)
        """
        self.client = Anthropic(api_key=anthropic_api_key)
        self.model = "claude-sonnet-4-20250514"
        self.db = db

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
                AgentPrompt.agent_name == "scraping_agent",
                AgentPrompt.is_active == True
            ).first()

            if prompt_record:
                logger.info(f"Loaded scraping_agent prompt (updated: {prompt_record.updated_at})")
                logger.debug(f"Prompt preview: {prompt_record.system_prompt[:100]}...")
                return prompt_record.system_prompt
            else:
                logger.warning("No active prompt found for scraping_agent, using fallback")
                return "Extract company names and addresses from the provided text."

        finally:
            if not self.db:
                db.close()

    def extract_companies_from_text(self, text: str, source_url: str) -> List[Dict[str, str]]:
        """
        Use Claude to extract company names and addresses from text content.

        Args:
            text: Text content to analyze
            source_url: URL where the content was found

        Returns:
            List of dictionaries containing company information
        """
        # Limit text length to avoid token limits
        max_chars = 100000
        if len(text) > max_chars:
            text = text[:max_chars]

        # Get system prompt from database
        system_prompt = self.get_system_prompt()

        user_prompt = f"""Extract all company names and addresses from this text:

{text}

Remember to return only valid JSON in the specified format."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            # Extract the response text
            response_text = response.content[0].text

            # Parse JSON response
            companies = json.loads(response_text)

            # Add source URL to each company
            for company in companies:
                company["source_url"] = source_url

            logger.info(f"Extracted {len(companies)} companies from {source_url}")
            return companies

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response was: {response_text[:500]}")
            return []
        except Exception as e:
            logger.error(f"Error extracting companies: {str(e)}")
            return []

    def scrape_and_extract(
        self,
        start_url: str,
        max_depth: int = 2,
        max_pages: int = 20
    ) -> Dict[str, Any]:
        """
        Scrape a website and extract company information using Claude.

        Args:
            start_url: Starting URL to scrape
            max_depth: Maximum crawl depth
            max_pages: Maximum number of pages to scrape

        Returns:
            Dictionary containing results and metadata
        """
        logger.info(f"Starting scrape of {start_url} with max_depth={max_depth}")

        # Initialize web scraper
        scraper = WebScraperTool(max_depth=max_depth, max_pages=max_pages)

        # Crawl the website
        pages = scraper.crawl(start_url)

        logger.info(f"Crawled {len(pages)} pages")

        # Extract companies from each page
        all_companies = []
        pages_processed = 0

        for url, text_content in pages:
            logger.info(f"Processing page: {url}")
            companies = self.extract_companies_from_text(text_content, url)
            all_companies.extend(companies)
            pages_processed += 1

        # Deduplicate companies based on name and address
        unique_companies = []
        seen = set()

        for company in all_companies:
            key = (company.get("company_name", "").lower(), company.get("address", "").lower())
            if key not in seen and key[0] and key[1]:
                seen.add(key)
                unique_companies.append(company)

        logger.info(f"Found {len(unique_companies)} unique companies")

        return {
            "success": True,
            "start_url": start_url,
            "pages_crawled": pages_processed,
            "companies_found": len(unique_companies),
            "companies": unique_companies,
            "max_depth": max_depth
        }


def create_agent() -> ScrapingAgent:
    """Create a scraping agent instance with the API key from settings."""
    # Get API key from environment
    anthropic_api_key = getattr(settings, 'anthropic_api_key', None)

    if not anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in settings")

    return ScrapingAgent(anthropic_api_key=anthropic_api_key)

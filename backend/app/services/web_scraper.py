"""Web scraping service for extracting company information from URLs."""

import httpx
import re
from bs4 import BeautifulSoup
from typing import List, Set, Optional
from urllib.parse import urljoin, urlparse
import logging

logger = logging.getLogger(__name__)


class WebScraperTool:
    """Tool for scraping web pages and extracting company information."""

    def __init__(self, max_depth: int = 2, timeout: int = 10, max_pages: int = 20):
        """
        Initialize the web scraper.

        Args:
            max_depth: Maximum depth to crawl from the starting URL
            timeout: HTTP request timeout in seconds
            max_pages: Maximum number of pages to scrape
        """
        self.max_depth = max_depth
        self.timeout = timeout
        self.max_pages = max_pages
        self.visited_urls: Set[str] = set()
        self.results: List[dict] = []

    def scrape_url(self, url: str) -> str:
        """
        Fetch and return the HTML content of a URL.

        Args:
            url: The URL to scrape

        Returns:
            HTML content as string
        """
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                response = client.get(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                })
                response.raise_for_status()
                return response.text
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return ""

    def extract_links(self, html: str, base_url: str) -> List[str]:
        """
        Extract internal links from HTML content.

        Args:
            html: HTML content
            base_url: Base URL for resolving relative links

        Returns:
            List of absolute URLs
        """
        soup = BeautifulSoup(html, 'lxml')
        links = []
        base_domain = urlparse(base_url).netloc

        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)
            parsed = urlparse(absolute_url)

            # Only include links from the same domain
            if parsed.netloc == base_domain and absolute_url not in self.visited_urls:
                # Skip common non-content pages
                if not any(x in absolute_url.lower() for x in ['#', 'javascript:', 'mailto:', '.pdf', '.jpg', '.png']):
                    links.append(absolute_url)

        return links

    def extract_text_blocks(self, html: str) -> str:
        """
        Extract clean text content from HTML.

        Args:
            html: HTML content

        Returns:
            Cleaned text content
        """
        soup = BeautifulSoup(html, 'lxml')

        # Remove script and style elements
        for script in soup(['script', 'style', 'nav', 'footer', 'header']):
            script.decompose()

        # Get text and clean it up
        text = soup.get_text(separator=' ', strip=True)
        # Collapse multiple whitespaces
        text = re.sub(r'\s+', ' ', text)

        return text

    def crawl(self, start_url: str, current_depth: int = 0) -> List[str]:
        """
        Crawl website starting from the given URL.

        Args:
            start_url: Starting URL to crawl
            current_depth: Current crawl depth

        Returns:
            List of tuples containing (url, text_content)
        """
        if current_depth > self.max_depth or len(self.visited_urls) >= self.max_pages:
            return []

        if start_url in self.visited_urls:
            return []

        logger.info(f"Crawling {start_url} at depth {current_depth}")
        self.visited_urls.add(start_url)

        # Fetch and parse the page
        html = self.scrape_url(start_url)
        if not html:
            return []

        # Extract text content
        text_content = self.extract_text_blocks(html)

        # Store the page content
        pages = [(start_url, text_content)]

        # If we haven't reached max depth, crawl subpages
        if current_depth < self.max_depth:
            links = self.extract_links(html, start_url)

            for link in links[:5]:  # Limit to 5 links per page to avoid explosion
                if len(self.visited_urls) >= self.max_pages:
                    break
                subpages = self.crawl(link, current_depth + 1)
                pages.extend(subpages)

        return pages

    def reset(self):
        """Reset the scraper state for a new crawl."""
        self.visited_urls.clear()
        self.results.clear()

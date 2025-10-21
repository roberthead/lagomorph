"""Pydantic schemas for web scraping endpoints."""

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional


class CompanyInfo(BaseModel):
    """Schema for company information."""

    company_name: str = Field(..., description="Name of the company")
    address: str = Field(..., description="Physical address of the company")
    source_url: str = Field(..., description="URL where the information was found")


class ScrapeRequest(BaseModel):
    """Schema for scraping request."""

    url: str = Field(..., description="Starting URL to scrape", examples=["https://example.com"])
    max_depth: int = Field(default=2, ge=0, le=3, description="Maximum crawl depth (0-3)")
    max_pages: int = Field(default=20, ge=1, le=50, description="Maximum number of pages to scrape (1-50)")


class ScrapeResponse(BaseModel):
    """Schema for scraping response."""

    success: bool = Field(..., description="Whether the scraping was successful")
    start_url: str = Field(..., description="Starting URL that was scraped")
    pages_crawled: int = Field(..., description="Number of pages that were crawled")
    companies_found: int = Field(..., description="Number of companies found")
    companies: List[CompanyInfo] = Field(..., description="List of companies extracted")
    max_depth: int = Field(..., description="Maximum depth used for crawling")
    error: Optional[str] = Field(None, description="Error message if scraping failed")

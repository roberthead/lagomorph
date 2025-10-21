"""
Example script for testing the web scraping agent.

This script demonstrates how to use the scraping API to extract
company information from a website.
"""

import httpx
import json
import sys


def scrape_website(url: str, max_depth: int = 2, max_pages: int = 20):
    """
    Scrape a website and extract company information.

    Args:
        url: Starting URL to scrape
        max_depth: Maximum crawl depth (0-3)
        max_pages: Maximum pages to scrape (1-50)

    Returns:
        Dictionary containing scraping results
    """
    api_url = "http://127.0.0.1:8000/api/scraping/scrape"

    print(f"\n{'='*60}")
    print(f"Starting scrape of: {url}")
    print(f"Max depth: {max_depth}, Max pages: {max_pages}")
    print(f"{'='*60}\n")

    try:
        # Make the API request with extended timeout
        response = httpx.post(
            api_url,
            json={
                "url": url,
                "max_depth": max_depth,
                "max_pages": max_pages
            },
            timeout=300.0  # 5 minute timeout
        )

        response.raise_for_status()
        result = response.json()

        return result

    except httpx.HTTPStatusError as e:
        print(f"HTTP Error: {e.response.status_code}")
        print(f"Response: {e.response.text}")
        return None
    except httpx.TimeoutException:
        print("Request timed out. The website may be slow or the scraping is taking too long.")
        return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None


def print_results(result):
    """Print scraping results in a formatted way."""
    if not result:
        print("No results to display.")
        return

    print(f"\n{'='*60}")
    print("SCRAPING RESULTS")
    print(f"{'='*60}\n")

    print(f"Status: {'✓ Success' if result['success'] else '✗ Failed'}")
    print(f"Pages crawled: {result['pages_crawled']}")
    print(f"Companies found: {result['companies_found']}")
    print(f"Starting URL: {result['start_url']}")
    print(f"Max depth used: {result['max_depth']}")

    if result['companies_found'] > 0:
        print(f"\n{'='*60}")
        print("COMPANIES EXTRACTED")
        print(f"{'='*60}\n")

        for i, company in enumerate(result['companies'], 1):
            print(f"{i}. {company['company_name']}")
            print(f"   Address: {company['address']}")
            print(f"   Source: {company['source_url']}")
            print()

        # Save to file
        filename = "scraping_results.json"
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Results saved to: {filename}")
    else:
        print("\nNo companies with addresses were found on this website.")

    print(f"\n{'='*60}\n")


def main():
    """Main function."""
    # Check if URL is provided
    if len(sys.argv) < 2:
        print("Usage: python test_scraping.py <url> [max_depth] [max_pages]")
        print("\nExample:")
        print("  python test_scraping.py https://example.com 2 20")
        print("\nNote: Make sure the backend server is running on http://127.0.0.1:8000")
        sys.exit(1)

    url = sys.argv[1]
    max_depth = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    max_pages = int(sys.argv[3]) if len(sys.argv) > 3 else 20

    # Validate parameters
    if max_depth < 0 or max_depth > 3:
        print("Error: max_depth must be between 0 and 3")
        sys.exit(1)

    if max_pages < 1 or max_pages > 50:
        print("Error: max_pages must be between 1 and 50")
        sys.exit(1)

    # Test health endpoint first
    try:
        health_response = httpx.get("http://127.0.0.1:8000/api/scraping/health", timeout=5.0)
        if health_response.status_code != 200:
            print("Error: Scraping service is not healthy")
            sys.exit(1)
    except Exception as e:
        print(f"Error: Cannot connect to backend server at http://127.0.0.1:8000")
        print(f"Details: {str(e)}")
        print("\nPlease start the backend server:")
        print("  cd backend")
        print("  source venv/bin/activate")
        print("  uvicorn app.main:app --reload")
        sys.exit(1)

    # Perform scraping
    result = scrape_website(url, max_depth, max_pages)

    # Print results
    print_results(result)


if __name__ == "__main__":
    main()

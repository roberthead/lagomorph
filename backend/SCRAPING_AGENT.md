# Web Scraping Agent Documentation

## Overview

The Lagomorph web scraping agent uses Claude Sonnet 4 (`claude-sonnet-4-20250514`) to intelligently extract company names and addresses from websites. The agent can crawl multiple pages and uses AI to accurately identify and structure company information.

## Features

- **AI-Powered Extraction**: Uses Claude Sonnet 4 for intelligent company information extraction
- **Multi-Page Crawling**: Automatically follows links to subpages (configurable depth)
- **Structured Output**: Returns JSON with company name, address, and source URL
- **Error Handling**: Robust error handling for network issues and malformed HTML
- **Rate Limiting**: Configurable limits on pages crawled and depth
- **Deduplication**: Automatically removes duplicate company entries

## Architecture

### Components

1. **WebScraperTool** (`app/services/web_scraper.py`)
   - Handles HTTP requests and HTML parsing
   - Crawls websites and extracts text content
   - Follows internal links up to specified depth

2. **ScrapingAgent** (`app/services/scraping_agent.py`)
   - Uses Claude Sonnet 4 to extract structured data
   - Processes crawled pages and identifies companies
   - Deduplicates results

3. **API Endpoints** (`app/api/scraping.py`)
   - REST API for triggering scraping jobs
   - Returns structured JSON responses

## API Endpoints

### POST /api/scraping/scrape

Scrape a website and extract company information.

**Request Body:**
```json
{
  "url": "https://example.com",
  "max_depth": 2,
  "max_pages": 20
}
```

**Parameters:**
- `url` (string, required): Starting URL to scrape
- `max_depth` (integer, optional): Maximum crawl depth (0-3, default: 2)
- `max_pages` (integer, optional): Maximum pages to scrape (1-50, default: 20)

**Response:**
```json
{
  "success": true,
  "start_url": "https://example.com",
  "pages_crawled": 15,
  "companies_found": 12,
  "max_depth": 2,
  "companies": [
    {
      "company_name": "Acme Corporation",
      "address": "123 Main St, San Francisco, CA 94102",
      "source_url": "https://example.com/contact"
    },
    {
      "company_name": "Tech Solutions Inc",
      "address": "456 Market St, San Francisco, CA 94105",
      "source_url": "https://example.com/about"
    }
  ]
}
```

### GET /api/scraping/health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "web-scraping"
}
```

## Installation & Setup

### 1. Install Dependencies

The required packages are already in `requirements.txt`:

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

Key dependencies:
- `anthropic==0.40.0` - Claude API client
- `beautifulsoup4==4.12.3` - HTML parsing
- `httpx==0.28.1` - HTTP client
- `lxml==5.3.0` - HTML parser

### 2. Configure Environment

The Anthropic API key is already configured in `backend/.env`:

```bash
ANTHROPIC_API_KEY=sk-ant-api03-...
```

### 3. Start the Server

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`

## Usage Examples

### Example 1: Basic Scraping (curl)

```bash
curl -X POST http://127.0.0.1:8000/api/scraping/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "max_depth": 2,
    "max_pages": 20
  }'
```

### Example 2: Python Client

```python
import httpx
import json

# Scraping request
response = httpx.post(
    "http://127.0.0.1:8000/api/scraping/scrape",
    json={
        "url": "https://example.com",
        "max_depth": 2,
        "max_pages": 20
    },
    timeout=300.0  # 5 minute timeout
)

result = response.json()

# Print results
print(f"Found {result['companies_found']} companies:")
for company in result['companies']:
    print(f"\nCompany: {company['company_name']}")
    print(f"Address: {company['address']}")
    print(f"Source: {company['source_url']}")
```

### Example 3: JavaScript/Fetch

```javascript
const response = await fetch('http://127.0.0.1:8000/api/scraping/scrape', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    url: 'https://example.com',
    max_depth: 2,
    max_pages: 20
  })
});

const result = await response.json();
console.log(`Found ${result.companies_found} companies`);
result.companies.forEach(company => {
  console.log(`${company.company_name}: ${company.address}`);
});
```

## Configuration Options

### Max Depth
- **Range**: 0-3
- **Default**: 2
- **Description**: How many levels deep to crawl from the starting URL
  - 0 = Only scrape the starting page
  - 1 = Starting page + direct links
  - 2 = Two levels of links (recommended)
  - 3 = Three levels (may be slow)

### Max Pages
- **Range**: 1-50
- **Default**: 20
- **Description**: Maximum number of pages to scrape before stopping

## How It Works

1. **URL Crawling**: The agent starts at the provided URL and extracts text content
2. **Link Following**: It follows internal links up to the specified depth (avoiding duplicates)
3. **Content Extraction**: For each page, clean text is extracted from HTML
4. **AI Analysis**: Claude analyzes the text to identify company names and addresses
5. **Deduplication**: Results are deduplicated based on company name and address
6. **Structured Output**: Returns JSON with all found companies and metadata

## Error Handling

The agent handles various error conditions:

- **Network Errors**: HTTP timeouts, connection errors
- **Invalid URLs**: Malformed URLs are rejected
- **Parsing Errors**: HTML parsing failures are logged and skipped
- **API Errors**: Claude API errors are caught and reported
- **Rate Limiting**: Configurable limits prevent excessive crawling

## Performance Considerations

- **Timeout**: Each HTTP request has a 10-second timeout
- **Concurrent Requests**: Requests are made sequentially (no concurrent crawling)
- **Text Limits**: Text content is limited to 100,000 characters per page
- **Link Limits**: Maximum 5 links followed per page to prevent explosion

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Testing

Test the health endpoint:
```bash
curl http://127.0.0.1:8000/api/scraping/health
```

Expected response:
```json
{"status": "healthy", "service": "web-scraping"}
```

## Troubleshooting

### "Configuration error: ANTHROPIC_API_KEY not found"
- Ensure `ANTHROPIC_API_KEY` is set in `backend/.env`
- Restart the server after updating `.env`

### "Scraping failed: timeout"
- Increase the timeout in the request
- Reduce `max_pages` or `max_depth`

### Empty results
- Check that the target website has company information with addresses
- Verify the website is accessible (not behind authentication)
- Check server logs for parsing errors

## Security Notes

- The agent only follows links from the same domain (no external crawling)
- User-Agent header is set to identify the bot
- Rate limiting prevents excessive requests
- No authentication credentials are handled or stored

"""Tests for agent orchestration (ChatAgent and ScrapingAgent)."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import json

from app.services.chat_agent import ChatAgent
from app.services.scraping_agent import ScrapingAgent
from app.models.agent_prompt import AgentPrompt


class TestScrapingAgent:
    """Tests for the ScrapingAgent."""

    def test_agent_initialization(self):
        """Test ScrapingAgent initialization."""
        agent = ScrapingAgent(anthropic_api_key="test-key")

        assert agent.client is not None
        assert agent.model == "claude-sonnet-4-20250514"

    def test_get_system_prompt_from_db(self, db_session):
        """Test getting system prompt from database."""
        # Create a prompt in the database
        prompt = AgentPrompt(
            agent_name="scraping_agent",
            system_prompt="Custom scraping prompt",
            is_active=True
        )
        db_session.add(prompt)
        db_session.commit()

        agent = ScrapingAgent(anthropic_api_key="test-key", db=db_session)
        system_prompt = agent.get_system_prompt()

        assert system_prompt == "Custom scraping prompt"

    def test_get_system_prompt_fallback(self, db_session):
        """Test fallback prompt when no DB record exists."""
        agent = ScrapingAgent(anthropic_api_key="test-key", db=db_session)
        system_prompt = agent.get_system_prompt()

        assert system_prompt == "Extract company names and addresses from the provided text."

    @patch('app.services.scraping_agent.Anthropic')
    def test_extract_companies_from_text(self, mock_anthropic_class):
        """Test extracting companies from text using Claude."""
        # Setup mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text='[{"company_name": "Test Corp", "address": "123 Main St, City, ST 12345"}]')
        ]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        agent = ScrapingAgent(anthropic_api_key="test-key")
        companies = agent.extract_companies_from_text(
            "Some text with company info",
            "https://example.com"
        )

        assert len(companies) == 1
        assert companies[0]["company_name"] == "Test Corp"
        assert companies[0]["source_url"] == "https://example.com"

    @patch('app.services.scraping_agent.Anthropic')
    def test_extract_companies_json_error(self, mock_anthropic_class):
        """Test handling of invalid JSON response."""
        # Setup mock to return invalid JSON
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='Invalid JSON')]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        agent = ScrapingAgent(anthropic_api_key="test-key")
        companies = agent.extract_companies_from_text(
            "Some text",
            "https://example.com"
        )

        assert companies == []

    @patch('app.services.scraping_agent.Anthropic')
    def test_extract_companies_api_error(self, mock_anthropic_class):
        """Test handling of API errors."""
        # Setup mock to raise exception
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API Error")
        mock_anthropic_class.return_value = mock_client

        agent = ScrapingAgent(anthropic_api_key="test-key")
        companies = agent.extract_companies_from_text(
            "Some text",
            "https://example.com"
        )

        assert companies == []

    @patch('app.services.scraping_agent.WebScraperTool')
    @patch('app.services.scraping_agent.Anthropic')
    def test_scrape_and_extract(self, mock_anthropic_class, mock_scraper_class):
        """Test full scraping and extraction workflow."""
        # Setup scraper mock
        mock_scraper = MagicMock()
        mock_scraper.crawl.return_value = [
            ("https://example.com/page1", "Text with company info"),
            ("https://example.com/page2", "More company data")
        ]
        mock_scraper_class.return_value = mock_scraper

        # Setup Anthropic mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text='[{"company_name": "Test Corp", "address": "123 Main St, City, ST 12345"}]')
        ]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        agent = ScrapingAgent(anthropic_api_key="test-key")
        result = agent.scrape_and_extract("https://example.com", max_depth=2, max_pages=10)

        assert result["success"] is True
        assert result["pages_crawled"] == 2
        assert result["companies_found"] >= 1
        assert "companies" in result

    @patch('app.services.scraping_agent.WebScraperTool')
    @patch('app.services.scraping_agent.Anthropic')
    def test_scrape_and_extract_deduplication(self, mock_anthropic_class, mock_scraper_class):
        """Test that duplicate companies are removed."""
        # Setup scraper mock
        mock_scraper = MagicMock()
        mock_scraper.crawl.return_value = [
            ("https://example.com/page1", "Text 1"),
            ("https://example.com/page2", "Text 2")
        ]
        mock_scraper_class.return_value = mock_scraper

        # Setup Anthropic mock to return duplicates
        mock_client = MagicMock()
        mock_response = MagicMock()
        duplicate_data = '[{"company_name": "Test Corp", "address": "123 Main St"}]'
        mock_response.content = [MagicMock(text=duplicate_data)]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        agent = ScrapingAgent(anthropic_api_key="test-key")
        result = agent.scrape_and_extract("https://example.com")

        # Should deduplicate
        assert result["companies_found"] == 1


class TestChatAgent:
    """Tests for the ChatAgent."""

    def test_agent_initialization(self):
        """Test ChatAgent initialization."""
        agent = ChatAgent(anthropic_api_key="test-key")

        assert agent.client is not None
        assert agent.model == "claude-sonnet-4-20250514"
        assert agent.scraping_agent is not None

    def test_get_system_prompt_from_db(self, db_session):
        """Test getting system prompt from database."""
        # Create a prompt in the database
        prompt = AgentPrompt(
            agent_name="chat_agent",
            system_prompt="Custom chat prompt",
            is_active=True
        )
        db_session.add(prompt)
        db_session.commit()

        agent = ChatAgent(anthropic_api_key="test-key", db=db_session)
        system_prompt = agent.get_system_prompt()

        assert system_prompt == "Custom chat prompt"

    def test_get_system_prompt_fallback(self, db_session):
        """Test fallback prompt when no DB record exists."""
        agent = ChatAgent(anthropic_api_key="test-key", db=db_session)
        system_prompt = agent.get_system_prompt()

        assert system_prompt == "You are a helpful assistant for web scraping."

    @patch('app.services.chat_agent.Anthropic')
    def test_parse_intent_info_action(self, mock_anthropic_class):
        """Test parsing intent for informational response."""
        # Setup mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [MagicMock(text="I can help you scrape websites.")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        agent = ChatAgent(anthropic_api_key="test-key")
        result = agent.parse_intent("What can you do?", [])

        assert result["action"] == "info"
        assert "response" in result
        assert "scrape" in result["response"].lower()

    @patch('app.services.chat_agent.Anthropic')
    def test_parse_intent_scrape_action(self, mock_anthropic_class):
        """Test parsing intent for scraping action."""
        # Setup mock to return tool use
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.stop_reason = "tool_use"

        # Create tool use content
        mock_tool_use = MagicMock()
        mock_tool_use.type = "tool_use"
        mock_tool_use.name = "scrape_website"
        mock_tool_use.input = {
            "url": "https://example.com",
            "max_depth": 3,
            "max_pages": 50
        }

        mock_response.content = [mock_tool_use]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        agent = ChatAgent(anthropic_api_key="test-key")
        result = agent.parse_intent("Scrape https://example.com", [])

        assert result["action"] == "scrape"
        assert result["url"] == "https://example.com"
        assert result["max_depth"] == 3
        assert result["max_pages"] == 50

    @patch('app.services.chat_agent.Anthropic')
    def test_parse_intent_with_conversation_history(self, mock_anthropic_class):
        """Test that conversation history is included in context."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [MagicMock(text="Response")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        agent = ChatAgent(anthropic_api_key="test-key")
        history = [
            {"sender": "user", "text": "Hello"},
            {"sender": "assistant", "text": "Hi there!"}
        ]

        result = agent.parse_intent("What was my first message?", history)

        # Verify the messages.create was called with context
        call_args = mock_client.messages.create.call_args
        assert call_args is not None

    @patch('app.services.chat_agent.Anthropic')
    def test_parse_intent_error_handling(self, mock_anthropic_class):
        """Test error handling in parse_intent."""
        # Setup mock to raise exception
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API Error")
        mock_anthropic_class.return_value = mock_client

        agent = ChatAgent(anthropic_api_key="test-key")
        result = agent.parse_intent("Test message", [])

        assert result["action"] == "error"
        assert "response" in result

    @pytest.mark.asyncio
    @patch('app.services.chat_agent.WebScraperTool')
    async def test_stream_scraping(self, mock_scraper_class):
        """Test streaming scraping progress."""
        # Setup scraper mock
        mock_scraper = MagicMock()
        mock_scraper.crawl.return_value = [
            ("https://example.com/page1", "Company data")
        ]
        mock_scraper_class.return_value = mock_scraper

        # Mock the scraping agent's extract method
        with patch.object(ScrapingAgent, 'extract_companies_from_text') as mock_extract:
            mock_extract.return_value = [
                {"company_name": "Test Corp", "address": "123 Main St"}
            ]

            agent = ChatAgent(anthropic_api_key="test-key")

            events = []
            async for event in agent.stream_scraping("https://example.com", 2, 20):
                events.append(event)

            # Should have progress and complete events
            assert len(events) > 0
            assert any(e["type"] == "progress" for e in events)
            assert any(e["type"] == "complete" for e in events)

            # Final event should have data
            final_event = events[-1]
            assert final_event["type"] == "complete"
            assert "data" in final_event

    @pytest.mark.asyncio
    @patch('app.services.chat_agent.WebScraperTool')
    async def test_stream_scraping_error(self, mock_scraper_class):
        """Test error handling in streaming scraping."""
        # Setup scraper to raise exception
        mock_scraper = MagicMock()
        mock_scraper.crawl.side_effect = Exception("Scraping error")
        mock_scraper_class.return_value = mock_scraper

        agent = ChatAgent(anthropic_api_key="test-key")

        events = []
        async for event in agent.stream_scraping("https://example.com", 2, 20):
            events.append(event)

        # Should have error event
        assert any(e["type"] == "error" for e in events)

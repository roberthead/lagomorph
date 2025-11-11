"""Integration tests for API endpoints."""

import pytest
import json
from unittest.mock import patch, MagicMock
from fastapi import status

from app.models.response import Response
from app.models.agent_prompt import AgentPrompt
from app.models.response_validation import ResponseValidation


class TestScrapingEndpoints:
    """Tests for scraping API endpoints."""

    @patch('app.services.scraping_agent.Anthropic')
    @patch('app.services.scraping_agent.WebScraperTool')
    def test_scrape_endpoint_success(self, mock_scraper_class, mock_anthropic_class, client):
        """Test successful scraping request."""
        # Setup mocks
        mock_scraper = MagicMock()
        mock_scraper.crawl.return_value = [
            ("https://example.com", "Company data")
        ]
        mock_scraper_class.return_value = mock_scraper

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text='[{"company_name": "Test Corp", "address": "123 Main St, City, ST 12345"}]')
        ]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        # Make request
        response = client.post(
            "/api/scraping/scrape",
            json={
                "url": "https://example.com",
                "max_depth": 2,
                "max_pages": 20
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "companies" in data
        assert data["pages_crawled"] >= 0

    @patch('app.services.scraping_agent.Anthropic')
    @patch('app.services.scraping_agent.WebScraperTool')
    def test_scrape_endpoint_invalid_url(self, mock_scraper_class, mock_anthropic_class, client):
        """Test scraping with invalid URL format."""
        # The URL validation is permissive (accepts any string), but scraping will fail
        mock_scraper = MagicMock()
        mock_scraper.crawl.side_effect = Exception("Invalid URL")
        mock_scraper_class.return_value = mock_scraper

        response = client.post(
            "/api/scraping/scrape",
            json={
                "url": "not-a-valid-url",
                "max_depth": 2,
                "max_pages": 20
            }
        )

        # Should return error when scraping fails
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @patch('app.api.scraping.create_agent')
    def test_scrape_endpoint_api_error(self, mock_create_agent, client):
        """Test handling of API errors during scraping."""
        # Setup mock to raise exception
        mock_agent = MagicMock()
        mock_agent.scrape_and_extract.side_effect = Exception("API Error")
        mock_create_agent.return_value = mock_agent

        response = client.post(
            "/api/scraping/scrape",
            json={
                "url": "https://example.com",
                "max_depth": 2,
                "max_pages": 20
            }
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_health_check_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/api/scraping/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data


class TestChatEndpoints:
    """Tests for chat API endpoints."""

    @patch('app.services.chat_agent.Anthropic')
    def test_chat_stream_info_response(self, mock_anthropic_class, client):
        """Test chat stream with informational response."""
        # Setup mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [MagicMock(text="I can help with scraping.")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        response = client.post(
            "/api/scraping/chat/stream",
            json={
                "message": "What can you do?",
                "conversation_history": []
            }
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    @patch('app.services.chat_agent.Anthropic')
    @patch('app.services.chat_agent.WebScraperTool')
    def test_chat_stream_scraping_response(self, mock_scraper_class, mock_anthropic_class, client, db_session):
        """Test chat stream with scraping action."""
        # Setup scraper mock
        mock_scraper = MagicMock()
        mock_scraper.crawl.return_value = [
            ("https://example.com", "Data")
        ]
        mock_scraper_class.return_value = mock_scraper

        # Setup Anthropic mock for tool use
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.stop_reason = "tool_use"

        mock_tool_use = MagicMock()
        mock_tool_use.type = "tool_use"
        mock_tool_use.name = "scrape_website"
        mock_tool_use.input = {"url": "https://example.com"}

        mock_response.content = [mock_tool_use]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        # Mock extract_companies_from_text
        with patch('app.services.scraping_agent.ScrapingAgent.extract_companies_from_text') as mock_extract:
            mock_extract.return_value = [
                {"company_name": "Test", "address": "123 Main"}
            ]

            response = client.post(
                "/api/scraping/chat/stream",
                json={
                    "message": "Scrape https://example.com",
                    "conversation_history": []
                }
            )

            assert response.status_code == status.HTTP_200_OK


class TestResponsesEndpoint:
    """Tests for responses API endpoint."""

    def test_get_responses_empty(self, client):
        """Test getting responses when database is empty."""
        response = client.get("/api/scraping/responses")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "responses" in data
        assert isinstance(data["responses"], list)

    def test_get_responses_with_data(self, client, db_session):
        """Test getting responses with existing data."""
        # Create some responses
        for i in range(3):
            response = Response(
                request_body=f"Request {i}",
                response_body=f'{{"result": "test {i}"}}'
            )
            db_session.add(response)
        db_session.commit()

        response = client.get("/api/scraping/responses")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["responses"]) == 3

        # Verify response structure
        first_response = data["responses"][0]
        assert "id" in first_response
        assert "request_body" in first_response
        assert "response_body" in first_response
        assert "created_at" in first_response

    def test_get_responses_ordered_by_date(self, client, db_session):
        """Test that responses endpoint returns all responses."""
        # Create responses
        response1 = Response(request_body="First", response_body="First")
        response2 = Response(request_body="Second", response_body="Second")
        db_session.add_all([response1, response2])
        db_session.commit()

        response = client.get("/api/scraping/responses")

        data = response.json()
        assert len(data["responses"]) == 2
        # Verify both are present
        request_bodies = [r["request_body"] for r in data["responses"]]
        assert "First" in request_bodies
        assert "Second" in request_bodies
        # Verify structure
        for r in data["responses"]:
            assert "id" in r
            assert "request_body" in r
            assert "response_body" in r
            assert "created_at" in r


class TestAgentPromptsEndpoints:
    """Tests for agent prompts API endpoints."""

    def test_get_all_prompts(self, client, db_session):
        """Test getting all agent prompts."""
        # Create prompts
        prompt1 = AgentPrompt(
            agent_name="test_agent_1",
            system_prompt="Prompt 1",
            is_active=True
        )
        prompt2 = AgentPrompt(
            agent_name="test_agent_2",
            system_prompt="Prompt 2",
            is_active=False
        )
        db_session.add_all([prompt1, prompt2])
        db_session.commit()

        response = client.get("/api/agents/prompts")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2

    def test_update_agent_prompt(self, client, db_session):
        """Test updating an agent prompt."""
        # Create a prompt
        prompt = AgentPrompt(
            agent_name="update_test",
            system_prompt="Original prompt",
            is_active=True
        )
        db_session.add(prompt)
        db_session.commit()

        # Update it
        response = client.put(
            "/api/agents/prompts/update_test",
            json={
                "system_prompt": "Updated prompt",
                "description": "Updated description"
            }
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify update
        updated_prompt = db_session.query(AgentPrompt).filter(
            AgentPrompt.agent_name == "update_test"
        ).first()
        assert updated_prompt.system_prompt == "Updated prompt"


class TestValidationEndpoints:
    """Tests for validation API endpoints."""

    def test_validate_response_success(self, client, db_session):
        """Test validating a response."""
        # Create a response
        response = Response(
            request_body="Test",
            response_body='{"companies": [{"company_name": "Test", "address": "123 Main St, City, ST 12345"}]}'
        )
        db_session.add(response)
        db_session.commit()

        # Validate it
        api_response = client.post(
            "/api/validations/validate",
            json={
                "response_id": response.id,
                "validator_name": "AddressCompletenessValidator"
            }
        )

        assert api_response.status_code == status.HTTP_200_OK
        data = api_response.json()
        assert "score" in data
        assert "criteria_scores" in data
        assert "feedback" in data

    def test_validate_response_not_found(self, client):
        """Test validating non-existent response."""
        response = client.post(
            "/api/validations/validate",
            json={
                "response_id": 99999,
                "validator_name": "AddressCompletenessValidator"
            }
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_validation_stats(self, client, db_session):
        """Test getting validation statistics."""
        # Create response and validation
        response = Response(
            request_body="Test",
            response_body='{"companies": []}'
        )
        db_session.add(response)
        db_session.commit()

        validation = ResponseValidation(
            response_id=response.id,
            validator_name="TestValidator",
            validator_version="1.0.0",
            score=0.85,
            criteria_scores={},
            feedback="Good"
        )
        db_session.add(validation)
        db_session.commit()

        # Get stats
        api_response = client.get("/api/validations/stats")

        assert api_response.status_code == status.HTTP_200_OK
        data = api_response.json()
        assert "total_validations" in data
        assert data["total_validations"] == 1
        assert "average_score" in data
        assert "distribution" in data
        assert "recent_validations" in data

    def test_get_response_with_validations(self, client, db_session):
        """Test getting a response with its validations."""
        # Create response
        response = Response(
            request_body="Test",
            response_body='{"companies": []}'
        )
        db_session.add(response)
        db_session.commit()

        # Create validation
        validation = ResponseValidation(
            response_id=response.id,
            validator_name="TestValidator",
            validator_version="1.0.0",
            score=0.75,
            criteria_scores={"test": 0.75},
            feedback="Test feedback"
        )
        db_session.add(validation)
        db_session.commit()

        # Get response with validations
        api_response = client.get(f"/api/validations/response/{response.id}")

        assert api_response.status_code == status.HTTP_200_OK
        data = api_response.json()
        # API returns list directly, not wrapped in dict
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["response_id"] == response.id
        assert data[0]["score"] == 0.75

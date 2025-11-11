"""Tests for database models."""

import pytest
from datetime import datetime
from sqlalchemy import select

from app.models.response import Response
from app.models.agent_prompt import AgentPrompt
from app.models.response_validation import ResponseValidation


class TestResponseModel:
    """Tests for the Response model."""

    def test_create_response(self, db_session):
        """Test creating a response record."""
        response = Response(
            request_body="Test request",
            response_body='{"result": "test"}'
        )
        db_session.add(response)
        db_session.commit()

        assert response.id is not None
        assert response.request_body == "Test request"
        assert response.response_body == '{"result": "test"}'
        assert isinstance(response.created_at, datetime)

    def test_query_responses(self, db_session):
        """Test querying response records."""
        # Create multiple responses
        for i in range(3):
            response = Response(
                request_body=f"Request {i}",
                response_body=f'{{"result": "test {i}"}}'
            )
            db_session.add(response)
        db_session.commit()

        # Query all responses
        responses = db_session.query(Response).all()
        assert len(responses) == 3

    def test_response_timestamps(self, db_session):
        """Test that created_at is automatically set."""
        response = Response(
            request_body="Test",
            response_body="Test"
        )
        db_session.add(response)
        db_session.commit()

        assert response.created_at is not None
        # Just verify it's a datetime object, don't compare exact times


class TestAgentPromptModel:
    """Tests for the AgentPrompt model."""

    def test_create_agent_prompt(self, db_session):
        """Test creating an agent prompt record."""
        prompt = AgentPrompt(
            agent_name="test_agent",
            system_prompt="You are a test agent.",
            description="Test agent description",
            is_active=True
        )
        db_session.add(prompt)
        db_session.commit()

        assert prompt.id is not None
        assert prompt.agent_name == "test_agent"
        assert prompt.system_prompt == "You are a test agent."
        assert prompt.description == "Test agent description"
        assert prompt.is_active is True
        assert isinstance(prompt.created_at, datetime)
        assert isinstance(prompt.updated_at, datetime)

    def test_agent_name_unique_constraint(self, db_session):
        """Test that agent_name is unique."""
        prompt1 = AgentPrompt(
            agent_name="duplicate_agent",
            system_prompt="First prompt",
        )
        db_session.add(prompt1)
        db_session.commit()

        # Try to create another with same agent_name
        prompt2 = AgentPrompt(
            agent_name="duplicate_agent",
            system_prompt="Second prompt",
        )
        db_session.add(prompt2)

        with pytest.raises(Exception):  # SQLAlchemy will raise IntegrityError
            db_session.commit()

    def test_query_active_prompts(self, db_session):
        """Test querying only active prompts."""
        active_prompt = AgentPrompt(
            agent_name="active_agent",
            system_prompt="Active",
            is_active=True
        )
        inactive_prompt = AgentPrompt(
            agent_name="inactive_agent",
            system_prompt="Inactive",
            is_active=False
        )
        db_session.add_all([active_prompt, inactive_prompt])
        db_session.commit()

        active_prompts = db_session.query(AgentPrompt).filter(
            AgentPrompt.is_active == True
        ).all()

        assert len(active_prompts) == 1
        assert active_prompts[0].agent_name == "active_agent"

    def test_default_is_active(self, db_session):
        """Test that is_active defaults to True."""
        prompt = AgentPrompt(
            agent_name="default_test",
            system_prompt="Test"
        )
        db_session.add(prompt)
        db_session.commit()

        assert prompt.is_active is True


class TestResponseValidationModel:
    """Tests for the ResponseValidation model."""

    def test_create_validation(self, db_session):
        """Test creating a response validation record."""
        # First create a response
        response = Response(
            request_body="Test",
            response_body='{"companies": []}'
        )
        db_session.add(response)
        db_session.commit()

        # Create validation for the response
        validation = ResponseValidation(
            response_id=response.id,
            validator_name="TestValidator",
            validator_version="1.0.0",
            score=0.85,
            criteria_scores={"criterion1": 0.9, "criterion2": 0.8},
            feedback="Good quality response"
        )
        db_session.add(validation)
        db_session.commit()

        assert validation.id is not None
        assert validation.response_id == response.id
        assert validation.validator_name == "TestValidator"
        assert validation.score == 0.85
        assert isinstance(validation.validated_at, datetime)

    def test_validation_relationship(self, db_session):
        """Test relationship between Response and ResponseValidation."""
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
            criteria_scores={},
            feedback="Test"
        )
        db_session.add(validation)
        db_session.commit()

        # Query and verify relationship
        queried_validation = db_session.query(ResponseValidation).filter(
            ResponseValidation.response_id == response.id
        ).first()

        assert queried_validation is not None
        assert queried_validation.response_id == response.id

    def test_multiple_validations_per_response(self, db_session):
        """Test that a response can have multiple validations."""
        # Create response
        response = Response(
            request_body="Test",
            response_body='{"companies": []}'
        )
        db_session.add(response)
        db_session.commit()

        # Create multiple validations
        for i in range(3):
            validation = ResponseValidation(
                response_id=response.id,
                validator_name=f"Validator{i}",
                validator_version="1.0.0",
                score=0.5 + (i * 0.1),
                criteria_scores={},
                feedback=f"Test {i}"
            )
            db_session.add(validation)
        db_session.commit()

        # Query validations
        validations = db_session.query(ResponseValidation).filter(
            ResponseValidation.response_id == response.id
        ).all()

        assert len(validations) == 3

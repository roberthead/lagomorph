"""Tests for the validation framework."""

import pytest
from app.services.validators.base import BaseValidator, ValidationResult
from app.services.validators.address_validator import AddressCompletenessValidator


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_validation_result_creation(self):
        """Test creating a ValidationResult."""
        result = ValidationResult(
            score=0.85,
            criteria_scores={"criterion1": 0.9, "criterion2": 0.8},
            feedback="Good quality",
            validator_name="TestValidator",
            validator_version="1.0.0"
        )

        assert result.score == 0.85
        assert result.criteria_scores == {"criterion1": 0.9, "criterion2": 0.8}
        assert result.feedback == "Good quality"
        assert result.validator_name == "TestValidator"
        assert result.validator_version == "1.0.0"

    def test_validation_result_to_dict(self):
        """Test converting ValidationResult to dictionary."""
        result = ValidationResult(
            score=0.75,
            criteria_scores={"test": 0.75},
            feedback="Test feedback",
            validator_name="TestValidator",
            validator_version="2.0.0"
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["score"] == 0.75
        assert result_dict["criteria_scores"] == {"test": 0.75}
        assert result_dict["feedback"] == "Test feedback"
        assert result_dict["validator_name"] == "TestValidator"
        assert result_dict["validator_version"] == "2.0.0"


class ConcreteValidator(BaseValidator):
    """Concrete implementation of BaseValidator for testing."""

    def get_criteria(self):
        return {
            "criterion1": 0.6,
            "criterion2": 0.4
        }

    def score_criterion(self, data, criterion):
        # Simple scoring logic for testing
        if criterion == "criterion1":
            return data.get("score1", 0.5)
        elif criterion == "criterion2":
            return data.get("score2", 0.5)
        return 0.0


class TestBaseValidator:
    """Tests for the BaseValidator abstract class."""

    def test_validator_initialization(self):
        """Test validator initialization."""
        validator = ConcreteValidator(version="2.0.0")

        assert validator.version == "2.0.0"
        assert validator.name == "ConcreteValidator"

    def test_validate_basic(self):
        """Test basic validation."""
        validator = ConcreteValidator()
        data = {"score1": 0.8, "score2": 0.9}

        result = validator.validate(data)

        assert isinstance(result, ValidationResult)
        assert result.validator_name == "ConcreteValidator"
        # 0.8 * 0.6 + 0.9 * 0.4 = 0.48 + 0.36 = 0.84
        assert abs(result.score - 0.84) < 0.01

    def test_score_clamping(self):
        """Test that scores are clamped to [0, 1]."""
        validator = ConcreteValidator()
        # Data that would produce out-of-range scores
        data = {"score1": 1.5, "score2": -0.5}

        result = validator.validate(data)

        # Scores should be clamped
        assert result.criteria_scores["criterion1"] == 1.0
        assert result.criteria_scores["criterion2"] == 0.0

    def test_generate_feedback_excellent(self):
        """Test feedback generation for excellent scores."""
        validator = ConcreteValidator()
        criteria_scores = {"criterion1": 0.95, "criterion2": 0.90}

        feedback = validator.generate_feedback(criteria_scores, 0.93)

        assert "Excellent" in feedback

    def test_generate_feedback_good(self):
        """Test feedback generation for good scores."""
        validator = ConcreteValidator()
        criteria_scores = {"criterion1": 0.75, "criterion2": 0.70}

        feedback = validator.generate_feedback(criteria_scores, 0.73)

        assert "Good" in feedback

    def test_generate_feedback_needs_improvement(self):
        """Test feedback generation for poor scores."""
        validator = ConcreteValidator()
        criteria_scores = {"criterion1": 0.3, "criterion2": 0.2}

        feedback = validator.generate_feedback(criteria_scores, 0.26)

        assert "improvement" in feedback.lower()


class TestAddressCompletenessValidator:
    """Tests for the AddressCompletenessValidator."""

    def test_validator_initialization(self):
        """Test AddressCompletenessValidator initialization."""
        validator = AddressCompletenessValidator()

        assert validator.name == "AddressCompletenessValidator"
        assert validator.version == "1.0.0"

    def test_get_criteria(self):
        """Test that criteria are properly defined."""
        validator = AddressCompletenessValidator()
        criteria = validator.get_criteria()

        assert "has_street_address" in criteria
        assert "has_city" in criteria
        assert "has_state" in criteria
        assert "has_postal_code" in criteria

        # Weights should sum to 1.0
        assert abs(sum(criteria.values()) - 1.0) < 0.01

    def test_validate_complete_addresses(self, sample_companies):
        """Test validation with complete addresses."""
        validator = AddressCompletenessValidator()
        data = {"companies": sample_companies}

        result = validator.validate(data)

        assert result.score > 0.8  # Should score high
        assert all(score > 0.8 for score in result.criteria_scores.values())

    def test_validate_incomplete_addresses(self, sample_incomplete_addresses):
        """Test validation with incomplete addresses."""
        validator = AddressCompletenessValidator()
        data = {"companies": sample_incomplete_addresses}

        result = validator.validate(data)

        # Only 1 out of 4 has complete address, score should be lower than complete addresses
        assert result.score < 0.8

    def test_has_street_address(self):
        """Test street address detection."""
        validator = AddressCompletenessValidator()

        assert validator._has_street_address("123 Main Street, City, ST")
        assert validator._has_street_address("456 Oak Avenue")
        assert validator._has_street_address("789 Pine Rd")
        assert not validator._has_street_address("City, ST 12345")
        assert not validator._has_street_address("")

    def test_has_city(self):
        """Test city detection."""
        validator = AddressCompletenessValidator()

        assert validator._has_city("123 Main St, Austin, TX 78701")
        assert validator._has_city("456 Oak Ave, Seattle, WA")
        # Note: "TX" might be detected as city if it's the second-to-last part
        # This is acceptable for this simple validator
        assert not validator._has_city("123 Main St")
        assert not validator._has_city("")

    def test_has_state(self):
        """Test state detection."""
        validator = AddressCompletenessValidator()

        # Test abbreviations
        assert validator._has_state("123 Main St, Austin, TX 78701")
        assert validator._has_state("456 Oak Ave, Seattle, WA 98101")
        assert validator._has_state("789 Pine Rd, Miami, FL")

        # Test full state names
        assert validator._has_state("123 Main St, City, California 90210")
        assert validator._has_state("456 Oak Ave, Town, New York 10001")

        assert not validator._has_state("123 Main St, City")
        assert not validator._has_state("")

    def test_has_postal_code(self):
        """Test postal code detection."""
        validator = AddressCompletenessValidator()

        assert validator._has_postal_code("123 Main St, City, ST 78701")
        assert validator._has_postal_code("456 Oak Ave, Town, ST 12345-6789")
        assert not validator._has_postal_code("123 Main St, City, ST")
        assert not validator._has_postal_code("")

    def test_extract_companies_from_dict(self):
        """Test extracting companies from dict format."""
        validator = AddressCompletenessValidator()

        data = {
            "companies": [
                {"company_name": "Test", "address": "123 Main St"}
            ]
        }

        companies = validator._extract_companies(data)
        assert len(companies) == 1
        assert companies[0]["company_name"] == "Test"

    def test_extract_companies_from_nested_dict(self):
        """Test extracting companies from nested dict format."""
        validator = AddressCompletenessValidator()

        data = {
            "data": {
                "companies": [
                    {"company_name": "Test", "address": "123 Main St"}
                ]
            }
        }

        companies = validator._extract_companies(data)
        assert len(companies) == 1

    def test_extract_companies_from_list(self):
        """Test extracting companies from list format."""
        validator = AddressCompletenessValidator()

        data = [
            {"company_name": "Test1", "address": "123 Main St"},
            {"company_name": "Test2", "address": "456 Oak Ave"}
        ]

        companies = validator._extract_companies(data)
        assert len(companies) == 2

    def test_extract_companies_from_json_string(self):
        """Test extracting companies from JSON string."""
        validator = AddressCompletenessValidator()

        data = '{"companies": [{"company_name": "Test", "address": "123 Main St"}]}'

        companies = validator._extract_companies(data)
        assert len(companies) == 1

    def test_score_criterion_empty_companies(self):
        """Test scoring with no companies."""
        validator = AddressCompletenessValidator()

        score = validator.score_criterion({"companies": []}, "has_street_address")

        assert score == 0.0

    def test_generate_feedback_specific(self):
        """Test address-specific feedback generation."""
        validator = AddressCompletenessValidator()

        criteria_scores = {
            "has_street_address": 0.9,
            "has_city": 0.8,
            "has_state": 0.3,
            "has_postal_code": 0.2
        }

        feedback = validator.generate_feedback(criteria_scores, 0.6)

        # Should mention weaknesses
        assert "30%" in feedback  # State percentage
        assert "20%" in feedback  # Postal code percentage

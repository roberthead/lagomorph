"""Base validator class for response validation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation operation."""

    score: float  # Overall score 0.0-1.0
    criteria_scores: Dict[str, float]  # Breakdown by criterion
    feedback: str  # Human-readable explanation
    validator_name: str
    validator_version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "score": self.score,
            "criteria_scores": self.criteria_scores,
            "feedback": self.feedback,
            "validator_name": self.validator_name,
            "validator_version": self.validator_version
        }


class BaseValidator(ABC):
    """Base class for all validators."""

    def __init__(self, version: str = "1.0.0"):
        """
        Initialize validator.

        Args:
            version: Version of the validator
        """
        self.version = version
        self.name = self.__class__.__name__

    @abstractmethod
    def get_criteria(self) -> Dict[str, float]:
        """
        Get validation criteria and their weights.

        Returns:
            Dictionary of criterion name to weight (weights should sum to 1.0)
        """
        pass

    @abstractmethod
    def score_criterion(self, data: Any, criterion: str) -> float:
        """
        Score a single criterion.

        Args:
            data: Data to validate
            criterion: Name of the criterion to score

        Returns:
            Score between 0.0 and 1.0
        """
        pass

    def validate(self, data: Any) -> ValidationResult:
        """
        Validate data and return a validation result.

        Args:
            data: Data to validate

        Returns:
            ValidationResult with scores and feedback
        """
        criteria = self.get_criteria()
        criteria_scores = {}

        # Score each criterion
        for criterion, weight in criteria.items():
            try:
                score = self.score_criterion(data, criterion)
                # Ensure score is between 0 and 1
                score = max(0.0, min(1.0, score))
                criteria_scores[criterion] = score
            except Exception as e:
                logger.error(f"Error scoring criterion '{criterion}': {str(e)}")
                criteria_scores[criterion] = 0.0

        # Calculate weighted overall score
        overall_score = sum(
            criteria_scores[criterion] * weight
            for criterion, weight in criteria.items()
        )

        # Generate feedback
        feedback = self.generate_feedback(criteria_scores, overall_score)

        return ValidationResult(
            score=overall_score,
            criteria_scores=criteria_scores,
            feedback=feedback,
            validator_name=self.name,
            validator_version=self.version
        )

    def generate_feedback(
        self,
        criteria_scores: Dict[str, float],
        overall_score: float
    ) -> str:
        """
        Generate human-readable feedback based on scores.

        Args:
            criteria_scores: Scores for each criterion
            overall_score: Overall validation score

        Returns:
            Feedback string
        """
        feedback_parts = []

        # Overall assessment
        if overall_score >= 0.9:
            feedback_parts.append("Excellent response quality.")
        elif overall_score >= 0.7:
            feedback_parts.append("Good response quality.")
        elif overall_score >= 0.5:
            feedback_parts.append("Acceptable response quality with room for improvement.")
        else:
            feedback_parts.append("Response quality needs significant improvement.")

        # Identify strengths and weaknesses
        strengths = [
            criterion for criterion, score in criteria_scores.items()
            if score >= 0.8
        ]
        weaknesses = [
            criterion for criterion, score in criteria_scores.items()
            if score < 0.5
        ]

        if strengths:
            feedback_parts.append(
                f"Strengths: {', '.join(strengths)}."
            )

        if weaknesses:
            feedback_parts.append(
                f"Needs improvement: {', '.join(weaknesses)}."
            )

        return " ".join(feedback_parts)

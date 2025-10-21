"""Pydantic schemas for validation."""

from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any, Optional


class ValidationResultSchema(BaseModel):
    """Schema for validation result."""

    score: float
    criteria_scores: Dict[str, float]
    feedback: str
    validator_name: str
    validator_version: str


class ResponseValidationResponse(BaseModel):
    """Response schema for validation."""

    id: int
    response_id: int
    validator_name: str
    score: float
    criteria_scores: Dict[str, Any]
    feedback: Optional[str]
    validator_version: str
    validated_at: datetime

    class Config:
        from_attributes = True


class ValidateRequest(BaseModel):
    """Request to validate a response."""

    response_id: int
    validator_name: str = "AddressCompletenessValidator"


class BatchValidateRequest(BaseModel):
    """Request to validate multiple responses."""

    response_ids: list[int]
    validator_name: str = "AddressCompletenessValidator"

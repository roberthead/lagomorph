"""API endpoints for response validation."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import logging
import json

from app.schemas.validation import (
    ResponseValidationResponse,
    ValidateRequest,
    BatchValidateRequest
)
from app.db.base import get_db
from app.models.response import Response
from app.models.response_validation import ResponseValidation
from app.services.validators.address_validator import AddressCompletenessValidator

logger = logging.getLogger(__name__)

router = APIRouter()

# Registry of available validators
VALIDATORS = {
    "AddressCompletenessValidator": AddressCompletenessValidator
}


@router.post("/validate", response_model=ResponseValidationResponse)
async def validate_response(
    request: ValidateRequest,
    db: Session = Depends(get_db)
):
    """
    Validate a single response.

    Args:
        request: Validation request with response_id and validator_name
        db: Database session

    Returns:
        Validation result

    Raises:
        HTTPException: If response not found or validation fails
    """
    try:
        # Get the response to validate
        response = db.query(Response).filter(Response.id == request.response_id).first()

        if not response:
            raise HTTPException(
                status_code=404,
                detail=f"Response {request.response_id} not found"
            )

        # Get the validator
        validator_class = VALIDATORS.get(request.validator_name)
        if not validator_class:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown validator: {request.validator_name}"
            )

        # Parse response body to get companies data
        try:
            response_data = json.loads(response.response_body)
        except json.JSONDecodeError:
            response_data = response.response_body

        # Extract companies from streaming response events
        companies_data = None
        if isinstance(response_data, list):
            # Look for the 'complete' event with companies data
            for event in response_data:
                if isinstance(event, dict) and event.get('type') == 'complete':
                    companies_data = event.get('data', {})
                    break
        elif isinstance(response_data, dict):
            # Direct data format
            companies_data = response_data

        if not companies_data:
            raise HTTPException(
                status_code=400,
                detail="No company data found in response to validate"
            )

        # Create validator and validate
        validator = validator_class()
        result = validator.validate(companies_data)

        logger.info(
            f"Validated response {request.response_id} with {request.validator_name}: "
            f"score={result.score:.2f}"
        )

        # Save validation result to database
        validation = ResponseValidation(
            response_id=request.response_id,
            validator_name=result.validator_name,
            score=result.score,
            criteria_scores=result.criteria_scores,
            feedback=result.feedback,
            validator_version=result.validator_version
        )

        db.add(validation)
        db.commit()
        db.refresh(validation)

        return validation

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating response: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )


@router.post("/validate/batch")
async def validate_batch(
    request: BatchValidateRequest,
    db: Session = Depends(get_db)
):
    """
    Validate multiple responses in batch.

    Args:
        request: Batch validation request with response_ids
        db: Database session

    Returns:
        List of validation results
    """
    results = []
    errors = []

    for response_id in request.response_ids:
        try:
            validate_request = ValidateRequest(
                response_id=response_id,
                validator_name=request.validator_name
            )
            result = await validate_response(validate_request, db)
            results.append(result)
        except Exception as e:
            errors.append({
                "response_id": response_id,
                "error": str(e)
            })
            logger.error(f"Error validating response {response_id}: {str(e)}")

    return {
        "validated": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors
    }


@router.get("/response/{response_id}", response_model=list[ResponseValidationResponse])
async def get_validations_for_response(
    response_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all validation results for a specific response.

    Args:
        response_id: ID of the response
        db: Database session

    Returns:
        List of validation results
    """
    try:
        validations = db.query(ResponseValidation).filter(
            ResponseValidation.response_id == response_id
        ).order_by(ResponseValidation.validated_at.desc()).all()

        return validations

    except Exception as e:
        logger.error(f"Error fetching validations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch validations: {str(e)}"
        )


@router.get("/stats")
async def get_validation_stats(db: Session = Depends(get_db)):
    """
    Get aggregate validation statistics.

    Returns:
        Statistics about all validations
    """
    try:
        from sqlalchemy import func

        # Count total validations
        total = db.query(func.count(ResponseValidation.id)).scalar()

        # Average score
        avg_score = db.query(func.avg(ResponseValidation.score)).scalar()

        # Score distribution
        excellent = db.query(func.count(ResponseValidation.id)).filter(
            ResponseValidation.score >= 0.9
        ).scalar()

        good = db.query(func.count(ResponseValidation.id)).filter(
            ResponseValidation.score >= 0.7,
            ResponseValidation.score < 0.9
        ).scalar()

        acceptable = db.query(func.count(ResponseValidation.id)).filter(
            ResponseValidation.score >= 0.5,
            ResponseValidation.score < 0.7
        ).scalar()

        poor = db.query(func.count(ResponseValidation.id)).filter(
            ResponseValidation.score < 0.5
        ).scalar()

        # Get recent validations
        recent = db.query(ResponseValidation).order_by(
            ResponseValidation.validated_at.desc()
        ).limit(10).all()

        return {
            "total_validations": total or 0,
            "average_score": round(float(avg_score or 0), 3),
            "distribution": {
                "excellent": excellent or 0,
                "good": good or 0,
                "acceptable": acceptable or 0,
                "poor": poor or 0
            },
            "recent_validations": [
                {
                    "id": v.id,
                    "response_id": v.response_id,
                    "score": v.score,
                    "validator_name": v.validator_name,
                    "validated_at": v.validated_at.isoformat()
                }
                for v in recent
            ]
        }

    except Exception as e:
        logger.error(f"Error fetching validation stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch stats: {str(e)}"
        )

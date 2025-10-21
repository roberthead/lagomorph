"""API endpoints for agent prompt management."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import logging

from app.schemas.agent_prompt import AgentPromptResponse, AgentPromptUpdate
from app.db.base import get_db
from app.models.agent_prompt import AgentPrompt

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/prompts/{agent_name}", response_model=AgentPromptResponse)
async def get_agent_prompt(agent_name: str, db: Session = Depends(get_db)):
    """
    Get the active prompt for a specific agent.

    Args:
        agent_name: Name of the agent (e.g., 'scraping_agent', 'chat_agent')
        db: Database session

    Returns:
        AgentPromptResponse with prompt details

    Raises:
        HTTPException: If agent prompt not found
    """
    try:
        prompt = db.query(AgentPrompt).filter(
            AgentPrompt.agent_name == agent_name,
            AgentPrompt.is_active == True
        ).first()

        if not prompt:
            raise HTTPException(
                status_code=404,
                detail=f"No active prompt found for agent '{agent_name}'"
            )

        return prompt

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching agent prompt: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch agent prompt: {str(e)}"
        )


@router.put("/prompts/{agent_name}", response_model=AgentPromptResponse)
async def update_agent_prompt(
    agent_name: str,
    update_data: AgentPromptUpdate,
    db: Session = Depends(get_db)
):
    """
    Update the prompt for a specific agent.

    Args:
        agent_name: Name of the agent to update
        update_data: Fields to update
        db: Database session

    Returns:
        Updated AgentPromptResponse

    Raises:
        HTTPException: If agent prompt not found or update fails
    """
    try:
        prompt = db.query(AgentPrompt).filter(
            AgentPrompt.agent_name == agent_name
        ).first()

        if not prompt:
            raise HTTPException(
                status_code=404,
                detail=f"Agent '{agent_name}' not found"
            )

        # Update fields that were provided
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(prompt, field, value)

        db.commit()
        db.refresh(prompt)

        logger.info(f"Updated prompt for agent '{agent_name}'")

        return prompt

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating agent prompt: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update agent prompt: {str(e)}"
        )


@router.get("/prompts", response_model=list[AgentPromptResponse])
async def list_agent_prompts(db: Session = Depends(get_db)):
    """
    Get all agent prompts.

    Returns:
        List of all agent prompts
    """
    try:
        prompts = db.query(AgentPrompt).all()
        return prompts

    except Exception as e:
        logger.error(f"Error listing agent prompts: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list agent prompts: {str(e)}"
        )

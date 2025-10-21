"""Pydantic schemas for agent prompts."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AgentPromptBase(BaseModel):
    agent_name: str
    system_prompt: str
    description: Optional[str] = None
    is_active: bool = True


class AgentPromptCreate(AgentPromptBase):
    pass


class AgentPromptUpdate(BaseModel):
    system_prompt: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class AgentPromptResponse(AgentPromptBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

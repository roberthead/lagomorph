"""Pydantic schemas for chat endpoints."""

from pydantic import BaseModel, Field
from typing import List, Optional


class ChatMessage(BaseModel):
    """Schema for a chat message."""

    sender: str = Field(..., description="Sender of the message: 'user' or 'agent'")
    text: str = Field(..., description="Message text")
    timestamp: Optional[str] = Field(None, description="ISO timestamp")


class ChatRequest(BaseModel):
    """Schema for chat request."""

    message: str = Field(..., description="User's message")
    conversation_history: List[ChatMessage] = Field(
        default=[],
        description="Previous conversation messages for context"
    )

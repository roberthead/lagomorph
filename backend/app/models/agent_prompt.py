from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from app.db.base import Base


class AgentPrompt(Base):
    __tablename__ = "agent_prompts"

    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String(100), unique=True, nullable=False, index=True)
    system_prompt = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

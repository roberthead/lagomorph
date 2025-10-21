from sqlalchemy import Column, Integer, Text, DateTime
from sqlalchemy.sql import func
from app.db.base import Base


class Response(Base):
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, index=True)
    request_body = Column(Text, nullable=False)
    response_body = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

from sqlalchemy import Column, Integer, Float, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class ResponseValidation(Base):
    __tablename__ = "response_validations"

    id = Column(Integer, primary_key=True, index=True)
    response_id = Column(Integer, ForeignKey("responses.id"), nullable=False, index=True)
    validator_name = Column(String(100), nullable=False)
    score = Column(Float, nullable=False)  # Overall score 0.0-1.0
    criteria_scores = Column(JSON, nullable=True)  # Breakdown by criterion
    feedback = Column(Text, nullable=True)  # Explanation of the score
    validator_version = Column(String(50), nullable=False, default="1.0.0")
    validated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship to Response
    response = relationship("Response", backref="validations")

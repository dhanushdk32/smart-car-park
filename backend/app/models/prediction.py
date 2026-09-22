from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from ..core.database import Base

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    area_id = Column(Integer, ForeignKey("parking_areas.id"), nullable=False)
    prediction_time = Column(DateTime(timezone=True), nullable=False)
    predicted_occupied = Column(Integer, nullable=False)
    predicted_free = Column(Integer, nullable=False)
    model_version = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

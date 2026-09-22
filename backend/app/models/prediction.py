from sqlalchemy import Column, Integer, String, Date, Time, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    area_id = Column(Integer, ForeignKey("parking_areas.id"), nullable=False, index=True)
    prediction_date = Column(Date, nullable=False, index=True)
    prediction_time = Column(Time, nullable=False)
    predicted_is_free = Column(Integer, nullable=False)  # 1 = Available, 0 = Full
    prediction_probability = Column(Float, nullable=False)  # availability probability %
    model_version = Column(String(50), nullable=True, default="gradient_boosting_v1")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    area = relationship("ParkingArea", backref="predictions")


from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from ..core.database import Base

class ParkingOccupancy(Base):
    __tablename__ = "parking_occupancy"

    id = Column(Integer, primary_key=True, index=True)
    area_id = Column(Integer, ForeignKey("parking_areas.id"), nullable=False)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    total_slots = Column(Integer, nullable=False)
    occupied_slots = Column(Integer, nullable=False)
    free_slots = Column(Integer, nullable=False)

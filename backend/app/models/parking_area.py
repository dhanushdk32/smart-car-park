from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base

class ParkingArea(Base):
    __tablename__ = "parking_areas"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    location = Column(String(255), nullable=False)
    total_slots = Column(Integer, nullable=False)
    price_per_hour = Column(Float, nullable=False)
    status = Column(String(50), default="Active") # Active, Inactive, Maintenance
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    slots = relationship("ParkingSlot", back_populates="area", cascade="all, delete-orphan")

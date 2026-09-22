from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base

class ParkingSlot(Base):
    __tablename__ = "parking_slots"

    id = Column(Integer, primary_key=True, index=True)
    area_id = Column(Integer, ForeignKey("parking_areas.id"), nullable=False)
    slot_number = Column(String(20), nullable=False)
    slot_type = Column(String(50), default="Regular") # Regular, EV, Accessible
    status = Column(String(50), default="Available") # Available, Occupied, Reserved, Maintenance
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    area = relationship("ParkingArea", back_populates="slots")

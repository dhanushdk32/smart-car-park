from sqlalchemy import Column, Integer, String, Float, Date, Time, DateTime, ForeignKey
from sqlalchemy.sql import func
from ..core.database import Base

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    booking_reference = Column(String(50), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    area_id = Column(Integer, ForeignKey("parking_areas.id"), nullable=False)
    slot_id = Column(Integer, ForeignKey("parking_slots.id"), nullable=False)
    booking_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    duration = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String(50), default="Pending") # Pending, Confirmed, Active, Completed, Cancelled
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

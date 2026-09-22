from sqlalchemy import Column, Integer, Float, String, Boolean, Date, Time, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base

class ParkingOccupancy(Base):
    __tablename__ = "parking_occupancy"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    area_id = Column(Integer, ForeignKey("parking_areas.id", ondelete="CASCADE"), nullable=False, index=True)
    recorded_date = Column(Date, nullable=False, index=True)
    recorded_time = Column(Time, nullable=False, index=True)
    total_slots = Column(Integer, nullable=False)
    occupied_slots = Column(Integer, nullable=False)
    free_slots = Column(Integer, nullable=False)
    reserved_slots = Column(Integer, default=0, nullable=False)
    maintenance_slots = Column(Integer, default=0, nullable=False)
    occupancy_percentage = Column(Float, nullable=False)
    day_of_week = Column(String(20), nullable=False)
    is_weekend = Column(Boolean, default=False, nullable=False)
    is_holiday = Column(Boolean, default=False, nullable=False)
    weather = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to ParkingArea
    parking_area = relationship("ParkingArea", backref="occupancy_records")

    __table_args__ = (
        UniqueConstraint("area_id", "recorded_date", "recorded_time", name="uq_area_date_time"),
        Index("idx_area_date", "area_id", "recorded_date"),
    )

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, time, datetime

class BookingCreate(BaseModel):
    area_id: int
    slot_id: int
    booking_date: date
    start_time: time
    duration: int = Field(..., gt=0, le=24) # Ensure valid duration

class BookingOut(BaseModel):
    id: int
    booking_reference: str
    user_id: int
    area_id: int
    slot_id: int
    booking_date: date
    start_time: time
    end_time: time
    duration: int
    amount: float
    status: str
    created_at: datetime
    
    # Extended fields for easy UI rendering
    area_name: Optional[str] = None
    slot_number: Optional[str] = None

    class Config:
        from_attributes = True

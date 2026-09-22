from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ParkingSlotBase(BaseModel):
    slot_number: str
    slot_type: str
    status: str

class ParkingSlotCreate(ParkingSlotBase):
    pass

class ParkingSlotUpdate(BaseModel):
    slot_type: Optional[str] = None
    status: Optional[str] = None

class ParkingSlotOut(ParkingSlotBase):
    id: int
    area_id: int

    class Config:
        from_attributes = True

class ParkingAreaBase(BaseModel):
    name: str
    location: str
    total_slots: int
    price_per_hour: float
    status: str

class ParkingAreaCreate(ParkingAreaBase):
    pass

class ParkingAreaUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    total_slots: Optional[int] = None
    price_per_hour: Optional[float] = None
    status: Optional[str] = None

class ParkingAreaOut(ParkingAreaBase):
    id: int
    available_slots: Optional[int] = None # Calculated field
    occupied_slots: Optional[int] = None # Calculated field

    class Config:
        from_attributes = True

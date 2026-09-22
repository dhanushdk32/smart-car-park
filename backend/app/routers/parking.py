from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List
from datetime import date, time, timedelta, datetime
from ..core.database import get_db
from ..models.parking_area import ParkingArea
from ..models.parking_slot import ParkingSlot
from ..models.booking import Booking
from ..schemas.parking import ParkingAreaOut, ParkingSlotOut

router = APIRouter()

@router.get("/areas", response_model=List[ParkingAreaOut])
def get_parking_areas(db: Session = Depends(get_db)):
    areas = db.query(ParkingArea).all()
    # Calculate available and occupied
    for area in areas:
        total = area.total_slots
        available = db.query(ParkingSlot).filter(ParkingSlot.area_id == area.id, ParkingSlot.status == 'Available').count()
        area.available_slots = available
        area.occupied_slots = total - available
    return areas

@router.get("/areas/{area_id}", response_model=ParkingAreaOut)
def get_parking_area(area_id: int, db: Session = Depends(get_db)):
    area = db.query(ParkingArea).filter(ParkingArea.id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Parking area not found")
    
    total = area.total_slots
    available = db.query(ParkingSlot).filter(ParkingSlot.area_id == area.id, ParkingSlot.status == 'Available').count()
    area.available_slots = available
    area.occupied_slots = total - available
    return area

@router.get("/areas/{area_id}/slots", response_model=List[ParkingSlotOut])
def get_parking_slots(area_id: int, db: Session = Depends(get_db)):
    area = db.query(ParkingArea).filter(ParkingArea.id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Parking area not found")
    
    slots = db.query(ParkingSlot).filter(ParkingSlot.area_id == area_id).all()
    return slots

@router.get("/areas/{area_id}/availability")
def get_parking_availability(area_id: int, booking_date: date, start_time: time, duration: int, db: Session = Depends(get_db)):
    area = db.query(ParkingArea).filter(ParkingArea.id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Parking area not found")
    if area.status != "Active":
        raise HTTPException(status_code=400, detail="Parking area is not active")

    # Calculate end_time
    # Time arithmetic in python requires datetime manipulation
    start_dt = datetime.combine(booking_date, start_time)
    end_dt = start_dt + timedelta(hours=duration)
    end_time = end_dt.time()
    
    # Check if end_dt went to the next day
    if end_dt.date() > booking_date:
        # For simplicity in this stage, we assume bookings are same-day.
        # But we can allow it if the system just checks time properly.
        # Let's enforce same day booking for simplicity or just handle time properly.
        pass

    # Find overlapping bookings
    # Overlap condition: (existing_start < requested_end) AND (existing_end > requested_start)
    overlapping_bookings = db.query(Booking).filter(
        Booking.area_id == area_id,
        Booking.booking_date == booking_date,
        Booking.status.in_(["Pending", "Confirmed", "Active"]),
        Booking.start_time < end_time,
        Booking.end_time > start_time
    ).all()

    booked_slot_ids = [b.slot_id for b in overlapping_bookings]

    all_slots = db.query(ParkingSlot).filter(ParkingSlot.area_id == area_id).all()
    
    slots_data = []
    available_count = 0
    unavailable_count = 0
    
    for slot in all_slots:
        is_available = slot.status == "Available" and slot.id not in booked_slot_ids
        slots_data.append({
            "id": slot.id,
            "slot_number": slot.slot_number,
            "slot_type": slot.slot_type,
            "available": is_available
        })
        if is_available:
            available_count += 1
        else:
            unavailable_count += 1

    return {
        "success": True,
        "data": {
            "total_slots": area.total_slots,
            "available_slots": available_count,
            "unavailable_slots": unavailable_count,
            "slots": slots_data
        }
    }

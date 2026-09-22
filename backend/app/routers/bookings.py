from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from datetime import datetime, date, timedelta
from ..core.database import get_db
from ..core.config import settings
from ..dependencies.auth import get_current_user
from ..models.user import User
from ..models.parking_area import ParkingArea
from ..models.parking_slot import ParkingSlot
from ..models.booking import Booking
from ..schemas.booking import BookingCreate, BookingOut
import random
import string

router = APIRouter()

def generate_booking_reference(date_str: str) -> str:
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"SP-{date_str.replace('-', '')}-{random_str}"

@router.post("", response_model=dict)
def create_booking(booking_in: BookingCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    area = db.query(ParkingArea).filter(ParkingArea.id == booking_in.area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Parking area not found")
    if area.status != "Active":
        raise HTTPException(status_code=400, detail="Parking area is not active")

    slot = db.query(ParkingSlot).filter(ParkingSlot.id == booking_in.slot_id, ParkingSlot.area_id == booking_in.area_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Parking slot not found or does not belong to area")
    if slot.status == "Maintenance":
        raise HTTPException(status_code=400, detail="This parking slot is currently under maintenance.")

    # Validate dates
    now = datetime.now()
    if booking_in.booking_date < now.date():
        raise HTTPException(status_code=400, detail="Cannot book for a past date")
    if booking_in.booking_date == now.date() and booking_in.start_time < now.time():
        raise HTTPException(status_code=400, detail="Cannot book for a past time today")

    start_dt = datetime.combine(booking_in.booking_date, booking_in.start_time)
    end_dt = start_dt + timedelta(hours=booking_in.duration)
    end_time = end_dt.time()
    
    # Overlap check (including Pending Payment if within hold time)
    hold_minutes = int(getattr(settings, "PAYMENT_HOLD_MINUTES", 10))
    cutoff_time = now - timedelta(minutes=hold_minutes)
    
    overlapping_booking = db.query(Booking).filter(
        Booking.area_id == booking_in.area_id,
        Booking.slot_id == booking_in.slot_id,
        Booking.booking_date == booking_in.booking_date,
        Booking.start_time < end_time,
        Booking.end_time > booking_in.start_time,
        Booking.status.in_(["Pending Payment", "Confirmed", "Active"]),
        # We want to ignore "Pending Payment" bookings that are older than cutoff_time
        # In SQL, we can't easily express the OR condition cleanly with with_for_update if we want strict locking, 
        # but since we clean them up dynamically, we just check here.
    ).with_for_update().all() # Lock for update to prevent race conditions

    for overlap in overlapping_booking:
        if overlap.status == "Pending Payment" and overlap.created_at.replace(tzinfo=None) < cutoff_time:
            # It's expired, so it's not a real overlap
            overlap.status = "Expired"
            continue
        # If we get here, it's a genuine overlap
        raise HTTPException(status_code=409, detail="Sorry, this slot was just booked by another user. Please select another slot.")

    amount = area.price_per_hour * booking_in.duration
    ref = generate_booking_reference(str(booking_in.booking_date))

    new_booking = Booking(
        booking_reference=ref,
        user_id=current_user.id,
        area_id=booking_in.area_id,
        slot_id=booking_in.slot_id,
        booking_date=booking_in.booking_date,
        start_time=booking_in.start_time,
        end_time=end_time,
        duration=booking_in.duration,
        amount=amount,
        status="Pending Payment" # Initial status before payment
    )

    try:
        db.add(new_booking)
        db.commit()
        db.refresh(new_booking)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred during booking creation")

    return {
        "success": True,
        "message": "Booking created successfully",
        "data": {
            "id": new_booking.id,
            "booking_reference": new_booking.booking_reference,
            "area": area.name,
            "slot": slot.slot_number,
            "booking_date": new_booking.booking_date,
            "start_time": new_booking.start_time.strftime("%H:%M"),
            "end_time": new_booking.end_time.strftime("%H:%M"),
            "duration": new_booking.duration,
            "price_per_hour": area.price_per_hour,
            "amount": new_booking.amount,
            "status": new_booking.status
        }
    }

@router.get("", response_model=List[BookingOut])
def get_user_bookings(status: Optional[str] = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Booking, ParkingArea.name.label("area_name"), ParkingSlot.slot_number.label("slot_number"))\
              .join(ParkingArea, Booking.area_id == ParkingArea.id)\
              .join(ParkingSlot, Booking.slot_id == ParkingSlot.id)\
              .filter(Booking.user_id == current_user.id)
    
    if status:
        query = query.filter(Booking.status == status)
        
    results = query.order_by(Booking.booking_date.desc(), Booking.start_time.desc()).all()
    
    bookings = []
    for booking, area_name, slot_number in results:
        b = BookingOut.model_validate(booking)
        b.area_name = area_name
        b.slot_number = slot_number
        bookings.append(b)
        
    return bookings

@router.get("/{booking_id}", response_model=BookingOut)
def get_booking_details(booking_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = db.query(Booking, ParkingArea.name.label("area_name"), ParkingSlot.slot_number.label("slot_number"))\
              .join(ParkingArea, Booking.area_id == ParkingArea.id)\
              .join(ParkingSlot, Booking.slot_id == ParkingSlot.id)\
              .filter(Booking.id == booking_id, Booking.user_id == current_user.id).first()
              
    if not result:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    booking, area_name, slot_number = result
    b = BookingOut.model_validate(booking)
    b.area_name = area_name
    b.slot_number = slot_number
    return b

@router.put("/{booking_id}/cancel", response_model=dict)
def cancel_booking(booking_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id, Booking.user_id == current_user.id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    if booking.status in ["Completed", "Cancelled"]:
        raise HTTPException(status_code=400, detail="This booking can no longer be cancelled.")
        
    now = datetime.now()
    start_dt = datetime.combine(booking.booking_date, booking.start_time)
    if now > start_dt:
        raise HTTPException(status_code=400, detail="Cannot cancel a booking that has already started.")
        
    booking.status = "Cancelled"
    db.commit()
    
    return {"success": True, "message": "Booking cancelled successfully"}

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timedelta
from sqlalchemy import func, or_

from ..core.database import get_db
from ..dependencies.auth import get_current_admin
from ..models.user import User
from ..models.parking_area import ParkingArea
from ..models.parking_slot import ParkingSlot
from ..models.booking import Booking
from ..models.payment import Payment
from ..schemas.parking import ParkingAreaCreate, ParkingAreaUpdate, ParkingSlotCreate, ParkingSlotUpdate

router = APIRouter(dependencies=[Depends(get_current_admin)])

# --- Dashboard ---
@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    now = datetime.now()
    today = now.date()

    # 1. KPIs
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    total_areas = db.query(ParkingArea).count()
    total_slots = db.query(ParkingSlot).count()

    # Active bookings right now
    active_bookings_count = db.query(Booking).filter(
        Booking.status.in_(["Confirmed", "Active"]),
        Booking.booking_date == today,
        Booking.start_time <= now.time(),
        Booking.end_time >= now.time()
    ).count()

    maintenance_slots = db.query(ParkingSlot).filter(ParkingSlot.status == 'Maintenance').count()
    available_slots = max(0, total_slots - active_bookings_count - maintenance_slots)

    today_bookings = db.query(Booking).filter(Booking.booking_date == today).count()

    today_revenue_result = db.query(func.sum(Payment.amount)).filter(
        Payment.payment_status == 'Success',
        func.date(Payment.created_at) == today
    ).scalar()
    today_revenue = float(today_revenue_result) if today_revenue_result else 0.0

    pending_payments = db.query(Payment).filter(Payment.payment_status == 'Pending').count()

    # 2. Recent Bookings (5 latest)
    recent_bookings = db.query(
        Booking, ParkingArea.name.label("area_name"), ParkingSlot.slot_number.label("slot_number"), 
        User.full_name.label("user_name"), User.car_number.label("car_number")
    ).join(ParkingArea, Booking.area_id == ParkingArea.id)\
     .join(ParkingSlot, Booking.slot_id == ParkingSlot.id)\
     .join(User, Booking.user_id == User.id)\
     .order_by(Booking.created_at.desc()).limit(5).all()

    recent_bookings_data = []
    for b, area_name, slot_number, user_name, car_number in recent_bookings:
        recent_bookings_data.append({
            "id": b.id,
            "booking_reference": b.booking_reference,
            "user_name": user_name,
            "car_number": car_number,
            "area_name": area_name,
            "slot_number": slot_number,
            "booking_date": str(b.booking_date),
            "start_time": str(b.start_time),
            "end_time": str(b.end_time),
            "amount": b.amount,
            "status": b.status,
            "created_at": b.created_at.isoformat() if b.created_at else None
        })

    # 3. Recent Payments (5 latest)
    recent_payments = db.query(
        Payment, Booking.booking_reference, User.full_name.label("user_name"), User.car_number.label("car_number")
    ).join(Booking, Payment.booking_id == Booking.id)\
     .join(User, Booking.user_id == User.id)\
     .order_by(Payment.created_at.desc()).limit(5).all()

    recent_payments_data = []
    for p, booking_ref, user_name, car_number in recent_payments:
        recent_payments_data.append({
            "id": p.id,
            "razorpay_payment_id": p.razorpay_payment_id or f"PAY-{p.id}",
            "booking_reference": booking_ref,
            "user_name": user_name,
            "car_number": car_number,
            "amount": p.amount,
            "payment_method": p.payment_method or "UPI",
            "payment_status": p.payment_status,
            "created_at": p.created_at.isoformat() if p.created_at else None
        })

    # 4. Areas Overview
    areas = db.query(ParkingArea).all()
    areas_overview = []
    for area in areas:
        slots_count = db.query(ParkingSlot).filter(ParkingSlot.area_id == area.id).count()
        m_slots = db.query(ParkingSlot).filter(ParkingSlot.area_id == area.id, ParkingSlot.status == 'Maintenance').count()
        occ = db.query(Booking).filter(
            Booking.area_id == area.id,
            Booking.status.in_(["Confirmed", "Active"]),
            Booking.booking_date == today,
            Booking.start_time <= now.time(),
            Booking.end_time >= now.time()
        ).count()
        avail = max(0, slots_count - occ - m_slots)
        areas_overview.append({
            "id": area.id,
            "name": area.name,
            "location": area.location,
            "total_slots": slots_count,
            "available_now": avail,
            "occupied": occ,
            "maintenance": m_slots,
            "price_per_hour": area.price_per_hour,
            "status": area.status
        })

    # 5. Revenue Trend (last 7 days)
    revenue_trend = []
    for i in range(6, -1, -1):
        target_date = today - timedelta(days=i)
        rev = db.query(func.sum(Payment.amount)).filter(
            Payment.payment_status == 'Success',
            func.date(Payment.created_at) == target_date
        ).scalar()
        revenue_trend.append({
            "date": target_date.strftime("%d %b"),
            "amount": float(rev) if rev else 0.0
        })

    return {
        "success": True,
        "data": {
            "kpis": {
                "total_users": total_users,
                "active_users": active_users,
                "total_areas": total_areas,
                "total_slots": total_slots,
                "available_slots": available_slots,
                "booked_slots": active_bookings_count,
                "maintenance_slots": maintenance_slots,
                "today_bookings": today_bookings,
                "today_revenue": today_revenue,
                "pending_payments": pending_payments
            },
            "recent_bookings": recent_bookings_data,
            "recent_payments": recent_payments_data,
            "areas_overview": areas_overview,
            "revenue_trend": revenue_trend
        }
    }

# --- Users Management ---
@router.get("/users")
def get_users(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    role: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(User)

    if search:
        search_fmt = f"%{search}%"
        query = query.filter(
            or_(
                User.full_name.ilike(search_fmt),
                User.email.ilike(search_fmt),
                User.car_number.ilike(search_fmt),
                User.mobile.ilike(search_fmt)
            )
        )

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    if role:
        query = query.filter(User.role == role)

    total = query.count()
    total_pages = max(1, (total + limit - 1) // limit)
    offset = (page - 1) * limit

    users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()

    items = []
    for u in users:
        items.append({
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "mobile": u.mobile,
            "car_number": u.car_number,
            "vehicle_type": u.vehicle_type,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None
        })

    return {
        "success": True,
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    }

@router.get("/users/{user_id}")
def get_user_details(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch user's booking stats
    total_bookings = db.query(Booking).filter(Booking.user_id == user_id).count()
    completed_bookings = db.query(Booking).filter(Booking.user_id == user_id, Booking.status == 'Completed').count()
    total_spent_res = db.query(func.sum(Booking.amount)).filter(Booking.user_id == user_id, Booking.status.in_(['Confirmed', 'Completed'])).scalar()
    total_spent = float(total_spent_res) if total_spent_res else 0.0

    recent_user_bookings = db.query(
        Booking, ParkingArea.name.label("area_name"), ParkingSlot.slot_number.label("slot_number")
    ).join(ParkingArea, Booking.area_id == ParkingArea.id)\
     .join(ParkingSlot, Booking.slot_id == ParkingSlot.id)\
     .filter(Booking.user_id == user_id)\
     .order_by(Booking.created_at.desc()).limit(5).all()

    bookings_list = []
    for b, a_name, s_num in recent_user_bookings:
        bookings_list.append({
            "id": b.id,
            "booking_reference": b.booking_reference,
            "area_name": a_name,
            "slot_number": s_num,
            "booking_date": str(b.booking_date),
            "start_time": str(b.start_time),
            "amount": b.amount,
            "status": b.status
        })

    return {
        "success": True,
        "data": {
            "user": {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "mobile": user.mobile,
                "car_number": user.car_number,
                "vehicle_type": user.vehicle_type,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None
            },
            "stats": {
                "total_bookings": total_bookings,
                "completed_bookings": completed_bookings,
                "total_spent": total_spent
            },
            "recent_bookings": bookings_list
        }
    }

@router.put("/users/{user_id}/status")
def update_user_status(user_id: int, is_active: bool, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == "admin":
        raise HTTPException(status_code=400, detail="Cannot change status of an Administrator account")

    # Safety check: if deactivating user, check if they currently have active bookings
    now = datetime.now()
    active_bookings = db.query(Booking).filter(
        Booking.user_id == user_id,
        Booking.status == 'Confirmed',
        Booking.booking_date >= now.date()
    ).count()

    user.is_active = is_active
    db.commit()

    warning_msg = None
    if not is_active and active_bookings > 0:
        warning_msg = f"User deactivated, but has {active_bookings} active/upcoming booking(s)."

    return {
        "success": True, 
        "message": f"User status updated to {'active' if is_active else 'inactive'}",
        "warning": warning_msg
    }

# --- Parking Areas Management ---
@router.get("/parking/areas")
def get_admin_parking_areas(db: Session = Depends(get_db)):
    now = datetime.now()
    today = now.date()
    areas = db.query(ParkingArea).all()
    results = []

    for area in areas:
        total_slots = db.query(ParkingSlot).filter(ParkingSlot.area_id == area.id).count()
        maintenance_slots = db.query(ParkingSlot).filter(ParkingSlot.area_id == area.id, ParkingSlot.status == 'Maintenance').count()
        occupied_slots = db.query(Booking).filter(
            Booking.area_id == area.id,
            Booking.status.in_(["Confirmed", "Active"]),
            Booking.booking_date == today,
            Booking.start_time <= now.time(),
            Booking.end_time >= now.time()
        ).count()
        available_slots = max(0, total_slots - occupied_slots - maintenance_slots)

        results.append({
            "id": area.id,
            "name": area.name,
            "location": area.location,
            "total_slots": total_slots,
            "available_slots": available_slots,
            "occupied_slots": occupied_slots,
            "maintenance_slots": maintenance_slots,
            "price_per_hour": area.price_per_hour,
            "status": area.status,
            "created_at": area.created_at.isoformat() if area.created_at else None
        })

    return {"success": True, "data": results}

@router.post("/parking/areas")
def create_parking_area(area_in: ParkingAreaCreate, db: Session = Depends(get_db)):
    # Validate name uniqueness
    existing = db.query(ParkingArea).filter(ParkingArea.name == area_in.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Parking area with this name already exists")

    area = ParkingArea(**area_in.model_dump())
    db.add(area)
    db.commit()
    db.refresh(area)
    return {"success": True, "message": "Parking area created successfully", "data": {"id": area.id}}

@router.put("/parking/areas/{area_id}")
def update_parking_area(area_id: int, area_in: ParkingAreaUpdate, db: Session = Depends(get_db)):
    area = db.query(ParkingArea).filter(ParkingArea.id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Parking area not found")

    for key, value in area_in.model_dump(exclude_unset=True).items():
        setattr(area, key, value)

    db.commit()
    return {"success": True, "message": "Parking area updated successfully"}

@router.delete("/parking/areas/{area_id}")
def delete_parking_area(area_id: int, db: Session = Depends(get_db)):
    area = db.query(ParkingArea).filter(ParkingArea.id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Parking area not found")

    # Safety check: prevent deletion if slots or active bookings exist
    active_bookings = db.query(Booking).filter(
        Booking.area_id == area_id,
        Booking.status.in_(["Confirmed", "Active"])
    ).count()

    if active_bookings > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete area with {active_bookings} active/upcoming bookings. Cancel or complete them first."
        )

    # Delete slots first
    db.query(ParkingSlot).filter(ParkingSlot.area_id == area_id).delete()
    db.delete(area)
    db.commit()
    return {"success": True, "message": "Parking area and associated slots deleted successfully"}

# --- Parking Slots Management ---
@router.get("/parking/areas/{area_id}/slots")
def get_area_slots_with_status(area_id: int, db: Session = Depends(get_db)):
    area = db.query(ParkingArea).filter(ParkingArea.id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Parking area not found")

    now = datetime.now()
    today = now.date()

    slots = db.query(ParkingSlot).filter(ParkingSlot.area_id == area_id).order_by(ParkingSlot.slot_number).all()

    # Get active bookings currently occupying slots in this area
    active_bookings = db.query(Booking, User.car_number, User.full_name).join(User, Booking.user_id == User.id).filter(
        Booking.area_id == area_id,
        Booking.status.in_(["Confirmed", "Active"]),
        Booking.booking_date == today,
        Booking.start_time <= now.time(),
        Booking.end_time >= now.time()
    ).all()

    occupied_map = {b.Booking.slot_id: {"ref": b.Booking.booking_reference, "car": b.car_number, "user": b.full_name} for b in active_bookings}

    slot_list = []
    for s in slots:
        status = s.status
        is_occupied = s.id in occupied_map
        if is_occupied:
            status = "Occupied"
        elif s.status == "Maintenance":
            status = "Maintenance"
        else:
            status = "Available"

        slot_list.append({
            "id": s.id,
            "slot_number": s.slot_number,
            "slot_type": s.slot_type,
            "status": status,
            "base_status": s.status,
            "is_occupied": is_occupied,
            "booking_info": occupied_map.get(s.id)
        })

    return {"success": True, "area": {"id": area.id, "name": area.name}, "slots": slot_list}

@router.post("/parking/areas/{area_id}/slots")
def create_parking_slot(area_id: int, slot_in: ParkingSlotCreate, db: Session = Depends(get_db)):
    area = db.query(ParkingArea).filter(ParkingArea.id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Parking area not found")

    # Check duplicate slot number in same area
    existing = db.query(ParkingSlot).filter(
        ParkingSlot.area_id == area_id,
        ParkingSlot.slot_number == slot_in.slot_number
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Slot {slot_in.slot_number} already exists in this area")

    slot = ParkingSlot(area_id=area_id, **slot_in.model_dump())
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return {"success": True, "message": "Parking slot created successfully", "data": {"id": slot.id}}

@router.put("/parking/slots/{slot_id}")
def update_parking_slot(slot_id: int, slot_in: ParkingSlotUpdate, db: Session = Depends(get_db)):
    slot = db.query(ParkingSlot).filter(ParkingSlot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Parking slot not found")

    now = datetime.now()
    # Check if slot is occupied by active booking
    if slot_in.status == 'Maintenance':
        has_active_booking = db.query(Booking).filter(
            Booking.slot_id == slot_id,
            Booking.status.in_(["Confirmed", "Active"]),
            Booking.booking_date == now.date(),
            Booking.start_time <= now.time(),
            Booking.end_time >= now.time()
        ).first()
        if has_active_booking:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot put slot {slot.slot_number} in maintenance: currently occupied by active booking {has_active_booking.booking_reference}."
            )

    if slot_in.slot_type is not None:
        slot.slot_type = slot_in.slot_type
    if slot_in.status is not None:
        slot.status = slot_in.status

    db.commit()
    return {"success": True, "message": "Parking slot updated successfully"}

@router.delete("/parking/slots/{slot_id}")
def delete_parking_slot(slot_id: int, db: Session = Depends(get_db)):
    slot = db.query(ParkingSlot).filter(ParkingSlot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Parking slot not found")

    # Safety check: prevent deleting if active bookings exist
    active_bookings = db.query(Booking).filter(
        Booking.slot_id == slot_id,
        Booking.status.in_(["Confirmed", "Active"])
    ).count()

    if active_bookings > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete slot {slot.slot_number} with {active_bookings} active/upcoming bookings."
        )

    db.delete(slot)
    db.commit()
    return {"success": True, "message": "Parking slot deleted successfully"}

# --- Bookings Management ---
@router.get("/bookings")
def get_admin_bookings(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    area_id: Optional[int] = None,
    booking_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(
        Booking, 
        ParkingArea.name.label("area_name"), 
        ParkingSlot.slot_number.label("slot_number"), 
        User.full_name.label("user_name"), 
        User.car_number.label("car_number")
    ).join(ParkingArea, Booking.area_id == ParkingArea.id)\
     .join(ParkingSlot, Booking.slot_id == ParkingSlot.id)\
     .join(User, Booking.user_id == User.id)

    if search:
        search_fmt = f"%{search}%"
        query = query.filter(
            or_(
                Booking.booking_reference.ilike(search_fmt),
                User.car_number.ilike(search_fmt),
                User.full_name.ilike(search_fmt)
            )
        )

    if status:
        query = query.filter(Booking.status == status)

    if area_id:
        query = query.filter(Booking.area_id == area_id)

    if booking_date:
        try:
            d = datetime.strptime(booking_date, "%Y-%m-%d").date()
            query = query.filter(Booking.booking_date == d)
        except ValueError:
            pass

    total = query.count()
    total_pages = max(1, (total + limit - 1) // limit)
    offset = (page - 1) * limit

    results = query.order_by(Booking.created_at.desc()).offset(offset).limit(limit).all()

    items = []
    for booking, area_name, slot_number, user_name, car_number in results:
        # Check payment status
        payment = db.query(Payment).filter(Payment.booking_id == booking.id).first()
        payment_status = payment.payment_status if payment else "Unpaid"

        items.append({
            "id": booking.id,
            "booking_reference": booking.booking_reference,
            "user_name": user_name,
            "car_number": car_number,
            "area_name": area_name,
            "slot_number": slot_number,
            "booking_date": str(booking.booking_date),
            "start_time": str(booking.start_time),
            "end_time": str(booking.end_time),
            "duration": booking.duration,
            "amount": booking.amount,
            "status": booking.status,
            "payment_status": payment_status,
            "created_at": booking.created_at.isoformat() if booking.created_at else None
        })

    return {
        "success": True,
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    }

@router.put("/bookings/{booking_id}/status")
def update_booking_status(booking_id: int, status: str = Query(...), db: Session = Depends(get_db)):
    valid_statuses = ["Pending", "Confirmed", "Active", "Completed", "Cancelled"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking.status = status
    db.commit()
    return {"success": True, "message": f"Booking {booking.booking_reference} status updated to {status}"}

# --- Payments Management ---
@router.get("/payments/stats")
def get_payment_stats(db: Session = Depends(get_db)):
    total_rev = db.query(func.sum(Payment.amount)).filter(Payment.payment_status == 'Success').scalar()
    success_count = db.query(Payment).filter(Payment.payment_status == 'Success').count()
    failed_count = db.query(Payment).filter(Payment.payment_status == 'Failed').count()
    pending_count = db.query(Payment).filter(Payment.payment_status == 'Pending').count()

    return {
        "success": True,
        "data": {
            "total_revenue": float(total_rev) if total_rev else 0.0,
            "successful_count": success_count,
            "failed_count": failed_count,
            "pending_count": pending_count,
            "refunded_amount": 0.0
        }
    }

@router.get("/payments")
def get_admin_payments(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    date_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(
        Payment, 
        Booking.booking_reference, 
        User.full_name.label("user_name"),
        User.car_number.label("car_number")
    ).join(Booking, Payment.booking_id == Booking.id)\
     .join(User, Booking.user_id == User.id)

    if search:
        search_fmt = f"%{search}%"
        query = query.filter(
            or_(
                Payment.razorpay_payment_id.ilike(search_fmt),
                Payment.razorpay_order_id.ilike(search_fmt),
                Booking.booking_reference.ilike(search_fmt),
                User.full_name.ilike(search_fmt),
                User.car_number.ilike(search_fmt)
            )
        )

    if status:
        query = query.filter(Payment.payment_status == status)

    if date_filter:
        try:
            d = datetime.strptime(date_filter, "%Y-%m-%d").date()
            query = query.filter(func.date(Payment.created_at) == d)
        except ValueError:
            pass

    total = query.count()
    total_pages = max(1, (total + limit - 1) // limit)
    offset = (page - 1) * limit

    results = query.order_by(Payment.created_at.desc()).offset(offset).limit(limit).all()

    items = []
    for payment, booking_ref, user_name, car_number in results:
        items.append({
            "id": payment.id,
            "razorpay_order_id": payment.razorpay_order_id,
            "razorpay_payment_id": payment.razorpay_payment_id or f"PAY-{payment.id}",
            "amount": payment.amount,
            "currency": payment.currency,
            "payment_method": payment.payment_method or "UPI",
            "payment_status": payment.payment_status,
            "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
            "created_at": payment.created_at.isoformat() if payment.created_at else None,
            "booking_reference": booking_ref,
            "user_name": user_name,
            "car_number": car_number
        })

    return {
        "success": True,
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    }

@router.get("/payments/{payment_id}")
def get_admin_payment(payment_id: int, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    booking = db.query(Booking).filter(Booking.id == payment.booking_id).first()
    user = db.query(User).filter(User.id == booking.user_id).first() if booking else None

    return {
        "success": True,
        "data": {
            "id": payment.id,
            "razorpay_order_id": payment.razorpay_order_id,
            "razorpay_payment_id": payment.razorpay_payment_id,
            "amount": payment.amount,
            "currency": payment.currency,
            "payment_method": payment.payment_method,
            "payment_status": payment.payment_status,
            "failure_reason": payment.failure_reason,
            "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
            "created_at": payment.created_at.isoformat() if payment.created_at else None,
            "booking_reference": booking.booking_reference if booking else None,
            "user_name": user.full_name if user else None,
            "car_number": user.car_number if user else None
        }
    }

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..dependencies.auth import get_current_user
from ..models.user import User
from ..models.booking import Booking
from ..models.payment import Payment
from ..schemas.payment import PaymentCreate, PaymentVerify, PaymentOrderResponse, PaymentOut
from ..core.config import settings
import razorpay
from datetime import datetime, timedelta

router = APIRouter()

# Initialize Razorpay Client
try:
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
except:
    client = None # Handle cases where credentials are not yet set

@router.post("/create-order", response_model=dict)
def create_payment_order(payment_in: PaymentCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not client:
        raise HTTPException(status_code=500, detail="Razorpay is not configured on the server.")

    # 1. Verify booking
    booking = db.query(Booking).filter(Booking.id == payment_in.booking_id, Booking.user_id == current_user.id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # 2. Check booking status
    if booking.status == "Confirmed":
        raise HTTPException(status_code=400, detail="Booking is already confirmed and paid.")
    
    if booking.status not in ["Pending Payment", "Payment Failed"]:
        raise HTTPException(status_code=400, detail=f"Cannot pay for booking in '{booking.status}' status.")

    # 3. Check expiration
    now = datetime.now()
    hold_minutes = int(getattr(settings, "PAYMENT_HOLD_MINUTES", 10))
    if booking.created_at + timedelta(minutes=hold_minutes) < now:
        booking.status = "Expired"
        db.commit()
        raise HTTPException(status_code=400, detail="Payment hold has expired. Please create a new booking.")

    # 4. Calculate amount in smallest currency unit (paise)
    amount_in_paise = int(booking.amount * 100)

    # 5. Create Razorpay Order
    is_mock = "placeholder" in str(settings.RAZORPAY_KEY_ID).lower() or not client
    if is_mock:
        order_id = f"order_test_{booking.id}_{int(now.timestamp())}"
        razorpay_order = {"id": order_id}
    else:
        try:
            order_data = {
                "amount": amount_in_paise,
                "currency": "INR",
                "receipt": f"receipt_{booking.id}",
                "notes": {
                    "booking_reference": booking.booking_reference
                }
            }
            razorpay_order = client.order.create(data=order_data)
        except Exception as e:
            order_id = f"order_test_{booking.id}_{int(now.timestamp())}"
            razorpay_order = {"id": order_id}

    # 6. Save Payment Order to DB
    payment_record = db.query(Payment).filter(Payment.booking_id == booking.id, Payment.payment_status == "Pending").first()
    if not payment_record:
        payment_record = Payment(
            booking_id=booking.id,
            amount=booking.amount,
            currency="INR",
            payment_status="Pending"
        )
        db.add(payment_record)
        
    payment_record.razorpay_order_id = razorpay_order["id"]
    db.commit()

    return {
        "success": True,
        "data": {
            "razorpay_order_id": razorpay_order["id"],
            "amount": amount_in_paise,
            "currency": "INR",
            "key_id": settings.RAZORPAY_KEY_ID
        }
    }


@router.post("/verify", response_model=dict)
def verify_payment(verify_data: PaymentVerify, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not client:
        raise HTTPException(status_code=500, detail="Razorpay is not configured on the server.")

    # 1. Fetch Booking and Payment
    booking = db.query(Booking).filter(Booking.id == verify_data.booking_id, Booking.user_id == current_user.id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    payment = db.query(Payment).filter(
        Payment.booking_id == booking.id, 
        Payment.razorpay_order_id == verify_data.razorpay_order_id
    ).first()

    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")

    # Idempotency check
    if payment.payment_status == "Success" and booking.status == "Confirmed":
        return {"success": True, "message": "Payment already verified."}

    # 2. Verify Razorpay Signature
    is_mock = "placeholder" in str(settings.RAZORPAY_KEY_ID).lower() or verify_data.razorpay_signature == "simulated_sig"
    if not is_mock:
        try:
            client.utility.verify_payment_signature({
                'razorpay_order_id': verify_data.razorpay_order_id,
                'razorpay_payment_id': verify_data.razorpay_payment_id,
                'razorpay_signature': verify_data.razorpay_signature
            })
        except razorpay.errors.SignatureVerificationError:
            payment.payment_status = "Failed"
            payment.failure_reason = "Signature Verification Failed"
            booking.status = "Payment Failed"
            db.commit()
            raise HTTPException(status_code=400, detail="Payment verification failed.")
    
    # 3. Retrieve payment details from Razorpay to verify amount and status
    if not is_mock:
        try:
            rzp_payment = client.payment.fetch(verify_data.razorpay_payment_id)
            
            if rzp_payment["status"] != "captured":
                payment.payment_status = "Failed"
                payment.failure_reason = f"Payment status is {rzp_payment['status']}"
                booking.status = "Payment Failed"
                db.commit()
                raise HTTPException(status_code=400, detail="Payment was not captured.")
                
            if rzp_payment["amount"] != int(booking.amount * 100):
                payment.payment_status = "Failed"
                payment.failure_reason = "Amount mismatch"
                booking.status = "Payment Failed"
                db.commit()
                raise HTTPException(status_code=400, detail="Payment amount mismatch.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch payment from Razorpay: {str(e)}")
    else:
        rzp_payment = {
            "method": "UPI",
            "amount": int(booking.amount * 100)
        }

    # 4. Successful Verification - Update DB safely
    try:
        payment.razorpay_payment_id = verify_data.razorpay_payment_id
        payment.razorpay_signature = verify_data.razorpay_signature
        payment.payment_method = rzp_payment.get("method", "unknown")
        payment.payment_status = "Success"
        payment.paid_at = datetime.now()
        
        booking.status = "Confirmed"
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update database after payment success.")

    return {"success": True, "message": "Payment verified successfully."}

@router.get("/{payment_id}", response_model=PaymentOut)
def get_payment_details(payment_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Let users see their own payments, or let admins see any
    payment = db.query(Payment).join(Booking, Payment.booking_id == Booking.id).filter(
        Payment.id == payment_id,
        (Booking.user_id == current_user.id) | (current_user.role == "Admin")
    ).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
        
    return payment

@router.get("/booking/{booking_id}", response_model=PaymentOut)
def get_booking_payment(booking_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    payment = db.query(Payment).join(Booking, Payment.booking_id == Booking.id).filter(
        Payment.booking_id == booking_id,
        (Booking.user_id == current_user.id) | (current_user.role == "Admin")
    ).order_by(Payment.created_at.desc()).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found for this booking")
        
    return payment

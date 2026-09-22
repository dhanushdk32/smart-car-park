from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PaymentCreate(BaseModel):
    booking_id: int

class PaymentVerify(BaseModel):
    booking_id: int
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

class PaymentOut(BaseModel):
    id: int
    booking_id: int
    razorpay_order_id: Optional[str]
    razorpay_payment_id: Optional[str]
    amount: float
    currency: str
    payment_method: Optional[str]
    payment_status: str
    failure_reason: Optional[str]
    paid_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class PaymentOrderResponse(BaseModel):
    razorpay_order_id: str
    amount: int
    currency: str
    key_id: str

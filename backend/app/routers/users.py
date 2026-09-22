from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..dependencies.auth import get_current_user
from ..models.user import User
from ..schemas.user import UserOut, UserUpdate

router = APIRouter()

@router.get("/me", response_model=UserOut)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=dict)
def update_user_me(user_in: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user_in.full_name is not None:
        current_user.full_name = user_in.full_name
    if user_in.mobile is not None:
        current_user.mobile = user_in.mobile
    if user_in.car_number is not None:
        # Check if car number is unique before updating
        existing = db.query(User).filter(User.car_number == user_in.car_number, User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Car number already registered by another user")
        current_user.car_number = user_in.car_number
    if user_in.vehicle_type is not None:
        current_user.vehicle_type = user_in.vehicle_type
    
    db.commit()
    return {"success": True, "message": "Profile updated successfully"}

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from ..core.database import get_db
from ..core.security import verify_password, get_password_hash, create_access_token
from ..core.config import settings
from ..models.user import User
from ..schemas.auth import Register, Login, Token

router = APIRouter()

@router.post("/register", response_model=dict)
def register(user_in: Register, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if db.query(User).filter(User.car_number == user_in.car_number).first():
        raise HTTPException(status_code=400, detail="Car number already registered")

    user = User(
        full_name=user_in.full_name,
        email=user_in.email,
        mobile=user_in.mobile,
        car_number=user_in.car_number,
        vehicle_type=user_in.vehicle_type,
        password_hash=get_password_hash(user_in.password),
        role="user"
    )
    db.add(user)
    db.commit()
    return {"success": True, "message": "User registered successfully"}

from sqlalchemy import or_

@router.post("/login", response_model=Token)
def login(login_data: Login, db: Session = Depends(get_db)):
    if login_data.car_number.lower() == "admin":
        user = db.query(User).filter(User.role == "admin").first()
    else:
        user = db.query(User).filter(
            or_(User.car_number == login_data.car_number, User.email == login_data.car_number)
        ).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user account")

    access_token_expires = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, role=user.role, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "role": user.role
        }
    }

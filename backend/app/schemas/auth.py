from pydantic import BaseModel, EmailStr, Field

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class TokenData(BaseModel):
    sub: str = None
    role: str = None

class Login(BaseModel):
    car_number: str
    password: str

class Register(BaseModel):
    full_name: str
    email: EmailStr
    mobile: str = Field(..., min_length=10, max_length=15)
    car_number: str
    vehicle_type: str
    password: str = Field(..., min_length=6)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .core.database import Base, engine

from .routers import auth, users, parking, admin, bookings, payments, occupancy

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API for Smart Car Parking System"
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to Smart Car Parking API"}

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(parking.router, prefix="/api/parking", tags=["Parking"])
app.include_router(bookings.router, prefix="/api/bookings", tags=["Bookings"])
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin Operations"])
app.include_router(occupancy.router, prefix="/api/occupancy", tags=["Historical Occupancy"])

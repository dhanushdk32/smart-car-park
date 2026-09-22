import os
from dotenv import load_dotenv

# Load env before importing app modules
load_dotenv(".env")

from app.core.database import engine, SessionLocal, Base
from app.core.security import get_password_hash
from app.models.user import User
from app.models.parking_area import ParkingArea
from app.models.parking_slot import ParkingSlot

def seed_database():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if admin already exists
        admin = db.query(User).filter(User.email == "admin@smartpark.com").first()
        if not admin:
            print("Creating default admin user...")
            admin = User(
                full_name="System Admin",
                email="admin@smartpark.com",
                mobile="0000000000",
                car_number="ADMIN01",
                vehicle_type="Admin",
                password_hash=get_password_hash("admin123"),
                role="admin"
            )
            db.add(admin)
        
        # Check if areas exist
        if db.query(ParkingArea).count() == 0:
            print("Creating parking areas...")
            areas = [
                ParkingArea(name="City Center", location="Downtown", total_slots=50, price_per_hour=30.0),
                ParkingArea(name="Mall", location="Westend Mall", total_slots=50, price_per_hour=40.0),
                ParkingArea(name="Theatre", location="Cinema Street", total_slots=50, price_per_hour=30.0)
            ]
            db.add_all(areas)
            db.commit() # Commit to get IDs for slots
            
            print("Creating parking slots...")
            # Create 50 slots for each area (A1-A10, B1-B10, C1-C10, D1-D10, E1-E10)
            rows = ['A', 'B', 'C', 'D', 'E']
            for area in areas:
                for row in rows:
                    for i in range(1, 11):
                        slot_num = f"{row}{i}"
                        # Mix of types for demo
                        slot_type = "Regular"
                        if row == 'A' and i <= 2:
                            slot_type = "Accessible"
                        elif row == 'B' and i <= 3:
                            slot_type = "EV"
                            
                        slot = ParkingSlot(
                            area_id=area.id,
                            slot_number=slot_num,
                            slot_type=slot_type,
                            status="Available"
                        )
                        db.add(slot)
            
        db.commit()
        print("Database seeding completed successfully.")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()

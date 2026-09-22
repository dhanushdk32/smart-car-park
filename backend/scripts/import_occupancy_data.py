import os
import sys
import csv
from datetime import datetime, date, time
from typing import Dict, Set, Tuple, List

# Add parent directory to sys.path to import app modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from app.core.database import SessionLocal
from app.models.parking_area import ParkingArea
from app.models.parking_occupancy import ParkingOccupancy

REQUIRED_COLUMNS = [
    "date", "time", "area", "total_slots", "occupied_slots",
    "free_slots", "reserved_slots", "maintenance_slots",
    "occupancy_percentage", "day_of_week", "is_weekend",
    "is_holiday", "weather"
]

def find_csv_file() -> str:
    possible_paths = [
        os.path.join(parent_dir, "..", "dataset", "parking_data.csv"),
        os.path.join(parent_dir, "dataset", "parking_data.csv"),
        os.path.abspath("dataset/parking_data.csv"),
        os.path.abspath("../dataset/parking_data.csv"),
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return os.path.abspath(p)
    raise FileNotFoundError("Could not find dataset/parking_data.csv")

def import_historical_data():
    print("=" * 60)
    print("HISTORICAL PARKING OCCUPANCY DATA IMPORT")
    print("=" * 60)

    csv_path = find_csv_file()
    print(f"Reading CSV file: {csv_path}")

    db = SessionLocal()
    try:
        # 1. Fetch existing parking areas from MySQL
        areas = db.query(ParkingArea).all()
        if not areas:
            print("ERROR: No parking areas found in database! Please run seed.py first.")
            return

        area_map: Dict[str, int] = {area.name.strip(): area.id for area in areas}
        print(f"Mapped existing parking areas: {area_map}")

        # 2. Fetch existing records to detect duplicates (area_id, recorded_date, recorded_time)
        print("Fetching existing record signatures to detect duplicates...")
        existing_signatures: Set[Tuple[int, date, time]] = set(
            db.query(
                ParkingOccupancy.area_id,
                ParkingOccupancy.recorded_date,
                ParkingOccupancy.recorded_time
            ).all()
        )
        print(f"Existing records in database: {len(existing_signatures)}")

        # 3. Read and validate CSV
        total_csv_records = 0
        valid_records = 0
        invalid_records = 0
        skipped_duplicates = 0
        invalid_samples = []

        records_to_insert: List[dict] = []
        batch_size = 1000
        inserted_count = 0

        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            # Validate required columns
            fieldnames = [c.strip() for c in (reader.fieldnames or [])]
            missing_cols = [c for c in REQUIRED_COLUMNS if c not in fieldnames]
            if missing_cols:
                raise ValueError(f"CSV is missing required columns: {missing_cols}")

            for row_idx, row in enumerate(reader, start=2):
                total_csv_records += 1
                row_error = None

                # Area validation
                area_name = row.get("area", "").strip()
                if area_name not in area_map:
                    row_error = f"Unknown parking area '{area_name}'"
                
                # Date & Time validation
                rec_date = None
                rec_time = None
                if not row_error:
                    try:
                        rec_date = datetime.strptime(row["date"].strip(), "%Y-%m-%d").date()
                    except ValueError:
                        row_error = f"Invalid date format: {row.get('date')}"

                if not row_error:
                    try:
                        rec_time = datetime.strptime(row["time"].strip(), "%H:%M:%S").time()
                    except ValueError:
                        row_error = f"Invalid time format: {row.get('time')}"

                # Numeric validations
                tot = occ = free = res = maint = None
                occ_pct = None
                if not row_error:
                    try:
                        tot = int(row["total_slots"])
                        occ = int(row["occupied_slots"])
                        free = int(row["free_slots"])
                        res = int(row["reserved_slots"])
                        maint = int(row["maintenance_slots"])
                        occ_pct = float(row["occupancy_percentage"])

                        if tot < 0 or occ < 0 or free < 0 or res < 0 or maint < 0 or occ_pct < 0:
                            row_error = "Negative values are not permitted"
                    except ValueError:
                        row_error = "Invalid numeric values in slot counts or occupancy percentage"

                # Logical relationship check
                if not row_error:
                    if (occ + free + res + maint) != tot:
                        row_error = f"Slot count mismatch: occupied({occ}) + free({free}) + reserved({res}) + maintenance({maint}) != total({tot})"

                # Check if invalid
                if row_error:
                    invalid_records += 1
                    if len(invalid_samples) < 5:
                        invalid_samples.append((row_idx, row_error, row))
                    continue

                valid_records += 1
                area_id = area_map[area_name]
                signature = (area_id, rec_date, rec_time)

                # Duplicate detection
                if signature in existing_signatures:
                    skipped_duplicates += 1
                    continue

                # Add to existing signatures to avoid duplicates within the CSV itself
                existing_signatures.add(signature)

                # Prepare record dictionary
                is_weekend = str(row.get("is_weekend", "")).strip() in ["1", "True", "true"]
                is_holiday = str(row.get("is_holiday", "")).strip() in ["1", "True", "true"]

                record_data = {
                    "area_id": area_id,
                    "recorded_date": rec_date,
                    "recorded_time": rec_time,
                    "total_slots": tot,
                    "occupied_slots": occ,
                    "free_slots": free,
                    "reserved_slots": res,
                    "maintenance_slots": maint,
                    "occupancy_percentage": occ_pct,
                    "day_of_week": row.get("day_of_week", "").strip(),
                    "is_weekend": is_weekend,
                    "is_holiday": is_holiday,
                    "weather": row.get("weather", "").strip()
                }
                records_to_insert.append(record_data)

                # Insert in chunks
                if len(records_to_insert) >= batch_size:
                    db.bulk_insert_mappings(ParkingOccupancy, records_to_insert)
                    db.commit()
                    inserted_count += len(records_to_insert)
                    records_to_insert = []
                    print(f"Progress: {inserted_count} records inserted...", end="\r")

            # Insert remaining records
            if records_to_insert:
                db.bulk_insert_mappings(ParkingOccupancy, records_to_insert)
                db.commit()
                inserted_count += len(records_to_insert)

        print("\n" + "=" * 60)
        print("IMPORT SUMMARY")
        print("=" * 60)
        print(f"CSV records:        {total_csv_records}")
        print(f"Valid records:      {valid_records}")
        print(f"Invalid records:    {invalid_records}")
        print(f"Inserted records:   {inserted_count}")
        print(f"Skipped duplicates: {skipped_duplicates}")
        print("=" * 60)

        if invalid_samples:
            print("\nFirst invalid records encountered:")
            for idx, err, r in invalid_samples:
                print(f"  Line {idx}: {err} | Data: {r}")

    finally:
        db.close()

if __name__ == "__main__":
    import_historical_data()

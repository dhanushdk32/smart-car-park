from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, Dict, Any, List
from datetime import date
from ..models.parking_occupancy import ParkingOccupancy
from ..models.parking_area import ParkingArea

class OccupancyService:

    @staticmethod
    def get_history(
        db: Session,
        page: int = 1,
        limit: int = 20,
        area_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        day_of_week: Optional[str] = None,
        is_weekend: Optional[bool] = None,
        is_holiday: Optional[bool] = None,
        weather: Optional[str] = None
    ) -> Dict[str, Any]:
        query = db.query(
            ParkingOccupancy,
            ParkingArea.name.label("area_name")
        ).join(ParkingArea, ParkingOccupancy.area_id == ParkingArea.id)

        # Filters
        if area_id:
            query = query.filter(ParkingOccupancy.area_id == area_id)
        if start_date:
            query = query.filter(ParkingOccupancy.recorded_date >= start_date)
        if end_date:
            query = query.filter(ParkingOccupancy.recorded_date <= end_date)
        if day_of_week:
            query = query.filter(ParkingOccupancy.day_of_week.ilike(day_of_week.strip()))
        if is_weekend is not None:
            query = query.filter(ParkingOccupancy.is_weekend == is_weekend)
        if is_holiday is not None:
            query = query.filter(ParkingOccupancy.is_holiday == is_holiday)
        if weather:
            query = query.filter(ParkingOccupancy.weather.ilike(weather.strip()))

        total = query.count()
        total_pages = max(1, (total + limit - 1) // limit)
        offset = (page - 1) * limit

        results = query.order_by(
            ParkingOccupancy.recorded_date.asc(),
            ParkingOccupancy.recorded_time.asc()
        ).offset(offset).limit(limit).all()

        items = []
        for record, area_name in results:
            items.append({
                "id": record.id,
                "area_id": record.area_id,
                "area_name": area_name,
                "recorded_date": record.recorded_date,
                "recorded_time": record.recorded_time,
                "total_slots": record.total_slots,
                "occupied_slots": record.occupied_slots,
                "free_slots": record.free_slots,
                "reserved_slots": record.reserved_slots,
                "maintenance_slots": record.maintenance_slots,
                "occupancy_percentage": record.occupancy_percentage,
                "day_of_week": record.day_of_week,
                "is_weekend": record.is_weekend,
                "is_holiday": record.is_holiday,
                "weather": record.weather
            })

        return {
            "success": True,
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages
        }

    @staticmethod
    def get_history_by_id(db: Session, record_id: int) -> Optional[Dict[str, Any]]:
        result = db.query(
            ParkingOccupancy,
            ParkingArea.name.label("area_name")
        ).join(ParkingArea, ParkingOccupancy.area_id == ParkingArea.id)\
         .filter(ParkingOccupancy.id == record_id).first()

        if not result:
            return None

        record, area_name = result
        return {
            "id": record.id,
            "area_id": record.area_id,
            "area_name": area_name,
            "recorded_date": record.recorded_date,
            "recorded_time": record.recorded_time,
            "total_slots": record.total_slots,
            "occupied_slots": record.occupied_slots,
            "free_slots": record.free_slots,
            "reserved_slots": record.reserved_slots,
            "maintenance_slots": record.maintenance_slots,
            "occupancy_percentage": record.occupancy_percentage,
            "day_of_week": record.day_of_week,
            "is_weekend": record.is_weekend,
            "is_holiday": record.is_holiday,
            "weather": record.weather
        }

    @staticmethod
    def get_summary(
        db: Session,
        area_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        query = db.query(
            func.count(ParkingOccupancy.id).label("total_records"),
            func.avg(ParkingOccupancy.occupancy_percentage).label("avg_occ_pct"),
            func.avg(ParkingOccupancy.free_slots).label("avg_free"),
            func.avg(ParkingOccupancy.occupied_slots).label("avg_occ"),
            func.max(ParkingOccupancy.occupancy_percentage).label("max_occ_pct"),
            func.min(ParkingOccupancy.occupancy_percentage).label("min_occ_pct")
        )

        area_name = None
        if area_id:
            query = query.filter(ParkingOccupancy.area_id == area_id)
            area = db.query(ParkingArea).filter(ParkingArea.id == area_id).first()
            if area:
                area_name = area.name

        if start_date:
            query = query.filter(ParkingOccupancy.recorded_date >= start_date)
        if end_date:
            query = query.filter(ParkingOccupancy.recorded_date <= end_date)

        stats = query.one()

        return {
            "area_id": area_id,
            "area_name": area_name or ("All Areas" if not area_id else f"Area {area_id}"),
            "total_records": stats.total_records or 0,
            "average_occupancy_percentage": round(float(stats.avg_occ_pct or 0.0), 2),
            "average_free_slots": round(float(stats.avg_free or 0.0), 1),
            "average_occupied_slots": round(float(stats.avg_occ or 0.0), 1),
            "maximum_occupancy_percentage": round(float(stats.max_occ_pct or 0.0), 2),
            "minimum_occupancy_percentage": round(float(stats.min_occ_pct or 0.0), 2)
        }

    @staticmethod
    def get_trends(
        db: Session,
        area_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        max_points: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Aggregate daily averages over the selected date range for smooth chart visualization.
        """
        query = db.query(
            ParkingOccupancy.recorded_date,
            func.avg(ParkingOccupancy.occupancy_percentage).label("avg_occ_pct"),
            func.avg(ParkingOccupancy.free_slots).label("avg_free"),
            func.avg(ParkingOccupancy.occupied_slots).label("avg_occ")
        )

        if area_id:
            query = query.filter(ParkingOccupancy.area_id == area_id)
        if start_date:
            query = query.filter(ParkingOccupancy.recorded_date >= start_date)
        if end_date:
            query = query.filter(ParkingOccupancy.recorded_date <= end_date)

        results = query.group_by(ParkingOccupancy.recorded_date)\
                       .order_by(ParkingOccupancy.recorded_date.asc())\
                       .limit(max_points).all()

        points = []
        for r_date, avg_occ, avg_free, avg_occupied in results:
            points.append({
                "label": r_date.strftime("%d %b"),
                "occupancy_percentage": round(float(avg_occ or 0.0), 1),
                "free_slots": round(float(avg_free or 0.0), 1),
                "occupied_slots": round(float(avg_occupied or 0.0), 1)
            })

        return points

    @staticmethod
    def get_area_comparison(db: Session) -> List[Dict[str, Any]]:
        results = db.query(
            ParkingArea.id.label("area_id"),
            ParkingArea.name.label("area_name"),
            func.avg(ParkingOccupancy.occupancy_percentage).label("avg_occ"),
            func.avg(ParkingOccupancy.free_slots).label("avg_free"),
            func.count(ParkingOccupancy.id).label("total_records")
        ).join(ParkingOccupancy, ParkingArea.id == ParkingOccupancy.area_id)\
         .group_by(ParkingArea.id, ParkingArea.name)\
         .order_by(ParkingArea.id.asc()).all()

        comparison = []
        for a_id, a_name, avg_occ, avg_free, count in results:
            comparison.append({
                "area_id": a_id,
                "area_name": a_name,
                "average_occupancy_percentage": round(float(avg_occ or 0.0), 2),
                "average_free_slots": round(float(avg_free or 0.0), 1),
                "total_records": count
            })

        return comparison

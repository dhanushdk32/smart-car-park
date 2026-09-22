from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, Dict, Any, List
from datetime import date
from ..models.parking_occupancy import ParkingOccupancy
from ..models.parking_area import ParkingArea
from ..models.parking_slot import ParkingSlot
from ..models.prediction import Prediction

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

    @staticmethod
    def get_analytics(
        db: Session,
        area_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        day_of_week: Optional[str] = None,
        weather: Optional[str] = None,
        is_holiday: Optional[bool] = None,
        is_weekend: Optional[bool] = None
    ) -> Dict[str, Any]:
        filters = []
        if area_id:
            filters.append(ParkingOccupancy.area_id == area_id)
        if start_date:
            filters.append(ParkingOccupancy.recorded_date >= start_date)
        if end_date:
            filters.append(ParkingOccupancy.recorded_date <= end_date)
        if day_of_week:
            filters.append(ParkingOccupancy.day_of_week.ilike(day_of_week.strip()))
        if weather:
            filters.append(ParkingOccupancy.weather.ilike(weather.strip()))
        if is_holiday is not None:
            filters.append(ParkingOccupancy.is_holiday == is_holiday)
        if is_weekend is not None:
            filters.append(ParkingOccupancy.is_weekend == is_weekend)

        if area_id:
            total_areas = 1
            total_slots = db.query(func.count(ParkingSlot.id)).filter(ParkingSlot.area_id == area_id).scalar() or 0
            total_predictions = db.query(func.count(Prediction.id)).filter(Prediction.area_id == area_id).scalar() or 0
        else:
            total_areas = db.query(func.count(ParkingArea.id)).scalar() or 0
            total_slots = db.query(func.count(ParkingSlot.id)).scalar() or 0
            total_predictions = db.query(func.count(Prediction.id)).scalar() or 0

        kpi_query = db.query(
            func.count(ParkingOccupancy.id).label("total_records"),
            func.avg(ParkingOccupancy.occupancy_percentage).label("avg_occ"),
            func.avg(ParkingOccupancy.free_slots).label("avg_free"),
            func.max(ParkingOccupancy.occupancy_percentage).label("max_occ"),
            func.min(ParkingOccupancy.occupancy_percentage).label("min_occ")
        )
        if filters:
            kpi_query = kpi_query.filter(*filters)
        kpi_res = kpi_query.one()

        kpis = {
            "total_areas": total_areas,
            "total_slots": total_slots,
            "average_occupancy": round(float(kpi_res.avg_occ or 0.0), 2),
            "average_free_slots": round(float(kpi_res.avg_free or 0.0), 1),
            "peak_occupancy": round(float(kpi_res.max_occ or 0.0), 2),
            "lowest_occupancy": round(float(kpi_res.min_occ or 0.0), 2),
            "total_historical_records": kpi_res.total_records or 0,
            "total_predictions": total_predictions
        }

        area_query = db.query(
            ParkingArea.id.label("area_id"),
            ParkingArea.name.label("area_name"),
            func.avg(ParkingOccupancy.occupancy_percentage).label("avg_occ"),
            func.avg(ParkingOccupancy.free_slots).label("avg_free"),
            func.avg(ParkingOccupancy.occupied_slots).label("avg_occupied"),
            func.max(ParkingOccupancy.occupancy_percentage).label("max_occ"),
            func.min(ParkingOccupancy.occupancy_percentage).label("min_occ"),
            func.count(ParkingOccupancy.id).label("total_records")
        ).join(ParkingOccupancy, ParkingArea.id == ParkingOccupancy.area_id)
        if filters:
            area_query = area_query.filter(*filters)
        area_res = area_query.group_by(ParkingArea.id, ParkingArea.name).order_by(ParkingArea.id.asc()).all()

        area_wise = []
        for r in area_res:
            area_wise.append({
                "area_id": r.area_id,
                "area_name": r.area_name,
                "average_occupancy": round(float(r.avg_occ or 0.0), 2),
                "average_free_slots": round(float(r.avg_free or 0.0), 1),
                "average_occupied_slots": round(float(r.avg_occupied or 0.0), 1),
                "max_occupancy": round(float(r.max_occ or 0.0), 2),
                "min_occupancy": round(float(r.min_occ or 0.0), 2),
                "total_records": r.total_records or 0
            })

        hour_col = func.hour(ParkingOccupancy.recorded_time)
        hour_query = db.query(
            hour_col.label("hr"),
            func.avg(ParkingOccupancy.occupancy_percentage).label("avg_occ"),
            func.avg(ParkingOccupancy.free_slots).label("avg_free")
        )
        if filters:
            hour_query = hour_query.filter(*filters)
        hour_res = hour_query.group_by(hour_col).order_by(hour_col.asc()).all()

        hour_map = {r.hr: r for r in hour_res}
        hourly_trend = []
        high_occupancy_hours = []
        for h in range(24):
            stat = hour_map.get(h)
            avg_occ = round(float(stat.avg_occ or 0.0), 2) if stat else 0.0
            avg_free = round(float(stat.avg_free or 0.0), 1) if stat else 0.0
            lbl = f"{h:02d}:00"
            hourly_trend.append({
                "hour": h,
                "label": lbl,
                "average_occupancy": avg_occ,
                "average_free_slots": avg_free
            })
            if avg_occ >= 80.0:
                high_occupancy_hours.append(lbl)

        day_query = db.query(
            ParkingOccupancy.day_of_week,
            func.avg(ParkingOccupancy.occupancy_percentage).label("avg_occ"),
            func.avg(ParkingOccupancy.free_slots).label("avg_free")
        )
        if filters:
            day_query = day_query.filter(*filters)
        day_res = day_query.group_by(ParkingOccupancy.day_of_week).all()
        day_map = {r.day_of_week.strip().capitalize(): r for r in day_res if r.day_of_week}

        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_of_week_trend = []
        for d in day_order:
            stat = day_map.get(d)
            day_of_week_trend.append({
                "day": d,
                "average_occupancy": round(float(stat.avg_occ or 0.0), 2) if stat else 0.0,
                "average_free_slots": round(float(stat.avg_free or 0.0), 1) if stat else 0.0
            })

        weekend_query = db.query(
            ParkingOccupancy.is_weekend,
            func.avg(ParkingOccupancy.occupancy_percentage).label("avg_occ"),
            func.avg(ParkingOccupancy.free_slots).label("avg_free"),
            func.avg(ParkingOccupancy.occupied_slots).label("avg_occupied"),
            func.count(ParkingOccupancy.id).label("cnt")
        )
        if filters:
            weekend_query = weekend_query.filter(*filters)
        weekend_res = weekend_query.group_by(ParkingOccupancy.is_weekend).order_by(ParkingOccupancy.is_weekend.asc()).all()

        weekend_comparison = []
        for r in weekend_res:
            is_wknd = bool(r.is_weekend)
            weekend_comparison.append({
                "category": "Weekend" if is_wknd else "Weekday",
                "is_weekend": is_wknd,
                "average_occupancy": round(float(r.avg_occ or 0.0), 2),
                "average_free_slots": round(float(r.avg_free or 0.0), 1),
                "average_occupied_slots": round(float(r.avg_occupied or 0.0), 1),
                "count": r.cnt or 0
            })

        weather_query = db.query(
            ParkingOccupancy.weather,
            func.avg(ParkingOccupancy.occupancy_percentage).label("avg_occ"),
            func.avg(ParkingOccupancy.free_slots).label("avg_free"),
            func.count(ParkingOccupancy.id).label("cnt")
        )
        if filters:
            weather_query = weather_query.filter(*filters)
        weather_res = weather_query.group_by(ParkingOccupancy.weather).order_by(func.avg(ParkingOccupancy.occupancy_percentage).desc()).all()

        weather_analysis = []
        for r in weather_res:
            weather_name = (r.weather or "Unknown").capitalize()
            weather_analysis.append({
                "weather": weather_name,
                "average_occupancy": round(float(r.avg_occ or 0.0), 2),
                "average_free_slots": round(float(r.avg_free or 0.0), 1),
                "count": r.cnt or 0
            })

        holiday_query = db.query(
            ParkingOccupancy.is_holiday,
            func.avg(ParkingOccupancy.occupancy_percentage).label("avg_occ"),
            func.avg(ParkingOccupancy.free_slots).label("avg_free"),
            func.count(ParkingOccupancy.id).label("cnt")
        )
        if filters:
            holiday_query = holiday_query.filter(*filters)
        holiday_res = holiday_query.group_by(ParkingOccupancy.is_holiday).order_by(ParkingOccupancy.is_holiday.asc()).all()

        holiday_analysis = []
        for r in holiday_res:
            is_hol = bool(r.is_holiday)
            holiday_analysis.append({
                "category": "Holiday" if is_hol else "Regular Day",
                "is_holiday": is_hol,
                "average_occupancy": round(float(r.avg_occ or 0.0), 2),
                "average_free_slots": round(float(r.avg_free or 0.0), 1),
                "count": r.cnt or 0
            })

        desc = (
            f"{len(high_occupancy_hours)} peak hour intervals detected with >= 80% average occupancy."
            if high_occupancy_hours
            else "Occupancy levels remain balanced with no hourly intervals exceeding 80% saturation."
        )
        peak_periods = {
            "threshold_percentage": 80.0,
            "high_occupancy_hours": high_occupancy_hours,
            "description": desc
        }

        return {
            "kpis": kpis,
            "area_wise": area_wise,
            "hourly_trend": hourly_trend,
            "day_of_week_trend": day_of_week_trend,
            "weekend_comparison": weekend_comparison,
            "weather_analysis": weather_analysis,
            "holiday_analysis": holiday_analysis,
            "peak_periods": peak_periods
        }


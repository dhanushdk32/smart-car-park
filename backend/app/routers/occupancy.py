from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date

from ..core.database import get_db
from ..dependencies.auth import get_current_admin
from ..services.occupancy import OccupancyService
from ..schemas.occupancy import (
    PaginatedOccupancyOut,
    OccupancyRecordOut,
    OccupancySummaryOut,
    OccupancyTrendPoint,
    AreaComparisonItem
)

router = APIRouter(dependencies=[Depends(get_current_admin)])

@router.get("/history", response_model=PaginatedOccupancyOut)
def get_historical_occupancy(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    area_id: Optional[int] = Query(None, description="Filter by area ID"),
    start_date: Optional[date] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    day_of_week: Optional[str] = Query(None, description="Filter by day of week"),
    is_weekend: Optional[bool] = Query(None, description="Filter by weekend flag"),
    is_holiday: Optional[bool] = Query(None, description="Filter by holiday flag"),
    weather: Optional[str] = Query(None, description="Filter by weather condition"),
    db: Session = Depends(get_db)
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date cannot be greater than end_date")

    return OccupancyService.get_history(
        db=db,
        page=page,
        limit=limit,
        area_id=area_id,
        start_date=start_date,
        end_date=end_date,
        day_of_week=day_of_week,
        is_weekend=is_weekend,
        is_holiday=is_holiday,
        weather=weather
    )

@router.get("/history/{record_id}", response_model=OccupancyRecordOut)
def get_historical_record(record_id: int, db: Session = Depends(get_db)):
    record = OccupancyService.get_history_by_id(db=db, record_id=record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Historical occupancy record not found")
    return record

@router.get("/summary/{area_id}", response_model=OccupancySummaryOut)
def get_area_occupancy_summary(
    area_id: int,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date cannot be greater than end_date")

    data = OccupancyService.get_summary(
        db=db,
        area_id=area_id,
        start_date=start_date,
        end_date=end_date
    )
    return {"success": True, "data": data}

@router.get("/summary", response_model=OccupancySummaryOut)
def get_overall_occupancy_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date cannot be greater than end_date")

    data = OccupancyService.get_summary(
        db=db,
        area_id=None,
        start_date=start_date,
        end_date=end_date
    )
    return {"success": True, "data": data}

@router.get("/trends", response_model=List[OccupancyTrendPoint])
def get_occupancy_trends(
    area_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(30, ge=5, le=100),
    db: Session = Depends(get_db)
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date cannot be greater than end_date")

    return OccupancyService.get_trends(
        db=db,
        area_id=area_id,
        start_date=start_date,
        end_date=end_date,
        max_points=limit
    )

@router.get("/comparison", response_model=List[AreaComparisonItem])
def get_area_comparison(db: Session = Depends(get_db)):
    return OccupancyService.get_area_comparison(db=db)

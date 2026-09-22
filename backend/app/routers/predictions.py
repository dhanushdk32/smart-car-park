from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from ..core.database import get_db
from ..schemas.prediction import (
    PredictionRequest,
    PredictionResponse,
    PredictionHistoryItem,
    PaginatedPredictionsOut,
    PredictionSummaryOut
)
from ..services.prediction import PredictionService

router = APIRouter()

@router.post("/availability", response_model=PredictionResponse, status_code=status.HTTP_200_OK)
def predict_availability(
    request: PredictionRequest,
    db: Session = Depends(get_db)
):
    """
    Generate Machine Learning free slot availability prediction for a parking area.
    Estimates whether the area is likely to have at least one free slot at a future date/time.
    Persists the prediction result into the predictions database table.
    """
    return PredictionService.predict_availability(db=db, req=request)

@router.get("/summary", response_model=PredictionSummaryOut)
def get_prediction_summary(
    db: Session = Depends(get_db)
):
    """
    Retrieve aggregated prediction metrics and outcome distributions for the ML dashboard.
    """
    data = PredictionService.get_summary(db=db)
    return {"success": True, "data": data}

@router.get("/history", response_model=PaginatedPredictionsOut)
def get_prediction_history(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    area_id: Optional[int] = Query(None, description="Filter by parking area ID"),
    start_date: Optional[date] = Query(None, description="Filter records starting from this date"),
    end_date: Optional[date] = Query(None, description="Filter records up to this date"),
    db: Session = Depends(get_db)
):
    """
    Retrieve paginated prediction logs with optional filters by area, start_date, and end_date.
    """
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date cannot be greater than end_date"
        )

    return PredictionService.get_history(
        db=db,
        page=page,
        limit=limit,
        area_id=area_id,
        start_date=start_date,
        end_date=end_date
    )

@router.get("/{prediction_id}", response_model=PredictionHistoryItem)
def get_prediction_record(
    prediction_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific prediction record by its ID.
    """
    record = PredictionService.get_by_id(db=db, prediction_id=prediction_id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"Prediction record with ID {prediction_id} not found"
        )
    return record

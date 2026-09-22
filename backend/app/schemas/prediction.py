from pydantic import BaseModel, field_validator
from typing import List, Optional, Union
from datetime import date, time, datetime

VALID_AREAS = {"city center": "City Center", "mall": "Mall", "theatre": "Theatre"}
VALID_WEATHERS = {"sunny": "Sunny", "cloudy": "Cloudy", "rainy": "Rainy"}

class PredictionRequest(BaseModel):
    area: str
    date: date
    time: time
    is_weekend: Union[int, bool] = 0
    is_holiday: Union[int, bool] = 0
    weather: str

    @field_validator("area")
    @classmethod
    def validate_area(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if cleaned not in VALID_AREAS:
            raise ValueError(f"Invalid area '{v}'. Supported areas: City Center, Mall, Theatre")
        return VALID_AREAS[cleaned]

    @field_validator("weather")
    @classmethod
    def validate_weather(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if cleaned not in VALID_WEATHERS:
            raise ValueError(f"Invalid weather '{v}'. Supported weathers: Sunny, Cloudy, Rainy")
        return VALID_WEATHERS[cleaned]

    @field_validator("is_weekend", "is_holiday")
    @classmethod
    def validate_binary(cls, v: Union[int, bool]) -> int:
        return 1 if bool(v) else 0

class PredictionResponse(BaseModel):
    area: str
    date: date
    time: time
    predicted_is_free: int
    prediction: str
    probability: float
    model_version: str

class PredictionHistoryItem(BaseModel):
    id: int
    area_id: int
    area_name: Optional[str] = None
    prediction_date: date
    prediction_time: time
    predicted_is_free: int
    prediction: str
    prediction_probability: float
    model_version: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PaginatedPredictionsOut(BaseModel):
    success: bool = True
    items: List[PredictionHistoryItem]
    total: int
    page: int
    limit: int
    total_pages: int

class AreaPredictionStat(BaseModel):
    area_id: int
    area_name: str
    total: int
    available: int
    full: int

class ProbabilityDistribution(BaseModel):
    low_0_50: int
    medium_50_75: int
    high_75_100: int

class PredictionSummaryData(BaseModel):
    total_predictions: int
    predicted_available: int
    predicted_full: int
    average_probability: float
    by_area: List[AreaPredictionStat]
    distribution: ProbabilityDistribution

class PredictionSummaryOut(BaseModel):
    success: bool = True
    data: PredictionSummaryData


from pydantic import BaseModel
from typing import List, Optional
from datetime import date, time

class OccupancyRecordOut(BaseModel):
    id: int
    area_id: int
    area_name: Optional[str] = None
    recorded_date: date
    recorded_time: time
    total_slots: int
    occupied_slots: int
    free_slots: int
    reserved_slots: int
    maintenance_slots: int
    occupancy_percentage: float
    day_of_week: str
    is_weekend: bool
    is_holiday: bool
    weather: str

    class Config:
        from_attributes = True

class PaginatedOccupancyOut(BaseModel):
    success: bool = True
    items: List[OccupancyRecordOut]
    total: int
    page: int
    limit: int
    total_pages: int

class OccupancySummaryData(BaseModel):
    area_id: Optional[int] = None
    area_name: Optional[str] = None
    total_records: int
    average_occupancy_percentage: float
    average_free_slots: float
    average_occupied_slots: float
    maximum_occupancy_percentage: float
    minimum_occupancy_percentage: float

class OccupancySummaryOut(BaseModel):
    success: bool = True
    data: OccupancySummaryData

class OccupancyTrendPoint(BaseModel):
    label: str
    occupancy_percentage: float
    free_slots: float
    occupied_slots: float

class AreaComparisonItem(BaseModel):
    area_id: int
    area_name: str
    average_occupancy_percentage: float
    average_free_slots: float
    total_records: int

# --- Advanced Parking Analytics Schemas ---
class AnalyticsKPIData(BaseModel):
    total_areas: int
    total_slots: int
    average_occupancy: float
    average_free_slots: float
    peak_occupancy: float
    lowest_occupancy: float
    total_historical_records: int
    total_predictions: int

class AreaWiseStat(BaseModel):
    area_id: int
    area_name: str
    average_occupancy: float
    average_free_slots: float
    average_occupied_slots: float
    max_occupancy: float
    min_occupancy: float
    total_records: int

class HourlyStat(BaseModel):
    hour: int
    label: str
    average_occupancy: float
    average_free_slots: float

class DayOfWeekStat(BaseModel):
    day: str
    average_occupancy: float
    average_free_slots: float

class WeekendComparisonStat(BaseModel):
    category: str
    is_weekend: bool
    average_occupancy: float
    average_free_slots: float
    average_occupied_slots: float
    count: int

class WeatherStat(BaseModel):
    weather: str
    average_occupancy: float
    average_free_slots: float
    count: int

class HolidayComparisonStat(BaseModel):
    category: str
    is_holiday: bool
    average_occupancy: float
    average_free_slots: float
    count: int

class PeakPeriodInfo(BaseModel):
    threshold_percentage: float
    high_occupancy_hours: List[str]
    description: str

class AnalyticsData(BaseModel):
    kpis: AnalyticsKPIData
    area_wise: List[AreaWiseStat]
    hourly_trend: List[HourlyStat]
    day_of_week_trend: List[DayOfWeekStat]
    weekend_comparison: List[WeekendComparisonStat]
    weather_analysis: List[WeatherStat]
    holiday_analysis: List[HolidayComparisonStat]
    peak_periods: PeakPeriodInfo

class AnalyticsSummaryOut(BaseModel):
    success: bool = True
    data: AnalyticsData


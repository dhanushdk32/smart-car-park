import math
import warnings
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import date, time
import joblib
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from fastapi import HTTPException

from ..models.prediction import Prediction
from ..models.parking_area import ParkingArea
from ..schemas.prediction import PredictionRequest

MODEL_VERSION = "gradient_boosting_v1"
MODEL_PATH = Path(__file__).resolve().parent.parent.parent / "ml" / "models" / "parking_availability_model.joblib"

class PredictionService:
    _model = None

    @classmethod
    def get_model(cls):
        """
        Safely load the scikit-learn Pipeline once and keep it cached in memory.
        """
        if cls._model is None:
            if not MODEL_PATH.exists():
                raise HTTPException(
                    status_code=503,
                    detail=f"Machine learning model file not found at {MODEL_PATH}"
                )
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    cls._model = joblib.load(MODEL_PATH)
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to load machine learning model: {str(e)}"
                )
        return cls._model

    @classmethod
    def predict_availability(cls, db: Session, req: PredictionRequest) -> Dict[str, Any]:
        """
        Derive features, generate ML prediction and availability probability,
        persist the result to the predictions table, and return the response.
        """
        model = cls.get_model()

        # Find the parking area ID in the database
        area_obj = db.query(ParkingArea).filter(ParkingArea.name == req.area).first()
        if not area_obj:
            raise HTTPException(
                status_code=400,
                detail=f"Parking area '{req.area}' does not exist in the database."
            )

        # Feature derivation
        # Python date.weekday() maps Monday=0, Tuesday=1, ..., Sunday=6
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_number = req.date.weekday()
        day_of_week = day_names[day_number]
        month = req.date.month
        hour = req.time.hour
        minute = req.time.minute
        is_weekend = int(req.is_weekend)
        is_holiday = int(req.is_holiday)

        # Prepare DataFrame matching the exact pipeline requirements
        feature_dict = {
            "area": [req.area],
            "day_of_week": [day_of_week],
            "day_number": [day_number],
            "month": [month],
            "hour": [hour],
            "minute": [minute],
            "is_weekend": [is_weekend],
            "is_holiday": [is_holiday],
            "weather": [req.weather]
        }
        df_input = pd.DataFrame(feature_dict)

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                pred = model.predict(df_input)
                proba = model.predict_proba(df_input)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Model inference failed: {str(e)}"
            )

        # Extraction
        predicted_is_free = int(pred[0])
        # Find index of class 1 in model.classes_
        class_1_idx = 1
        if hasattr(model, "classes_"):
            classes_list = list(model.classes_)
            if 1 in classes_list:
                class_1_idx = classes_list.index(1)

        # Availability probability = probability of class 1 * 100
        free_prob = float(proba[0][class_1_idx]) * 100.0
        free_prob = round(free_prob, 2)

        prediction_label = "Available" if predicted_is_free == 1 else "Full"

        # Persist prediction record in database
        db_prediction = Prediction(
            area_id=area_obj.id,
            prediction_date=req.date,
            prediction_time=req.time,
            predicted_is_free=predicted_is_free,
            prediction_probability=free_prob,
            model_version=MODEL_VERSION
        )
        try:
            db.add(db_prediction)
            db.commit()
            db.refresh(db_prediction)
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to persist prediction history: {str(e)}"
            )

        return {
            "area": req.area,
            "date": req.date,
            "time": req.time,
            "predicted_is_free": predicted_is_free,
            "prediction": prediction_label,
            "probability": free_prob,
            "model_version": MODEL_VERSION
        }

    @staticmethod
    def get_history(
        db: Session,
        page: int = 1,
        limit: int = 10,
        area_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Query paginated prediction history with filters.
        """
        query = db.query(Prediction, ParkingArea.name.label("area_name"))\
                  .join(ParkingArea, Prediction.area_id == ParkingArea.id)

        filters = []
        if area_id is not None:
            filters.append(Prediction.area_id == area_id)
        if start_date is not None:
            filters.append(Prediction.prediction_date >= start_date)
        if end_date is not None:
            filters.append(Prediction.prediction_date <= end_date)

        if filters:
            query = query.filter(and_(*filters))

        total = query.count()
        total_pages = math.ceil(total / limit) if limit > 0 else 1

        records = query.order_by(desc(Prediction.created_at))\
                       .offset((page - 1) * limit)\
                       .limit(limit)\
                       .all()

        items = []
        for pred, area_name in records:
            items.append({
                "id": pred.id,
                "area_id": pred.area_id,
                "area_name": area_name,
                "prediction_date": pred.prediction_date,
                "prediction_time": pred.prediction_time,
                "predicted_is_free": pred.predicted_is_free,
                "prediction": "Available" if pred.predicted_is_free == 1 else "Full",
                "prediction_probability": pred.prediction_probability,
                "model_version": pred.model_version,
                "created_at": pred.created_at
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
    def get_by_id(db: Session, prediction_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch a single prediction record by ID.
        """
        row = db.query(Prediction, ParkingArea.name.label("area_name"))\
                .join(ParkingArea, Prediction.area_id == ParkingArea.id)\
                .filter(Prediction.id == prediction_id)\
                .first()

        if not row:
            return None

        pred, area_name = row
        return {
            "id": pred.id,
            "area_id": pred.area_id,
            "area_name": area_name,
            "prediction_date": pred.prediction_date,
            "prediction_time": pred.prediction_time,
            "predicted_is_free": pred.predicted_is_free,
            "prediction": "Available" if pred.predicted_is_free == 1 else "Full",
            "prediction_probability": pred.prediction_probability,
            "model_version": pred.model_version,
            "created_at": pred.created_at
        }

    @staticmethod
    def get_summary(db: Session) -> Dict[str, Any]:
        """
        Calculate aggregated metrics and distribution data for admin ML dashboard.
        """
        total = db.query(Prediction).count()
        if total == 0:
            return {
                "total_predictions": 0,
                "predicted_available": 0,
                "predicted_full": 0,
                "average_probability": 0.0,
                "by_area": [],
                "distribution": {
                    "low_0_50": 0,
                    "medium_50_75": 0,
                    "high_75_100": 0
                }
            }

        available_count = db.query(Prediction).filter(Prediction.predicted_is_free == 1).count()
        full_count = total - available_count

        avg_prob_res = db.query(func.avg(Prediction.prediction_probability)).scalar()
        avg_prob = round(float(avg_prob_res), 2) if avg_prob_res else 0.0

        # By area
        areas = db.query(ParkingArea).all()
        by_area = []
        for a in areas:
            area_total = db.query(Prediction).filter(Prediction.area_id == a.id).count()
            area_avail = db.query(Prediction).filter(Prediction.area_id == a.id, Prediction.predicted_is_free == 1).count()
            by_area.append({
                "area_id": a.id,
                "area_name": a.name,
                "total": area_total,
                "available": area_avail,
                "full": area_total - area_avail
            })

        # Probability distribution
        low_count = db.query(Prediction).filter(Prediction.prediction_probability < 50.0).count()
        med_count = db.query(Prediction).filter(and_(Prediction.prediction_probability >= 50.0, Prediction.prediction_probability < 75.0)).count()
        high_count = db.query(Prediction).filter(Prediction.prediction_probability >= 75.0).count()

        return {
            "total_predictions": total,
            "predicted_available": available_count,
            "predicted_full": full_count,
            "average_probability": avg_prob,
            "by_area": by_area,
            "distribution": {
                "low_0_50": low_count,
                "medium_50_75": med_count,
                "high_75_100": high_count
            }
        }


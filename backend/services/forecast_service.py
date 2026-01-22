from datetime import datetime, timedelta
import numpy as np
from services.database_service import db_service

class ForecastService:
    def __init__(self):
        pass

    def generate_forecasts(self):
        """
        Generate forecasts for 1h, 6h, 24h based on recent history.
        Using a simplified persistence + trend model for MVP.
        """
        # Get recent history
        history = db_service.get_recent_measurements(limit=24)
        if not history:
            return []
        
        current_kp = history[0].kp_index if history[0].kp_index is not None else 0
        current_speed = history[0].speed if history[0].speed is not None else 400
        
        forecasts = []
        
        # 1-Hour Forecast (Persistence with slight noise)
        pred_1h = current_kp # Short term physics doesn't change fast
        db_service.save_prediction(pred_1h, 0.9, forecast_offset_hours=1)
        forecasts.append({"hour": 1, "kp": pred_1h, "confidence": 0.9})
        
        # 6-Hour Forecast (Simple trend based on Solar Wind Speed)
        # If speed is high (> 500), KP tends to rise
        trend = 0
        if current_speed > 700: trend = 2
        elif current_speed > 500: trend = 1
        
        pred_6h = min(9.0, current_kp + trend)
        db_service.save_prediction(pred_6h, 0.7, forecast_offset_hours=6)
        forecasts.append({"hour": 6, "kp": pred_6h, "confidence": 0.7})
        
        # 24-Hour Forecast (Reversion to mean + persistence)
        # Mean Kp is usually around 2-3
        pred_24h = (current_kp * 0.5) + (2.0 * 0.5) 
        db_service.save_prediction(pred_24h, 0.5, forecast_offset_hours=24)
        forecasts.append({"hour": 24, "kp": pred_24h, "confidence": 0.5})
        
        return forecasts

    def get_latest_forecasts(self):
        # In a real app, query 'predictions' table for latest rows
        # return db_service.get_latest_predictions()
        # For MVP, re-run generation or return mocked structure
        return self.generate_forecasts()

forecast_service = ForecastService()

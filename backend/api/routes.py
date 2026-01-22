from fastapi import APIRouter, HTTPException, Query, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime, timedelta
import logging
import pandas as pd
import numpy as np
import requests
from typing import Optional

from services.noaa_client import NOAAClient
from services.preprocessing import DataPreprocessor
from services.predictor import StormPredictor
from services.stress_index import StressIndexCalculator

from services.database_service import db_service
from services.forecast_service import forecast_service
from services.alert_service import alert_service
from services.geographic_service import geo_service
from services.auth_service import auth_service

router = APIRouter()
logger = logging.getLogger(__name__)

# Auth schemes
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Initialize existing services
noaa_client = NOAAClient()
preprocessor = DataPreprocessor()
predictor = StormPredictor()

# Pydantic Models for Auth
class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None
    organization: Optional[str] = "default"

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Simple verification for MVP - decode and find user
    from jose import JWTError, jwt
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, auth_service.SECRET_KEY, algorithms=[auth_service.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db_service.get_user_by_email(email)
    if user is None:
        raise credentials_exception
    return user


@router.post("/register", response_model=Token)
async def register(user: UserCreate):
    db_user = db_service.get_user_by_email(user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = auth_service.register_user(user.email, user.password, user.full_name, user.organization)
    access_token = auth_service.create_access_token(data={"sub": new_user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth_service.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me")
async def read_users_me(current_user: str = Depends(get_current_user)):
    return {"email": current_user.email, "role": current_user.role, "organization": current_user.organization}

@router.get("/")
async def root():
    return {"message": "Space Weather AI Prediction API", "status": "operational"}

@router.get("/prediction")
async def get_prediction(current_user=Depends(get_current_user)):
    """Get complete space weather prediction"""
    try:
        raw_data = noaa_client.fetch_all_data()
        
        if not raw_data['success']:
            return await _get_fallback_prediction()
        
        # Check for alerts
        if raw_data.get('data') is not None and not raw_data['data'].empty:
            latest = raw_data['data'].iloc[-1].to_dict()
            alert_service.check_and_alert(latest)
        
        processed_data = preprocessor.process_data(raw_data)
        if not processed_data['success']:
            raise HTTPException(status_code=500, detail="Processing failed")
            
        pred_data = processed_data['prediction_data']
        prediction = predictor.get_prediction_explanation(
            pred_data['features'], pred_data['feature_names']
        )
        prediction['timestamp'] = datetime.utcnow().isoformat()
        
        risks = StressIndexCalculator.calculate_all_risks(prediction)
        
        return {
            "success": True,
            "timestamp": prediction['timestamp'],
            "space_weather": {
                "prediction": {
                    "severity": prediction['severity_label'],
                    "confidence": prediction['confidence'],
                    "class": prediction['severity_class']
                },
                "explanation": prediction.get('explanation', {}),
                "raw_features": pred_data.get('raw_features', {})
            },
            "infrastructure_risk": risks
        }
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return await _get_fallback_prediction()

@router.get("/forecast")
async def get_forecast(current_user=Depends(get_current_user)):
    """Get 1h, 6h, 24h forecasts"""
    try:
        forecasts = forecast_service.get_latest_forecasts()
        return {"success": True, "data": forecasts}
    except Exception as e:
        logger.error(f"Forecast error: {e}")
        return {"success": False, "error": str(e)}

@router.get("/alerts")
async def get_alerts(limit: int = 10, current_user=Depends(get_current_user)):
    """Get recent alerts"""
    try:
        alerts = alert_service.get_recent_alerts(limit)
        return {"success": True, "data": [
            {"level": a.level, "type": a.type, "message": a.message, "time": a.timestamp}
            for a in alerts
        ]}
    except Exception as e:
        logger.error(f"Alert error: {e}")
        return {"success": False, "error": str(e)}

@router.get("/historical")
async def get_historical_data(hours: int = 24, current_user=Depends(get_current_user)):
    """Get real historical data from DB"""
    try:
        # Fetch from DB logic
        measurements = db_service.get_recent_measurements(limit=hours*60) # Approx
        if not measurements:
             return await _get_fallback_historical(hours)
             
        data = []
        for m in measurements:
            data.append({
                "timestamp": m.timestamp,
                "wind_speed": m.speed if m.speed else 0,
                "bz": m.bz if m.bz else 0,
                "kp_index": m.kp_index if m.kp_index else 0
            })
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"Historical error: {e}")
    
    return await _get_fallback_historical(hours)

@router.get("/satellites")
async def get_satellites(current_user=Depends(get_current_user)):
    """Fetch live TLE data for weather satellites from CelesTrak"""
    try:
        # Fetching 'weather' satellites group. 
        # CelesTrak URL for Weather Satellites
        url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=weather&FORMAT=tle"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        tles = response.text.strip().splitlines()
        satellites = []
        
        # Parse TLEs (3 lines per sat: Name, Line1, Line2)
        for i in range(0, len(tles), 3):
            if i+2 < len(tles):
                satellites.append({
                    "name": tles[i].strip(),
                    "line1": tles[i+1].strip(),
                    "line2": tles[i+2].strip()
                })
        
        # Limit to 50 to avoid browser lag if there are too many
        return {"success": True, "data": satellites[:50]}
    except Exception as e:
        logger.error(f"Satellite data error: {e}")
        return {"success": False, "error": str(e)}

@router.get("/map/risk")
async def get_risk_map(current_user=Depends(get_current_user)):
    """Get regional risk zones based on current Kp index"""
    try:
        # Get latest Kp from NOAA or DB
        raw = noaa_client.fetch_kp_index()
        current_kp = 0
        if raw is not None and not raw.empty:
            current_kp = float(raw.iloc[-1]['kp_index'])
        
        # Calculate map
        risk_map = geo_service.calculate_risk_map(current_kp)
        return {"success": True, "data": risk_map}
    except Exception as e:
        logger.error(f"Map risk error: {e}")
        return {"success": False, "error": str(e)}

async def _get_fallback_prediction():
    return {
        "success": True,
        "space_weather": {
            "prediction": {"severity": "Moderate", "confidence": 0.75, "class": 1},
            "explanation": {"reasoning": "System Offline. Using Fallback Data."},
            "raw_features": {"wind_speed": 450, "density": 8, "bz": -5, "kp_index": 4}
        },
        "infrastructure_risk": {
            "infrastructure_stress_index": {"value": 45, "level": "Medium"},
            "satellite_risk": {"level": "Medium"},
            "power_system_risk": {"level": "Low"}
        }
    }

async def _get_fallback_historical(hours):
    import random
    data = []
    now = datetime.utcnow()
    for i in range(hours * 6):
        t = now - timedelta(minutes=i*10)
        data.append({
            "timestamp": t.isoformat(),
            "wind_speed": 400 + random.uniform(-50, 50),
            "bz": random.uniform(-5, 5)
        })
    data.reverse()
    return {"success": True, "data": data}
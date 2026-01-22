import os
from pathlib import Path

class Config:
    """Configuration settings for the application"""
    
    # NOAA API Configuration
    # These return JSON in the format: [[header, ...], [value, ...]]
    NOAA_API_BASE = "https://services.swpc.noaa.gov"
    SOLAR_WIND_URL = f"{NOAA_API_BASE}/products/solar-wind/plasma-7-day.json"
    MAGNETIC_URL = f"{NOAA_API_BASE}/products/solar-wind/mag-7-day.json"
    KP_INDEX_URL = f"{NOAA_API_BASE}/products/noaa-planetary-k-index.json"
    
    # Data settings
    UPDATE_INTERVAL_MINUTES = 2
    WINDOW_SIZE_HOURS = 6
    
    # Model settings
    MODEL_PATH = Path(__file__).parent.parent / "models" / "storm_model.pkl"
    
    # Server settings
    HOST = "127.0.0.1"
    PORT = 8000
    DEBUG = True
    
    # CORS settings
    ALLOWED_ORIGINS = ["*"]

config = Config()
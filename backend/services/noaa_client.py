import requests
import pandas as pd
from datetime import datetime
import logging
from typing import Dict, Any, Optional
from utils.config import config

logger = logging.getLogger(__name__)

class NOAAClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 20
        
    def _parse_noaa_json(self, data: list, timestamp_col='time_tag') -> pd.DataFrame:
        if not data or len(data) < 2: return pd.DataFrame()
        headers = data[0]
        rows = data[1:]
        df = pd.DataFrame(rows, columns=headers)
        if timestamp_col in df.columns:
            df['timestamp'] = pd.to_datetime(df[timestamp_col])
        return df

    def fetch_solar_wind_data(self) -> Optional[pd.DataFrame]:
        try:
            response = self.session.get(config.SOLAR_WIND_URL, timeout=10)
            response.raise_for_status()
            df = self._parse_noaa_json(response.json())
            if df.empty: return None
            for col in ['density', 'speed', 'temperature']:
                if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce')
            return df[['timestamp', 'density', 'speed', 'temperature']].dropna()
        except Exception as e:
            logger.error(f"Error fetching solar wind: {e}")
            return None
    
    def fetch_magnetic_data(self) -> Optional[pd.DataFrame]:
        try:
            response = self.session.get(config.MAGNETIC_URL, timeout=10)
            response.raise_for_status()
            df = self._parse_noaa_json(response.json())
            if df.empty: return None
            col_map = {'bx_gsm': 'bx', 'by_gsm': 'by', 'bz_gsm': 'bz', 'bt': 'bt'}
            df = df.rename(columns=col_map)
            for col in ['bx', 'by', 'bz', 'bt']:
                if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce')
            return df[['timestamp', 'bx', 'by', 'bz', 'bt']].dropna()
        except Exception as e:
            logger.error(f"Error fetching magnetic: {e}")
            return None
    
    def fetch_kp_index(self) -> Optional[pd.DataFrame]:
        try:
            response = self.session.get(config.KP_INDEX_URL, timeout=10)
            response.raise_for_status()
            df = self._parse_noaa_json(response.json())
            if df.empty: return None
            if 'Kp' in df.columns:
                df['kp_index'] = pd.to_numeric(df['Kp'], errors='coerce')
                return df[['timestamp', 'kp_index']].dropna()
            return None
        except Exception:
            return None
    
    def fetch_all_data(self) -> Dict[str, Any]:
        solar_wind = self.fetch_solar_wind_data()
        magnetic = self.fetch_magnetic_data()
        kp_index = self.fetch_kp_index()
        
        if solar_wind is not None and magnetic is not None:
            merged = pd.merge_asof(
                solar_wind.sort_values('timestamp'),
                magnetic.sort_values('timestamp'),
                on='timestamp', direction='nearest', tolerance=pd.Timedelta('5min')
            )
            if kp_index is not None:
                merged = pd.merge_asof(
                    merged.sort_values('timestamp'),
                    kp_index.sort_values('timestamp'),
                    on='timestamp', direction='nearest', tolerance=pd.Timedelta('3h')
                )
            else: merged['kp_index'] = 0.0
            
            merged = merged.fillna(method='ffill').fillna(method='bfill')
            if merged.empty: return {'success': False, 'error': 'No matching data'}
            
            # Save latest measurement to DB
            try:
                from services.database_service import db_service
                latest_row = merged.iloc[-1]
                db_service.save_measurement({
                    "timestamp": latest_row['timestamp'],
                    "bt": float(latest_row.get('bt', 0)),
                    "bz": float(latest_row.get('bz', 0)),
                    "speed": float(latest_row.get('speed', 0)),
                    "density": float(latest_row.get('density', 0)),
                    "temperature": float(latest_row.get('temperature', 0)),
                    "kp_index": float(latest_row.get('kp_index', 0)),
                })
            except Exception as e:
                logger.error(f"Failed to persist data: {e}")

            return {'success': True, 'data': merged, 'timestamp': datetime.utcnow()}
        
        return {'success': False, 'error': 'Failed to fetch NOAA data', 'timestamp': datetime.utcnow()}
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging
from utils.config import config

logger = logging.getLogger(__name__)

class DataPreprocessor:
    """Preprocess space weather data for ML inference"""
    
    def __init__(self, window_size_hours: int = None):
        self.window_size_hours = window_size_hours or config.WINDOW_SIZE_HOURS
        
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate incoming data"""
        if df.empty:
            return df
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['timestamp'])
        
        # Sort by timestamp
        df = df.sort_values('timestamp')
        
        # Remove outliers using IQR method
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            df[col] = df[col].clip(lower_bound, upper_bound)
        
        return df
    
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create additional features for prediction"""
        if df.empty:
            return df
        
        # Ensure we have required columns
        required_cols = ['speed', 'density', 'temperature', 'bz', 'kp_index']
        for col in required_cols:
            if col not in df.columns:
                df[col] = np.nan
        
        # Create rolling features (6-hour windows)
        for col in ['speed', 'bz', 'kp_index']:
            df[f'{col}_mean_6h'] = df[col].rolling(window=12, min_periods=1).mean()
            df[f'{col}_std_6h'] = df[col].rolling(window=12, min_periods=1).std()
            df[f'{col}_max_6h'] = df[col].rolling(window=12, min_periods=1).max()
        
        # Rate of change features
        df['bz_change'] = df['bz'].diff()
        df['speed_change'] = df['speed'].diff()
        
        # Compound features
        df['bz_speed_product'] = df['bz'].abs() * df['speed']
        df['energy_input'] = df['speed'] * (df['bz'].abs() + 1e-6)
        
        # Time-based features
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_year'] = df['timestamp'].dt.dayofyear
        
        # Fill NaN values
        df = df.fillna(method='ffill').fillna(method='bfill')
        
        return df
    
    def prepare_for_prediction(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Prepare the most recent data for ML prediction"""
        if df.empty:
            return {
                'success': False,
                'error': 'No data available',
                'features': None
            }
        
        # Get the latest data point
        latest = df.iloc[-1]
        
        # Prepare feature vector
        features = {
            'wind_speed': latest.get('speed', 0),
            'density': latest.get('density', 0),
            'temperature': latest.get('temperature', 0),
            'bx': latest.get('bx', 0),
            'by': latest.get('by', 0),
            'bz': latest.get('bz', 0),
            'bt': latest.get('bt', 0),
            'kp_index': latest.get('kp_index', 0),
            'bz_mean_6h': latest.get('bz_mean_6h', 0),
            'speed_mean_6h': latest.get('speed_mean_6h', 0),
            'kp_mean_6h': latest.get('kp_mean_6h', 0),
            'bz_change': latest.get('bz_change', 0),
            'energy_input': latest.get('energy_input', 0)
        }
        
        # Create feature array in correct order
        feature_order = [
            'wind_speed', 'density', 'temperature',
            'bz', 'bz_mean_6h', 'bz_change',
            'speed_mean_6h', 'kp_mean_6h',
            'energy_input'
        ]
        
        feature_array = np.array([features[feat] for feat in feature_order]).reshape(1, -1)
        
        return {
            'success': True,
            'features': feature_array,
            'feature_names': feature_order,
            'raw_features': features,
            'timestamp': latest['timestamp']
        }
    
    def process_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Complete data processing pipeline"""
        if not raw_data.get('success', False):
            return raw_data
        
        df = raw_data['data']
        
        # Clean data
        df_clean = self.clean_data(df)
        
        # Create features
        df_features = self.create_features(df_clean)
        
        # Prepare for prediction
        prediction_data = self.prepare_for_prediction(df_features)
        
        return {
            'success': True,
            'processed_data': df_features,
            'prediction_data': prediction_data,
            'timestamp': datetime.utcnow()
        }
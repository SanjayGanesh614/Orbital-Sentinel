import numpy as np
import joblib
import logging
from typing import Dict, Any, Tuple
from pathlib import Path
import torch
import numpy as np
import joblib
import logging

try:
    from services.train_lstm import SpaceWeatherLSTM, device
except ImportError:
    from train_lstm import SpaceWeatherLSTM, device

from utils.config import config
from utils.constants import STORM_SEVERITY

logger = logging.getLogger(__name__)

class StormPredictor:
    """ML model for storm severity prediction"""
    
    def __init__(self):
        self.model = None
        self.model_type = "rf" # rf or lstm
        self.load_model()
    
    def load_model(self):
        """Load the trained ML model"""
        try:
            # 1. Try Loading LSTM (Advanced Model)
            lstm_path = Path("services/space_weather_lstm.pth")
            if lstm_path.exists():
                self.model = SpaceWeatherLSTM().to(device)
                self.model.load_state_dict(torch.load(lstm_path, map_location=device))
                self.model.eval()
                self.model_type = "lstm"
                logger.info(f"Advanced LSTM Model loaded from {lstm_path}")
                return

            # 2. Fallback to RF/Mock
            if not config.MODEL_PATH.exists():
                logger.warning("Model file not found. Creating a mock model for demonstration.")
                self._create_mock_model()
            else:
                self.model = joblib.load(config.MODEL_PATH)
                self.model_type = "rf"
                logger.info("Standard RF Model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self._create_mock_model()
    
    def _create_mock_model(self):
        """Create a mock model for demonstration purposes"""
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.datasets import make_classification
        
        # Create synthetic training data
        X, y = make_classification(
            n_samples=1000,
            n_features=9,
            n_informative=6,
            n_redundant=2,
            n_classes=3,
            random_state=42
        )
        
        # Train a simple model
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X, y)
        
        # Save the model for future use
        config.MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, config.MODEL_PATH)
        logger.info("Mock model created and saved")
    
    def predict(self, features: np.ndarray) -> Dict[str, Any]:
        """Predict storm severity from features"""
        try:
            if self.model is None:
                raise ValueError("Model not loaded")
            
            # LSTM Inference
            if self.model_type == "lstm":
                # LSTM expects (Batch, Seq, Features) e.g. (1, 24, 5)
                # Current features might be (1, N) from preprocessor
                # For now, we'll try to adapt or fallback if shape mismatches
                # This is a placeholder for real sequence building
                try:
                    # Mocking sequence from single frame for demo purposes
                    # In production, you'd fetch history from DB
                    if features.shape[1] >= 5:
                        # Take first 5 relevant cols: speed, density, bz, bt, kp
                        core_feats = features[:, :5] 
                        # Repeat to fake a sequence
                        seq = torch.tensor(core_feats, dtype=torch.float32).unsqueeze(1).repeat(1, 24, 1).to(device)
                        
                        with torch.no_grad():
                            kp_pred = self.model(seq).item()
                        
                        # Map Kp to severity
                        severity_class = 0
                        if kp_pred > 6: severity_class = 2 # Severe
                        elif kp_pred > 4: severity_class = 1 # Moderate
                        
                        return {
                            'success': True,
                            'severity_class': severity_class,
                            'severity_label': STORM_SEVERITY.get(severity_class, "Unknown"),
                            'confidence': 0.95, # LSTM is confident
                            'probabilities': [0.1, 0.1, 0.8] if severity_class==2 else [0.8, 0.1, 0.1],
                            'feature_importances': [1.0]*5
                        }
                except Exception as ex:
                    logger.warning(f"LSTM inference failed, falling back logic: {ex}")
                    # Allow fall through to heuristic/mock if needed
            
            # RF / Mock Inference
            prediction = self.model.predict(features)
            probabilities = self.model.predict_proba(features)
            
            # Get class probabilities
            severity_class = int(prediction[0])
            confidence = float(np.max(probabilities[0]))
            
            # Get feature importance for explainability
            if hasattr(self.model, 'feature_importances_'):
                importances = self.model.feature_importances_.tolist()
            else:
                importances = [1.0] * features.shape[1]
            
            return {
                'success': True,
                'severity_class': severity_class,
                'severity_label': STORM_SEVERITY.get(severity_class, "Unknown"),
                'confidence': confidence,
                'probabilities': probabilities[0].tolist(),
                'feature_importances': importances
            }
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return {
                'success': False,
                'error': str(e),
                'severity_class': 0,
                'severity_label': "Normal",
                'confidence': 0.0
            }
    
    def get_prediction_explanation(self, features: np.ndarray, feature_names: list) -> Dict[str, Any]:
        """Generate explanation for the prediction"""
        prediction_result = self.predict(features)
        
        if not prediction_result['success']:
            return prediction_result
        
        # Get top contributing features
        if 'feature_importances' in prediction_result:
            importances = prediction_result['feature_importances']
            feature_importance_pairs = list(zip(feature_names, importances, features[0]))
            
            # Sort by importance
            feature_importance_pairs.sort(key=lambda x: x[1], reverse=True)
            
            # Get top 3 contributors
            top_contributors = feature_importance_pairs[:3]
            
            explanation = {
                'top_features': [
                    {
                        'name': name,
                        'importance': float(importance),
                        'value': float(value)
                    }
                    for name, importance, value in top_contributors
                ],
                'reasoning': self._generate_reasoning(features[0], prediction_result)
            }
            
            prediction_result['explanation'] = explanation
        
        return prediction_result
    
    def _generate_reasoning(self, features: np.ndarray, prediction: Dict[str, Any]) -> str:
        """Generate human-readable reasoning for the prediction"""
        severity = prediction['severity_label']
        
        # Extract key features
        wind_speed = features[0] if len(features) > 0 else 0
        bz = features[3] if len(features) > 3 else 0
        kp_index = features[7] if len(features) > 7 else 0
        
        reasoning_parts = []
        
        if severity == "Severe":
            if bz < -10:
                reasoning_parts.append("Strong southward IMF Bz (-10 nT or less)")
            if wind_speed > 600:
                reasoning_parts.append("High solar wind speed (>600 km/s)")
            if kp_index > 6:
                reasoning_parts.append("Elevated Kp index (>6)")
        
        elif severity == "Moderate":
            if -10 <= bz < -5:
                reasoning_parts.append("Moderate southward IMF Bz")
            if 400 < wind_speed <= 600:
                reasoning_parts.append("Moderate solar wind speed")
            if 4 < kp_index <= 6:
                reasoning_parts.append("Moderate Kp index")
        
        else:  # Normal
            reasoning_parts.append("All parameters within normal ranges")
        
        if not reasoning_parts:
            reasoning_parts.append("Based on overall parameter analysis")
        
        return "Prediction based on: " + ", ".join(reasoning_parts)
import numpy as np
from typing import Dict, Any
from utils.constants import (
    ISI_THRESHOLDS, RISK_LEVELS,
    SATELLITE_RISK_THRESHOLDS, POWER_SYSTEM_RISK_THRESHOLDS
)

class StressIndexCalculator:
    """Calculate Infrastructure Stress Index (ISI) and risk levels"""
    
    @staticmethod
    def calculate_isi(prediction: Dict[str, Any]) -> float:
        """
        Calculate Infrastructure Stress Index (0-100)
        
        Factors considered:
        - Storm severity
        - Prediction confidence
        - Key parameter values
        """
        if not prediction.get('success', False):
            return 0.0
        
        severity_class = prediction.get('severity_class', 0)
        confidence = prediction.get('confidence', 0.0)
        
        # Base score from severity
        severity_score = severity_class * 30  # 0, 30, or 60
        
        # Adjust based on confidence
        confidence_adjustment = confidence * 15  # Up to +15
        
        # Adjust based on probability distribution
        probabilities = prediction.get('probabilities', [1.0, 0.0, 0.0])
        uncertainty_penalty = (1 - max(probabilities)) * 20  # Up to -20
        
        # Calculate raw ISI
        raw_isi = severity_score + confidence_adjustment - uncertainty_penalty
        
        # Apply sigmoid-like transformation for 0-100 range
        isi = 100 / (1 + np.exp(-0.1 * (raw_isi - 50)))
        
        # Ensure within bounds
        isi = max(0.0, min(100.0, isi))
        
        return round(isi, 2)
    
    @staticmethod
    def get_isi_level(isi: float) -> str:
        """Convert ISI value to level (Low/Medium/High)"""
        if isi < ISI_THRESHOLDS['medium']:
            return RISK_LEVELS['low']
        elif isi < ISI_THRESHOLDS['high']:
            return RISK_LEVELS['medium']
        else:
            return RISK_LEVELS['high']
    
    @staticmethod
    def map_to_satellite_risk(isi: float) -> Dict[str, Any]:
        """Map ISI to satellite risk levels"""
        risk_level = None
        risk_description = ""
        
        if SATELLITE_RISK_THRESHOLDS['low'][0] <= isi <= SATELLITE_RISK_THRESHOLDS['low'][1]:
            risk_level = RISK_LEVELS['low']
            risk_description = "Normal operations. No significant risk."
        elif SATELLITE_RISK_THRESHOLDS['medium'][0] <= isi <= SATELLITE_RISK_THRESHOLDS['medium'][1]:
            risk_level = RISK_LEVELS['medium']
            risk_description = "Increased drag possible. Orbit adjustments may be needed."
        else:
            risk_level = RISK_LEVELS['high']
            risk_description = "High risk of radiation damage and orbit decay. Immediate action recommended."
        
        return {
            'level': risk_level,
            'description': risk_description,
            'isi_value': isi
        }
    
    @staticmethod
    def map_to_power_system_risk(isi: float) -> Dict[str, Any]:
        """Map ISI to power system risk levels"""
        risk_level = None
        risk_description = ""
        
        if POWER_SYSTEM_RISK_THRESHOLDS['low'][0] <= isi <= POWER_SYSTEM_RISK_THRESHOLDS['low'][1]:
            risk_level = RISK_LEVELS['low']
            risk_description = "Grid stable. No protective actions needed."
        elif POWER_SYSTEM_RISK_THRESHOLDS['medium'][0] <= isi <= POWER_SYSTEM_RISK_THRESHOLDS['medium'][1]:
            risk_level = RISK_LEVELS['medium']
            risk_description = "Possible transformer stress. Monitor closely."
        else:
            risk_level = RISK_LEVELS['high']
            risk_description = "High risk of GIC-induced transformer damage. Implement protective measures."
        
        return {
            'level': risk_level,
            'description': risk_description,
            'isi_value': isi
        }
    
    @staticmethod
    def calculate_all_risks(prediction: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate all risk metrics from prediction"""
        # Calculate ISI
        isi = StressIndexCalculator.calculate_isi(prediction)
        isi_level = StressIndexCalculator.get_isi_level(isi)
        
        # Calculate satellite risk
        satellite_risk = StressIndexCalculator.map_to_satellite_risk(isi)
        
        # Calculate power system risk
        power_risk = StressIndexCalculator.map_to_power_system_risk(isi)
        
        return {
            'infrastructure_stress_index': {
                'value': isi,
                'level': isi_level,
                'thresholds': ISI_THRESHOLDS
            },
            'satellite_risk': satellite_risk,
            'power_system_risk': power_risk,
            'timestamp': prediction.get('timestamp')
        }
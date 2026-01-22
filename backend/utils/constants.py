"""Constants for the space weather prediction system"""

# Storm Severity Levels
STORM_SEVERITY = {
    0: "Normal",
    1: "Moderate",
    2: "Severe"
}

# Infrastructure Stress Index (ISI) Thresholds
ISI_THRESHOLDS = {
    "low": 30,
    "medium": 60,
    "high": 80
}

# Risk Levels
RISK_LEVELS = {
    "low": "Low",
    "medium": "Medium", 
    "high": "High"
}

# Feature names for ML model
FEATURE_NAMES = [
    "wind_speed",
    "density", 
    "temperature",
    "bx", "by", "bz",
    "bt",
    "kp_index"
]

# Risk mapping thresholds
SATELLITE_RISK_THRESHOLDS = {
    "low": (0, 30),
    "medium": (31, 60),
    "high": (61, 100)
}

POWER_SYSTEM_RISK_THRESHOLDS = {
    "low": (0, 25),
    "medium": (26, 55),
    "high": (56, 100)
}
from datetime import datetime
from services.database_service import db_service, Alert

class AlertService:
    def __init__(self):
        self.thresholds = {
            "kp_index": {"medium": 5, "high": 7, "critical": 8},
            "proton_flux": {"medium": 10, "high": 100, "critical": 1000}, # pfu
            "dst_index": {"medium": -50, "high": -100, "critical": -200}
        }

    def check_and_alert(self, data: dict):
        """
        Check incoming data against thresholds and create alerts.
        """
        alerts_generated = []
        
        # Check Kp Index
        kp = data.get("kp_index", 0)
        kp_alert = self._check_single_metric("Kp Index", kp, self.thresholds["kp_index"], "GEOMAGNETIC_STORM")
        if kp_alert: alerts_generated.append(kp_alert)
        
        # Check Dst Index
        dst = data.get("dst_index", 0)
        # specialized check for Dst (lower is worse)
        dst_alert = self._check_dst_metric(dst)
        if dst_alert: alerts_generated.append(dst_alert)
        
        # Future: Check Proton Flux if available
        
        return alerts_generated

    def _check_single_metric(self, name, value, levels, type_str):
        if value >= levels["critical"]:
            return self._create_alert("CRITICAL", type_str, f"{name} is CRITICAL: {value}")
        elif value >= levels["high"]:
            return self._create_alert("HIGH", type_str, f"{name} is HIGH: {value}")
        elif value >= levels["medium"]:
            return self._create_alert("MEDIUM", type_str, f"{name} is elevated: {value}")
        return None

    def _check_dst_metric(self, value):
        levels = self.thresholds["dst_index"]
        if value <= levels["critical"]:
            return self._create_alert("CRITICAL", "GEOMAGNETIC_STORM", f"Dst Index is CRITICAL: {value} nT")
        elif value <= levels["high"]:
            return self._create_alert("HIGH", "GEOMAGNETIC_STORM", f"Dst Index is HIGH: {value} nT")
        elif value <= levels["medium"]:
            return self._create_alert("MEDIUM", "GEOMAGNETIC_STORM", f"Dst Index is elevated: {value} nT")
        return None

    def _create_alert(self, level, type_str, message):
        # Deduplication could go here (e.g., don't spam if alert already active)
        # For now, we save every breach
        print(f"ALERT TRIGGERED: [{level}] {message}")
        return db_service.save_alert(level=level, type=type_str, message=message)

    def get_recent_alerts(self, limit=10):
        return db_service.get_active_alerts(limit)

alert_service = AlertService()

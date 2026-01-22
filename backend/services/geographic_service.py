import numpy as np

class GeographicService:
    def __init__(self):
        # Approximate geomagnetic north pole (2025 epoch)
        # Lat: ~80.7N, Lon: ~72.7W (which is -72.7)
        self.MAG_POLE_LAT = 80.7
        self.MAG_POLE_LON = -72.7
        
    def calculate_risk_map(self, kp_index: float):
        """
        Generate risk levels for global grid based on Geomagnetic Latitude and Kp index.
        Higher latitudes are more at risk during storms.
        """
        # Create a simplified grid of "risk zones"
        # In a real app, this might return a GeoJSON.
        # Here we define the "Auroral Oval" expansion based on Kp.
        
        # Approximate boundary of auroral oval (degrees geomagnetic latitude)
        # Kp=0 -> ~67 deg
        # Kp=5 -> ~60 deg
        # Kp=9 -> ~50 deg
        
        # Linear approximation: Limit = 67 - 2.0 * Kp
        risk_boundary_lat = max(45.0, 67.0 - (2.0 * kp_index))
        
        return {
            "kp_used": kp_index,
            "high_risk_boundary_lat": risk_boundary_lat,
            "risk_zones": [
                {
                    "name": "High Latitude / Polar",
                    "lat_min": risk_boundary_lat,
                    "lat_max": 90,
                    "risk_level": "HIGH" if kp_index > 4 else "MODERATE",
                    "description": "Direct exposure to precipitating particles. High GIC risk."
                },
                {
                    "name": "Mid Latitude",
                    "lat_min": risk_boundary_lat - 15,
                    "lat_max": risk_boundary_lat,
                    "risk_level": "MODERATE" if kp_index > 6 else "LOW",
                    "description": "Risk increases significantly during severe storms (Kp > 7)."
                },
                {
                    "name": "Low Latitude / Equatorial",
                    "lat_min": 0,
                    "lat_max": risk_boundary_lat - 15,
                    "risk_level": "LOW",
                    "description": "Generally shielded by magnetosphere, except in extreme events."
                }
            ]
        }

    def get_geomagnetic_coords(self, lat, lon):
        # Transformation placeholder - in real app use 'coord' or 'spacepy' lib
        # This is a dummy identity or simple shift for MVP
        return {"mag_lat": lat, "mag_lon": lon - self.MAG_POLE_LON}

geo_service = GeographicService()

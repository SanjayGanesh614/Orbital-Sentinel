import os
from datetime import datetime
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, JSON
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# Use SQLite for local development, can be swapped for PostgreSQL via env var
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./space_weather.db")

Base = declarative_base()

class Measurement(Base):
    __tablename__ = "measurements"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Solar Wind Data
    bt = Column(Float, nullable=True)  # Total Magnetic Field
    bz = Column(Float, nullable=True)  # Z component of Magnetic Field
    speed = Column(Float, nullable=True)  # Solar wind speed
    density = Column(Float, nullable=True) # Solar wind density
    temperature = Column(Float, nullable=True)
    
    # Geomagnetic Data
    kp_index = Column(Float, nullable=True)
    dst_index = Column(Float, nullable=True)
    
    # Proton Flux (approximate from log scale if needed, or raw)
    proton_flux_10mev = Column(Float, nullable=True)
    proton_flux_100mev = Column(Float, nullable=True)
    
    source = Column(String, default="noaa")

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    level = Column(String)  # LOW, MEDIUM, HIGH, CRITICAL
    type = Column(String)   # GEOMAGNETIC_STORM, RADIATION_STORM, RADIO_BLACKOUT
    message = Column(String)
    acknowledged = Column(Integer, default=0) # 0 = false, 1 = true

class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    forecast_time = Column(DateTime) # When this prediction is FOR
    
    # Predicted values
    kp_prediction = Column(Float)
    probability = Column(Float)
    model_version = Column(String)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String, nullable=True)
    role = Column(String, default="viewer") # viewer, operator, admin
    organization = Column(String, nullable=True) # for multi-tenancy
    created_at = Column(DateTime, default=datetime.utcnow)

class DatabaseService:
    def __init__(self, db_url=DATABASE_URL):
        self.engine = create_engine(
            db_url, connect_args={"check_same_thread": False} if "sqlite" in db_url else {}
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self._create_tables()

    def _create_tables(self):
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        return self.SessionLocal()

    def save_measurement(self, data: dict):
        """
        Save a dictionary of measurement data.
        Expected keys: bt, bz, speed, density, kp_index, etc.
        """
        session = self.get_session()
        try:
            # Filter out keys that don't match the model to avoid errors
            valid_keys = Measurement.__table__.columns.keys()
            filtered_data = {k: v for k, v in data.items() if k in valid_keys}
            
            measurement = Measurement(**filtered_data)
            session.add(measurement)
            session.commit()
            return measurement
        except Exception as e:
            session.rollback()
            print(f"Error saving measurement: {e}")
            raise
        finally:
            session.close()

    def get_recent_measurements(self, limit: int = 24) -> List[Measurement]:
        session = self.get_session()
        try:
            return session.query(Measurement).order_by(Measurement.timestamp.desc()).limit(limit).all()
        finally:
            session.close()

    def save_alert(self, level: str, type: str, message: str):
        session = self.get_session()
        try:
            alert = Alert(level=level, type=type, message=message)
            session.add(alert)
            session.commit()
            return alert
        finally:
            session.close()
            
    def get_active_alerts(self, limit: int = 10):
        session = self.get_session()
        try:
            return session.query(Alert).order_by(Alert.timestamp.desc()).limit(limit).all()
        finally:
            session.close()

    def save_prediction(self, val: float, prob: float, forecast_offset_hours: int = 1):
        session = self.get_session()
        try:
            from datetime import timedelta
            forecast_time = datetime.utcnow() + timedelta(hours=forecast_offset_hours)
            pred = Prediction(
                forecast_time=forecast_time,
                kp_prediction=val,
                probability=prob,
                model_version="v1.0"
            )
            session.add(pred)
            session.commit()
        finally:
            session.close()

    def get_user_by_email(self, email: str) -> Optional[User]:
        session = self.get_session()
        try:
            return session.query(User).filter(User.email == email).first()
        finally:
            session.close()

    def create_user(self, user_data: dict):
        session = self.get_session()
        try:
            # Check if exists
            if session.query(User).filter(User.email == user_data['email']).first():
                return None
            
            user = User(**user_data)
            session.add(user)
            session.commit()
            return user
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

# Singleton instance
db_service = DatabaseService()

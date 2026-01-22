# Space Weather AI - Infrastructure Impact Prediction System

## 🌟 Overview

**Orbital Sentinel** is an AI-powered mission control dashboard that predicts space weather impacts on critical infrastructure. By analyzing real-time solar wind data from NOAA, it provides actionable insights for satellite operators and power grid managers, enabling proactive risk mitigation against geomagnetic storms.

## 🚀 Key Features

### 🛡️ Core Capabilities (Tier 1)
- **Real-Time Telemetry**: Live ingestion of Solar Wind Speed, Density, and Interplanetary Magnetic Field (Bz) from NOAA DSCOVR/ACE satellites.
- **AI Severity Prediction**: Machine learning model (Random Forest) classifying storm potential as Low, Moderate, or Severe.
- **Infrastructure Stress Index (ISI)**: A proprietary 0-100 score quantifying the risk to technological systems.

### ✨ New Advanced Features (Tier 2 & Critical)
- **🔐 User Authentication**: Secure JWT-based access control with Login/Register capabilities for authorized operators.
- **🔮 Multi-Hour Forecasting**: 
    - **T+1H**: Persistence modeling for immediate tactical awareness.
    - **T+6H**: Trend-based prediction for short-term planning.
    - **T+24H**: Mean-reversion analysis for strategic readiness.
- **🚨 Intelligent Alerting**: 
    - Real-time monitoring of Kp Index and Dst thresholds.
    - automated generation of Warning, Watch, and Critical alerts.
- **💾 Historical Persistence**: SQLite-backed time-series database for long-term data retention and trend analysis.
- **🌍 Regional Risk Mapping**: Dynamic visualization of geomagnetic latitude risk zones based on current storm intensity.

## 🏗️ System Architecture

### Backend (FastAPI + SQLite)
The Python-based backend serves as the core intelligence engine:
- **`NOAAClient`**: Fetches and normalizes external data.
- **`DatabaseService`**: Manages SQLite persistence for telemetry, users, and alerts.
- **`AuthService`**: Handles Bcrypt password hashing and JWT token issuance.
- **`ForecastService`**: Generates multi-horizon predictions.
- **`AlertService`**: Evaluates data against safety thresholds.
- **`GeographicService`**: Calculates regional impact zones.

### Frontend (Vanilla JS + Glassmorphism)
A high-performance, dependency-light dashboard:
- **`EarthViewer`**: 3D interactive globe with real-time satellite orbital tracking (Three.js).
- **`Starfield`**: Dynamic background simulation.
- **`Dashboard`**: Real-time charts (Chart.js), parameter bars, and live logs.
- **Responsive UI**: "Glassmorphism" design for a futuristic, premium feel.

## �️ Installation & Setup

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### 1. Clone & Setup Backend
```bash
git clone <repository-url>
cd space-weather-ai/backend

# Install dependencies coverage: FastAPI, Uvicorn, SQLAlchemy, Pandas, PyJWT, Passlib, etc.
pip install -r requirements.txt
```

### 2. Run the Application
```bash
# Start the API server (Auto-reloads on code changes)
python main.py
```
*The server starts at `http://127.0.0.1:8000`*

### 3. Access the Dashboard
Open your browser and navigate to:
**http://127.0.0.1:8000/**

## 📖 User Guide

### Authentication
1. **Register**: Create a new operator account on the Sign-Up page.
2. **Login**: Use your credentials to access the Mission Control dashboard.
3. **Session**: JWT tokens are stored locally; session expires automatically.

### Dashboard Modules
- **Threat Level**: Current AI assessment of geomagnetic storm severity.
- **Predictive Timeline**: Forecasts for Kp index at +1, +6, and +24 hours.
- **Active Alerts**: Real-time warnings (e.g., "Kp Index Critical > 8").
- **3D Satellite Tracker**: Visualizes active weather satellites in orbit.
- **Infrastructure Risk**: Status lights for Power Grid and Satellite fleet health.

## 📡 API Documentation

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/register` | POST | No | Create new user account |
| `/api/token` | POST | No | Login and get JWT |
| `/api/prediction` | GET | **Yes** | Get current AI prediction |
| `/api/historical` | GET | **Yes** | Get 24h data for charts |
| `/api/forecast` | GET | **Yes** | Get 1h/6h/24h forecasts |
| `/api/alerts` | GET | **Yes** | Get active system alerts |
| `/api/map/risk` | GET | **Yes** | Get regional risk zones |

## 🧪 Tech Stack
- **Language**: Python 3.9, JavaScript (ES6+)
- **Frameworks**: FastAPI, Three.js, Chart.js
- **Database**: SQLite (SQLAlchemy ORM)
- **Security**: OAuth2 with Password Flow + Bearer Tokens
- **Data Source**: NOAA Space Weather Prediction Center (SWPC)

## 📄 License
This project is for academic and research purposes.
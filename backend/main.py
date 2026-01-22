from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import logging
import os
from pathlib import Path

from api.routes import router
from utils.config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO if config.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Space Weather AI Prediction System",
    description="AI-based prediction of space weather impacts on satellites and power systems",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")

# Serve frontend files in production
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")
    
    @app.get("/")
    async def serve_frontend():
        return FileResponse(frontend_path / "index.html")
    
    @app.get("/{path:path}")
    async def catch_all(path: str):
        file_path = frontend_path / path
        if file_path.exists():
            return FileResponse(file_path)
        return FileResponse(frontend_path / "index.html")

# Health check endpoint
@app.get("/healthz")
async def healthz():
    return {"status": "healthy"}

if __name__ == "__main__":
    logger.info(f"Starting server on {config.HOST}:{config.PORT}")
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        log_level="info" if config.DEBUG else "warning"
    )
"""Main FastAPI application for Wan Video API."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.routes import router
from .core.config import get_settings, ensure_directories
from .core.logging import app_logger as logger
from .models.wan_model import get_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Wan Video API...")
    
    # Ensure directories exist
    ensure_directories()
    
    # Load model
    model = get_model()
    try:
        await model.load_model()
        logger.info("Model loaded successfully during startup")
    except Exception as e:
        logger.error(f"Failed to load model during startup: {e}")
        # Don't fail startup, allow manual model loading via API
    
    yield
    
    # Shutdown
    logger.info("Shutting down Wan Video API...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="Wan Image to Video API",
        description="Generate videos from images using Wan2.2 model",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure as needed
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routes
    app.include_router(router, prefix="/api/v1")
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": "Wan Image to Video API",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/api/v1/health"
        }
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error(f"Global exception handler caught: {exc}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    
    uvicorn.run(
        "wan_video_api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        workers=1 if settings.reload else settings.workers
    )
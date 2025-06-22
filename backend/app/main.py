"""
Main FastAPI application entry point for O'Reilly RAG Quiz system.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging

from app import __version__
from config import settings, setup_logging
from app.utils.database import check_database_connection, create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    setup_logging(settings)
    logger = logging.getLogger(__name__)
    logger.info("🚀 Starting O'Reilly RAG Quiz Backend...")
    logger.info(f"Environment: {'Development' if settings.debug else 'Production'}")
    logger.info(f"Database URL: {settings.database_url}")
    logger.info(f"Vector DB URL: {settings.qdrant_url}")
    
    # Check database connection
    if check_database_connection():
        create_tables()
    else:
        logger.error("Failed to connect to database. Exiting...")
        raise Exception("Database connection failed")
    
    yield
    # Shutdown
    logger.info("👋 Shutting down O'Reilly RAG Quiz Backend...")


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="A quiz-based learning platform powered by RAG for O'Reilly books",
    version=__version__,
    lifespan=lifespan,
    debug=settings.debug,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint to verify the API is running."""
    return {
        "message": "O'Reilly RAG Quiz API",
        "version": __version__,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": __version__}


# Include API routers (will be added as we build them)
# app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
# app.include_router(quizzes.router, prefix="/api/v1/quizzes", tags=["quizzes"])
# app.include_router(learning.router, prefix="/api/v1/learning", tags=["learning"])
# app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
# app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 
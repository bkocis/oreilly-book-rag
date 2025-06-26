"""
Configuration settings for the O'Reilly RAG Quiz Backend.
"""

import os
from pydantic_settings import BaseSettings
from typing import List
import logging


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "O'Reilly RAG Quiz API"
    debug: bool = False
    
    # API
    api_v1_str: str = "/api/v1"
    
    # CORS
    backend_cors_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    
    # Database
    database_url: str = "sqlite:///./quiz_app.db"  # Default to SQLite for development
    
    # Vector Database (Qdrant)
    qdrant_url: str = "http://localhost:6333"  # Default Qdrant URL
    qdrant_api_key: str = ""  # Optional API key for Qdrant Cloud
    vector_collection_name: str = "oreilly_documents"
    
    # Document Processing
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # Embeddings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # LLM Settings (can be configured for different providers)
    openai_api_key: str = ""
    llm_model: str = "gpt-3.5-turbo"
    
    # Authentication
    secret_key: str = "your-secret-key-change-in-production"  # Change this in production
    
    # Quiz Generation
    max_questions_per_quiz: int = 20
    default_difficulty_level: str = "medium"
    
    # File Storage
    upload_dir: str = "./data/uploads"
    processed_dir: str = "./data/processed"
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


def setup_logging(settings: Settings):
    """Configure logging for the application."""
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(settings.log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(settings.log_file),
            logging.StreamHandler()  # Also log to console
        ]
    )
    
    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)


# Global settings instance
settings = Settings() 
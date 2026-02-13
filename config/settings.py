"""
AssessIQ Configuration Settings
================================
Central configuration for the Student Answer Evaluation System.
All environment variables and system settings are managed here.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application Settings using Pydantic for validation.
    Environment variables can override default values.
    """
    
    # ========== Application Settings ==========
    APP_NAME: str = "AssessIQ"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "AI-Powered Student Answer Evaluation System"
    DEBUG: bool = True
    
    # ========== API Settings ==========
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list = [
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "https://*.vercel.app",
        "https://*.azurestaticapps.net",  # Azure Static Web Apps
        "https://*.azurewebsites.net",     # Azure App Service
        "https://*.onrender.com",          # Render
        "https://assessiq-frontend.onrender.com",  # Your Render frontend
        # Add your custom domain here:
        # "https://yourdomain.com",
    ]
    
    # ========== Database Settings ==========
    DATABASE_URL: str = "sqlite:///./assessiq.db"
    # For PostgreSQL: "postgresql://user:password@localhost:5432/assessiq"
    # For MongoDB: "mongodb://localhost:27017/assessiq"
    
    # ========== File Upload Settings ==========
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: list = [".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".jfif", ".webp", ".gif"]
    
    # ========== OCR Settings ==========
    OCR_ENGINE: str = "sarvam"  # Use advanced OCR APIs for handwriting
    OCR_LANGUAGES: list = ["en"]  # Languages for OCR
    TESSERACT_PATH: Optional[str] = None  # Path to tesseract executable
    LOW_MEMORY_MODE: bool = False  # Disable for better OCR accuracy
    FAST_OCR_MODE: bool = True  # Skip heavy preprocessing for faster OCR
    
    # ========== Sarvam AI OCR Settings ==========
    SARVAM_API_KEY: str = "sk_dejvv3m8_y0cDisH2QsCaSUW6zvA7oYNd"  # Sarvam AI API key
    SARVAM_API_URL: str = "https://api.sarvam.ai/parse-image"  # Sarvam AI OCR endpoint
    
    # ========== OCR.space Settings (Free, good for handwriting) ==========
    OCRSPACE_API_KEY: str = "K88888888888957"  # Free public key (limited)
    # Get your own key at https://ocr.space/ocrapi for higher limits
    
    # ========== Google Cloud Vision (Optional - Best accuracy) ==========
    GOOGLE_CLOUD_API_KEY: Optional[str] = None  # Set for best handwriting OCR
    # Get key from https://console.cloud.google.com/apis/credentials
    
    # ========== NLP Settings ==========
    SPACY_MODEL: str = "en_core_web_sm"
    SENTENCE_TRANSFORMER_MODEL: str = "all-MiniLM-L6-v2"
    
    # ========== Semantic Analysis Thresholds ==========
    SEMANTIC_EXCELLENT_THRESHOLD: float = 0.85
    SEMANTIC_GOOD_THRESHOLD: float = 0.70
    SEMANTIC_AVERAGE_THRESHOLD: float = 0.50
    
    # ========== Scoring Weights ==========
    WEIGHT_SEMANTIC: float = 0.6
    WEIGHT_KEYWORD: float = 0.2
    WEIGHT_DIAGRAM: float = 0.2
    
    # ========== Length Penalty Settings ==========
    LENGTH_PENALTY_THRESHOLD: float = 0.5  # Penalty if answer < 50% of expected length
    LENGTH_PENALTY_FACTOR: float = 0.1
    
    # ========== Diagram Evaluation Settings ==========
    DIAGRAM_SSIM_WEIGHT: float = 0.4
    DIAGRAM_FEATURE_WEIGHT: float = 0.6
    MIN_FEATURE_MATCHES: int = 10
    
    # ========== Logging Settings ==========
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/assessiq.log"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Create cached settings instance.
    This ensures settings are only loaded once.
    """
    return Settings()


# Global settings instance
settings = get_settings()


# ========== Directory Setup ==========
def setup_directories():
    """Create necessary directories if they don't exist."""
    directories = [
        settings.UPLOAD_DIR,
        os.path.join(settings.UPLOAD_DIR, "student_answers"),
        os.path.join(settings.UPLOAD_DIR, "model_answers"),
        os.path.join(settings.UPLOAD_DIR, "processed"),
        "logs",
        "temp"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


# Initialize directories on module load
setup_directories()

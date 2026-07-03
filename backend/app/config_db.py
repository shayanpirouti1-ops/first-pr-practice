"""Database configuration updates"""
# Add to config.py

from pydantic import BaseSettings
import os

class Settings(BaseSettings):
    # Existing settings...
    
    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./trading_platform.db"
    )
    
    # Database Pool Settings
    database_pool_size: int = int(os.getenv("DATABASE_POOL_SIZE", "5"))
    database_max_overflow: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))
    database_pool_recycle: int = int(os.getenv("DATABASE_POOL_RECYCLE", "3600"))
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()

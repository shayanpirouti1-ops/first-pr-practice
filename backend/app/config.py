"""Application configuration"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Tradovate
    tradovate_api_key: str
    tradovate_api_secret: str
    tradovate_sandbox: bool = False
    
    # Database
    database_url: str = "sqlite:///./copytrader.db"
    
    # Risk Management
    max_position_size: float = 10000
    max_account_exposure: float = 80
    max_daily_loss: float = 5
    default_stop_loss: float = 2
    default_take_profit: float = 5
    
    # Server
    debug: bool = False
    secret_key: str
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()

"""Database configuration and session management"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Create database URL
if settings.database_url:
    DATABASE_URL = settings.database_url
else:
    # Default to SQLite for development
    DATABASE_URL = "sqlite:///./trading_platform.db"

logger.info(f"Using database: {DATABASE_URL}")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=settings.debug,
    pool_pre_ping=True  # Verify connections before using
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """
    Get database session
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initialize database tables
    """
    from app.database.models import Base
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")

def drop_db():
    """
    Drop all database tables (for testing)
    """
    from app.database.models import Base
    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables dropped")

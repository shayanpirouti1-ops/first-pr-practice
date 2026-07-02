"""Dependency injection for FastAPI"""
from typing import AsyncGenerator
from app.traders.tradovate import TradovateClient
from app.traders.manager import TradovateManager
from app.copytrader.engine import CopyTradingEngine
from app.risk.manager import RiskManager, RiskConfig
from app.config import settings

# Global instances
_tradovate_manager: TradovateManager = None
_copy_engine: CopyTradingEngine = None
_risk_manager: RiskManager = None

async def initialize_dependencies():
    """Initialize all dependencies"""
    global _tradovate_manager, _copy_engine, _risk_manager
    
    # Initialize Tradovate
    _tradovate_manager = TradovateManager(
        settings.tradovate_api_key,
        settings.tradovate_api_secret,
        settings.tradovate_sandbox
    )
    await _tradovate_manager.initialize()
    
    # Initialize Copy Engine
    _copy_engine = CopyTradingEngine()
    
    # Initialize Risk Manager
    risk_config = RiskConfig(
        max_position_size=settings.max_position_size,
        max_account_exposure=settings.max_account_exposure,
        max_daily_loss=settings.max_daily_loss,
        stop_loss_percent=settings.default_stop_loss,
        take_profit_percent=settings.default_take_profit
    )
    _risk_manager = RiskManager(risk_config)

async def shutdown_dependencies():
    """Shutdown all dependencies"""
    global _tradovate_manager
    if _tradovate_manager:
        await _tradovate_manager.close()

async def get_tradovate_client() -> AsyncGenerator[TradovateClient, None]:
    """
    Dependency for getting Tradovate client
    
    Yields:
        TradovateClient instance
    """
    if not _tradovate_manager:
        raise RuntimeError("Tradovate manager not initialized")
    yield await _tradovate_manager.get_client()

def get_copy_engine() -> CopyTradingEngine:
    """
    Dependency for getting Copy Trading Engine
    
    Returns:
        CopyTradingEngine instance
    """
    if not _copy_engine:
        raise RuntimeError("Copy engine not initialized")
    return _copy_engine

def get_risk_manager() -> RiskManager:
    """
    Dependency for getting Risk Manager
    
    Returns:
        RiskManager instance
    """
    if not _risk_manager:
        raise RuntimeError("Risk manager not initialized")
    return _risk_manager

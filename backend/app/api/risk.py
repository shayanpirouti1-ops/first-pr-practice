"""Risk management routes"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from app.risk.manager import RiskManager, RiskConfig
from app.dependencies import get_risk_manager

router = APIRouter(prefix="/risk", tags=["risk"])

class CalculatePositionSizeRequest(BaseModel):
    """Request model for position size calculation"""
    account_balance: float
    risk_per_trade: float  # in %

class ValidatePositionRequest(BaseModel):
    """Request model for position validation"""
    current_exposure: float  # in %
    new_position_size: float

class CalculateStopLossRequest(BaseModel):
    """Request model for stop loss calculation"""
    entry_price: float
    position_type: str  # 'long' or 'short'

class CalculateTakeProfitRequest(BaseModel):
    """Request model for take profit calculation"""
    entry_price: float
    position_type: str  # 'long' or 'short'

@router.get("/config")
async def get_risk_config(
    manager: RiskManager = Depends(get_risk_manager)
) -> Dict[str, Any]:
    """
    Get current risk configuration
    
    Returns:
        Risk configuration
    """
    try:
        config = manager.config
        return {
            "success": True,
            "config": {
                "max_position_size": config.max_position_size,
                "max_account_exposure": config.max_account_exposure,
                "max_daily_loss": config.max_daily_loss,
                "stop_loss_percent": config.stop_loss_percent,
                "take_profit_percent": config.take_profit_percent
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/calculate-position-size")
async def calculate_position_size(
    request: CalculatePositionSizeRequest,
    manager: RiskManager = Depends(get_risk_manager)
) -> Dict[str, Any]:
    """
    Calculate position size based on account balance and risk
    
    Args:
        request: Account balance and risk per trade
    
    Returns:
        Calculated position size
    """
    try:
        position_size = manager.calculate_position_size(
            request.account_balance,
            request.risk_per_trade
        )
        return {
            "success": True,
            "position_size": position_size,
            "account_balance": request.account_balance,
            "risk_per_trade": request.risk_per_trade
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/validate-position")
async def validate_position(
    request: ValidatePositionRequest,
    manager: RiskManager = Depends(get_risk_manager)
) -> Dict[str, Any]:
    """
    Validate if position respects risk limits
    
    Args:
        request: Current exposure and new position size
    
    Returns:
        Validation result
    """
    try:
        is_valid = manager.validate_position(
            request.current_exposure,
            request.new_position_size
        )
        total_exposure = request.current_exposure + request.new_position_size
        
        return {
            "success": True,
            "is_valid": is_valid,
            "current_exposure": request.current_exposure,
            "new_position_size": request.new_position_size,
            "total_exposure": total_exposure,
            "max_exposure": manager.config.max_account_exposure
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/calculate-stop-loss")
async def calculate_stop_loss(
    request: CalculateStopLossRequest,
    manager: RiskManager = Depends(get_risk_manager)
) -> Dict[str, Any]:
    """
    Calculate stop loss price
    
    Args:
        request: Entry price and position type
    
    Returns:
        Stop loss price
    """
    try:
        stop_loss = manager.calculate_stop_loss(
            request.entry_price,
            request.position_type
        )
        return {
            "success": True,
            "entry_price": request.entry_price,
            "position_type": request.position_type,
            "stop_loss_price": stop_loss,
            "risk_percent": manager.config.stop_loss_percent
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/calculate-take-profit")
async def calculate_take_profit(
    request: CalculateTakeProfitRequest,
    manager: RiskManager = Depends(get_risk_manager)
) -> Dict[str, Any]:
    """
    Calculate take profit price
    
    Args:
        request: Entry price and position type
    
    Returns:
        Take profit price
    """
    try:
        take_profit = manager.calculate_take_profit(
            request.entry_price,
            request.position_type
        )
        return {
            "success": True,
            "entry_price": request.entry_price,
            "position_type": request.position_type,
            "take_profit_price": take_profit,
            "profit_percent": manager.config.take_profit_percent
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

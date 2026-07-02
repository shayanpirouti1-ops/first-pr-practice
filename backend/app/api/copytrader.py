"""Copy trading routes"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from app.copytrader.engine import CopyTradingEngine, CopyConfig
from app.dependencies import get_copy_engine

router = APIRouter(prefix="/copytrader", tags=["copytrader"])

class AddTraderRequest(BaseModel):
    """Request model for adding trader to copy"""
    trader_id: str
    copy_ratio: float  # 0.0 to 1.0
    max_position_size: float
    enabled: bool = True

class UpdateTraderRequest(BaseModel):
    """Request model for updating trader config"""
    copy_ratio: Optional[float] = None
    max_position_size: Optional[float] = None
    enabled: Optional[bool] = None

@router.post("/traders")
async def add_trader_to_copy(
    request: AddTraderRequest,
    engine: CopyTradingEngine = Depends(get_copy_engine)
) -> Dict[str, Any]:
    """
    Add a trader to copy
    
    Args:
        request: Trader configuration
    
    Returns:
        Confirmation
    """
    try:
        config = CopyConfig(
            trader_id=request.trader_id,
            copy_ratio=request.copy_ratio,
            max_position_size=request.max_position_size,
            enabled=request.enabled
        )
        result = engine.add_trader_to_copy(config)
        return {
            "success": result,
            "message": f"Trader {request.trader_id} added to copy"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/traders")
async def list_traders(
    engine: CopyTradingEngine = Depends(get_copy_engine)
) -> Dict[str, Any]:
    """
    List all traders being copied
    
    Returns:
        List of trader configurations
    """
    try:
        traders = list(engine.configs.values())
        return {
            "success": True,
            "traders": [t.__dict__ for t in traders],
            "count": len(traders)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/traders/{trader_id}")
async def update_trader(
    trader_id: str,
    request: UpdateTraderRequest,
    engine: CopyTradingEngine = Depends(get_copy_engine)
) -> Dict[str, Any]:
    """
    Update trader configuration
    
    Args:
        trader_id: Trader ID
        request: Updated configuration
    
    Returns:
        Updated configuration
    """
    try:
        config = engine.configs.get(trader_id)
        if not config:
            raise HTTPException(status_code=404, detail="Trader not found")
        
        if request.copy_ratio is not None:
            config.copy_ratio = request.copy_ratio
        if request.max_position_size is not None:
            config.max_position_size = request.max_position_size
        if request.enabled is not None:
            config.enabled = request.enabled
        
        return {
            "success": True,
            "trader": config.__dict__
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/traders/{trader_id}")
async def remove_trader(
    trader_id: str,
    engine: CopyTradingEngine = Depends(get_copy_engine)
) -> Dict[str, Any]:
    """
    Stop copying a trader
    
    Args:
        trader_id: Trader ID
    
    Returns:
        Confirmation
    """
    try:
        result = engine.remove_trader(trader_id)
        if not result:
            raise HTTPException(status_code=404, detail="Trader not found")
        return {
            "success": True,
            "message": f"Trader {trader_id} removed from copy"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/traders/{trader_id}/copies")
async def get_active_copies(
    trader_id: str,
    engine: CopyTradingEngine = Depends(get_copy_engine)
) -> Dict[str, Any]:
    """
    Get active copies for a trader
    
    Args:
        trader_id: Trader ID
    
    Returns:
        List of active copies
    """
    try:
        copies = engine.get_active_copies(trader_id)
        return {
            "success": True,
            "copies": copies,
            "count": len(copies)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/stats")
async def get_stats(
    engine: CopyTradingEngine = Depends(get_copy_engine)
) -> Dict[str, Any]:
    """
    Get copy trading statistics
    
    Returns:
        Statistics
    """
    try:
        total_traders = len(engine.configs)
        active_traders = sum(1 for c in engine.configs.values() if c.enabled)
        total_copies = sum(len(copies) for copies in engine.active_copies.values())
        
        return {
            "success": True,
            "total_traders": total_traders,
            "active_traders": active_traders,
            "total_active_copies": total_copies
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

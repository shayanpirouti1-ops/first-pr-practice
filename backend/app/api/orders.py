"""Order management routes"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.traders.tradovate import TradovateClient
from app.dependencies import get_tradovate_client

router = APIRouter(prefix="/orders", tags=["orders"])

class PlaceOrderRequest(BaseModel):
    """Request model for placing orders"""
    account_id: int
    symbol: str
    quantity: int
    order_type: str  # Market, Limit, Stop, StopLimit
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: str = "Day"

class ModifyOrderRequest(BaseModel):
    """Request model for modifying orders"""
    quantity: Optional[int] = None
    price: Optional[float] = None
    stop_price: Optional[float] = None

@router.post("/")
async def place_order(
    request: PlaceOrderRequest,
    client: TradovateClient = Depends(get_tradovate_client)
) -> Dict[str, Any]:
    """
    Place a new order
    
    Args:
        request: Order details
    
    Returns:
        Order confirmation
    """
    try:
        order = await client.place_order(
            account_id=request.account_id,
            symbol=request.symbol,
            quantity=request.quantity,
            order_type=request.order_type,
            price=request.price,
            stop_price=request.stop_price,
            time_in_force=request.time_in_force
        )
        return {
            "success": True,
            "order": order
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/")
async def get_orders(
    account_id: int = Query(...),
    status: str = Query("Working"),
    client: TradovateClient = Depends(get_tradovate_client)
) -> Dict[str, Any]:
    """
    Get orders for an account
    
    Args:
        account_id: Account ID
        status: Order status filter (Working, Filled, Cancelled, All)
    
    Returns:
        List of orders
    """
    try:
        orders = await client.get_orders(account_id, status)
        return {
            "success": True,
            "orders": orders,
            "count": len(orders)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{order_id}")
async def get_order(
    order_id: int,
    client: TradovateClient = Depends(get_tradovate_client)
) -> Dict[str, Any]:
    """
    Get specific order details
    
    Args:
        order_id: Order ID
    
    Returns:
        Order details
    """
    try:
        order = await client.get_order(order_id)
        return {
            "success": True,
            "order": order
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{order_id}")
async def modify_order(
    order_id: int,
    request: ModifyOrderRequest,
    client: TradovateClient = Depends(get_tradovate_client)
) -> Dict[str, Any]:
    """
    Modify an existing order
    
    Args:
        order_id: Order ID
        request: Modification details
    
    Returns:
        Modified order details
    """
    try:
        order = await client.modify_order(
            order_id=order_id,
            quantity=request.quantity,
            price=request.price,
            stop_price=request.stop_price
        )
        return {
            "success": True,
            "order": order
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{order_id}")
async def cancel_order(
    order_id: int,
    client: TradovateClient = Depends(get_tradovate_client)
) -> Dict[str, Any]:
    """
    Cancel an order
    
    Args:
        order_id: Order ID
    
    Returns:
        Cancellation confirmation
    """
    try:
        result = await client.cancel_order(order_id)
        return {
            "success": True,
            "order": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{account_id}/fills")
async def get_fills(
    account_id: int,
    days: int = Query(1),
    client: TradovateClient = Depends(get_tradovate_client)
) -> Dict[str, Any]:
    """
    Get filled orders (trades) for account
    
    Args:
        account_id: Account ID
        days: Number of days to look back
    
    Returns:
        List of fills
    """
    try:
        fills = await client.get_fills(account_id, days)
        return {
            "success": True,
            "fills": fills,
            "count": len(fills)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

"""WebSocket routes for real-time subscriptions"""
from fastapi import APIRouter, Depends, HTTPException, WebSocket
from typing import Dict, Any
from app.websocket.manager import WebSocketManager
from app.dependencies import get_websocket_manager

router = APIRouter(prefix="/ws", tags=["websocket"])

@router.post("/subscribe/quote")
async def subscribe_quote(
    contract_id: int,
    ws_manager: WebSocketManager = Depends(get_websocket_manager)
) -> Dict[str, Any]:
    """
    Subscribe to quote updates for a contract
    
    Args:
        contract_id: Contract ID
    
    Returns:
        Subscription confirmation
    """
    try:
        result = await ws_manager.subscribe_quote(contract_id)
        return {
            "success": result,
            "contract_id": contract_id,
            "message": "Subscribed to quotes" if result else "Failed to subscribe"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/unsubscribe/quote")
async def unsubscribe_quote(
    contract_id: int,
    ws_manager: WebSocketManager = Depends(get_websocket_manager)
) -> Dict[str, Any]:
    """
    Unsubscribe from quote updates
    
    Args:
        contract_id: Contract ID
    
    Returns:
        Unsubscription confirmation
    """
    try:
        result = await ws_manager.unsubscribe_quote(contract_id)
        return {
            "success": result,
            "contract_id": contract_id,
            "message": "Unsubscribed from quotes" if result else "Failed to unsubscribe"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/subscribe/orders")
async def subscribe_orders(
    account_id: int,
    ws_manager: WebSocketManager = Depends(get_websocket_manager)
) -> Dict[str, Any]:
    """
    Subscribe to order updates
    
    Args:
        account_id: Account ID
    
    Returns:
        Subscription confirmation
    """
    try:
        result = await ws_manager.subscribe_orders(account_id)
        return {
            "success": result,
            "account_id": account_id,
            "message": "Subscribed to orders" if result else "Failed to subscribe"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/subscribe/fills")
async def subscribe_fills(
    account_id: int,
    ws_manager: WebSocketManager = Depends(get_websocket_manager)
) -> Dict[str, Any]:
    """
    Subscribe to fill notifications
    
    Args:
        account_id: Account ID
    
    Returns:
        Subscription confirmation
    """
    try:
        result = await ws_manager.subscribe_fills(account_id)
        return {
            "success": result,
            "account_id": account_id,
            "message": "Subscribed to fills" if result else "Failed to subscribe"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/status")
async def ws_status(
    ws_manager: WebSocketManager = Depends(get_websocket_manager)
) -> Dict[str, Any]:
    """
    Get WebSocket connection status
    
    Returns:
        Status information
    """
    return {
        "connected": ws_manager.is_connected(),
        "subscriptions": list(ws_manager.get_subscriptions()),
        "subscription_count": len(ws_manager.get_subscriptions()),
        "sandbox": ws_manager.sandbox
    }

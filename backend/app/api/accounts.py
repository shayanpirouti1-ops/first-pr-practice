"""Account management routes"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from app.traders.tradovate import TradovateClient
from app.dependencies import get_tradovate_client

router = APIRouter(prefix="/accounts", tags=["accounts"])

@router.get("/")
async def list_accounts(client: TradovateClient = Depends(get_tradovate_client)) -> Dict[str, Any]:
    """
    Get all user accounts
    
    Returns:
        List of accounts with details
    """
    try:
        accounts = await client.get_accounts()
        return {
            "success": True,
            "accounts": accounts,
            "count": len(accounts)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{account_id}")
async def get_account(account_id: int, client: TradovateClient = Depends(get_tradovate_client)) -> Dict[str, Any]:
    """
    Get specific account details
    
    Args:
        account_id: Account ID
    
    Returns:
        Account details
    """
    try:
        account = await client.get_account(account_id)
        return {
            "success": True,
            "account": account
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{account_id}/balance")
async def get_balance(account_id: int, client: TradovateClient = Depends(get_tradovate_client)) -> Dict[str, Any]:
    """
    Get account balance and trading power
    
    Args:
        account_id: Account ID
    
    Returns:
        Balance information
    """
    try:
        balance = await client.get_balance(account_id)
        return {
            "success": True,
            "balance": balance
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{account_id}/positions")
async def get_positions(account_id: int, client: TradovateClient = Depends(get_tradovate_client)) -> Dict[str, Any]:
    """
    Get open positions for account
    
    Args:
        account_id: Account ID
    
    Returns:
        List of open positions
    """
    try:
        positions = await client.get_positions(account_id)
        return {
            "success": True,
            "positions": positions,
            "count": len(positions)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

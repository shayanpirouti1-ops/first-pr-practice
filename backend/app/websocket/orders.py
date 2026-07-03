"""Order and fill notifications handler"""
import logging
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class OrderStatus(str, Enum):
    """Order statuses"""
    PENDING = "Pending"
    WORKING = "Working"
    FILLED = "Filled"
    CANCELLED = "Cancelled"
    REJECTED = "Rejected"

@dataclass
class OrderNotification:
    """Order update notification"""
    order_id: int
    account_id: int
    symbol: str
    quantity: int
    price: float
    status: str
    timestamp: datetime

@dataclass
class FillNotification:
    """Fill/Trade notification"""
    order_id: int
    account_id: int
    symbol: str
    quantity: int
    fill_price: float
    fill_quantity: int
    commission: float
    timestamp: datetime

class OrderAndFillHandler:
    """Handle order and fill updates"""
    
    def __init__(self):
        self.order_callbacks: Dict[int, list] = {}  # order_id -> callbacks
        self.fill_callbacks: list = []  # Global fill callbacks
        self.order_history: Dict[int, OrderNotification] = {}
        self.fill_history: List[FillNotification] = []
    
    def on_order_update(self, order_id: int, callback: Callable):
        """
        Register callback for order updates
        
        Args:
            order_id: Order ID to watch
            callback: Async callback function
        """
        if order_id not in self.order_callbacks:
            self.order_callbacks[order_id] = []
        self.order_callbacks[order_id].append(callback)
    
    def on_fill(self, callback: Callable):
        """
        Register global fill callback
        
        Args:
            callback: Async callback function
        """
        self.fill_callbacks.append(callback)
    
    async def handle_order_update(self, data: Dict[str, Any]) -> Optional[OrderNotification]:
        """
        Handle order update
        
        Args:
            data: Order update data
        
        Returns:
            OrderNotification object
        """
        try:
            order_id = data.get('orderId')
            
            notification = OrderNotification(
                order_id=order_id,
                account_id=data.get('accountId'),
                symbol=data.get('symbol'),
                quantity=data.get('quantity'),
                price=data.get('price'),
                status=data.get('status'),
                timestamp=datetime.utcnow()
            )
            
            # Store in history
            self.order_history[order_id] = notification
            
            # Emit to order-specific callbacks
            if order_id in self.order_callbacks:
                for callback in self.order_callbacks[order_id]:
                    try:
                        await callback(notification)
                    except Exception as e:
                        logger.error(f"Error in order callback: {str(e)}")
            
            logger.info(f"Order update: {order_id} - {notification.status}")
            return notification
        
        except Exception as e:
            logger.error(f"Error handling order update: {str(e)}", exc_info=True)
            return None
    
    async def handle_fill(self, data: Dict[str, Any]) -> Optional[FillNotification]:
        """
        Handle fill/trade notification
        
        Args:
            data: Fill data
        
        Returns:
            FillNotification object
        """
        try:
            notification = FillNotification(
                order_id=data.get('orderId'),
                account_id=data.get('accountId'),
                symbol=data.get('symbol'),
                quantity=data.get('quantity'),
                fill_price=data.get('fillPrice'),
                fill_quantity=data.get('fillQuantity'),
                commission=data.get('commission', 0),
                timestamp=datetime.utcnow()
            )
            
            # Store in history
            self.fill_history.append(notification)
            
            # Emit to global fill callbacks
            for callback in self.fill_callbacks:
                try:
                    await callback(notification)
                except Exception as e:
                    logger.error(f"Error in fill callback: {str(e)}")
            
            logger.info(f"Fill: {notification.symbol} x{notification.fill_quantity} @ {notification.fill_price}")
            return notification
        
        except Exception as e:
            logger.error(f"Error handling fill: {str(e)}", exc_info=True)
            return None
    
    def get_order_status(self, order_id: int) -> Optional[str]:
        """
        Get current order status
        
        Args:
            order_id: Order ID
        
        Returns:
            Order status or None
        """
        notification = self.order_history.get(order_id)
        return notification.status if notification else None
    
    def get_fills_for_order(self, order_id: int) -> List[FillNotification]:
        """
        Get all fills for an order
        
        Args:
            order_id: Order ID
        
        Returns:
            List of fill notifications
        """
        return [f for f in self.fill_history if f.order_id == order_id]

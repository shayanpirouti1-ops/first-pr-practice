"""WebSocket manager for real-time market data and trading updates"""
import asyncio
import json
import logging
from typing import Callable, Dict, Any, Optional, List
from datetime import datetime
import aiohttp
from enum import Enum

logger = logging.getLogger(__name__)

class EventType(str, Enum):
    """WebSocket event types"""
    QUOTE = "quote"
    ORDER_UPDATE = "order_update"
    FILL = "fill"
    POSITION_UPDATE = "position_update"
    ACCOUNT_UPDATE = "account_update"
    ERROR = "error"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"

class WebSocketManager:
    """Manage WebSocket connections for real-time data"""
    
    def __init__(self, access_token: str, sandbox: bool = False):
        """
        Initialize WebSocket manager
        
        Args:
            access_token: Tradovate API access token
            sandbox: Use sandbox environment
        """
        self.access_token = access_token
        self.sandbox = sandbox
        self.ws_url = "wss://sandbox.tradovate.com/ws" if sandbox else "wss://api.tradovate.com/ws"
        self.ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self.callbacks: Dict[str, List[Callable]] = {}
        self.running = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5  # seconds
        self.subscriptions: set = set()  # Active subscriptions
    
    def on(self, event_type: str, callback: Callable):
        """
        Register callback for event type
        
        Args:
            event_type: Type of event (EventType enum)
            callback: Async callback function
        """
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        self.callbacks[event_type].append(callback)
        logger.info(f"Registered callback for {event_type}")
    
    def off(self, event_type: str, callback: Callable):
        """
        Unregister callback
        
        Args:
            event_type: Type of event
            callback: Callback to remove
        """
        if event_type in self.callbacks:
            self.callbacks[event_type].remove(callback)
    
    async def _emit(self, event_type: str, data: Dict[str, Any]):
        """
        Emit event to all registered callbacks
        
        Args:
            event_type: Type of event
            data: Event data
        """
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    logger.error(f"Error in {event_type} callback: {str(e)}", exc_info=True)
    
    async def connect(self) -> bool:
        """
        Connect to WebSocket
        
        Returns:
            True if connected successfully
        """
        try:
            if self.session is None:
                self.session = aiohttp.ClientSession()
            
            self.ws = await self.session.ws_connect(
                self.ws_url,
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=aiohttp.ClientTimeout(total=30)
            )
            
            self.running = True
            self.reconnect_attempts = 0
            logger.info("WebSocket connected successfully")
            
            await self._emit(EventType.CONNECTED, {"timestamp": datetime.utcnow().isoformat()})
            
            # Start message listener
            asyncio.create_task(self._listen())
            return True
        
        except Exception as e:
            logger.error(f"WebSocket connection failed: {str(e)}", exc_info=True)
            self.running = False
            await self._handle_disconnection()
            return False
    
    async def _listen(self):
        """
        Listen for incoming WebSocket messages
        """
        try:
            async for msg in self.ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        await self._route_message(data)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode message: {str(e)}")
                
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {self.ws.exception()}")
                    break
        
        except Exception as e:
            logger.error(f"Error in WebSocket listener: {str(e)}", exc_info=True)
        
        finally:
            await self._handle_disconnection()
    
    async def _route_message(self, data: Dict[str, Any]):
        """
        Route incoming message to appropriate handler
        
        Args:
            data: Message data
        """
        message_type = data.get('type')
        
        if message_type == 'quote':
            await self._emit(EventType.QUOTE, data)
        elif message_type == 'order':
            await self._emit(EventType.ORDER_UPDATE, data)
        elif message_type == 'fill':
            await self._emit(EventType.FILL, data)
        elif message_type == 'position':
            await self._emit(EventType.POSITION_UPDATE, data)
        elif message_type == 'account':
            await self._emit(EventType.ACCOUNT_UPDATE, data)
        elif message_type == 'error':
            await self._emit(EventType.ERROR, data)
        else:
            logger.debug(f"Unknown message type: {message_type}")
    
    async def _handle_disconnection(self):
        """
        Handle disconnection with reconnection attempts
        """
        self.running = False
        logger.warning("WebSocket disconnected")
        await self._emit(EventType.DISCONNECTED, {"timestamp": datetime.utcnow().isoformat()})
        
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            logger.info(f"Reconnecting in {self.reconnect_delay}s (attempt {self.reconnect_attempts})")
            await asyncio.sleep(self.reconnect_delay)
            await self.connect()
    
    async def subscribe_quote(self, contract_id: int) -> bool:
        """
        Subscribe to quote updates for a contract
        
        Args:
            contract_id: Contract ID
        
        Returns:
            True if subscription sent
        """
        if not self.ws or not self.running:
            logger.error("WebSocket not connected")
            return False
        
        try:
            subscribe_msg = {
                "action": "subscribe",
                "entity": "quote",
                "id": contract_id
            }
            await self.ws.send_json(subscribe_msg)
            self.subscriptions.add(f"quote:{contract_id}")
            logger.info(f"Subscribed to quotes for contract {contract_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to subscribe: {str(e)}")
            return False
    
    async def unsubscribe_quote(self, contract_id: int) -> bool:
        """
        Unsubscribe from quote updates
        
        Args:
            contract_id: Contract ID
        
        Returns:
            True if unsubscription sent
        """
        if not self.ws or not self.running:
            logger.error("WebSocket not connected")
            return False
        
        try:
            unsubscribe_msg = {
                "action": "unsubscribe",
                "entity": "quote",
                "id": contract_id
            }
            await self.ws.send_json(unsubscribe_msg)
            self.subscriptions.discard(f"quote:{contract_id}")
            logger.info(f"Unsubscribed from quotes for contract {contract_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to unsubscribe: {str(e)}")
            return False
    
    async def subscribe_orders(self, account_id: int) -> bool:
        """
        Subscribe to order updates for an account
        
        Args:
            account_id: Account ID
        
        Returns:
            True if subscription sent
        """
        if not self.ws or not self.running:
            logger.error("WebSocket not connected")
            return False
        
        try:
            subscribe_msg = {
                "action": "subscribe",
                "entity": "order",
                "accountId": account_id
            }
            await self.ws.send_json(subscribe_msg)
            self.subscriptions.add(f"order:{account_id}")
            logger.info(f"Subscribed to orders for account {account_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to subscribe to orders: {str(e)}")
            return False
    
    async def subscribe_fills(self, account_id: int) -> bool:
        """
        Subscribe to fill notifications
        
        Args:
            account_id: Account ID
        
        Returns:
            True if subscription sent
        """
        if not self.ws or not self.running:
            logger.error("WebSocket not connected")
            return False
        
        try:
            subscribe_msg = {
                "action": "subscribe",
                "entity": "fill",
                "accountId": account_id
            }
            await self.ws.send_json(subscribe_msg)
            self.subscriptions.add(f"fill:{account_id}")
            logger.info(f"Subscribed to fills for account {account_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to subscribe to fills: {str(e)}")
            return False
    
    async def close(self):
        """
        Close WebSocket connection
        """
        self.running = False
        if self.ws:
            await self.ws.close()
            self.ws = None
        if self.session:
            await self.session.close()
            self.session = None
        logger.info("WebSocket closed")
    
    def is_connected(self) -> bool:
        """
        Check if WebSocket is connected
        
        Returns:
            True if connected
        """
        return self.running and self.ws is not None
    
    def get_subscriptions(self) -> set:
        """
        Get all active subscriptions
        
        Returns:
            Set of subscription identifiers
        """
        return self.subscriptions.copy()

"""WebSocket connection handler for Tradovate real-time data"""
import asyncio
import json
import logging
from typing import Callable, Optional, Dict, Any
import aiohttp

logger = logging.getLogger(__name__)

class TradovateWebSocket:
    """WebSocket handler for Tradovate streaming data"""
    
    def __init__(self, access_token: str, sandbox: bool = False):
        self.access_token = access_token
        self.sandbox = sandbox
        self.ws_url = "wss://sandbox.tradovate.com/ws" if sandbox else "wss://api.tradovate.com/ws"
        self.ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self.callbacks: Dict[str, list] = {}
        self.running = False
    
    def on(self, event_type: str, callback: Callable):
        """
        Register callback for event type
        
        Args:
            event_type: Type of event ('quote', 'order', 'position', etc.)
            callback: Async callback function
        """
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        self.callbacks[event_type].append(callback)
    
    async def _emit(self, event_type: str, data: Dict[str, Any]):
        """Emit event to all registered callbacks"""
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    await callback(data)
                except Exception as e:
                    logger.error(f"Error in callback: {str(e)}")
    
    async def connect(self):
        """Connect to WebSocket"""
        try:
            session = aiohttp.ClientSession()
            self.ws = await session.ws_connect(
                self.ws_url,
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            self.running = True
            logger.info("WebSocket connected")
            
            # Start listening for messages
            asyncio.create_task(self._listen())
        except Exception as e:
            logger.error(f"WebSocket connection failed: {str(e)}")
            raise
    
    async def _listen(self):
        """Listen for incoming WebSocket messages"""
        try:
            async for msg in self.ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    
                    # Route message to appropriate callback
                    if 'event' in data:
                        await self._emit(data['event'], data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {self.ws.exception()}")
                    break
        except Exception as e:
            logger.error(f"Error in WebSocket listener: {str(e)}")
        finally:
            self.running = False
    
    async def subscribe_quote(self, contract_id: int):
        """
        Subscribe to quote updates for a contract
        
        Args:
            contract_id: Contract ID to subscribe to
        """
        if not self.ws:
            raise RuntimeError("WebSocket not connected")
        
        subscribe_msg = {
            "action": "subscribe",
            "entity": "quote",
            "id": contract_id
        }
        await self.ws.send_json(subscribe_msg)
        logger.info(f"Subscribed to quotes for contract {contract_id}")
    
    async def unsubscribe_quote(self, contract_id: int):
        """
        Unsubscribe from quote updates
        
        Args:
            contract_id: Contract ID to unsubscribe from
        """
        if not self.ws:
            raise RuntimeError("WebSocket not connected")
        
        unsubscribe_msg = {
            "action": "unsubscribe",
            "entity": "quote",
            "id": contract_id
        }
        await self.ws.send_json(unsubscribe_msg)
        logger.info(f"Unsubscribed from quotes for contract {contract_id}")
    
    async def close(self):
        """Close WebSocket connection"""
        if self.ws:
            await self.ws.close()
            self.running = False
            logger.info("WebSocket closed")

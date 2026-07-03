"""Real-time quote data handler"""
import logging
from typing import Dict, Any, Callable, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class QuoteUpdate(Enum):
    """Quote update types"""
    PRICE_CHANGE = "price_change"
    VOLUME_CHANGE = "volume_change"
    VOLATILITY_CHANGE = "volatility_change"

@dataclass
class Quote:
    """Real-time quote data"""
    contract_id: int
    symbol: str
    bid: float
    ask: float
    last: float
    bid_size: int
    ask_size: int
    last_size: int
    volume: int
    high: float
    low: float
    open_price: float
    settlement: float
    timestamp: datetime

class QuoteHandler:
    """Handle real-time quote updates"""
    
    def __init__(self):
        self.quotes: Dict[int, Quote] = {}  # contract_id -> Quote
        self.quote_callbacks: Dict[int, list] = {}  # contract_id -> callbacks
        self.price_change_callbacks: list = []  # Global price change callbacks
    
    def on_quote_update(self, contract_id: int, callback: Callable):
        """
        Register callback for quote updates
        
        Args:
            contract_id: Contract ID to watch
            callback: Async callback function
        """
        if contract_id not in self.quote_callbacks:
            self.quote_callbacks[contract_id] = []
        self.quote_callbacks[contract_id].append(callback)
    
    def on_any_price_change(self, callback: Callable):
        """
        Register global price change callback
        
        Args:
            callback: Async callback function
        """
        self.price_change_callbacks.append(callback)
    
    async def handle_quote(self, data: Dict[str, Any]) -> Optional[Quote]:
        """
        Handle incoming quote data
        
        Args:
            data: Quote data from WebSocket
        
        Returns:
            Quote object
        """
        try:
            contract_id = data.get('contractId')
            
            quote = Quote(
                contract_id=contract_id,
                symbol=data.get('symbol'),
                bid=data.get('bid'),
                ask=data.get('ask'),
                last=data.get('last'),
                bid_size=data.get('bidSize'),
                ask_size=data.get('askSize'),
                last_size=data.get('lastSize'),
                volume=data.get('volume'),
                high=data.get('high'),
                low=data.get('low'),
                open_price=data.get('open'),
                settlement=data.get('settlement'),
                timestamp=datetime.utcnow()
            )
            
            # Store quote
            old_quote = self.quotes.get(contract_id)
            self.quotes[contract_id] = quote
            
            # Check for price changes
            if old_quote and old_quote.last != quote.last:
                await self._emit_price_change(old_quote, quote)
            
            # Emit to contract-specific callbacks
            if contract_id in self.quote_callbacks:
                for callback in self.quote_callbacks[contract_id]:
                    try:
                        await callback(quote)
                    except Exception as e:
                        logger.error(f"Error in quote callback: {str(e)}")
            
            logger.debug(f"Quote updated for {quote.symbol}: {quote.last}")
            return quote
        
        except Exception as e:
            logger.error(f"Error handling quote: {str(e)}", exc_info=True)
            return None
    
    async def _emit_price_change(self, old_quote: Quote, new_quote: Quote):
        """
        Emit price change to all global callbacks
        
        Args:
            old_quote: Previous quote
            new_quote: New quote
        """
        change = new_quote.last - old_quote.last
        change_percent = (change / old_quote.last * 100) if old_quote.last != 0 else 0
        
        event = {
            "symbol": new_quote.symbol,
            "old_price": old_quote.last,
            "new_price": new_quote.last,
            "change": change,
            "change_percent": change_percent,
            "bid": new_quote.bid,
            "ask": new_quote.ask,
            "timestamp": new_quote.timestamp.isoformat()
        }
        
        for callback in self.price_change_callbacks:
            try:
                await callback(event)
            except Exception as e:
                logger.error(f"Error in price change callback: {str(e)}")
    
    def get_quote(self, contract_id: int) -> Optional[Quote]:
        """
        Get latest quote for a contract
        
        Args:
            contract_id: Contract ID
        
        Returns:
            Latest quote or None
        """
        return self.quotes.get(contract_id)
    
    def get_all_quotes(self) -> Dict[int, Quote]:
        """
        Get all stored quotes
        
        Returns:
            Dictionary of quotes
        """
        return self.quotes.copy()

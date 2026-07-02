"""Copy trading engine"""
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class CopyConfig:
    """Configuration for copying a trader"""
    trader_id: str
    copy_ratio: float  # 0.0 to 1.0
    max_position_size: float
    enabled: bool = True

class CopyTradingEngine:
    """Main copy trading engine"""
    
    def __init__(self):
        self.configs: Dict[str, CopyConfig] = {}
        self.active_copies: Dict[str, List[Dict]] = {}
    
    def add_trader_to_copy(self, config: CopyConfig) -> bool:
        """Add a trader to copy"""
        self.configs[config.trader_id] = config
        return True
    
    def remove_trader(self, trader_id: str) -> bool:
        """Stop copying a trader"""
        if trader_id in self.configs:
            del self.configs[trader_id]
            return True
        return False
    
    async def process_trade(self, trader_id: str, trade_signal: Dict) -> Optional[Dict]:
        """Process a trade signal from a trader"""
        config = self.configs.get(trader_id)
        if not config or not config.enabled:
            return None
        
        # TODO: Apply risk management and copy the trade
        return {"status": "pending", "trader_id": trader_id}
    
    def get_active_copies(self, trader_id: str) -> List[Dict]:
        """Get active copies for a trader"""
        return self.active_copies.get(trader_id, [])

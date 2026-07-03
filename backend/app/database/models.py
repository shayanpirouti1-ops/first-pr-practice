"""Database models for copy trading platform"""
from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum

Base = declarative_base()

class OrderStatusEnum(str, Enum):
    """Order status enum"""
    PENDING = "Pending"
    WORKING = "Working"
    FILLED = "Filled"
    CANCELLED = "Cancelled"
    REJECTED = "Rejected"

class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    api_key = Column(String(255), nullable=False)
    api_secret = Column(String(255), nullable=False)
    sandbox_mode = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    accounts = relationship("Account", back_populates="user")
    traders = relationship("CopyTrader", back_populates="user")
    orders = relationship("Order", back_populates="user")

class Account(Base):
    """Trading account model"""
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(Integer, nullable=False, unique=True)
    account_name = Column(String(255))
    balance = Column(Float, default=0.0)
    equity = Column(Float, default=0.0)
    buying_power = Column(Float, default=0.0)
    cash = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="accounts")
    positions = relationship("Position", back_populates="account")
    orders = relationship("Order", back_populates="account")
    fills = relationship("Fill", back_populates="account")
    account_stats = relationship("AccountStats", back_populates="account")

class CopyTrader(Base):
    """Trader being copied model"""
    __tablename__ = "copy_traders"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    trader_id = Column(String(255), nullable=False)
    trader_name = Column(String(255))
    copy_ratio = Column(Float, default=1.0)  # 0.0 to 1.0
    max_position_size = Column(Float, default=10000.0)
    enabled = Column(Boolean, default=True)
    total_copies = Column(Integer, default=0)
    successful_copies = Column(Integer, default=0)
    total_pnl = Column(Float, default=0.0)
    win_rate = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="traders")
    copy_orders = relationship("CopyOrder", back_populates="trader")

class Order(Base):
    """Order model"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    order_id = Column(Integer, nullable=False, unique=True)
    symbol = Column(String(50), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float)
    order_type = Column(String(50))  # Market, Limit, Stop, StopLimit
    status = Column(SQLEnum(OrderStatusEnum), default=OrderStatusEnum.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    filled_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="orders")
    account = relationship("Account", back_populates="orders")
    fills = relationship("Fill", back_populates="order")
    copy_orders = relationship("CopyOrder", back_populates="order")

class Fill(Base):
    """Fill/Trade model"""
    __tablename__ = "fills"
    
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    symbol = Column(String(50), nullable=False)
    quantity = Column(Integer, nullable=False)
    fill_price = Column(Float, nullable=False)
    commission = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    account = relationship("Account", back_populates="fills")
    order = relationship("Order", back_populates="fills")

class Position(Base):
    """Open position model"""
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    symbol = Column(String(50), nullable=False)
    quantity = Column(Integer, nullable=False)
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float)
    unrealized_pnl = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    account = relationship("Account", back_populates="positions")

class CopyOrder(Base):
    """Copy order model"""
    __tablename__ = "copy_orders"
    
    id = Column(Integer, primary_key=True)
    trader_id = Column(Integer, ForeignKey("copy_traders.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    trader_order_id = Column(String(255), nullable=False)
    copy_order_id = Column(Integer, nullable=False)
    original_quantity = Column(Integer, nullable=False)
    copy_quantity = Column(Integer, nullable=False)
    copy_ratio = Column(Float, nullable=False)
    pnl = Column(Float)
    status = Column(SQLEnum(OrderStatusEnum), default=OrderStatusEnum.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    filled_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    trader = relationship("CopyTrader", back_populates="copy_orders")
    order = relationship("Order", back_populates="copy_orders")

class AccountStats(Base):
    """Account daily statistics model"""
    __tablename__ = "account_stats"
    
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    daily_pnl = Column(Float, default=0.0)
    daily_trades = Column(Integer, default=0)
    daily_wins = Column(Integer, default=0)
    daily_losses = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    total_volume = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    account = relationship("Account", back_populates="account_stats")

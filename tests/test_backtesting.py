"""Tests for backtesting engine."""

import pytest
from datetime import datetime, timedelta

import polars as pl

from quant_infra.backtesting import BacktestEngine, Position, BacktestResult


def test_position_class():
    """Test Position dataclass."""
    pos = Position(
        symbol="BTCUSDT",
        size=1.0,
        entry_price=50000.0,
        entry_time=datetime.now(),
    )
    
    assert pos.symbol == "BTCUSDT"
    assert pos.size == 1.0
    assert pos.entry_price == 50000.0
    assert pos.is_open
    assert pos.pnl == 0.0


def test_position_realized_pnl():
    """Test realized PnL calculation."""
    pos = Position(
        symbol="BTCUSDT",
        size=1.0,
        entry_price=50000.0,
        entry_time=datetime.now(),
        exit_price=55000.0,
        exit_time=datetime.now() + timedelta(hours=1),
    )
    
    assert not pos.is_open
    assert pos.pnl == 5000.0
    assert pos.holding_period is not None


def test_backtest_engine_init():
    """Test backtest engine initialization."""
    engine = BacktestEngine(
        capital=10000,
        fees=0.001,
        slippage=0.0005,
    )
    
    assert engine.initial_capital == 10000
    assert engine.capital == 10000
    assert engine.fees == 0.001
    assert engine.slippage == 0.0005
    assert len(engine.positions) == 0
    assert len(engine.orders) == 0

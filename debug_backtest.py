#!/usr/bin/env python3
"""Debug backtest to see what's happening."""

from datetime import datetime, timedelta

import polars as pl

from quant_infra.backtesting import BacktestEngine
from quant_infra.data import DataLoader, Exchange
from quant_algos.strategies import get_strategy


def main():
    """Debug backtest."""
    print("Debugging backtest...")
    
    # Load data
    loader = DataLoader(exchange=Exchange.BINANCE)
    data = loader.load('BTCUSDT', datetime.now() - timedelta(days=7), datetime.now())
    
    print(f"Data shape: {data.shape}")
    print(f"Latest close: {data['close'].last()}")
    
    # Test momentum strategy
    strategy = get_strategy('momentum')(period=20, threshold=0.002)
    
    # Manually call strategy
    signals = strategy(data, [], 10000)
    print(f"\nGenerated {len(signals)} signals: {signals}")
    
    # Now test with backtest
    engine = BacktestEngine(capital=10000)
    
    # Monkey-patch to see what's happening
    original_run = engine.run
    
    def debug_run(data, strategy_fn, start=None, end=None):
        result = original_run(data, strategy_fn, start, end)
        print(f"\nEngine positions: {len(engine.positions)}")
        print(f"Engine orders: {len(engine.orders)}")
        print(f"Trades: {result.num_trades}")
        return result
    
    engine.run = debug_run
    
    result = engine.run(data, strategy)
    print(f"\nFinal result: {result.num_trades} trades")


if __name__ == "__main__":
    main()

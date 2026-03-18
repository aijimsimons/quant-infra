#!/usr/bin/env python3
"""Comprehensive backtest example with real data."""

from datetime import datetime, timedelta

import polars as pl

from quant_infra.backtesting import BacktestEngine
from quant_infra.data import DataLoader, Exchange
from quant_algos.strategies import get_strategy


def main():
    """Run comprehensive backtest."""
    print("=" * 70)
    print("COMPREHENSIVE BACKTEST EXAMPLE")
    print("=" * 70)
    
    # Fetch real data from Binance
    print("\nFetching real BTCUSDT data from Binance...")
    loader = DataLoader(exchange=Exchange.BINANCE)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    try:
        data = loader.load(
            symbol="BTCUSDT",
            start=start_date,
            end=end_date,
            interval="1h"
        )
        print(f"✓ Fetched {len(data)} data points from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    except Exception as e:
        print(f"⚠ Data fetch failed: {e}")
        print("Using sample data instead...")
        # Generate sample data
        dates = [start_date + timedelta(hours=i) for i in range(720)]
        prices = [100.0]
        for i in range(1, len(dates)):
            prices.append(prices[-1] * (1 + 0.001 if i % 10 == 0 else -0.0005))
        data = pl.DataFrame({
            "datetime": dates,
            "symbol": ["BTCUSDT"] * len(dates),
            "open": prices,
            "high": [p * 1.002 for p in prices],
            "low": [p * 0.998 for p in prices],
            "close": prices,
            "volume": [1000 + i * 10 for i in range(len(dates))],
        })
    
    # Test multiple strategies
    strategies = {
        "momentum": get_strategy("momentum")(period=20, threshold=0.002),
        "mean_reversion": get_strategy("mean_reversion")(period=20, z_threshold=2.0),
        "bollinger": get_strategy("bollinger")(period=20, num_std=2.0),
    }
    
    print("\n" + "-" * 70)
    
    for name, strategy in strategies.items():
        print(f"\nTesting {name} strategy...")
        
        engine = BacktestEngine(
            capital=10000,
            fees=0.001,
            slippage=0.0005,
        )
        
        result = engine.run(data, strategy)
        
        print(f"  Initial: ${result.initial_capital:,.2f}")
        print(f"  Final: ${result.final_capital:,.2f}")
        print(f"  Return: {result.total_return:.2%}")
        print(f"  Sharpe: {result.sharpe_ratio:.2f}")
        print(f"  Max DD: {result.max_drawdown:.2%}")
        print(f"  Trades: {result.num_trades}")
        print(f"  Win Rate: {result.win_rate:.2%}")
        
        print("-" * 70)
    
    print("\n" + "=" * 70)
    print("BACKTEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()

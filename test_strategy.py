#!/usr/bin/env python3
"""Test strategy signal generation."""

from datetime import datetime, timedelta

import polars as pl

from quant_infra.data import DataLoader, Exchange
from quant_algos.strategies import get_strategy


def main():
    """Test strategy signal generation."""
    print("Testing strategy signal generation...")
    
    # Load data
    loader = DataLoader(exchange=Exchange.BINANCE)
    data = loader.load('BTCUSDT', datetime.now() - timedelta(days=7), datetime.now())
    
    print(f"Data shape: {data.shape}")
    print(f"Latest close: {data['close'].last()}")
    
    # Test momentum strategy
    strategy = get_strategy('momentum')(period=20, threshold=0.05)
    
    signals = strategy(data, [], 10000)
    print(f"\nGenerated signals: {len(signals)}")
    for s in signals:
        print(f"  {s}")


if __name__ == "__main__":
    main()

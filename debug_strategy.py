#!/usr/bin/env python3
"""Debug strategy signal generation."""

from datetime import datetime, timedelta

import polars as pl

from quant_infra.data import DataLoader, Exchange
from quant_algos.strategies import get_strategy


def main():
    """Debug strategy signal generation."""
    print("Debugging strategy signal generation...")
    
    # Load data
    loader = DataLoader(exchange=Exchange.BINANCE)
    data = loader.load('BTCUSDT', datetime.now() - timedelta(days=7), datetime.now())
    
    print(f"Data shape: {data.shape}")
    
    # Manually run the strategy logic
    period = 20
    threshold = 0.002
    
    # Calculate returns
    df = data.with_columns(
        (pl.col("close") / pl.col("close").shift(period) - 1).alias(f"return_{period}d")
    )
    
    print(f"\nLatest return_{period}d: {df[f'return_{period}d'].last()}")
    print(f"Threshold: {threshold}")
    
    # Generate signals
    df = df.with_columns(
        pl.when(pl.col(f"return_{period}d") > threshold).then(1.0)
         .when(pl.col(f"return_{period}d") < -threshold).then(-1.0)
         .otherwise(0.0)
         .alias("signal")
    )
    
    print(f"Latest signal: {df['signal'].last()}")
    
    # Get latest row
    latest = df.sort("datetime").tail(1)
    print(f"Latest datetime: {latest['datetime'].item()}")
    print(f"Latest signal: {latest['signal'].item()}")
    
    # Generate signals
    signal = latest["signal"].item()
    print(f"\nFinal signal: {signal}")
    
    if signal != 0:
        print("Should generate trade!")
    else:
        print("No trade generated - signal is 0")


if __name__ == "__main__":
    main()

"""Simple backtest example."""

from datetime import datetime, timedelta

import polars as pl

from quant_infra.backtesting import BacktestEngine
from quant_algos.strategies import get_strategy


def generate_sample_data(symbol: str, n_days: int = 30) -> pl.DataFrame:
    """Generate sample data for backtesting."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=n_days)
    
    # Generate datetime range
    dates = [start_date + timedelta(hours=i) for i in range(n_days * 24)]
    
    # Generate realistic price data
    prices = [100.0]
    for i in range(1, len(dates)):
        change = 0.001 if i % 10 == 0 else -0.0005
        prices.append(prices[-1] * (1 + change))
    
    df = pl.DataFrame({
        "datetime": dates,
        "symbol": [symbol] * len(dates),
        "open": prices,
        "high": [p * 1.002 for p in prices],
        "low": [p * 0.998 for p in prices],
        "close": prices,
        "volume": [1000 + i * 10 for i in range(len(dates))],
    })
    
    return df


def main():
    """Run simple backtest."""
    print("=" * 60)
    print("SIMPLE BACKTEST EXAMPLE")
    print("=" * 60)
    
    # Generate sample data
    data = generate_sample_data("BTCUSDT", n_days=30)
    print(f"\nGenerated {len(data)} data points")
    
    # Get momentum strategy
    strategy_fn = get_strategy("momentum")
    strategy = strategy_fn(period=20, threshold=0.05)
    
    # Initialize backtest engine
    engine = BacktestEngine(
        capital=10000,
        fees=0.001,
        slippage=0.0005,
    )
    
    # Run backtest
    result = engine.run(data, strategy)
    
    # Print results
    print("\n" + "=" * 60)
    print("BACKTEST RESULTS")
    print("=" * 60)
    print(f"Initial Capital: ${result.initial_capital:,.2f}")
    print(f"Final Capital: ${result.final_capital:,.2f}")
    print(f"Total Return: {result.total_return:.2%}")
    print(f"Annualized Return: {result.annualized_return:.2%}")
    print(f"Max Drawdown: {result.max_drawdown:.2%}")
    print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
    print(f"Sortino Ratio: {result.sortino_ratio:.2f}")
    print(f"Win Rate: {result.win_rate:.2%}")
    print(f"Profit Factor: {result.profit_factor:.2f}")
    print(f"Number of Trades: {result.num_trades}")
    print(f"Avg Win: ${result.avg_win:.2f}")
    print(f"Avg Loss: ${result.avg_loss:.2f}")
    print("=" * 60)


if __name__ == "__main__":
    main()

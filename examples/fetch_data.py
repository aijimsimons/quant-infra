"""Example script to fetch crypto data from exchanges."""

from datetime import datetime, timedelta

from quant_infra.data import DataLoader, Exchange


def main():
    """Fetch sample data from Binance."""
    # Initialize loader
    loader = DataLoader(exchange=Exchange.BINANCE)
    
    # Define parameters
    symbol = "BTCUSDT"
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    print(f"Fetching {symbol} data from {start_date} to {end_date}...")
    
    # Fetch data
    data = loader.load(
        symbol=symbol,
        start=start_date,
        end=end_date,
        interval="1h"
    )
    
    print(f"Fetched {len(data)} rows")
    print(data.head())
    print(data.tail())
    
    # Save to CSV
    data.write_csv(f"{symbol}_data.csv")
    print(f"\nSaved to {symbol}_data.csv")


if __name__ == "__main__":
    main()

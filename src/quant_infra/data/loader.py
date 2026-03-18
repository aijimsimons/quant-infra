"""Data loader with multi-exchange support."""

from datetime import datetime
from typing import Optional
from enum import Enum
import httpx

import polars as pl


class Exchange(Enum):
    """Supported exchanges."""
    BINANCE = "binance"
    BYBIT = "bybit"
    KUCOIN = "kucoin"


class DataLoader:
    """Multi-exchange data loader for crypto market data."""
    
    def __init__(self, exchange: Exchange = Exchange.BINANCE):
        """
        Initialize loader.
        
        Args:
            exchange: Exchange to fetch from
        """
        self.exchange = exchange
        self.base_urls = {
            Exchange.BINANCE: "https://api.binance.com",
            Exchange.BYBIT: "https://api.bybit.com",
            Exchange.KUCOIN: "https://api.kucoin.com",
        }
        self.client = httpx.Client(timeout=30.0)
    
    def fetch_klines(
        self,
        symbol: str,
        interval: str,
        start_ts: int,
        end_ts: Optional[int] = None,
        limit: int = 1000
    ) -> list[dict]:
        """
        Fetch klines (candlestick data).
        
        Args:
            symbol: Trading pair (e.g., BTCUSDT)
            interval: Candle interval (1m, 5m, 15m, 30m, 1h, 4h, 1d)
            start_ts: Start timestamp in milliseconds
            end_ts: End timestamp (optional)
            limit: Max records per request
            
        Returns:
            List of kline data
        """
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": start_ts,
            "limit": limit,
        }
        if end_ts:
            params["endTime"] = end_ts
        
        url = f"{self.base_urls[self.exchange]}/api/v3/klines"
        response = self.client.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return self._parse_klines(data, symbol)
    
    def _parse_klines(self, data: list, symbol: str) -> list[dict]:
        """Parse kline data to standard format."""
        records = []
        for kline in data:
            records.append({
                "datetime": datetime.fromtimestamp(kline[0] / 1000),
                "symbol": symbol,
                "open": float(kline[1]),
                "high": float(kline[2]),
                "low": float(kline[3]),
                "close": float(kline[4]),
                "volume": float(kline[5]),
            })
        return records
    
    def load(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        interval: str = "1h"
    ) -> pl.DataFrame:
        """
        Load market data for a symbol.
        
        Args:
            symbol: Trading pair
            start: Start datetime
            end: End datetime
            interval: Candle interval
            
        Returns:
            DataFrame with market data
        """
        all_records = []
        current_start = int(start.timestamp() * 1000)
        current_end = int(end.timestamp() * 1000)
        
        while current_start < current_end:
            records = self.fetch_klines(
                symbol=symbol,
                interval=interval,
                start_ts=current_start,
                end_ts=current_end
            )
            
            if not records:
                break
            
            all_records.extend(records)
            current_start = int(records[-1]["datetime"].timestamp() * 1000) + 1
        
        df = pl.DataFrame(all_records)
        
        # Ensure correct types
        df = df.with_columns(
            pl.col("datetime").cast(pl.Datetime),
            pl.col("open").cast(pl.Float64),
            pl.col("high").cast(pl.Float64),
            pl.col("low").cast(pl.Float64),
            pl.col("close").cast(pl.Float64),
            pl.col("volume").cast(pl.Float64),
        )
        
        # Sort by datetime
        df = df.sort("datetime")
        
        return df

"""Technical indicators and feature engineering."""

import polars as pl


def add_rsi(df: pl.DataFrame, period: int = 14) -> pl.DataFrame:
    """Add RSI indicator."""
    delta = pl.col("close").diff()
    gain = delta.clip(min=0)
    loss = -delta.clip(max=0)
    
    avg_gain = gain.rolling_mean(window_size=period)
    avg_loss = loss.rolling_mean(window_size=period)
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return df.with_columns(rsi.alias(f"rsi_{period}"))


def add_macd(df: pl.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pl.DataFrame:
    """Add MACD indicator."""
    ema_fast = pl.col("close").ewm_mean(span=fast)
    ema_slow = pl.col("close").ewm_mean(span=slow)
    
    macd = ema_fast - ema_slow
    signal_line = macd.ewm_mean(span=signal)
    histogram = macd - signal_line
    
    return df.with_columns([
        macd.alias(f"macd_{fast}_{slow}"),
        signal_line.alias(f"macd_signal_{signal}"),
        histogram.alias(f"macd_hist_{fast}_{slow}_{signal}"),
    ])


def add_bollinger_bands(df: pl.DataFrame, period: int = 20, num_std: float = 2.0) -> pl.DataFrame:
    """Add Bollinger Bands."""
    close = pl.col("close")
    middle = close.rolling_mean(window_size=period)
    std = close.rolling_std(window_size=period)
    
    upper = middle + (std * num_std)
    lower = middle - (std * num_std)
    
    return df.with_columns([
        upper.alias(f"bb_upper_{period}"),
        middle.alias(f"bb_middle_{period}"),
        lower.alias(f"bb_lower_{period}"),
    ])


def add_sma(df: pl.DataFrame, period: int) -> pl.DataFrame:
    """Add Simple Moving Average."""
    return df.with_columns(
        pl.col("close").rolling_mean(window_size=period).alias(f"sma_{period}")
    )


def add_ema(df: pl.DataFrame, period: int) -> pl.DataFrame:
    """Add Exponential Moving Average."""
    return df.with_columns(
        pl.col("close").ewm_mean(span=period).alias(f"ema_{period}")
    )


def add_returns(df: pl.DataFrame, period: int = 1) -> pl.DataFrame:
    """Add returns."""
    return df.with_columns(
        (pl.col("close") / pl.col("close").shift(period) - 1).alias(f"return_{period}d")
    )


def add_volatility(df: pl.DataFrame, period: int = 20) -> pl.DataFrame:
    """Add realized volatility."""
    returns = pl.col("close").pct_change()
    volatility = returns.pow(2).rolling_mean(window_size=period).sqrt()
    
    return df.with_columns(volatility.alias(f"volatility_{period}d"))


def add_price_channels(df: pl.DataFrame, period: int = 20) -> pl.DataFrame:
    """Add price channels (highest high / lowest low)."""
    return df.with_columns([
        pl.col("high").rolling_max(window_size=period).alias(f"channel_high_{period}"),
        pl.col("low").rolling_min(window_size=period).alias(f"channel_low_{period}"),
    ])

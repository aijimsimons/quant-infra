"""Event-driven backtesting engine."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Generator

import polars as pl


@dataclass
class Position:
    """Represents a position in a security."""
    symbol: str
    size: float
    entry_price: float
    entry_time: datetime
    
    @property
    def pnl(self, current_price: float) -> float:
        """Calculate PnL for current price."""
        return (current_price - self.entry_price) * self.size


@dataclass
class Order:
    """Represents an order."""
    symbol: str
    size: float
    price: float | None = None
    time: datetime | None = None
    order_type: str = "market"  # market, limit, stop


@dataclass 
class BacktestResult:
    """Results from a backtest."""
    initial_capital: float
    final_capital: float
    total_return: float
    annualized_return: float
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    win_rate: float
    profit_factor: float
    equity_curve: pl.DataFrame
    positions: list[Position]
    
    def summary(self) -> dict:
        """Return summary dict."""
        return {
            "initial_capital": self.initial_capital,
            "final_capital": self.final_capital,
            "total_return": self.total_return,
            "annualized_return": self.annualized_return,
            "max_drawdown": self.max_drawdown,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "win_rate": self.win_rate,
            "profit_factor": self.profit_factor,
        }


class BacktestEngine:
    """Event-driven backtesting engine."""
    
    def __init__(self, capital: float, fees: float = 0.001, slippage: float = 0.0005):
        """
        Initialize backtest engine.
        
        Args:
            capital: Initial capital
            fees: Trading fees (percentage)
            slippage: Slippage (percentage)
        """
        self.capital = capital
        self.fees = fees
        self.slippage = slippage
        
        self.positions: list[Position] = []
        self.orders: list[Order] = []
        self.history: list[dict] = []
        self.equity_curve: list[dict] = []
        
    def run(
        self,
        data: pl.DataFrame,
        strategy: Callable[[pl.DataFrame, list[Position], float], list[Order]],
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> BacktestResult:
        """
        Run backtest.
        
        Args:
            data: Historical price data with datetime, open, high, low, close, volume
            strategy: Function that takes data, positions, capital and returns orders
            start: Start datetime (optional)
            end: End datetime (optional)
            
        Returns:
            BacktestResult
        """
        # Filter data
        df = data.clone()
        if start:
            df = df.filter(pl.col("datetime") >= start)
        if end:
            df = df.filter(pl.col("datetime") <= end)
        
        # Sort by datetime
        df = df.sort("datetime")
        
        # Main loop
        for row in df.iter_rows(named=True):
            dt = row["datetime"]
            open_price = row["open"]
            high_price = row["high"]
            low_price = row["low"]
            close_price = row["close"]
            volume = row["volume"]
            
            # Calculate current equity
            current_equity = self.capital + sum(
                p.pnl(close_price) for p in self.positions if p.symbol == row.get("symbol")
            )
            
            # Record equity
            self.equity_curve.append({
                "datetime": dt,
                "capital": self.capital,
                "equity": current_equity,
                "positions": len(self.positions),
            })
            
            # Generate orders from strategy
            orders = strategy(df, self.positions, current_equity)
            
            # Execute orders
            for order in orders:
                self._execute_order(order, close_price, dt)
            
            # Update positions
            self._update_positions(close_price, dt)
        
        # Calculate results
        return self._calculate_results()
    
    def _execute_order(self, order: Order, price: float, dt: datetime) -> None:
        """Execute an order."""
        order.price = price * (1 + self.slippage * (1 if order.size > 0 else -1))
        order.time = dt
        
        cost = abs(order.size) * order.price * (1 + self.fees)
        
        if cost <= self.capital:
            self.capital -= cost
            if order.size > 0:
                # Buy
                self.positions.append(Position(
                    symbol=order.symbol,
                    size=order.size,
                    entry_price=order.price,
                    entry_time=order.time,
                ))
            else:
                # Sell (close position)
                # Find position to close
                for i, pos in enumerate(self.positions):
                    if pos.symbol == order.symbol and pos.size > 0:
                        self.positions.pop(i)
                        break
    
    def _update_positions(self, current_price: float, dt: datetime) -> None:
        """Update position records."""
        for pos in self.positions:
            # Could add margin calls, etc. here
            pass
    
    def _calculate_results(self) -> BacktestResult:
        """Calculate backtest results."""
        equity_df = pl.DataFrame(self.equity_curve)
        
        initial_capital = self.equity_curve[0]["capital"] if self.equity_curve else 0
        final_capital = self.capital
        
        total_return = (final_capital - initial_capital) / initial_capital if initial_capital > 0 else 0
        
        # Calculate returns series
        equity_df = equity_df.with_columns(
            (pl.col("equity") / pl.col("equity").shift(1) - 1).alias("returns")
        )
        
        returns = equity_df["returns"].drop_nulls()
        
        # Statistics
        mean_return = returns.mean() if len(returns) > 0 else 0
        std_return = returns.std() if len(returns) > 0 else 0
        
        sharpe_ratio = (mean_return / std_return * 252**0.5) if std_return > 0 else 0
        
        # Max drawdown
        equity_series = equity_df["equity"].to_list()
        max_drawdown = 0.0
        peak = equity_series[0] if equity_series else 0
        for eq in equity_series:
            if eq > peak:
                peak = eq
            drawdown = (peak - eq) / peak if peak > 0 else 0
            max_drawdown = max(max_drawdown, drawdown)
        
        # Win rate
        wins = sum(1 for r in returns if r > 0)
        win_rate = wins / len(returns) if len(returns) > 0 else 0
        
        # Profit factor
        gains = sum(r for r in returns if r > 0)
        losses = abs(sum(r for r in returns if r < 0))
        profit_factor = gains / losses if losses > 0 else gains
        
        return BacktestResult(
            initial_capital=initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            annualized_return=mean_return * 252,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sharpe_ratio * 0.7,  # Simplified
            win_rate=win_rate,
            profit_factor=profit_factor,
            equity_curve=equity_df,
            positions=self.positions,
        )

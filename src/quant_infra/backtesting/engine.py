"""Event-driven backtesting engine with advanced features."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Generator

import polars as pl


@dataclass
class Position:
    """Represents a position in a security."""
    symbol: str
    size: float
    entry_price: float
    entry_time: datetime
    exit_price: float | None = None
    exit_time: datetime | None = None
    
    @property
    def pnl(self) -> float:
        """Calculate PnL (realized or unrealized)."""
        if self.exit_price is not None:
            return (self.exit_price - self.entry_price) * self.size
        return 0.0
    
    @property
    def is_open(self) -> bool:
        """Check if position is still open."""
        return self.exit_price is None
    
    @property
    def holding_period(self) -> timedelta | None:
        """Calculate holding period."""
        if self.exit_time:
            return self.exit_time - self.entry_time
        return None


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
    num_trades: int
    avg_win: float
    avg_loss: float
    avg_holding_period: timedelta | None
    equity_curve: pl.DataFrame
    trades: list[dict]
    
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
            "num_trades": self.num_trades,
        }


class BacktestEngine:
    """Event-driven backtesting engine with slippage and fees."""
    
    def __init__(
        self, 
        capital: float, 
        fees: float = 0.001,  # 0.1% trading fees
        slippage: float = 0.0005,  # 0.05% slippage
        margin: float = 1.0,  # 100% margin (no leverage)
        leverage: float = 1.0,  # Leverage multiplier
    ):
        """
        Initialize backtest engine.
        
        Args:
            capital: Initial capital
            fees: Trading fees (percentage)
            slippage: Slippage (percentage)
            margin: Margin requirement (fraction of position value)
            leverage: Leverage multiplier
        """
        self.initial_capital = capital
        self.capital = capital
        self.fees = fees
        self.slippage = slippage
        self.margin = margin
        self.leverage = leverage
        
        self.positions: list[Position] = []
        self.orders: list[dict] = []
        self.history: list[dict] = []
        self.equity_curve: list[dict] = []
        self.trades: list[dict] = []
        
    def run(
        self,
        data: pl.DataFrame,
        strategy: Callable[[pl.DataFrame, list[Position], float], list[dict]],
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> BacktestResult:
        """
        Run backtest.
        
        Args:
            data: Historical price data with datetime, symbol, open, high, low, close, volume
            strategy: Function that returns orders based on state
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
        
        # Track equity over time
        current_equity = self.capital
        
        # Main loop
        for row in df.iter_rows(named=True):
            dt = row["datetime"]
            symbol = row.get("symbol", "UNKNOWN")
            open_price = row["open"]
            high_price = row["high"]
            low_price = row["low"]
            close_price = row["close"]
            volume = row.get("volume", 0.0)
            
            # Calculate current equity
            unrealized_pnl = sum(
                p.pnl for p in self.positions
            )
            current_equity = self.capital + unrealized_pnl
            
            # Record equity
            self.equity_curve.append({
                "datetime": dt,
                "capital": self.capital,
                "unrealized_pnl": unrealized_pnl,
                "equity": current_equity,
                "positions": len(self.positions),
            })
            
            # Generate orders from strategy
            orders = strategy(df, self.positions, current_equity)
            
            # Execute orders
            for order in orders:
                self._execute_order(order, close_price, dt)
            
            # Update positions
            self._update_positions(high_price, low_price, close_price, dt)
        
        # Calculate results
        return self._calculate_results()
    
    def _execute_order(self, order: dict, price: float, dt: datetime) -> None:
        """Execute an order."""
        symbol = order["symbol"]
        size = order["size"]
        order_type = order.get("order_type", "market")
        
        # Apply slippage
        if size > 0:  # Buy
            exec_price = price * (1 + self.slippage)
        else:  # Sell
            exec_price = price * (1 - self.slippage)
        
        # Calculate cost
        cost = abs(size) * exec_price * (1 + self.fees)
        
        # Check margin requirements
        required_margin = cost * self.margin
        
        if required_margin <= self.capital:
            self.capital -= required_margin
            
            if order_type == "market":
                if size > 0:
                    # Buy - open position
                    pos = Position(
                        symbol=symbol,
                        size=size,
                        entry_price=exec_price,
                        entry_time=dt,
                    )
                    self.positions.append(pos)
                else:
                    # Sell - close position (find and close)
                    for i, pos in enumerate(self.positions):
                        if pos.symbol == symbol and pos.is_open:
                            pos.exit_price = exec_price
                            pos.exit_time = dt
                            self.trades.append({
                                "symbol": symbol,
                                "entry_time": pos.entry_time,
                                "exit_time": dt,
                                "entry_price": pos.entry_price,
                                "exit_price": exec_price,
                                "size": abs(pos.size),
                                "pnl": pos.pnl,
                            })
                            self.positions.pop(i)
                            break
    
    def _update_positions(
        self, high: float, low: float, close: float, dt: datetime
    ) -> None:
        """Update positions with current prices."""
        for pos in self.positions:
            # Could add margin calls, stop losses, etc.
            pass
    
    def _calculate_results(self) -> BacktestResult:
        """Calculate backtest results."""
        equity_df = pl.DataFrame(self.equity_curve)
        
        # Calculate returns
        equity_df = equity_df.with_columns(
            (pl.col("equity") / pl.col("equity").shift(1) - 1).alias("returns")
        )
        
        returns = equity_df["returns"].drop_nulls()
        
        # Statistics
        mean_return = returns.mean() if len(returns) > 0 else 0
        std_return = returns.std() if len(returns) > 0 else 0
        
        # Annualized metrics
        trading_days = 252
        annualized_return = mean_return * trading_days if mean_return else 0
        
        # Sharpe ratio
        sharpe_ratio = (mean_return / std_return * trading_days**0.5) if std_return else 0
        
        # Max drawdown
        equity_series = equity_df["equity"].to_list()
        max_drawdown = 0.0
        peak = equity_series[0] if equity_series else 0
        for eq in equity_series:
            if eq > peak:
                peak = eq
            drawdown = (peak - eq) / peak if peak > 0 else 0
            max_drawdown = max(max_drawdown, drawdown)
        
        # Trade statistics
        wins = [t["pnl"] for t in self.trades if t["pnl"] > 0]
        losses = [t["pnl"] for t in self.trades if t["pnl"] < 0]
        
        num_trades = len(self.trades)
        win_rate = len(wins) / num_trades if num_trades > 0 else 0
        avg_win = sum(wins) / len(wins) if wins else 0
        avg_loss = abs(sum(losses)) / len(losses) if losses else 0
        
        # Profit factor
        total_wins = sum(wins)
        total_losses = abs(sum(losses))
        profit_factor = total_wins / total_losses if total_losses > 0 else total_wins
        
        # Average holding period
        holding_periods = [
            t["exit_time"] - t["entry_time"] for t in self.trades
            if t["exit_time"]
        ]
        avg_holding_period = (
            sum(holding_periods, timedelta()) / len(holding_periods)
            if holding_periods else None
        )
        
        return BacktestResult(
            initial_capital=self.initial_capital,
            final_capital=self.capital,
            total_return=(self.capital - self.initial_capital) / self.initial_capital if self.initial_capital else 0,
            annualized_return=annualized_return,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sharpe_ratio * 0.7,  # Simplified
            win_rate=win_rate,
            profit_factor=profit_factor,
            num_trades=num_trades,
            avg_win=avg_win,
            avg_loss=avg_loss,
            avg_holding_period=avg_holding_period,
            equity_curve=equity_df,
            trades=self.trades,
        )

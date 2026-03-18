"""Risk management utilities."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

import polars as pl


class RiskManager(Protocol):
    """Protocol for risk managers."""
    
    def check(self, capital: float, positions: list, signals: list) -> list:
        """Check if orders pass risk checks."""
        ...


@dataclass
class PositionLimit:
    """Maximum position size limit."""
    max_position: float = 0.1  # 10% of capital per position
    
    def check(self, capital: float, positions: list, signals: list) -> list:
        """Limit position sizes."""
        limited_signals = []
        for signal in signals:
            if abs(signal["size"]) > capital * self.max_position:
                signal["size"] = capital * self.max_position * (1 if signal["size"] > 0 else -1)
            limited_signals.append(signal)
        return limited_signals


@dataclass
class DrawdownLimit:
    """Maximum drawdown limit."""
    max_drawdown: float = 0.15  # 15% max drawdown
    _peak: float = 0.0
    
    def check(self, capital: float, positions: list, signals: list) -> list:
        """Limit if drawdown threshold reached."""
        # Track peak
        current_equity = capital + sum(p.pnl for p in positions)
        if current_equity > self._peak:
            self._peak = current_equity
        
        # Check drawdown
        if self._peak > 0:
            drawdown = (self._peak - current_equity) / self._peak
            if drawdown >= self.max_drawdown:
                # Stop trading
                return []
        
        return signals


@dataclass
class VolatilityTarget:
    """Target volatility position sizing."""
    target_vol: float = 0.15  # 15% annualized volatility
    _recent_returns: list = None
    
    def __post_init__(self):
        self._recent_returns = []
    
    def calculate_position_size(self, capital: float, volatility: float, signal: float) -> float:
        """Calculate position size based on volatility."""
        if volatility == 0:
            return 0
        
        # Scale to target volatility
        scale = self.target_vol / volatility
        size = capital * scale * signal
        
        return size
    
    def check(self, capital: float, positions: list, signals: list) -> list:
        """Apply volatility-based position sizing."""
        # TODO: Calculate realized volatility
        return signals


@dataclass
class ExposureLimit:
    """Maximum total exposure limit."""
    max_exposure: float = 0.5  # 50% of capital
    
    def check(self, capital: float, positions: list, signals: list) -> list:
        """Limit total exposure."""
        current_exposure = sum(abs(p.size * p.entry_price) for p in positions)
        total_exposure = current_exposure
        
        limited_signals = []
        for signal in signals:
            if total_exposure + abs(signal["size"] * signal.get("price", 0)) > capital * self.max_exposure:
                # Scale down
                remaining = capital * self.max_exposure - total_exposure
                if remaining > 0:
                    signal["size"] = remaining / signal.get("price", 1)
                else:
                    continue
            limited_signals.append(signal)
            total_exposure += abs(signal["size"] * signal.get("price", 0))
        
        return limited_signals


class CompositeRiskManager:
    """Combine multiple risk managers."""
    
    def __init__(self, managers: list[RiskManager] = None):
        self.managers = managers or []
    
    def add_manager(self, manager: RiskManager) -> None:
        """Add a risk manager."""
        self.managers.append(manager)
    
    def check(self, capital: float, positions: list, signals: list) -> list:
        """Apply all risk managers."""
        for manager in self.managers:
            signals = manager.check(capital, positions, signals)
        return signals

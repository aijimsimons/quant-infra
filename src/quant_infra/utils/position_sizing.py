"""Position sizing utilities."""

from dataclasses import dataclass
from typing import Protocol

import polars as pl


class SizingStrategy(Protocol):
    """Protocol for position sizing strategies."""
    
    def size_position(self, capital: float, signal: float, volatility: float) -> float:
        """
        Calculate position size.
        
        Args:
            capital: Available capital
            signal: Signal strength (-1 to 1)
            volatility: Asset volatility
            
        Returns:
            Position size (number of units)
        """
        ...


@dataclass
class FixedFractional:
    """Fixed fractional position sizing."""
    fraction: float = 0.02
    
    def size_position(self, capital: float, signal: float, volatility: float) -> float:
        """Size based on fixed fraction of capital."""
        return int((capital * self.fraction) / (volatility * 100))


@dataclass
class Kelly:
    """Kelly criterion position sizing."""
    kelly_fraction: float = 0.25
    win_rate: float = 0.55
    win_loss_ratio: float = 1.5
    
    def size_position(self, capital: float, signal: float, volatility: float) -> float:
        """Kelly fraction of capital."""
        kelly = self.win_rate - (1 - self.win_rate) / self.win_loss_ratio
        kelly *= self.kelly_fraction
        return int(capital * kelly / volatility)


@dataclass
class VolatilityTarget:
    """Target volatility position sizing."""
    target_vol: float = 0.15
    annualization: float = 252
    
    def size_position(self, capital: float, signal: float, volatility: float) -> float:
        """Scale to target volatility."""
        if volatility == 0:
            return 0
        scale = self.target_vol / (volatility * self.annualization**0.5)
        return int(capital * scale / 100)

# quant-infra

Quantitative trading infrastructure with modern Python stack.

## Overview

A modular, production-ready infrastructure for quantitative crypto trading, featuring:

- **Multi-exchange data loading** (Binance, Bybit, KuCoin)
- **Advanced technical indicators** (RSI, MACD, Bollinger Bands, etc.)
- **Event-driven backtesting engine** with detailed metrics
- **Comprehensive risk management**
- **Data caching with LRU eviction**

## Stack

- **Data**: `polars` for fast columnar data processing
- **ML**: `numpy`, `scipy`, `pandas`
- **Validation**: `pydantic`
- **Testing**: `pytest` + `hypothesis`
- **Type checking**: `mypy`
- **Linting**: `ruff`

## Installation

```bash
# Clone the repo
git clone https://github.com/aijimsimons/quant-infra.git
cd quant-infra

# Install dependencies with uv
uv sync

# Activate virtual environment
source .venv/bin/activate
```

## Project Structure

```
quant-infra/
├── src/
│   └── quant_infra/
│       ├── backtesting/     # Backtesting engine
│       │   └── engine.py
│       ├── data/            # Data ingestion & preprocessing
│       │   ├── loader.py    # Multi-exchange data loader
│       │   ├── cache.py     # LRU caching
│       │   ├── pipeline.py  # Data pipeline
│       │   └── transform.py # Technical indicators
│       ├── risk/            # Risk management
│       │   └── managers.py  # Risk managers
│       └── utils/           # Common utilities
│           └── position_sizing.py
├── tests/
└── notebooks/
```

## Quick Start

### Load Data

```python
from datetime import datetime
from quant_infra.data import DataLoader, Exchange

loader = DataLoader(exchange=Exchange.BINANCE)

data = loader.load(
    symbol="BTCUSDT",
    start=datetime(2024, 1, 1),
    end=datetime(2024, 12, 31),
    interval="1h"
)
```

### Backtest a Strategy

```python
from quant_infra.backtesting import BacktestEngine
from quant_algos.strategies import get_strategy

engine = BacktestEngine(capital=10000)
strategy = get_strategy("momentum")(period=20, threshold=0.05)

result = engine.run(data, strategy)

print(f"Sharpe: {result.sharpe_ratio:.2f}")
print(f"Max Drawdown: {result.max_drawdown:.2%}")
```

### Risk Management

```python
from quant_infra.risk import DrawdownLimit, ExposureLimit, CompositeRiskManager

risk_manager = CompositeRiskManager([
    DrawdownLimit(max_drawdown=0.15),
    ExposureLimit(max_exposure=0.5),
])

# Use risk_manager.check() before executing orders
```

## Development

```bash
# Run linter
uv run ruff check .

# Run type checker
uv run mypy .

# Run tests
uv run pytest
```

## Documentation

- [API Reference](docs/api.md)
- [Development Plan](DEVELOPMENT_PLAN.md)
- [Strategy Examples](../quant-algos/examples/)

## License

MIT

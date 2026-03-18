# quant-infra

Quantitative trading infrastructure with modern Python stack.

## Stack

- **Data**: `polars` for fast columnar data
- **ML**: `numpy`, `scipy`, `pandas`
- **Validation**: `pydantic`
- **Testing**: `pytest` + `hypothesis`
- **Type checking**: `mypy`
- **Linting**: `ruff`

## Setup

```bash
uv sync
uv run ruff check .
uv run mypy .
```

## Structure

```
quant-infra/
├── src/
│   └── quant_infra/
│       ├── backtesting/     # Backtesting engine
│       ├── data/            # Data ingestion & preprocessing
│       ├── risk/            # Risk management
│       └── utils/           # Common utilities
├── tests/
└── notebooks/
```

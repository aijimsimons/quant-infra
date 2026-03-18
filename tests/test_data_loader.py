"""Tests for data loader."""

import pytest

from quant_infra.data.loader import DataLoader, Exchange


def test_data_loader_init():
    """Test data loader initialization."""
    loader = DataLoader(exchange=Exchange.BINANCE)
    assert loader.exchange == Exchange.BINANCE
    assert loader.client is not None


def test_data_loader_symbols():
    """Test that we can list supported exchanges."""
    assert len(list(Exchange)) >= 3  # Binance, Bybit, KuCoin at minimum

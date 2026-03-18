#!/usr/bin/env python3
"""Quant Infra - Main entry point."""

import argparse

from examples.backtest_comprehensive import main as backtest_main


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Quant Infra - Trading Infrastructure")
    parser.add_argument("command", choices=["backtest"], help="Command to run")
    
    args = parser.parse_args()
    
    if args.command == "backtest":
        backtest_main()


if __name__ == "__main__":
    main()

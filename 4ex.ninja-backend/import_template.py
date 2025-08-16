#!/usr/bin/env python3
"""
Import Template for 4ex.ninja Backend Modules

This script demonstrates the correct way to import modules from the
backtesting framework when working from the backend root directory.
"""

import sys
import os

# Add the backend root and src directories to Python path
backend_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(backend_root, "src")
sys.path.insert(0, backend_root)
sys.path.insert(0, src_path)


# Example imports for portfolio management components
def demonstrate_imports():
    """Demonstrate correct import patterns."""

    print("📦 Importing Portfolio Management Components...")

    # Core portfolio management
    from src.backtesting.portfolio_manager import (
        UniversalPortfolioManager,
        PortfolioState,
    )
    from src.backtesting.risk_manager import UniversalRiskManager, RiskLevel
    from src.backtesting.correlation_manager import CorrelationManager
    from src.backtesting.multi_strategy_coordinator import MultiStrategyCoordinator

    # Strategy interfaces
    from src.backtesting.strategy_interface import BaseStrategy, TradeSignal

    # Backtesting engine
    from src.backtesting.universal_backtesting_engine import UniversalBacktestingEngine

    print("✅ All imports successful!")
    print("\n📝 Import Pattern:")
    print("   1. Add backend root and src to sys.path")
    print("   2. Use 'from src.backtesting.module_name import ClassName'")
    print("   3. Ensure __init__.py exists in backtesting directory")


if __name__ == "__main__":
    demonstrate_imports()

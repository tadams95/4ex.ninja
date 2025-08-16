"""
Strategy implementations for the universal backtesting framework.

This module contains strategy implementations that work with the universal
backtesting engine through the BaseStrategy interface.
"""

from .base_strategy import ConcreteBaseStrategy
from .ma_crossover_strategy import MAStrategy
from .rsi_strategy import RSIStrategy
from .bollinger_strategy import BollingerStrategy
from .strategy_factory import StrategyFactory
from .strategy_registry import strategy_registry

# Re-export BaseStrategy from strategy_interface for convenience
from ..strategy_interface import BaseStrategy

__all__ = [
    "BaseStrategy",
    "ConcreteBaseStrategy",
    "MAStrategy",
    "RSIStrategy",
    "BollingerStrategy",
    "StrategyFactory",
    "strategy_registry",
]

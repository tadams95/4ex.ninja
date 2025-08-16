"""
Strategy Factory for creating strategy instances.

This module provides a factory pattern for creating strategy instances
and managing strategy configuration.
"""

from typing import Dict, List, Any, Type
from .base_strategy import ConcreteBaseStrategy
from .ma_crossover_strategy import MAStrategy
from .rsi_strategy import RSIStrategy
from .bollinger_strategy import BollingerStrategy


class StrategyFactory:
    """
    Factory for creating strategy instances.

    This factory provides a centralized way to create strategy instances
    and manages the mapping between strategy names and their classes.
    """

    # Registry of available strategies
    STRATEGIES: Dict[str, Type[ConcreteBaseStrategy]] = {
        "ma_crossover": MAStrategy,
        "moving_average": MAStrategy,  # Alias
        "rsi": RSIStrategy,
        "rsi_momentum": RSIStrategy,  # Alias
        "bollinger": BollingerStrategy,
        "bollinger_bands": BollingerStrategy,  # Alias
    }

    @classmethod
    def create_strategy(
        cls, strategy_name: str, config: Dict[str, Any]
    ) -> ConcreteBaseStrategy:
        """
        Create strategy instance by name.

        Args:
            strategy_name: Name of the strategy to create
            config: Configuration dictionary for the strategy

        Returns:
            Strategy instance

        Raises:
            ValueError: If strategy name is not found
        """
        strategy_name = strategy_name.lower()

        if strategy_name not in cls.STRATEGIES:
            available = list(cls.STRATEGIES.keys())
            raise ValueError(
                f"Unknown strategy '{strategy_name}'. Available: {available}"
            )

        strategy_class = cls.STRATEGIES[strategy_name]
        return strategy_class(config)

    @classmethod
    def get_available_strategies(cls) -> List[str]:
        """
        Get list of available strategy names.

        Returns:
            List of strategy names
        """
        return list(cls.STRATEGIES.keys())

    @classmethod
    def register_strategy(
        cls, name: str, strategy_class: Type[ConcreteBaseStrategy]
    ) -> None:
        """
        Register a new strategy.

        Args:
            name: Name to register the strategy under
            strategy_class: Strategy class to register
        """
        cls.STRATEGIES[name.lower()] = strategy_class

    @classmethod
    def get_strategy_info(cls, strategy_name: str) -> Dict[str, Any]:
        """
        Get information about a strategy.

        Args:
            strategy_name: Name of the strategy

        Returns:
            Dictionary with strategy information
        """
        strategy_name = strategy_name.lower()

        if strategy_name not in cls.STRATEGIES:
            raise ValueError(f"Unknown strategy '{strategy_name}'")

        strategy_class = cls.STRATEGIES[strategy_name]

        # Create a temporary instance to get info
        temp_config = {}
        temp_instance = strategy_class(temp_config)

        return {
            "name": strategy_name,
            "class": strategy_class.__name__,
            "description": strategy_class.__doc__ or "No description available",
            "category": temp_instance._get_strategy_category(),
            "default_config": cls._get_default_config(strategy_class),
        }

    @classmethod
    def _get_default_config(
        cls, strategy_class: Type[ConcreteBaseStrategy]
    ) -> Dict[str, Any]:
        """
        Get default configuration for a strategy class.

        Args:
            strategy_class: Strategy class

        Returns:
            Default configuration dictionary
        """
        # Strategy-specific default configurations
        defaults = {
            MAStrategy: {
                "fast_ma": 10,
                "slow_ma": 20,
                "ma_type": "SMA",
                "min_crossover_strength": 0.0,
                "atr_period": 14,
                "sl_atr_multiplier": 2.0,
                "tp_atr_multiplier": 3.0,
                "min_atr_value": 0.0001,
                "min_rr_ratio": 1.5,
                "risk_per_trade": 0.02,
            },
            RSIStrategy: {
                "rsi_period": 14,
                "overbought_level": 70,
                "oversold_level": 30,
                "min_rsi_strength": 0.1,
                "atr_period": 14,
                "sl_atr_multiplier": 2.0,
                "tp_atr_multiplier": 3.0,
                "min_atr_value": 0.0001,
                "min_rr_ratio": 1.5,
                "risk_per_trade": 0.02,
            },
            BollingerStrategy: {
                "bb_period": 20,
                "bb_std": 2.0,
                "signal_mode": "reversal",
                "min_squeeze_bars": 5,
                "min_band_width": 0.001,
                "atr_period": 14,
                "sl_atr_multiplier": 2.0,
                "tp_atr_multiplier": 3.0,
                "min_atr_value": 0.0001,
                "min_rr_ratio": 1.5,
                "risk_per_trade": 0.02,
            },
        }

        return defaults.get(strategy_class, {})

    @classmethod
    def validate_config(
        cls, strategy_name: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate and complete strategy configuration.

        Args:
            strategy_name: Name of the strategy
            config: Configuration to validate

        Returns:
            Validated and completed configuration
        """
        strategy_name = strategy_name.lower()

        if strategy_name not in cls.STRATEGIES:
            raise ValueError(f"Unknown strategy '{strategy_name}'")

        strategy_class = cls.STRATEGIES[strategy_name]
        default_config = cls._get_default_config(strategy_class)

        # Merge with defaults
        validated_config = default_config.copy()
        validated_config.update(config)

        return validated_config

    @classmethod
    def list_strategies_by_category(cls) -> Dict[str, List[str]]:
        """
        List strategies grouped by category.

        Returns:
            Dictionary mapping categories to strategy names
        """
        categories: Dict[str, List[str]] = {}

        for name, strategy_class in cls.STRATEGIES.items():
            # Create temporary instance to get category
            temp_config = {}
            temp_instance = strategy_class(temp_config)
            category = temp_instance._get_strategy_category()

            if category not in categories:
                categories[category] = []
            categories[category].append(name)

        return categories

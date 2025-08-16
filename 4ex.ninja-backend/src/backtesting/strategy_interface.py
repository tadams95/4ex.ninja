"""
Universal Strategy Interface for 4ex.ninja Backtesting Framework.

This module defines the abstract base class that ALL trading strategies must implement,
providing a standardized interface for the universal backtesting engine.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import pandas as pd

from .regime_detector import MarketRegime, RegimeDetectionResult


@dataclass
class TradeSignal:
    """Universal trade signal format for any strategy type."""

    pair: str
    direction: str  # "BUY" or "SELL"
    entry_price: float
    stop_loss: float
    take_profit: float
    signal_strength: float  # 0.0 to 1.0
    signal_time: datetime
    strategy_name: str
    regime_context: Optional[MarketRegime] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize metadata if not provided."""
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AccountInfo:
    """Account information for position sizing calculations."""

    balance: float
    equity: float
    margin_used: float
    free_margin: float
    max_position_size: float
    risk_per_trade: float = 0.02  # Default 2% risk per trade
    max_total_risk: float = 0.10  # Default 10% total portfolio risk


class BaseStrategy(ABC):
    """
    Universal interface that ANY swing trading strategy must implement.

    This abstract base class ensures all strategies can work seamlessly
    with the universal backtesting engine regardless of their internal logic.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize strategy with configuration.

        Args:
            config: Strategy-specific configuration dictionary
        """
        self.config = config
        self.strategy_name = self.__class__.__name__
        self._initialized = True

    @abstractmethod
    def generate_signals(
        self, data: pd.DataFrame, regime: Optional[MarketRegime] = None
    ) -> List[TradeSignal]:
        """
        Generate trade signals for ANY strategy type.

        This method must be implemented by each strategy to define how it
        generates trading signals based on market data and regime context.

        Args:
            data: OHLCV market data with any additional indicators
            regime: Current market regime context (optional)

        Returns:
            List of TradeSignal objects

        Examples:
            - MA strategies: crossover logic
            - RSI strategies: overbought/oversold
            - Bollinger: squeeze/expansion
            - ICT: smart money concepts
        """
        pass

    @abstractmethod
    def get_regime_parameters(self, regime: MarketRegime) -> Dict[str, Any]:
        """
        Get regime-specific parameter overrides for this strategy.

        Each strategy can adapt its parameters based on market regime
        to optimize performance in different market conditions.

        Args:
            regime: Current market regime

        Returns:
            Dictionary of parameter overrides for this regime
        """
        pass

    @abstractmethod
    def calculate_position_size(
        self, signal: TradeSignal, account_info: AccountInfo
    ) -> float:
        """
        Calculate position size for this specific strategy type.

        Each strategy can implement its own position sizing logic
        while respecting universal risk management constraints.

        Args:
            signal: Trade signal to calculate position size for
            account_info: Current account information

        Returns:
            Position size in base currency units
        """
        pass

    @abstractmethod
    def validate_signal(self, signal: TradeSignal, market_data: pd.DataFrame) -> bool:
        """
        Strategy-specific signal validation.

        Each strategy can implement custom validation logic to ensure
        signals are still valid at execution time.

        Args:
            signal: Trade signal to validate
            market_data: Current market data

        Returns:
            True if signal is valid, False otherwise
        """
        pass

    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get strategy metadata and information.

        Returns:
            Dictionary containing strategy information
        """
        return {
            "name": self.strategy_name,
            "config": self.config,
            "category": self._get_strategy_category(),
            "description": self._get_strategy_description(),
            "version": "1.0.0",
        }

    def _get_strategy_category(self) -> str:
        """
        Get strategy category for classification.

        Returns:
            Strategy category string
        """
        name = self.strategy_name.lower()
        if "ma" in name or "moving" in name:
            return "trend_following"
        elif "rsi" in name or "stoch" in name:
            return "momentum"
        elif "bollinger" in name or "envelope" in name:
            return "volatility"
        elif "ict" in name or "smart" in name:
            return "smart_money"
        else:
            return "other"

    def _get_strategy_description(self) -> str:
        """
        Get strategy description.

        Returns:
            Strategy description string
        """
        return f"{self.strategy_name} trading strategy"

    def get_validation_metrics(
        self, signals: List[TradeSignal], historical_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Get strategy-specific validation metrics.

        This method can be overridden by strategies to provide custom
        validation metrics for signal quality analysis.

        Args:
            signals: List of generated signals
            historical_data: Historical market data

        Returns:
            Dictionary of strategy-specific metrics
        """
        return {
            "total_signals": len(signals),
            "avg_signal_strength": (
                sum(s.signal_strength for s in signals) / len(signals) if signals else 0
            ),
            "signal_frequency": (
                len(signals) / len(historical_data) if len(historical_data) > 0 else 0
            ),
        }

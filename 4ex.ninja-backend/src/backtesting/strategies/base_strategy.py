"""
Base strategy implementation with common functionality.

This module provides a concrete base class that strategies can inherit from,
extending the abstract BaseStrategy interface with common utility methods.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime

from ..strategy_interface import BaseStrategy, TradeSignal, AccountInfo
from ..regime_detector import MarketRegime


class ConcreteBaseStrategy(BaseStrategy):
    """
    Concrete base strategy with common utility methods.

    This class provides default implementations for common functionality
    while maintaining the universal interface requirements.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize strategy with common parameters."""
        super().__init__(config)

        # Common parameters
        self.atr_period = config.get("atr_period", 14)
        self.sl_atr_multiplier = config.get("sl_atr_multiplier", 2.0)
        self.tp_atr_multiplier = config.get("tp_atr_multiplier", 3.0)
        self.min_atr_value = config.get("min_atr_value", 0.0001)
        self.min_rr_ratio = config.get("min_rr_ratio", 1.5)
        self.risk_per_trade = config.get("risk_per_trade", 0.02)

        # Regime-specific parameters
        self.regime_parameters = config.get("regime_parameters", {})

    def calculate_atr(self, data: pd.DataFrame) -> pd.Series:
        """Calculate Average True Range."""
        high = data["high"]
        low = data["low"]
        close = data["close"].shift(1)

        tr = pd.concat([high - low, abs(high - close), abs(low - close)], axis=1).max(
            axis=1
        )

        return tr.rolling(window=self.atr_period).mean()

    def calculate_position_size(
        self, signal: TradeSignal, account_info: AccountInfo
    ) -> float:
        """
        Universal position sizing based on ATR and risk per trade.

        This provides a default implementation that most strategies can use.
        Strategies can override this for custom position sizing logic.
        """
        # Calculate risk amount
        risk_amount = account_info.balance * self.risk_per_trade

        # Calculate stop loss distance in pips
        sl_distance = abs(signal.entry_price - signal.stop_loss)

        # Adjust for JPY pairs (different pip value)
        is_jpy_pair = "JPY" in signal.pair
        pip_size = 0.01 if is_jpy_pair else 0.0001
        sl_pips = sl_distance / pip_size

        # Calculate position size
        # For forex: risk_amount / (sl_pips * pip_value)
        # Simplified calculation assuming 1 pip = $1 for 10k units
        if sl_pips > 0:
            position_size = min(
                risk_amount / sl_pips * 1000,  # Simplified calculation
                account_info.max_position_size,
            )
        else:
            position_size = (
                account_info.max_position_size * 0.1
            )  # Conservative fallback

        return max(1000, position_size)  # Minimum position size

    def validate_signal(self, signal: TradeSignal, market_data: pd.DataFrame) -> bool:
        """
        Universal signal validation.

        Provides basic validation that most strategies can use.
        Strategies can override for additional validation logic.
        """
        try:
            # Check if signal has required fields
            if not all([signal.entry_price, signal.stop_loss, signal.take_profit]):
                return False

            # Check risk-reward ratio
            risk = abs(signal.entry_price - signal.stop_loss)
            reward = abs(signal.take_profit - signal.entry_price)

            if risk <= 0:
                return False

            rr_ratio = reward / risk
            if rr_ratio < self.min_rr_ratio:
                return False

            # Check ATR minimum (if available in signal metadata)
            if signal.metadata and "atr" in signal.metadata:
                atr = signal.metadata["atr"]
                if atr < self.min_atr_value:
                    return False

            return True

        except Exception as e:
            print(f"Error validating signal: {e}")
            return False

    def get_regime_parameters(self, regime: MarketRegime) -> Dict[str, Any]:
        """
        Get regime-specific parameter overrides.

        Returns parameters specific to the current market regime.
        Strategies should override this to provide regime-specific logic.
        """
        if regime in self.regime_parameters:
            return self.regime_parameters[regime]
        return {}

    def calculate_stop_loss_take_profit(
        self, entry_price: float, direction: str, atr_value: float
    ) -> tuple[float, float]:
        """
        Calculate stop loss and take profit based on ATR.

        Args:
            entry_price: Entry price for the trade
            direction: "BUY" or "SELL"
            atr_value: Current ATR value

        Returns:
            Tuple of (stop_loss, take_profit)
        """
        if direction == "BUY":
            stop_loss = entry_price - (atr_value * self.sl_atr_multiplier)
            take_profit = entry_price + (atr_value * self.tp_atr_multiplier)
        else:  # SELL
            stop_loss = entry_price + (atr_value * self.sl_atr_multiplier)
            take_profit = entry_price - (atr_value * self.tp_atr_multiplier)

        return stop_loss, take_profit

    def create_signal(
        self,
        pair: str,
        direction: str,
        entry_price: float,
        signal_time: datetime,
        atr_value: float,
        signal_strength: float = 1.0,
        regime: Optional[MarketRegime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TradeSignal:
        """
        Create a properly formatted trade signal.

        This utility method helps strategies create consistent signals.
        """
        stop_loss, take_profit = self.calculate_stop_loss_take_profit(
            entry_price, direction, atr_value
        )

        if metadata is None:
            metadata = {}

        metadata.update(
            {
                "atr": atr_value,
                "sl_atr_multiplier": self.sl_atr_multiplier,
                "tp_atr_multiplier": self.tp_atr_multiplier,
            }
        )

        return TradeSignal(
            pair=pair,
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            signal_strength=signal_strength,
            signal_time=signal_time,
            strategy_name=self.strategy_name,
            regime_context=regime,
            metadata=metadata,
        )

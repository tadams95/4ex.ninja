"""
RSI Strategy Implementation.

This strategy generates signals based on RSI overbought/oversold levels,
implementing the universal strategy interface for the backtesting framework.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime

from .base_strategy import ConcreteBaseStrategy
from ..strategy_interface import TradeSignal
from ..regime_detector import MarketRegime


class RSIStrategy(ConcreteBaseStrategy):
    """
    RSI momentum strategy implementation.

    This strategy generates SELL signals when RSI is overbought (>70)
    and BUY signals when RSI is oversold (<30).
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize RSI strategy with specific parameters.

        Expected config parameters:
        - rsi_period: RSI calculation period (default: 14)
        - overbought_level: RSI level for sell signals (default: 70)
        - oversold_level: RSI level for buy signals (default: 30)
        - min_rsi_strength: Minimum strength for RSI signals (default: 0.1)
        """
        super().__init__(config)

        # RSI-specific parameters
        self.rsi_period = config.get("rsi_period", 14)
        self.overbought_level = config.get("overbought_level", 70)
        self.oversold_level = config.get("oversold_level", 30)
        self.min_rsi_strength = config.get("min_rsi_strength", 0.1)

        # Regime-aware parameter adjustments
        self._setup_regime_parameters()

    def _setup_regime_parameters(self):
        """Setup default regime-specific parameters."""
        if not self.regime_parameters:
            self.regime_parameters = {
                MarketRegime.TRENDING_HIGH_VOL: {
                    "overbought_level": 80,  # More extreme levels in trending markets
                    "oversold_level": 20,
                    "min_rsi_strength": 0.2,
                },
                MarketRegime.TRENDING_LOW_VOL: {
                    "overbought_level": 75,
                    "oversold_level": 25,
                    "min_rsi_strength": 0.15,
                },
                MarketRegime.RANGING_HIGH_VOL: {
                    "overbought_level": self.overbought_level,  # Standard levels for ranging
                    "oversold_level": self.oversold_level,
                    "min_rsi_strength": 0.1,
                },
                MarketRegime.RANGING_LOW_VOL: {
                    "overbought_level": 65,  # More sensitive in low vol ranging
                    "oversold_level": 35,
                    "min_rsi_strength": 0.1,
                },
                MarketRegime.TRANSITION: {
                    "overbought_level": 80,  # Conservative during transitions
                    "oversold_level": 20,
                    "min_rsi_strength": 0.3,
                },
                MarketRegime.UNCERTAIN: {
                    "overbought_level": 85,  # Very conservative when uncertain
                    "oversold_level": 15,
                    "min_rsi_strength": 0.4,
                },
            }

    def generate_signals(
        self, data: pd.DataFrame, regime: Optional[MarketRegime] = None
    ) -> List[TradeSignal]:
        """
        Generate RSI signals.

        Args:
            data: OHLCV data with datetime index
            regime: Current market regime for parameter adjustment

        Returns:
            List of TradeSignal objects
        """
        try:
            # Get regime-adjusted parameters
            params = self._get_effective_parameters(regime)

            # Calculate RSI and ATR
            data_with_rsi = self._calculate_rsi(data)
            data_with_rsi["atr"] = self.calculate_atr(data_with_rsi)

            # Detect RSI signals
            signals = self._detect_rsi_signals(data_with_rsi, params, regime)

            return signals

        except Exception as e:
            print(f"Error generating RSI signals: {e}")
            return []

    def _get_effective_parameters(
        self, regime: Optional[MarketRegime]
    ) -> Dict[str, Any]:
        """Get effective parameters considering regime adjustments."""
        base_params = {
            "overbought_level": self.overbought_level,
            "oversold_level": self.oversold_level,
            "min_rsi_strength": self.min_rsi_strength,
        }

        if regime and regime in self.regime_parameters:
            regime_params = self.regime_parameters[regime]
            base_params.update(regime_params)

        return base_params

    def _calculate_rsi(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate RSI indicator."""
        df = data.copy()

        # Calculate price changes
        delta = df["close"].diff()

        # Separate gains and losses using apply to avoid typing issues
        gains = delta.apply(lambda x: x if x > 0 else 0.0)
        losses = delta.apply(lambda x: -x if x < 0 else 0.0)

        # Calculate average gains and losses
        avg_gains = gains.rolling(window=self.rsi_period).mean()
        avg_losses = losses.rolling(window=self.rsi_period).mean()

        # Calculate RSI, avoiding division by zero
        rs = avg_gains / (avg_losses + 1e-10)
        rsi = 100 - (100 / (1 + rs))

        df["rsi"] = rsi
        return df

    def _detect_rsi_signals(
        self, data: pd.DataFrame, params: Dict[str, Any], regime: Optional[MarketRegime]
    ) -> List[TradeSignal]:
        """Detect RSI overbought/oversold signals."""
        signals = []

        # Ensure we have enough data
        min_period = max(self.rsi_period, self.atr_period)
        if len(data) < min_period:
            return signals

        overbought = params["overbought_level"]
        oversold = params["oversold_level"]

        # Generate signals for each RSI condition
        for i in range(min_period, len(data)):
            try:
                row = data.iloc[i]

                if pd.isna(row["rsi"]) or pd.isna(row["atr"]) or row["atr"] == 0:
                    continue

                rsi_value = float(row["rsi"])

                signal_strength = self._calculate_signal_strength(data, i, params)

                if signal_strength < params["min_rsi_strength"]:
                    continue

                # RSI oversold - potential BUY signal
                if rsi_value <= oversold:
                    signal = self._create_buy_signal(data, i, signal_strength, regime)
                    if signal:
                        signals.append(signal)

                # RSI overbought - potential SELL signal
                elif rsi_value >= overbought:
                    signal = self._create_sell_signal(data, i, signal_strength, regime)
                    if signal:
                        signals.append(signal)

            except (IndexError, KeyError, ValueError):
                continue

        return signals

    def _calculate_signal_strength(
        self, data: pd.DataFrame, idx: int, params: Dict[str, Any]
    ) -> float:
        """
        Calculate signal strength based on RSI extremity and momentum.

        Returns value between 0.0 and 1.0.
        """
        try:
            row = data.iloc[idx]
            rsi_value = float(row["rsi"])
            overbought = params["overbought_level"]
            oversold = params["oversold_level"]

            # Calculate extremity score
            if rsi_value <= oversold:
                # More extreme = higher strength
                extremity_score = (oversold - rsi_value) / oversold
            elif rsi_value >= overbought:
                # More extreme = higher strength
                extremity_score = (rsi_value - overbought) / (100 - overbought)
            else:
                extremity_score = 0.0

            # Calculate RSI momentum (rate of change)
            momentum_score = 0.0
            lookback = 3
            if idx >= lookback:
                try:
                    rsi_change = abs(
                        float(data.iloc[idx]["rsi"])
                        - float(data.iloc[idx - lookback]["rsi"])
                    )
                    momentum_score = min(rsi_change / 20.0, 1.0)  # Normalize to 0-1
                except (ValueError, KeyError, IndexError):
                    momentum_score = 0.0

            # Combine factors
            strength = (extremity_score * 0.7) + (momentum_score * 0.3)

            return max(0.0, min(1.0, strength))

        except (ValueError, KeyError, IndexError, TypeError):
            return 0.0

    def _create_buy_signal(
        self,
        data: pd.DataFrame,
        idx: int,
        signal_strength: float,
        regime: Optional[MarketRegime],
    ) -> Optional[TradeSignal]:
        """Create a BUY signal."""
        try:
            row = data.iloc[idx]
            entry_price = float(row["close"])
            atr_value = float(row["atr"])
            rsi_value = float(row["rsi"])

            # Get timestamp
            if hasattr(data.index, "to_pydatetime"):
                signal_time = data.index[idx].to_pydatetime()
            elif isinstance(data.index[idx], datetime):
                signal_time = data.index[idx]
            else:
                signal_time = datetime.now()

            # Extract pair from data if available, otherwise use default
            pair = getattr(data, "pair", "UNKNOWN")

            metadata = {
                "rsi": rsi_value,
                "rsi_period": self.rsi_period,
                "signal_type": "oversold",
            }

            return self.create_signal(
                pair=pair,
                direction="BUY",
                entry_price=entry_price,
                signal_time=signal_time,
                atr_value=atr_value,
                signal_strength=signal_strength,
                regime=regime,
                metadata=metadata,
            )

        except Exception as e:
            print(f"Error creating BUY signal: {e}")
            return None

    def _create_sell_signal(
        self,
        data: pd.DataFrame,
        idx: int,
        signal_strength: float,
        regime: Optional[MarketRegime],
    ) -> Optional[TradeSignal]:
        """Create a SELL signal."""
        try:
            row = data.iloc[idx]
            entry_price = float(row["close"])
            atr_value = float(row["atr"])
            rsi_value = float(row["rsi"])

            # Get timestamp
            if hasattr(data.index, "to_pydatetime"):
                signal_time = data.index[idx].to_pydatetime()
            elif isinstance(data.index[idx], datetime):
                signal_time = data.index[idx]
            else:
                signal_time = datetime.now()

            # Extract pair from data if available, otherwise use default
            pair = getattr(data, "pair", "UNKNOWN")

            metadata = {
                "rsi": rsi_value,
                "rsi_period": self.rsi_period,
                "signal_type": "overbought",
            }

            return self.create_signal(
                pair=pair,
                direction="SELL",
                entry_price=entry_price,
                signal_time=signal_time,
                atr_value=atr_value,
                signal_strength=signal_strength,
                regime=regime,
                metadata=metadata,
            )

        except Exception as e:
            print(f"Error creating SELL signal: {e}")
            return None

    def get_regime_parameters(self, regime: MarketRegime) -> Dict[str, Any]:
        """Get regime-specific RSI parameters."""
        return self.regime_parameters.get(regime, {})

    def validate_signal(self, signal: TradeSignal, market_data: pd.DataFrame) -> bool:
        """
        RSI-specific signal validation.

        Adds validation for RSI signal quality.
        """
        # First run base validation
        if not super().validate_signal(signal, market_data):
            return False

        # RSI-specific validation
        try:
            if signal.metadata:
                rsi_value = signal.metadata.get("rsi", 50)
                signal_type = signal.metadata.get("signal_type", "")

                # Check that RSI values align with signal direction
                if signal.direction == "BUY" and signal_type != "oversold":
                    return False
                elif signal.direction == "SELL" and signal_type != "overbought":
                    return False

                # Check RSI is in valid range
                if not (0 <= rsi_value <= 100):
                    return False

            return True

        except Exception:
            return False

    def get_validation_metrics(
        self, signals: List[TradeSignal], historical_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Get RSI strategy-specific validation metrics."""
        base_metrics = super().get_validation_metrics(signals, historical_data)

        # Add RSI-specific metrics
        rsi_metrics = {
            "avg_rsi_level": 0.0,
            "oversold_signals": 0,
            "overbought_signals": 0,
            "avg_rsi_extremity": 0.0,
        }

        if signals:
            rsi_values = []
            oversold_count = 0
            overbought_count = 0

            for signal in signals:
                if signal.metadata and "rsi" in signal.metadata:
                    rsi = signal.metadata["rsi"]
                    rsi_values.append(rsi)

                    if signal.metadata.get("signal_type") == "oversold":
                        oversold_count += 1
                    elif signal.metadata.get("signal_type") == "overbought":
                        overbought_count += 1

            if rsi_values:
                rsi_metrics.update(
                    {
                        "avg_rsi_level": sum(rsi_values) / len(rsi_values),
                        "oversold_signals": oversold_count,
                        "overbought_signals": overbought_count,
                        "signal_bias": (oversold_count - overbought_count)
                        / len(signals),
                    }
                )

        base_metrics.update(rsi_metrics)
        return base_metrics

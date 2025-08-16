"""
Moving Average Crossover Strategy Implementation.

This strategy generates signals based on moving average crossovers,
implementing the universal strategy interface for the backtesting framework.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime

from .base_strategy import ConcreteBaseStrategy
from ..strategy_interface import TradeSignal
from ..regime_detector import MarketRegime


class MAStrategy(ConcreteBaseStrategy):
    """
    Moving Average crossover strategy implementation.

    This strategy generates BUY signals when fast MA crosses above slow MA
    and SELL signals when fast MA crosses below slow MA.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize MA strategy with specific parameters.

        Expected config parameters:
        - fast_ma: Fast moving average period (default: 10)
        - slow_ma: Slow moving average period (default: 20)
        - ma_type: Type of MA ('SMA', 'EMA') (default: 'SMA')
        - min_crossover_strength: Minimum strength for crossover (default: 0.0)
        """
        super().__init__(config)

        # MA-specific parameters
        self.fast_ma = config.get("fast_ma", 10)
        self.slow_ma = config.get("slow_ma", 20)
        self.ma_type = config.get("ma_type", "SMA")
        self.min_crossover_strength = config.get("min_crossover_strength", 0.0)

        # Regime-aware parameter adjustments
        self._setup_regime_parameters()

    def _setup_regime_parameters(self):
        """Setup default regime-specific parameters."""
        if not self.regime_parameters:
            self.regime_parameters = {
                MarketRegime.TRENDING_HIGH_VOL: {
                    "fast_ma": self.fast_ma,
                    "slow_ma": self.slow_ma,
                    "min_crossover_strength": 0.1,
                },
                MarketRegime.TRENDING_LOW_VOL: {
                    "fast_ma": self.fast_ma,
                    "slow_ma": self.slow_ma,
                    "min_crossover_strength": 0.2,
                },
                MarketRegime.RANGING_HIGH_VOL: {
                    "fast_ma": max(5, self.fast_ma - 5),
                    "slow_ma": min(30, self.slow_ma + 10),
                    "min_crossover_strength": 0.3,
                },
                MarketRegime.RANGING_LOW_VOL: {
                    "fast_ma": max(5, self.fast_ma - 2),
                    "slow_ma": self.slow_ma,
                    "min_crossover_strength": 0.2,
                },
                MarketRegime.TRANSITION: {
                    "fast_ma": self.fast_ma + 2,
                    "slow_ma": self.slow_ma + 5,
                    "min_crossover_strength": 0.4,
                },
                MarketRegime.UNCERTAIN: {
                    "fast_ma": self.fast_ma + 2,
                    "slow_ma": self.slow_ma + 5,
                    "min_crossover_strength": 0.5,
                },
            }

    def generate_signals(
        self, data: pd.DataFrame, regime: Optional[MarketRegime] = None
    ) -> List[TradeSignal]:
        """
        Generate MA crossover signals.

        Args:
            data: OHLCV data with datetime index
            regime: Current market regime for parameter adjustment

        Returns:
            List of TradeSignal objects
        """
        try:
            # Get regime-adjusted parameters
            params = self._get_effective_parameters(regime)

            # Calculate moving averages
            data_with_ma = self._calculate_moving_averages(data, params)

            # Calculate ATR for stop loss/take profit
            data_with_ma["atr"] = self.calculate_atr(data_with_ma)

            # Detect crossovers
            signals = self._detect_crossovers(data_with_ma, params, regime)

            return signals

        except Exception as e:
            print(f"Error generating MA signals: {e}")
            return []

    def _get_effective_parameters(
        self, regime: Optional[MarketRegime]
    ) -> Dict[str, Any]:
        """Get effective parameters considering regime adjustments."""
        base_params = {
            "fast_ma": self.fast_ma,
            "slow_ma": self.slow_ma,
            "min_crossover_strength": self.min_crossover_strength,
        }

        if regime and regime in self.regime_parameters:
            regime_params = self.regime_parameters[regime]
            base_params.update(regime_params)

        return base_params

    def _calculate_moving_averages(
        self, data: pd.DataFrame, params: Dict[str, Any]
    ) -> pd.DataFrame:
        """Calculate moving averages based on type and parameters."""
        df = data.copy()

        fast_period = params["fast_ma"]
        slow_period = params["slow_ma"]

        if self.ma_type == "EMA":
            df["fast_ma"] = df["close"].ewm(span=fast_period).mean()
            df["slow_ma"] = df["close"].ewm(span=slow_period).mean()
        else:  # SMA
            df["fast_ma"] = df["close"].rolling(window=fast_period).mean()
            df["slow_ma"] = df["close"].rolling(window=slow_period).mean()

        return df

    def _detect_crossovers(
        self, data: pd.DataFrame, params: Dict[str, Any], regime: Optional[MarketRegime]
    ) -> List[TradeSignal]:
        """Detect MA crossovers and generate signals."""
        signals = []

        # Ensure we have enough data
        min_period = max(params["fast_ma"], params["slow_ma"], self.atr_period)
        if len(data) < min_period:
            return signals

        # Calculate crossover conditions
        fast_ma = data["fast_ma"]
        slow_ma = data["slow_ma"]

        # Bullish crossover: fast MA crosses above slow MA
        bullish_crossover = (fast_ma > slow_ma) & (fast_ma.shift(1) <= slow_ma.shift(1))

        # Bearish crossover: fast MA crosses below slow MA
        bearish_crossover = (fast_ma < slow_ma) & (fast_ma.shift(1) >= slow_ma.shift(1))

        # Generate signals for each crossover
        for i in range(min_period, len(data)):
            try:
                if pd.isna(data.iloc[i]["atr"]) or data.iloc[i]["atr"] == 0:
                    continue

                signal_strength = self._calculate_signal_strength(data, i, params)

                if signal_strength < params["min_crossover_strength"]:
                    continue

                if bullish_crossover.iloc[i]:
                    signal = self._create_buy_signal(data, i, signal_strength, regime)
                    if signal:
                        signals.append(signal)

                elif bearish_crossover.iloc[i]:
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
        Calculate signal strength based on MA separation and momentum.

        Returns value between 0.0 and 1.0.
        """
        try:
            row = data.iloc[idx]
            fast_ma = float(row["fast_ma"])
            slow_ma = float(row["slow_ma"])
            atr = float(row["atr"])

            # Calculate MA separation as percentage of ATR
            if atr > 0:
                ma_separation = abs(fast_ma - slow_ma) / atr
            else:
                ma_separation = 0.0

            # Calculate momentum (rate of change in fast MA)
            lookback = 3
            fast_ma_momentum = 0.0
            if idx >= lookback:
                if atr > 0:
                    fast_ma_momentum = (
                        abs(
                            float(data.iloc[idx]["fast_ma"])
                            - float(data.iloc[idx - lookback]["fast_ma"])
                        )
                        / atr
                    )

            # Combine factors (normalized to 0-1)
            separation_score = min(ma_separation / 2.0, 1.0)  # Normalize
            momentum_score = min(fast_ma_momentum, 1.0)  # Normalize

            # Weighted combination
            strength = (separation_score * 0.6) + (momentum_score * 0.4)

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
                "fast_ma": float(row["fast_ma"]),
                "slow_ma": float(row["slow_ma"]),
                "ma_type": self.ma_type,
                "crossover_type": "bullish",
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
                "fast_ma": float(row["fast_ma"]),
                "slow_ma": float(row["slow_ma"]),
                "ma_type": self.ma_type,
                "crossover_type": "bearish",
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
        """Get regime-specific MA parameters."""
        return self.regime_parameters.get(regime, {})

    def validate_signal(self, signal: TradeSignal, market_data: pd.DataFrame) -> bool:
        """
        MA-specific signal validation.

        Adds validation for MA crossover quality.
        """
        # First run base validation
        if not super().validate_signal(signal, market_data):
            return False

        # MA-specific validation
        try:
            if signal.metadata:
                fast_ma = signal.metadata.get("fast_ma", 0)
                slow_ma = signal.metadata.get("slow_ma", 0)

                # Check that MAs are properly separated
                if signal.direction == "BUY" and fast_ma <= slow_ma:
                    return False
                elif signal.direction == "SELL" and fast_ma >= slow_ma:
                    return False

            return True

        except Exception:
            return False

    def get_validation_metrics(
        self, signals: List[TradeSignal], historical_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Get MA strategy-specific validation metrics."""
        base_metrics = super().get_validation_metrics(signals, historical_data)

        # Add MA-specific metrics
        ma_metrics = {
            "avg_ma_separation": 0.0,
            "bullish_signals": 0,
            "bearish_signals": 0,
            "avg_crossover_strength": 0.0,
        }

        if signals:
            bullish_count = sum(1 for s in signals if s.direction == "BUY")
            bearish_count = sum(1 for s in signals if s.direction == "SELL")

            ma_metrics.update(
                {
                    "bullish_signals": bullish_count,
                    "bearish_signals": bearish_count,
                    "signal_bias": (bullish_count - bearish_count) / len(signals),
                }
            )

        base_metrics.update(ma_metrics)
        return base_metrics

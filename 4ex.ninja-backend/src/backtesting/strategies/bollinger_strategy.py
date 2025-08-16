"""
Bollinger Bands Strategy Implementation.

This strategy generates signals based on Bollinger Band breakouts and reversals,
implementing the universal strategy interface for the backtesting framework.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime

from .base_strategy import ConcreteBaseStrategy
from ..strategy_interface import TradeSignal
from ..regime_detector import MarketRegime


class BollingerStrategy(ConcreteBaseStrategy):
    """
    Bollinger Bands strategy implementation.

    This strategy generates signals based on:
    - Band breakouts (momentum)
    - Band reversals (mean reversion)
    - Band squeeze patterns
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Bollinger strategy with specific parameters.

        Expected config parameters:
        - bb_period: Bollinger Band period (default: 20)
        - bb_std: Standard deviation multiplier (default: 2.0)
        - signal_mode: 'breakout' or 'reversal' (default: 'reversal')
        - min_squeeze_bars: Minimum bars for squeeze detection (default: 5)
        - min_band_width: Minimum band width for valid signals (default: 0.001)
        """
        super().__init__(config)

        # Bollinger-specific parameters
        self.bb_period = config.get("bb_period", 20)
        self.bb_std = config.get("bb_std", 2.0)
        self.signal_mode = config.get(
            "signal_mode", "reversal"
        )  # 'breakout' or 'reversal'
        self.min_squeeze_bars = config.get("min_squeeze_bars", 5)
        self.min_band_width = config.get("min_band_width", 0.001)

        # Regime-aware parameter adjustments
        self._setup_regime_parameters()

    def _setup_regime_parameters(self):
        """Setup default regime-specific parameters."""
        if not self.regime_parameters:
            self.regime_parameters = {
                MarketRegime.TRENDING_HIGH_VOL: {
                    "bb_std": 2.5,  # Wider bands in high volatility
                    "signal_mode": "breakout",  # Trend following in trending markets
                    "min_band_width": 0.002,
                },
                MarketRegime.TRENDING_LOW_VOL: {
                    "bb_std": 2.0,
                    "signal_mode": "breakout",
                    "min_band_width": 0.001,
                },
                MarketRegime.RANGING_HIGH_VOL: {
                    "bb_std": self.bb_std,
                    "signal_mode": "reversal",  # Mean reversion in ranging markets
                    "min_band_width": 0.0015,
                },
                MarketRegime.RANGING_LOW_VOL: {
                    "bb_std": 1.5,  # Tighter bands in low volatility
                    "signal_mode": "reversal",
                    "min_band_width": 0.0005,
                },
                MarketRegime.TRANSITION: {
                    "bb_std": 2.5,  # Conservative during transitions
                    "signal_mode": "reversal",
                    "min_band_width": 0.002,
                },
                MarketRegime.UNCERTAIN: {
                    "bb_std": 3.0,  # Very wide bands when uncertain
                    "signal_mode": "reversal",
                    "min_band_width": 0.003,
                },
            }

    def generate_signals(
        self, data: pd.DataFrame, regime: Optional[MarketRegime] = None
    ) -> List[TradeSignal]:
        """
        Generate Bollinger Band signals.

        Args:
            data: OHLCV data with datetime index
            regime: Current market regime for parameter adjustment

        Returns:
            List of TradeSignal objects
        """
        try:
            # Get regime-adjusted parameters
            params = self._get_effective_parameters(regime)

            # Calculate Bollinger Bands and ATR
            data_with_bb = self._calculate_bollinger_bands(data, params)
            data_with_bb["atr"] = self.calculate_atr(data_with_bb)

            # Detect signals based on mode
            if params["signal_mode"] == "breakout":
                signals = self._detect_breakout_signals(data_with_bb, params, regime)
            else:  # reversal
                signals = self._detect_reversal_signals(data_with_bb, params, regime)

            return signals

        except Exception as e:
            print(f"Error generating Bollinger Band signals: {e}")
            return []

    def _get_effective_parameters(
        self, regime: Optional[MarketRegime]
    ) -> Dict[str, Any]:
        """Get effective parameters considering regime adjustments."""
        base_params = {
            "bb_std": self.bb_std,
            "signal_mode": self.signal_mode,
            "min_band_width": self.min_band_width,
        }

        if regime and regime in self.regime_parameters:
            regime_params = self.regime_parameters[regime]
            base_params.update(regime_params)

        return base_params

    def _calculate_bollinger_bands(
        self, data: pd.DataFrame, params: Dict[str, Any]
    ) -> pd.DataFrame:
        """Calculate Bollinger Bands."""
        df = data.copy()

        # Calculate moving average (middle band)
        df["bb_middle"] = df["close"].rolling(window=self.bb_period).mean()

        # Calculate standard deviation
        std = df["close"].rolling(window=self.bb_period).std()

        # Calculate upper and lower bands
        bb_std_multiplier = params["bb_std"]
        df["bb_upper"] = df["bb_middle"] + (std * bb_std_multiplier)
        df["bb_lower"] = df["bb_middle"] - (std * bb_std_multiplier)

        # Calculate band width (for squeeze detection)
        df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_middle"]

        # Calculate %B (position within bands)
        df["bb_percent"] = (df["close"] - df["bb_lower"]) / (
            df["bb_upper"] - df["bb_lower"]
        )

        return df

    def _detect_breakout_signals(
        self, data: pd.DataFrame, params: Dict[str, Any], regime: Optional[MarketRegime]
    ) -> List[TradeSignal]:
        """Detect Bollinger Band breakout signals."""
        signals = []

        # Ensure we have enough data
        min_period = max(self.bb_period, self.atr_period)
        if len(data) < min_period:
            return signals

        # Generate signals for breakouts
        for i in range(min_period, len(data)):
            try:
                row = data.iloc[i]
                prev_row = data.iloc[i - 1]

                if pd.isna(row["bb_width"]) or pd.isna(row["atr"]) or row["atr"] == 0:
                    continue

                # Check minimum band width
                if float(row["bb_width"]) < params["min_band_width"]:
                    continue

                close = float(row["close"])
                prev_close = float(prev_row["close"])
                bb_upper = float(row["bb_upper"])
                bb_lower = float(row["bb_lower"])
                prev_bb_upper = float(prev_row["bb_upper"])
                prev_bb_lower = float(prev_row["bb_lower"])

                signal_strength = self._calculate_signal_strength(data, i, params)

                # Upper band breakout - BUY signal
                if close > bb_upper and prev_close <= prev_bb_upper:
                    signal = self._create_buy_signal(
                        data, i, signal_strength, regime, "breakout"
                    )
                    if signal:
                        signals.append(signal)

                # Lower band breakout - SELL signal
                elif close < bb_lower and prev_close >= prev_bb_lower:
                    signal = self._create_sell_signal(
                        data, i, signal_strength, regime, "breakout"
                    )
                    if signal:
                        signals.append(signal)

            except (IndexError, KeyError, ValueError):
                continue

        return signals

    def _detect_reversal_signals(
        self, data: pd.DataFrame, params: Dict[str, Any], regime: Optional[MarketRegime]
    ) -> List[TradeSignal]:
        """Detect Bollinger Band reversal signals."""
        signals = []

        # Ensure we have enough data
        min_period = max(self.bb_period, self.atr_period)
        if len(data) < min_period:
            return signals

        # Generate signals for reversals
        for i in range(min_period, len(data)):
            try:
                row = data.iloc[i]

                if pd.isna(row["bb_percent"]) or pd.isna(row["atr"]) or row["atr"] == 0:
                    continue

                # Check minimum band width
                if float(row["bb_width"]) < params["min_band_width"]:
                    continue

                bb_percent = float(row["bb_percent"])
                signal_strength = self._calculate_signal_strength(data, i, params)

                # Oversold reversal - BUY signal (price near lower band)
                if bb_percent <= 0.1:  # Very close to lower band
                    signal = self._create_buy_signal(
                        data, i, signal_strength, regime, "reversal"
                    )
                    if signal:
                        signals.append(signal)

                # Overbought reversal - SELL signal (price near upper band)
                elif bb_percent >= 0.9:  # Very close to upper band
                    signal = self._create_sell_signal(
                        data, i, signal_strength, regime, "reversal"
                    )
                    if signal:
                        signals.append(signal)

            except (IndexError, KeyError, ValueError):
                continue

        return signals

    def _calculate_signal_strength(
        self, data: pd.DataFrame, idx: int, params: Dict[str, Any]
    ) -> float:
        """
        Calculate signal strength based on band width and position.

        Returns value between 0.0 and 1.0.
        """
        try:
            row = data.iloc[idx]
            bb_width = float(row["bb_width"])
            bb_percent = float(row["bb_percent"])

            # Band width score (wider bands = stronger signals)
            width_score = min(bb_width / 0.05, 1.0)  # Normalize to 0-1

            # Position score (more extreme = stronger)
            if params["signal_mode"] == "breakout":
                # For breakouts, extreme positions are stronger
                position_score = max(abs(bb_percent - 0.5) * 2, 0.0)
            else:  # reversal
                # For reversals, very extreme positions are stronger
                if bb_percent <= 0.1:
                    position_score = (0.1 - bb_percent) * 10  # 0-1 scale
                elif bb_percent >= 0.9:
                    position_score = (bb_percent - 0.9) * 10  # 0-1 scale
                else:
                    position_score = 0.0

            # Check for squeeze (low band width followed by expansion)
            squeeze_score = 0.0
            if idx >= self.min_squeeze_bars:
                try:
                    recent_widths = [
                        float(data.iloc[idx - j]["bb_width"])
                        for j in range(self.min_squeeze_bars)
                    ]
                    if all(
                        w < params["min_band_width"] * 1.5 for w in recent_widths[1:]
                    ):
                        squeeze_score = 0.3  # Bonus for post-squeeze breakout
                except (ValueError, KeyError, IndexError):
                    squeeze_score = 0.0

            # Combine factors
            strength = (
                (width_score * 0.4) + (position_score * 0.4) + (squeeze_score * 0.2)
            )

            return max(0.0, min(1.0, strength))

        except (ValueError, KeyError, IndexError, TypeError):
            return 0.0

    def _create_buy_signal(
        self,
        data: pd.DataFrame,
        idx: int,
        signal_strength: float,
        regime: Optional[MarketRegime],
        signal_type: str,
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
                "bb_upper": float(row["bb_upper"]),
                "bb_middle": float(row["bb_middle"]),
                "bb_lower": float(row["bb_lower"]),
                "bb_percent": float(row["bb_percent"]),
                "bb_width": float(row["bb_width"]),
                "signal_type": signal_type,
                "bb_period": self.bb_period,
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
        signal_type: str,
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
                "bb_upper": float(row["bb_upper"]),
                "bb_middle": float(row["bb_middle"]),
                "bb_lower": float(row["bb_lower"]),
                "bb_percent": float(row["bb_percent"]),
                "bb_width": float(row["bb_width"]),
                "signal_type": signal_type,
                "bb_period": self.bb_period,
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
        """Get regime-specific Bollinger parameters."""
        return self.regime_parameters.get(regime, {})

    def validate_signal(self, signal: TradeSignal, market_data: pd.DataFrame) -> bool:
        """
        Bollinger-specific signal validation.

        Adds validation for Bollinger signal quality.
        """
        # First run base validation
        if not super().validate_signal(signal, market_data):
            return False

        # Bollinger-specific validation
        try:
            if signal.metadata:
                bb_percent = signal.metadata.get("bb_percent", 0.5)
                bb_width = signal.metadata.get("bb_width", 0)
                signal_type = signal.metadata.get("signal_type", "")

                # Check band width is sufficient
                if bb_width < self.min_band_width:
                    return False

                # Check signal consistency
                if signal_type == "breakout":
                    if signal.direction == "BUY" and bb_percent < 0.9:
                        return False
                    elif signal.direction == "SELL" and bb_percent > 0.1:
                        return False
                elif signal_type == "reversal":
                    if signal.direction == "BUY" and bb_percent > 0.2:
                        return False
                    elif signal.direction == "SELL" and bb_percent < 0.8:
                        return False

            return True

        except Exception:
            return False

    def get_validation_metrics(
        self, signals: List[TradeSignal], historical_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Get Bollinger strategy-specific validation metrics."""
        base_metrics = super().get_validation_metrics(signals, historical_data)

        # Add Bollinger-specific metrics
        bb_metrics = {
            "avg_band_width": 0.0,
            "breakout_signals": 0,
            "reversal_signals": 0,
            "avg_bb_percent": 0.0,
        }

        if signals:
            band_widths = []
            bb_percents = []
            breakout_count = 0
            reversal_count = 0

            for signal in signals:
                if signal.metadata:
                    if "bb_width" in signal.metadata:
                        band_widths.append(signal.metadata["bb_width"])
                    if "bb_percent" in signal.metadata:
                        bb_percents.append(signal.metadata["bb_percent"])

                    signal_type = signal.metadata.get("signal_type", "")
                    if signal_type == "breakout":
                        breakout_count += 1
                    elif signal_type == "reversal":
                        reversal_count += 1

            if band_widths:
                bb_metrics["avg_band_width"] = sum(band_widths) / len(band_widths)
            if bb_percents:
                bb_metrics["avg_bb_percent"] = sum(bb_percents) / len(bb_percents)

            bb_metrics.update(
                {"breakout_signals": breakout_count, "reversal_signals": reversal_count}
            )

        base_metrics.update(bb_metrics)
        return base_metrics

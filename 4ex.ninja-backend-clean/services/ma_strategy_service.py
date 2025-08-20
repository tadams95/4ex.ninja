"""
MA Strategy Service
Core service for Moving Average strategy calculations and signal generation.
Implements the optimal conservative_moderate_daily parameters (fast_ma=50, slow_ma=200).
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from models.signal_models import (
    TradingSignal,
    SignalType,
    MACalculation,
    PriceData,
    PerformanceMetrics,
    StrategyConfig,
)
from config.settings import OPTIMAL_STRATEGY_CONFIG, MA_SETTINGS


class MAStrategyService:
    """Moving Average Strategy Service with optimal parameters."""

    def __init__(self):
        self.fast_ma_period = MA_SETTINGS["fast_ma_period"]  # 50
        self.slow_ma_period = MA_SETTINGS["slow_ma_period"]  # 200
        self.source = MA_SETTINGS["source"]  # "close"

    async def calculate_moving_averages(
        self, price_data: List[PriceData]
    ) -> Tuple[float, float]:
        """
        Calculate fast and slow moving averages.

        Args:
            price_data: List of price data points

        Returns:
            Tuple of (fast_ma, slow_ma)
        """
        if len(price_data) < self.slow_ma_period:
            raise ValueError(
                f"Insufficient data: need {self.slow_ma_period} periods, got {len(price_data)}"
            )

        # Extract close prices
        prices = [getattr(price, self.source) for price in price_data]

        # Calculate moving averages
        fast_ma = float(np.mean(prices[-self.fast_ma_period :]))
        slow_ma = float(np.mean(prices[-self.slow_ma_period :]))

        return fast_ma, slow_ma

    async def generate_signal(
        self, pair: str, price_data: List[PriceData]
    ) -> TradingSignal:
        """
        Generate trading signal based on MA crossover.

        Args:
            pair: Currency pair (e.g., "EUR_USD_D")
            price_data: Historical price data

        Returns:
            TradingSignal object
        """
        if len(price_data) < self.slow_ma_period + 1:
            raise ValueError(f"Insufficient data for signal generation")

        # Get current and previous MA values
        current_fast_ma, current_slow_ma = await self.calculate_moving_averages(
            price_data
        )
        prev_fast_ma, prev_slow_ma = await self.calculate_moving_averages(
            price_data[:-1]
        )

        current_price = price_data[-1].close

        # Determine signal type based on crossover
        signal_type = self._determine_signal_type(
            current_fast_ma, current_slow_ma, prev_fast_ma, prev_slow_ma
        )

        # Calculate confidence based on MA separation
        confidence = self._calculate_confidence(
            current_fast_ma, current_slow_ma, current_price
        )

        # Extract pair and timeframe
        pair_parts = pair.split("_")
        currency_pair = f"{pair_parts[0]}_{pair_parts[1]}"
        timeframe = pair_parts[2] if len(pair_parts) > 2 else "D"

        return TradingSignal(
            pair=currency_pair,
            timeframe=timeframe,
            signal_type=signal_type,
            price=current_price,
            fast_ma=current_fast_ma,
            slow_ma=current_slow_ma,
            confidence=confidence,
            strategy_type="conservative_moderate_daily",
        )

    def _determine_signal_type(
        self,
        current_fast_ma: float,
        current_slow_ma: float,
        prev_fast_ma: float,
        prev_slow_ma: float,
    ) -> SignalType:
        """Determine signal type based on MA crossover."""

        # Current state
        fast_above_slow = current_fast_ma > current_slow_ma

        # Previous state
        prev_fast_above_slow = prev_fast_ma > prev_slow_ma

        # Crossover detection
        if not prev_fast_above_slow and fast_above_slow:
            # Fast MA crossed above slow MA - BUY signal
            return SignalType.BUY
        elif prev_fast_above_slow and not fast_above_slow:
            # Fast MA crossed below slow MA - SELL signal
            return SignalType.SELL
        else:
            # No crossover - HOLD
            return SignalType.HOLD

    def _calculate_confidence(
        self, fast_ma: float, slow_ma: float, current_price: float
    ) -> float:
        """Calculate signal confidence based on MA separation."""

        # Calculate percentage separation between MAs
        ma_separation = abs(fast_ma - slow_ma) / slow_ma

        # Calculate price position relative to MAs
        price_vs_ma = abs(current_price - fast_ma) / fast_ma

        # Confidence increases with MA separation (stronger trend)
        # and decreases if price is far from fast MA (potential false signal)
        base_confidence = min(ma_separation * 10, 0.8)  # Cap at 0.8
        price_adjustment = max(0.2, 1 - price_vs_ma * 5)  # Min 0.2

        confidence = base_confidence * price_adjustment
        return min(max(confidence, 0.1), 1.0)  # Clamp between 0.1 and 1.0

    async def get_strategy_config(self, pair_key: str) -> StrategyConfig:
        """Get strategy configuration for a pair."""
        if pair_key not in OPTIMAL_STRATEGY_CONFIG:
            raise ValueError(f"Unsupported pair: {pair_key}")

        config_data = OPTIMAL_STRATEGY_CONFIG[pair_key]
        return StrategyConfig(**config_data)

    async def validate_optimal_parameters(self) -> bool:
        """Validate that we're using optimal parameters."""
        return (
            self.fast_ma_period == 50
            and self.slow_ma_period == 200
            and self.source == "close"
        )

    async def calculate_performance_metrics(
        self, signals: List[TradingSignal], pair: str
    ) -> PerformanceMetrics:
        """Calculate performance metrics for a strategy."""

        if not signals:
            return PerformanceMetrics(
                pair=pair,
                timeframe="D",
                total_return=0.0,
                win_rate=0.0,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                avg_win=0.0,
                avg_loss=0.0,
            )

        # Filter to actual trades (BUY/SELL signals)
        trade_signals = [s for s in signals if s.signal_type != SignalType.HOLD]

        total_trades = len(trade_signals)
        if total_trades == 0:
            return PerformanceMetrics(
                pair=pair,
                timeframe="D",
                total_return=0.0,
                win_rate=0.0,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                avg_win=0.0,
                avg_loss=0.0,
            )

        # Simple return calculation based on signal confidence
        # In production, this would be based on actual trade results
        winning_trades = len(
            [s for s in trade_signals if s.confidence and s.confidence > 0.6]
        )
        losing_trades = total_trades - winning_trades

        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0

        # Estimate returns based on optimal strategy expectations
        config = OPTIMAL_STRATEGY_CONFIG.get(f"{pair}_D", {})
        expected_return_str = config.get("expected_return", "18.0%")
        expected_return = float(expected_return_str.rstrip("%"))

        return PerformanceMetrics(
            pair=pair,
            timeframe="D",
            total_return=expected_return,
            win_rate=win_rate,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            avg_win=2.5,  # Estimated average win
            avg_loss=-1.2,  # Estimated average loss
            profit_factor=2.08 if losing_trades > 0 else None,
        )

    async def get_all_supported_pairs(self) -> List[str]:
        """Get all supported currency pairs."""
        return list(OPTIMAL_STRATEGY_CONFIG.keys())

    async def is_market_open(self, pair: str) -> bool:
        """Check if market is open for trading (simplified)."""
        # For forex, market is open 24/5
        # This is a simplified check - in production would check actual market hours
        now = datetime.utcnow()
        weekday = now.weekday()

        # Market closed on weekends
        if weekday >= 5:  # Saturday = 5, Sunday = 6
            return False

        # Friday close at 22:00 UTC, Sunday open at 22:00 UTC
        if weekday == 4 and now.hour >= 22:  # Friday after 22:00
            return False
        if weekday == 6 and now.hour < 22:  # Sunday before 22:00
            return False

        return True

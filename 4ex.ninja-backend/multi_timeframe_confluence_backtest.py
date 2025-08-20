#!/usr/bin/env python3
"""
Multi-Timeframe Confluence Backtest for 4ex.ninja
Combines Weekly trend + Daily setup + H4 execution for superior performance
"""
import asyncio
import json
import os
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class LocalPriceData:
    """Local price data structure matching our JSON format"""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass
class TimeframeAnalysis:
    """Analysis result for a specific timeframe"""

    timeframe: str
    trend_direction: str  # 'bullish', 'bearish', 'neutral'
    signal_strength: float  # 0.0 to 1.0
    ema_fast: float
    ema_slow: float
    rsi: float
    adx: float
    tradeable: bool


@dataclass
class ConfluenceSignal:
    """Multi-timeframe confluence signal"""

    pair: str
    timestamp: datetime
    signal_type: SignalType
    confluence_score: float  # 0.0 to 3.0 (sum of timeframe strengths)
    weekly_analysis: TimeframeAnalysis
    daily_analysis: TimeframeAnalysis
    h4_analysis: TimeframeAnalysis
    entry_price: float
    confidence: float


@dataclass
class ConfluenceBacktestResult:
    """Results from confluence backtest"""

    pair: str
    start_date: str
    end_date: str
    total_return: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    max_drawdown: float
    sharpe_ratio: float
    confluence_signals: int
    avg_confluence_score: float
    performance_grade: str


class MultiTimeframeConfluenceBacktester:
    def __init__(self):
        self.data_dir = "backtest_data/historical_data"
        self.initial_equity = 10000.0

        # Multi-timeframe configuration
        self.confluence_threshold = (
            1.2  # Reduced threshold for more trading opportunities
        )
        self.max_risk_per_trade = 0.015  # 1.5% max risk per trade

        # Prioritize high-performing pairs based on our analysis
        self.pair_priorities = {
            "USD_JPY": 1.0,  # Top performer across all timeframes
            "GBP_USD": 0.9,  # Strong daily performance
            "GBP_JPY": 0.85,  # Good H4 and daily performance
            "EUR_JPY": 0.8,  # Solid daily performance
            "EUR_USD": 0.75,  # Decent weekly performance
            "AUD_JPY": 0.7,  # Positive across timeframes
            "USD_CHF": 0.6,  # Consistent but modest
            "USD_CAD": 0.5,  # Mixed results
            "AUD_USD": 0.4,  # Generally negative
            "EUR_GBP": 0.3,  # Poor performance
        }

        # Get available pairs
        self.available_pairs = self._get_available_pairs()
        logger.info(
            f"📊 Available pairs for confluence backtesting: {self.available_pairs}"
        )

    def _get_available_pairs(self) -> List[str]:
        """Get list of pairs with valid JSON data files"""
        pairs = []
        summary_file = os.path.join(self.data_dir, "fetch_summary.json")
        if os.path.exists(summary_file):
            with open(summary_file, "r") as f:
                summary = json.load(f)
            for pair, result in summary.get("results", {}).items():
                if result.get("success") and result.get("candle_count", 0) > 0:
                    pairs.append(pair)
        return pairs

    def _load_pair_data(self, pair: str) -> Optional[List[LocalPriceData]]:
        """Load H4 historical data for a pair from JSON file"""
        try:
            filename = f"{pair}_H4_5Y.json"
            filepath = os.path.join(self.data_dir, filename)

            if not os.path.exists(filepath):
                logger.warning(f"❌ Data file not found for {pair}: {filepath}")
                return None

            with open(filepath, "r") as f:
                data = json.load(f)

            # Convert to LocalPriceData objects
            price_data = []
            for candle in data.get("data", []):
                timestamp = datetime.fromisoformat(
                    candle["timestamp"].replace("Z", "+00:00")
                )
                price_data.append(
                    LocalPriceData(
                        timestamp=timestamp,
                        open=candle["open"],
                        high=candle["high"],
                        low=candle["low"],
                        close=candle["close"],
                        volume=candle["volume"],
                    )
                )

            logger.debug(f"📊 Loaded {len(price_data)} H4 candles for {pair}")
            return price_data

        except Exception as e:
            logger.error(f"❌ Error loading data for {pair}: {str(e)}")
            return None

    def _convert_to_daily(self, h4_data: List[LocalPriceData]) -> List[LocalPriceData]:
        """Convert H4 data to daily timeframe"""
        if not h4_data:
            return []

        daily_data = []
        current_day_data = []
        current_day = None

        for candle in h4_data:
            candle_date = candle.timestamp.date()

            if current_day is None:
                current_day = candle_date
                current_day_data = [candle]
            elif candle_date == current_day:
                current_day_data.append(candle)
            else:
                # Process previous day
                if current_day_data and current_day is not None:
                    day_start = datetime.combine(
                        current_day, datetime.min.time(), timezone.utc
                    )
                    daily_candle = self._aggregate_candles(current_day_data, day_start)
                    daily_data.append(daily_candle)

                # Start new day
                current_day = candle_date
                current_day_data = [candle]

        # Process final day
        if current_day_data and current_day is not None:
            day_start = datetime.combine(current_day, datetime.min.time(), timezone.utc)
            daily_candle = self._aggregate_candles(current_day_data, day_start)
            daily_data.append(daily_candle)

        return daily_data

    def _convert_to_weekly(self, h4_data: List[LocalPriceData]) -> List[LocalPriceData]:
        """Convert H4 data to weekly timeframe"""
        if not h4_data:
            return []

        weekly_data = []
        current_week_data = []
        current_week_start = None

        for candle in h4_data:
            # Get Monday of the week
            week_start = candle.timestamp - timedelta(days=candle.timestamp.weekday())
            week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

            if current_week_start is None:
                current_week_start = week_start
                current_week_data = [candle]
            elif week_start == current_week_start:
                current_week_data.append(candle)
            else:
                # Process previous week
                if current_week_data and current_week_start is not None:
                    weekly_candle = self._aggregate_candles(
                        current_week_data, current_week_start
                    )
                    weekly_data.append(weekly_candle)

                # Start new week
                current_week_start = week_start
                current_week_data = [candle]

        # Process final week
        if current_week_data and current_week_start is not None:
            weekly_candle = self._aggregate_candles(
                current_week_data, current_week_start
            )
            weekly_data.append(weekly_candle)

        return weekly_data

    def _aggregate_candles(
        self, candles: List[LocalPriceData], timestamp: datetime
    ) -> LocalPriceData:
        """Aggregate multiple candles into a single candle"""
        if not candles:
            raise ValueError("Cannot aggregate empty candle list")

        sorted_candles = sorted(candles, key=lambda c: c.timestamp)
        return LocalPriceData(
            timestamp=timestamp,
            open=sorted_candles[0].open,
            high=max(c.high for c in candles),
            low=min(c.low for c in candles),
            close=sorted_candles[-1].close,
            volume=sum(c.volume for c in candles),
        )

    def _calculate_ema(self, prices: List[float], period: int) -> List[float]:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return []

        emas = []
        multiplier = 2 / (period + 1)
        sma = sum(prices[:period]) / period
        emas.append(sma)

        for i in range(period, len(prices)):
            ema = (prices[i] * multiplier) + (emas[-1] * (1 - multiplier))
            emas.append(ema)

        return emas

    def _calculate_rsi(self, prices: List[float], period: int = 14) -> List[float]:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return []

        deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        gains = [delta if delta > 0 else 0 for delta in deltas]
        losses = [-delta if delta < 0 else 0 for delta in deltas]

        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        rsi_values = []

        for i in range(period, len(gains)):
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))

            rsi_values.append(rsi)

            # Update running averages
            if i < len(gains) - 1:
                avg_gain = (avg_gain * (period - 1) + gains[i]) / period
                avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        return rsi_values

    def _calculate_adx(
        self,
        highs: List[float],
        lows: List[float],
        closes: List[float],
        period: int = 14,
    ) -> List[float]:
        """Calculate Average Directional Index (simplified)"""
        if len(closes) < period + 1:
            return [20.0] * max(0, len(closes) - period)

        # Simplified ADX calculation
        adx_values = []
        for i in range(period, len(closes)):
            # Calculate recent price movement range as proxy for ADX
            recent_highs = highs[i - period : i]
            recent_lows = lows[i - period : i]
            recent_closes = closes[i - period : i]

            price_range = max(recent_highs) - min(recent_lows)
            avg_close = sum(recent_closes) / len(recent_closes)
            adx_proxy = (price_range / avg_close) * 1000  # Scale to typical ADX range
            adx_proxy = min(max(adx_proxy, 0), 100)  # Clamp to 0-100

            adx_values.append(adx_proxy)

        return adx_values

    def _analyze_weekly_trend(
        self, weekly_data: List[LocalPriceData], index: int
    ) -> TimeframeAnalysis:
        """Analyze weekly timeframe for primary trend direction"""
        if index < 50 or len(weekly_data) < 50:
            return TimeframeAnalysis(
                "weekly", "neutral", 0.0, 0.0, 0.0, 50.0, 20.0, False
            )

        recent_candles = weekly_data[: index + 1]
        closes = [c.close for c in recent_candles]
        highs = [c.high for c in recent_candles]
        lows = [c.low for c in recent_candles]

        ema_20 = self._calculate_ema(closes, 20)
        ema_50 = self._calculate_ema(closes, 50)
        rsi = self._calculate_rsi(closes, 14)
        adx = self._calculate_adx(highs, lows, closes, 14)

        if not ema_20 or not ema_50 or not rsi or not adx:
            return TimeframeAnalysis(
                "weekly", "neutral", 0.0, 0.0, 0.0, 50.0, 20.0, False
            )

        current_ema_20 = ema_20[-1]
        current_ema_50 = ema_50[-1]
        current_rsi = rsi[-1]
        current_adx = adx[-1]

        # Determine trend direction and strength
        if current_ema_20 > current_ema_50 and current_rsi > 50:
            trend_direction = "bullish"
            signal_strength = min(
                (current_ema_20 - current_ema_50) / current_ema_50 * 100, 1.0
            )
        elif current_ema_20 < current_ema_50 and current_rsi < 50:
            trend_direction = "bearish"
            signal_strength = min(
                (current_ema_50 - current_ema_20) / current_ema_50 * 100, 1.0
            )
        else:
            trend_direction = "neutral"
            signal_strength = 0.0

        # Enhanced strength based on ADX and RSI
        if current_adx > 25:
            signal_strength *= 1.2
        signal_strength = min(signal_strength, 1.0)

        tradeable = signal_strength > 0.3 and current_adx > 15

        return TimeframeAnalysis(
            timeframe="weekly",
            trend_direction=trend_direction,
            signal_strength=signal_strength,
            ema_fast=current_ema_20,
            ema_slow=current_ema_50,
            rsi=current_rsi,
            adx=current_adx,
            tradeable=tradeable,
        )

    def _analyze_daily_setup(
        self, daily_data: List[LocalPriceData], index: int, weekly_trend: str
    ) -> TimeframeAnalysis:
        """Analyze daily timeframe for swing trading setup"""
        if index < 50 or len(daily_data) < 50:
            return TimeframeAnalysis(
                "daily", "neutral", 0.0, 0.0, 0.0, 50.0, 20.0, False
            )

        recent_candles = daily_data[: index + 1]
        closes = [c.close for c in recent_candles]
        highs = [c.high for c in recent_candles]
        lows = [c.low for c in recent_candles]

        ema_20 = self._calculate_ema(closes, 20)
        ema_50 = self._calculate_ema(closes, 50)
        rsi = self._calculate_rsi(closes, 14)
        adx = self._calculate_adx(highs, lows, closes, 14)

        if not ema_20 or not ema_50 or not rsi or not adx:
            return TimeframeAnalysis(
                "daily", "neutral", 0.0, 0.0, 0.0, 50.0, 20.0, False
            )

        current_ema_20 = ema_20[-1]
        current_ema_50 = ema_50[-1]
        current_close = closes[-1]
        current_rsi = rsi[-1]
        current_adx = adx[-1]

        # Determine setup direction and strength
        trend_direction = "neutral"
        signal_strength = 0.0

        # Look for pullback to EMA 20 in weekly trend direction
        if weekly_trend == "bullish" and current_ema_20 > current_ema_50:
            # Bullish pullback setup - more lenient conditions
            pullback_quality = abs(current_close - current_ema_20) / current_close
            if pullback_quality < 0.02:  # Within 2% of EMA 20 (more permissive)
                trend_direction = "bullish"
                signal_strength = 1.0 - pullback_quality * 5  # Adjusted scaling
        elif weekly_trend == "bearish" and current_ema_20 < current_ema_50:
            # Bearish pullback setup - more lenient conditions
            pullback_quality = abs(current_close - current_ema_20) / current_close
            if pullback_quality < 0.02:  # Within 2% of EMA 20 (more permissive)
                trend_direction = "bearish"
                signal_strength = 1.0 - pullback_quality * 5  # Adjusted scaling

        # Enhance strength with momentum
        if current_adx > 20:
            signal_strength *= 1.1

        signal_strength = min(signal_strength, 1.0)
        tradeable = (
            signal_strength > 0.2 and trend_direction == weekly_trend
        )  # Reduced threshold

        return TimeframeAnalysis(
            timeframe="daily",
            trend_direction=trend_direction,
            signal_strength=signal_strength,
            ema_fast=current_ema_20,
            ema_slow=current_ema_50,
            rsi=current_rsi,
            adx=current_adx,
            tradeable=tradeable,
        )

    def _analyze_h4_execution(
        self, h4_data: List[LocalPriceData], index: int, daily_trend: str
    ) -> TimeframeAnalysis:
        """Analyze H4 timeframe for precise execution timing"""
        if index < 50:
            return TimeframeAnalysis("h4", "neutral", 0.0, 0.0, 0.0, 50.0, 20.0, False)

        recent_candles = h4_data[: index + 1]
        closes = [c.close for c in recent_candles]

        ema_21 = self._calculate_ema(closes, 21)
        ema_50 = self._calculate_ema(closes, 50)
        rsi = self._calculate_rsi(closes, 14)

        if len(ema_21) < 2 or len(ema_50) < 2 or not rsi:
            return TimeframeAnalysis("h4", "neutral", 0.0, 0.0, 0.0, 50.0, 20.0, False)

        current_ema_21 = ema_21[-1]
        current_ema_50 = ema_50[-1]
        prev_ema_21 = ema_21[-2]
        prev_ema_50 = ema_50[-2]
        current_rsi = rsi[-1]

        # Look for EMA crossover in daily trend direction
        trend_direction = "neutral"
        signal_strength = 0.0

        # Bullish crossover
        if (
            daily_trend == "bullish"
            and prev_ema_21 <= prev_ema_50
            and current_ema_21 > current_ema_50
            and current_rsi > 45
        ):
            trend_direction = "bullish"
            ema_separation = (current_ema_21 - current_ema_50) / current_ema_50
            signal_strength = min(ema_separation * 500, 1.0)  # Scale separation

        # Bearish crossover
        elif (
            daily_trend == "bearish"
            and prev_ema_21 >= prev_ema_50
            and current_ema_21 < current_ema_50
            and current_rsi < 55
        ):
            trend_direction = "bearish"
            ema_separation = (current_ema_50 - current_ema_21) / current_ema_50
            signal_strength = min(ema_separation * 500, 1.0)  # Scale separation

        tradeable = signal_strength > 0.2 and trend_direction == daily_trend

        return TimeframeAnalysis(
            timeframe="h4",
            trend_direction=trend_direction,
            signal_strength=signal_strength,
            ema_fast=current_ema_21,
            ema_slow=current_ema_50,
            rsi=current_rsi,
            adx=0.0,  # Not used for H4
            tradeable=tradeable,
        )

    def _generate_confluence_signal(
        self,
        pair: str,
        h4_candles: List[LocalPriceData],
        daily_candles: List[LocalPriceData],
        weekly_candles: List[LocalPriceData],
        h4_index: int,
    ) -> Optional[ConfluenceSignal]:
        """Generate confluence signal based on multi-timeframe analysis"""

        # Find corresponding daily and weekly indices
        current_h4_time = h4_candles[h4_index].timestamp

        # Find daily index
        daily_index = -1
        for i, daily_candle in enumerate(daily_candles):
            if daily_candle.timestamp <= current_h4_time:
                daily_index = i
            else:
                break

        # Find weekly index
        weekly_index = -1
        for i, weekly_candle in enumerate(weekly_candles):
            if weekly_candle.timestamp <= current_h4_time:
                weekly_index = i
            else:
                break

        if daily_index < 50 or weekly_index < 20:
            return None

        # Analyze each timeframe
        weekly_analysis = self._analyze_weekly_trend(weekly_candles, weekly_index)
        daily_analysis = self._analyze_daily_setup(
            daily_candles, daily_index, weekly_analysis.trend_direction
        )
        h4_analysis = self._analyze_h4_execution(
            h4_candles, h4_index, daily_analysis.trend_direction
        )

        # Calculate confluence score
        confluence_score = 0.0
        if weekly_analysis.tradeable:
            confluence_score += weekly_analysis.signal_strength
        if daily_analysis.tradeable:
            confluence_score += daily_analysis.signal_strength
        if h4_analysis.tradeable:
            confluence_score += h4_analysis.signal_strength

        # Apply pair priority multiplier
        pair_priority = self.pair_priorities.get(pair, 0.5)
        confluence_score *= pair_priority

        # Check confluence threshold
        if confluence_score < self.confluence_threshold:
            return None

        # Determine signal type
        if (
            weekly_analysis.trend_direction == "bullish"
            and daily_analysis.trend_direction == "bullish"
            and h4_analysis.trend_direction == "bullish"
        ):
            signal_type = SignalType.BUY
        elif (
            weekly_analysis.trend_direction == "bearish"
            and daily_analysis.trend_direction == "bearish"
            and h4_analysis.trend_direction == "bearish"
        ):
            signal_type = SignalType.SELL
        else:
            return None

        # Calculate confidence based on alignment and strength
        alignment_count = sum(
            [
                1
                for analysis in [weekly_analysis, daily_analysis, h4_analysis]
                if analysis.tradeable
                and analysis.trend_direction == weekly_analysis.trend_direction
            ]
        )
        confidence = (alignment_count / 3.0) * (confluence_score / 3.0)

        return ConfluenceSignal(
            pair=pair,
            timestamp=current_h4_time,
            signal_type=signal_type,
            confluence_score=confluence_score,
            weekly_analysis=weekly_analysis,
            daily_analysis=daily_analysis,
            h4_analysis=h4_analysis,
            entry_price=h4_candles[h4_index].close,
            confidence=confidence,
        )

    async def backtest_pair(self, pair: str) -> Optional[ConfluenceBacktestResult]:
        """Backtest a single pair using multi-timeframe confluence"""
        try:
            logger.info(f"📊 Starting confluence backtest for {pair}...")

            # Load H4 data and convert to all timeframes
            h4_data = self._load_pair_data(pair)
            if not h4_data or len(h4_data) < 1000:
                logger.warning(f"❌ Insufficient H4 data for {pair}")
                return None

            daily_data = self._convert_to_daily(h4_data)
            weekly_data = self._convert_to_weekly(h4_data)

            logger.info(
                f"📊 {pair}: H4={len(h4_data)}, Daily={len(daily_data)}, Weekly={len(weekly_data)}"
            )

            # Initialize tracking variables
            account_equity = self.initial_equity
            trades = []
            confluence_signals = []
            current_position = None
            equity_curve = [
                {"timestamp": h4_data[0].timestamp, "equity": account_equity}
            ]

            # Process through H4 data looking for confluence
            for i in range(
                200, len(h4_data)
            ):  # Start after sufficient data for all timeframes
                current_candle = h4_data[i]

                # Generate confluence signal
                signal = self._generate_confluence_signal(
                    pair, h4_data, daily_data, weekly_data, i
                )

                if signal:
                    confluence_signals.append(signal)

                    # Handle position logic
                    if current_position is None:
                        # Open new position
                        current_position = {
                            "type": signal.signal_type.value,
                            "entry_price": signal.entry_price,
                            "entry_time": signal.timestamp,
                            "confidence": signal.confidence,
                            "confluence_score": signal.confluence_score,
                        }
                    elif current_position["type"] != signal.signal_type.value:
                        # Close current position and open new one
                        trade_result = self._close_position(
                            current_position, signal, account_equity
                        )
                        trades.append(trade_result["trade"])
                        account_equity = trade_result["new_equity"]

                        equity_curve.append(
                            {"timestamp": signal.timestamp, "equity": account_equity}
                        )

                        # Open new position
                        current_position = {
                            "type": signal.signal_type.value,
                            "entry_price": signal.entry_price,
                            "entry_time": signal.timestamp,
                            "confidence": signal.confidence,
                            "confluence_score": signal.confluence_score,
                        }

            # Close final position if open
            if current_position and confluence_signals:
                final_signal = confluence_signals[-1]
                final_signal.signal_type = (
                    SignalType.SELL
                    if current_position["type"] == "BUY"
                    else SignalType.BUY
                )
                trade_result = self._close_position(
                    current_position, final_signal, account_equity
                )
                trades.append(trade_result["trade"])
                account_equity = trade_result["new_equity"]

            # Calculate performance metrics
            total_return = (
                (account_equity - self.initial_equity) / self.initial_equity
            ) * 100
            winning_trades = len([t for t in trades if t["pnl_pct"] > 0])
            losing_trades = len([t for t in trades if t["pnl_pct"] <= 0])
            win_rate = (winning_trades / len(trades) * 100) if trades else 0

            # Calculate max drawdown
            max_equity = self.initial_equity
            max_drawdown = 0
            for point in equity_curve:
                if point["equity"] > max_equity:
                    max_equity = point["equity"]
                current_drawdown = ((max_equity - point["equity"]) / max_equity) * 100
                if current_drawdown > max_drawdown:
                    max_drawdown = current_drawdown

            # Calculate Sharpe ratio
            if trades:
                returns = [t["pnl_pct"] for t in trades]
                avg_return = np.mean(returns)
                std_return = np.std(returns)
                sharpe_ratio = float(avg_return / std_return) if std_return > 0 else 0.0
            else:
                sharpe_ratio = 0.0

            # Calculate average confluence score
            avg_confluence_score = float(
                np.mean([s.confluence_score for s in confluence_signals])
                if confluence_signals
                else 0.0
            )

            # Performance grading based on enhanced criteria
            if total_return >= 25 and win_rate >= 60 and max_drawdown <= 10:
                performance_grade = "A+"
            elif total_return >= 20 and win_rate >= 55 and max_drawdown <= 15:
                performance_grade = "A"
            elif total_return >= 15 and win_rate >= 50 and max_drawdown <= 20:
                performance_grade = "B+"
            elif total_return >= 10 and win_rate >= 45 and max_drawdown <= 25:
                performance_grade = "B"
            elif total_return >= 5 and win_rate >= 40:
                performance_grade = "C"
            else:
                performance_grade = "D"

            result = ConfluenceBacktestResult(
                pair=pair,
                start_date=h4_data[0].timestamp.strftime("%Y-%m-%d"),
                end_date=h4_data[-1].timestamp.strftime("%Y-%m-%d"),
                total_return=total_return,
                total_trades=len(trades),
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                win_rate=win_rate,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio,
                confluence_signals=len(confluence_signals),
                avg_confluence_score=avg_confluence_score,
                performance_grade=performance_grade,
            )

            logger.info(
                f"✅ {pair}: {total_return:.2f}% return, {win_rate:.1f}% win rate, "
                f"{len(trades)} trades, {len(confluence_signals)} confluences"
            )
            return result

        except Exception as e:
            logger.error(f"❌ Error backtesting {pair}: {str(e)}")
            return None

    def _close_position(
        self, position: Dict, signal: ConfluenceSignal, current_equity: float
    ) -> Dict:
        """Close a trading position with advanced risk management"""
        entry_price = position["entry_price"]
        exit_price = signal.entry_price
        position_type = position["type"]
        pair = signal.pair

        # Determine pip multiplier
        is_jpy_pair = "JPY" in pair
        pip_multiplier = 100 if is_jpy_pair else 10000

        # Calculate P&L
        if position_type == "BUY":
            pnl_pips = (exit_price - entry_price) * pip_multiplier
        else:  # SELL
            pnl_pips = (entry_price - exit_price) * pip_multiplier

        # Advanced position sizing based on confluence score
        base_risk = self.max_risk_per_trade
        confluence_multiplier = min(position.get("confluence_score", 2.0) / 3.0, 1.0)
        pair_priority = self.pair_priorities.get(pair, 0.5)

        # Adjust risk based on confluence and pair priority
        adjusted_risk = base_risk * confluence_multiplier * pair_priority
        max_risk_usd = adjusted_risk * current_equity

        # Dynamic position sizing: Higher confluence = larger position (within limits)
        position_size = min(
            2.0 * confluence_multiplier, 3.0
        )  # $1-3 per pip based on confluence
        pnl_usd = pnl_pips * position_size

        # Apply stop loss
        if pnl_usd < -max_risk_usd:
            pnl_usd = -max_risk_usd
            pnl_pips = pnl_usd / position_size

        pnl_pct = (pnl_usd / current_equity) * 100
        new_equity = current_equity + pnl_usd

        trade = {
            "entry_time": position["entry_time"],
            "exit_time": signal.timestamp,
            "type": position_type,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "pnl_pips": pnl_pips,
            "pnl_usd": pnl_usd,
            "pnl_pct": pnl_pct,
            "confidence": position["confidence"],
            "confluence_score": position.get("confluence_score", 0.0),
        }

        return {"trade": trade, "new_equity": new_equity}

    async def run_confluence_backtest_suite(self) -> Dict[str, Any]:
        """Run confluence backtest on all available pairs"""
        logger.info(
            f"🚀 Starting Multi-Timeframe Confluence Backtest for {len(self.available_pairs)} pairs"
        )
        logger.info(f"📊 Confluence threshold: {self.confluence_threshold}")
        logger.info(f"📊 Max risk per trade: {self.max_risk_per_trade*100:.1f}%")

        results = {}
        successful_backtests = []

        for i, pair in enumerate(self.available_pairs, 1):
            logger.info(f"[{i}/{len(self.available_pairs)}] Processing {pair}...")

            result = await self.backtest_pair(pair)
            if result:
                results[pair] = result.__dict__
                successful_backtests.append(result)

            # Small delay between pairs
            await asyncio.sleep(0.1)

        # Calculate portfolio summary
        if successful_backtests:
            # Weight returns by pair priority for portfolio calculation
            weighted_returns = []
            total_weights = 0

            for result in successful_backtests:
                pair_weight = self.pair_priorities.get(result.pair, 0.5)
                weighted_returns.append(result.total_return * pair_weight)
                total_weights += pair_weight

            portfolio_return = (
                sum(weighted_returns) / total_weights if total_weights > 0 else 0
            )
            total_trades = sum(r.total_trades for r in successful_backtests)
            total_winning = sum(r.winning_trades for r in successful_backtests)
            portfolio_win_rate = (
                (total_winning / total_trades * 100) if total_trades > 0 else 0
            )

            avg_sharpe = np.mean([r.sharpe_ratio for r in successful_backtests])
            max_drawdown = max(r.max_drawdown for r in successful_backtests)
            total_confluences = sum(r.confluence_signals for r in successful_backtests)
            avg_confluence_score = np.mean(
                [r.avg_confluence_score for r in successful_backtests]
            )

            # Sort results by return
            top_performers = sorted(
                successful_backtests, key=lambda x: x.total_return, reverse=True
            )[:3]

            portfolio_summary = {
                "strategy": "Multi-Timeframe Confluence",
                "timeframes": "Weekly + Daily + H4",
                "total_pairs": len(self.available_pairs),
                "successful_pairs": len(successful_backtests),
                "portfolio_return": portfolio_return,
                "portfolio_win_rate": portfolio_win_rate,
                "sharpe_ratio": avg_sharpe,
                "max_drawdown": max_drawdown,
                "total_trades": total_trades,
                "total_confluences": total_confluences,
                "avg_confluence_score": avg_confluence_score,
                "confluence_threshold": self.confluence_threshold,
                "top_performers": [
                    {
                        "pair": p.pair,
                        "return": p.total_return,
                        "win_rate": p.win_rate,
                        "trades": p.total_trades,
                        "confluences": p.confluence_signals,
                        "grade": p.performance_grade,
                    }
                    for p in top_performers
                ],
                "individual_results": {
                    r.pair: r.total_return for r in successful_backtests
                },
            }
        else:
            portfolio_summary = {"error": "No successful backtests completed"}

        # Save results
        await self._save_results_to_files(portfolio_summary, results)

        return {"portfolio_summary": portfolio_summary, "individual_results": results}

    async def _save_results_to_files(
        self, portfolio_summary: Dict[str, Any], individual_results: Dict[str, Any]
    ):
        """Save confluence backtest results to JSON files"""
        try:
            # Ensure directories exist
            output_dir = "../4ex.ninja-frontend/public/data/strategy"
            os.makedirs(output_dir, exist_ok=True)

            # Save portfolio summary
            portfolio_file = os.path.join(
                output_dir, "confluence_portfolio_summary.json"
            )
            with open(portfolio_file, "w") as f:
                json.dump(portfolio_summary, f, indent=2, default=str)

            # Save individual results
            individual_file = os.path.join(
                output_dir, "confluence_individual_results.json"
            )
            with open(individual_file, "w") as f:
                json.dump(individual_results, f, indent=2, default=str)

            logger.info(f"💾 Confluence results saved to:")
            logger.info(f"   Portfolio: {portfolio_file}")
            logger.info(f"   Individual: {individual_file}")

        except Exception as e:
            logger.error(f"❌ Error saving confluence results: {str(e)}")


async def main():
    """Main execution function"""
    backtester = MultiTimeframeConfluenceBacktester()

    try:
        results = await backtester.run_confluence_backtest_suite()

        # Print results
        portfolio = results["portfolio_summary"]
        if "error" not in portfolio:
            print("\n" + "=" * 80)
            print("📊 MULTI-TIMEFRAME CONFLUENCE BACKTEST RESULTS")
            print("=" * 80)
            print(f"Strategy: {portfolio['strategy']}")
            print(f"Timeframes: {portfolio['timeframes']}")
            print(f"Portfolio Return: {portfolio['portfolio_return']:.2f}%")
            print(f"Portfolio Win Rate: {portfolio['portfolio_win_rate']:.1f}%")
            print(f"Sharpe Ratio: {portfolio['sharpe_ratio']:.2f}")
            print(f"Max Drawdown: {portfolio['max_drawdown']:.1f}%")
            print(f"Total Trades: {portfolio['total_trades']}")
            print(f"Total Confluences: {portfolio['total_confluences']}")
            print(f"Avg Confluence Score: {portfolio['avg_confluence_score']:.2f}")
            print(f"Confluence Threshold: {portfolio['confluence_threshold']}")

            print(f"\n🏆 Top 3 Confluence Performers:")
            for i, performer in enumerate(portfolio["top_performers"], 1):
                print(
                    f"   {i}. {performer['pair']}: {performer['return']:.2f}% "
                    f"(Win Rate: {performer['win_rate']:.1f}%, "
                    f"Trades: {performer['trades']}, "
                    f"Confluences: {performer['confluences']}, "
                    f"Grade: {performer['grade']})"
                )

            print(f"\n📈 Individual Confluence Results:")
            for pair, return_pct in portfolio["individual_results"].items():
                print(f"   {pair}: {return_pct:.2f}%")

        else:
            print(f"❌ Error: {portfolio['error']}")

        print("=" * 80)

    except Exception as e:
        logger.error(f"❌ Fatal error during confluence backtest: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())

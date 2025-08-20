#!/usr/bin/env python3
"""
Weekly-Only Backtest for 4ex.ninja
Position trading backtest using weekly data converted from H4
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import numpy as np

from models.signal_models import TradingSignal, SignalType, PriceData

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
class WeeklyBacktestResult:
    """Results from weekly-only backtest"""

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
    candles_analyzed: int
    weekly_candles: int
    signals_generated: int
    performance_grade: str


class WeeklyJSONBacktester:
    def __init__(self):
        self.data_dir = "backtest_data/historical_data"
        self.initial_equity = 10000.0

        # Get available pairs from successful fetches
        self.available_pairs = self._get_available_pairs()
        logger.info(
            f"📊 Available pairs for weekly backtesting: {self.available_pairs}"
        )

    def _get_available_pairs(self) -> List[str]:
        """Get list of pairs with valid JSON data files"""
        pairs = []

        # Check fetch summary for successful pairs
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
                logger.error(f"❌ Data file not found: {filename}")
                return None

            with open(filepath, "r") as f:
                data = json.load(f)

            # Convert to LocalPriceData objects
            price_data = []
            for candle in data.get("data", []):
                timestamp = datetime.fromisoformat(candle["timestamp"])
                # Ensure timezone-aware
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)

                price_data.append(
                    LocalPriceData(
                        timestamp=timestamp,
                        open=float(candle["open"]),
                        high=float(candle["high"]),
                        low=float(candle["low"]),
                        close=float(candle["close"]),
                        volume=int(candle["volume"]),
                    )
                )

            logger.info(f"📊 Loaded {len(price_data)} H4 candles for {pair}")
            return price_data

        except Exception as e:
            logger.error(f"❌ Error loading data for {pair}: {str(e)}")
            return None

    def _convert_to_weekly(
        self, fourhour_data: List[LocalPriceData]
    ) -> List[LocalPriceData]:
        """Convert H4 data to weekly timeframe (Monday to Sunday)"""
        if not fourhour_data:
            return []

        weekly_data = []
        current_week_data = []
        current_week_start = None

        for candle in fourhour_data:
            # Get Monday of the week for this candle
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

        logger.debug(
            f"📊 Converted {len(fourhour_data)} H4 candles to {len(weekly_data)} weekly candles"
        )
        return weekly_data

    def _aggregate_candles(
        self, candles: List[LocalPriceData], timestamp: datetime
    ) -> LocalPriceData:
        """Aggregate multiple candles into a single weekly candle"""
        if not candles:
            raise ValueError("Cannot aggregate empty candle list")

        # Sort by timestamp to ensure proper OHLC
        sorted_candles = sorted(candles, key=lambda c: c.timestamp)

        open_price = sorted_candles[0].open
        close_price = sorted_candles[-1].close
        high_price = max(c.high for c in candles)
        low_price = min(c.low for c in candles)
        total_volume = sum(c.volume for c in candles)

        return LocalPriceData(
            timestamp=timestamp,
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            volume=total_volume,
        )

    def _calculate_ema(self, prices: List[float], period: int) -> List[float]:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return []

        emas = []
        multiplier = 2 / (period + 1)

        # Start with SMA for first value
        sma = sum(prices[:period]) / period
        emas.append(sma)

        # Calculate EMA for remaining values
        for i in range(period, len(prices)):
            ema = (prices[i] * multiplier) + (emas[-1] * (1 - multiplier))
            emas.append(ema)

        return emas

    def _calculate_rsi(self, prices: List[float], period: int = 14) -> List[float]:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return []

        # Calculate price changes
        deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]

        # Separate gains and losses
        gains = [delta if delta > 0 else 0 for delta in deltas]
        losses = [-delta if delta < 0 else 0 for delta in deltas]

        # Calculate initial averages
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period

        rsi_values = []

        # Calculate RSI for each period
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
            return []

        # Calculate True Range and Directional Movement
        tr_values = []
        plus_dm = []
        minus_dm = []

        for i in range(1, len(closes)):
            # True Range
            high_low = highs[i] - lows[i]
            high_close_prev = abs(highs[i] - closes[i - 1])
            low_close_prev = abs(lows[i] - closes[i - 1])
            tr = max(high_low, high_close_prev, low_close_prev)
            tr_values.append(tr)

            # Directional Movement
            up_move = highs[i] - highs[i - 1]
            down_move = lows[i - 1] - lows[i]

            plus_dm.append(up_move if up_move > down_move and up_move > 0 else 0)
            minus_dm.append(down_move if down_move > up_move and down_move > 0 else 0)

        # Calculate smoothed values and ADX
        adx_values = []

        if len(tr_values) >= period:
            # Initial smoothed values
            tr_smooth = sum(tr_values[:period])
            plus_dm_smooth = sum(plus_dm[:period])
            minus_dm_smooth = sum(minus_dm[:period])

            for i in range(period, len(tr_values)):
                # Update smoothed values
                tr_smooth = tr_smooth - (tr_smooth / period) + tr_values[i]
                plus_dm_smooth = plus_dm_smooth - (plus_dm_smooth / period) + plus_dm[i]
                minus_dm_smooth = (
                    minus_dm_smooth - (minus_dm_smooth / period) + minus_dm[i]
                )

                # Calculate DI+ and DI-
                di_plus = 100 * (plus_dm_smooth / tr_smooth) if tr_smooth > 0 else 0
                di_minus = 100 * (minus_dm_smooth / tr_smooth) if tr_smooth > 0 else 0

                # Calculate DX
                di_sum = di_plus + di_minus
                dx = 100 * abs(di_plus - di_minus) / di_sum if di_sum > 0 else 0

                adx_values.append(dx)

        # Smooth DX to get ADX (simplified)
        if len(adx_values) >= period:
            smoothed_adx = []
            for i in range(period - 1, len(adx_values)):
                adx = sum(adx_values[i - period + 1 : i + 1]) / period
                smoothed_adx.append(adx)
            return smoothed_adx

        return adx_values if adx_values else [20.0]  # Default value

    def _generate_weekly_signal(
        self, weekly_candles: List[LocalPriceData], pair: str, index: int
    ) -> Optional[TradingSignal]:
        """Generate weekly EMA 20/50 crossover signal with RSI and ADX filters"""
        # Need at least 50 weekly candles for proper calculation
        if index < 50 or len(weekly_candles) < 50:
            return None

        # Get recent candles up to current index
        recent_candles = weekly_candles[: index + 1]
        closes = [c.close for c in recent_candles]
        highs = [c.high for c in recent_candles]
        lows = [c.low for c in recent_candles]

        # Calculate indicators
        ema_20 = self._calculate_ema(closes, 20)
        ema_50 = self._calculate_ema(closes, 50)
        rsi = self._calculate_rsi(closes, 14)
        adx = self._calculate_adx(highs, lows, closes, 14)

        if len(ema_20) < 2 or len(ema_50) < 2 or len(rsi) < 1 or len(adx) < 1:
            return None

        # Current and previous values
        current_ema_20 = ema_20[-1]
        current_ema_50 = ema_50[-1]
        prev_ema_20 = ema_20[-2]
        prev_ema_50 = ema_50[-2]
        current_rsi = rsi[-1]
        current_adx = adx[-1]

        current_candle = recent_candles[-1]
        signal_type = SignalType.HOLD
        confidence = 0.5

        # Weekly trend conditions (position trading) - Simplified for more signals
        # Reduced filtering to generate more trading opportunities

        # Basic EMA crossover with minimal filtering
        if current_adx > 15:  # Lowered ADX threshold for more signals
            # Bullish crossover with basic momentum
            if prev_ema_20 <= prev_ema_50 and current_ema_20 > current_ema_50:
                signal_type = SignalType.BUY
                # Higher confidence with strong momentum
                if current_rsi > 55 and current_adx > 25:
                    confidence = 0.85
                elif current_rsi > 50:
                    confidence = 0.75
                else:
                    confidence = 0.65

            # Bearish crossover with basic momentum
            elif prev_ema_20 >= prev_ema_50 and current_ema_20 < current_ema_50:
                signal_type = SignalType.SELL
                # Higher confidence with strong momentum
                if current_rsi < 45 and current_adx > 25:
                    confidence = 0.85
                elif current_rsi < 50:
                    confidence = 0.75
                else:
                    confidence = 0.65

        if signal_type != SignalType.HOLD:
            return TradingSignal(
                pair=pair,
                timeframe="Weekly",
                signal_type=signal_type,
                price=current_candle.close,
                fast_ma=current_ema_20,
                slow_ma=current_ema_50,
                timestamp=current_candle.timestamp,
                confidence=confidence,
            )

        return None

    async def backtest_pair(self, pair: str) -> Optional[WeeklyBacktestResult]:
        """Backtest a single pair using weekly data"""
        try:
            logger.info(f"📊 Starting weekly backtest for {pair}...")

            # Load H4 data and convert to weekly
            h4_candles = self._load_pair_data(pair)
            if not h4_candles:
                return None

            weekly_candles = self._convert_to_weekly(h4_candles)

            # Check if we have sufficient weekly data
            if len(weekly_candles) < 100:
                logger.warning(
                    f"⚠️ Insufficient weekly data for {pair}: {len(weekly_candles)} candles"
                )
                return None

            logger.info(
                f"📊 {pair}: {len(h4_candles)} H4 → {len(weekly_candles)} weekly candles"
            )

            # Initialize tracking variables
            account_equity = self.initial_equity
            trades = []
            signals = []
            current_position = None
            equity_curve = [
                {"timestamp": weekly_candles[0].timestamp, "equity": account_equity}
            ]

            # Simulate trading through weekly data
            for i in range(
                50, len(weekly_candles)
            ):  # Start after enough data for indicators
                # Generate weekly signal
                signal = self._generate_weekly_signal(weekly_candles, pair, i)

                if signal:
                    signals.append(signal)

                    # Simulate trade execution (weekly timeframe = position trading)
                    if signal.signal_type.value in ["BUY", "SELL"]:
                        # Close existing position if opposite signal
                        if (
                            current_position
                            and current_position["type"] != signal.signal_type.value
                        ):
                            trade_result = self._close_position(
                                current_position, signal, account_equity
                            )
                            trades.append(trade_result["trade"])
                            account_equity = trade_result["new_equity"]

                        # Open new position
                        current_position = {
                            "type": signal.signal_type.value,
                            "entry_price": signal.price,
                            "entry_time": signal.timestamp,
                            "confidence": signal.confidence,
                        }

                # Update equity curve
                equity_curve.append(
                    {"timestamp": weekly_candles[i].timestamp, "equity": account_equity}
                )

            # Close final position if open
            if current_position:
                final_signal = TradingSignal(
                    pair=pair,
                    timeframe="Weekly",
                    signal_type=SignalType.HOLD,
                    price=weekly_candles[-1].close,
                    fast_ma=0.0,
                    slow_ma=0.0,
                    timestamp=weekly_candles[-1].timestamp,
                    confidence=0.5,
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
                equity = point["equity"]
                if equity > max_equity:
                    max_equity = equity
                drawdown = ((max_equity - equity) / max_equity) * 100
                if drawdown > max_drawdown:
                    max_drawdown = drawdown

            # Simple Sharpe ratio calculation
            if trades:
                returns = [t["pnl_pct"] for t in trades]
                avg_return = sum(returns) / len(returns)
                return_std = (
                    sum((r - avg_return) ** 2 for r in returns) / len(returns)
                ) ** 0.5
                sharpe_ratio = avg_return / return_std if return_std > 0 else 0
            else:
                sharpe_ratio = 0

            # Performance grading
            if total_return >= 20 and win_rate >= 60:
                performance_grade = "A"
            elif total_return >= 10 and win_rate >= 50:
                performance_grade = "B"
            elif total_return >= 0 and win_rate >= 40:
                performance_grade = "C"
            else:
                performance_grade = "D"

            result = WeeklyBacktestResult(
                pair=pair,
                start_date=weekly_candles[0].timestamp.strftime("%Y-%m-%d"),
                end_date=weekly_candles[-1].timestamp.strftime("%Y-%m-%d"),
                total_return=total_return,
                total_trades=len(trades),
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                win_rate=win_rate,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio,
                candles_analyzed=len(h4_candles),
                weekly_candles=len(weekly_candles),
                signals_generated=len(signals),
                performance_grade=performance_grade,
            )

            logger.info(
                f"✅ {pair}: {total_return:.2f}% return, {win_rate:.1f}% win rate, {len(trades)} trades"
            )
            return result

        except Exception as e:
            logger.error(f"❌ Error backtesting {pair}: {str(e)}")
            return None

    def _close_position(
        self, position: Dict, signal: TradingSignal, current_equity: float
    ) -> Dict:
        """Close a trading position and calculate P&L with strict risk management"""
        entry_price = position["entry_price"]
        exit_price = signal.price
        position_type = position["type"]
        pair = signal.pair

        # Determine pip multiplier based on pair type
        is_jpy_pair = "JPY" in pair
        pip_multiplier = 100 if is_jpy_pair else 10000

        # Calculate P&L based on position type
        if position_type == "BUY":
            pnl_pips = (exit_price - entry_price) * pip_multiplier
        else:  # SELL
            pnl_pips = (entry_price - exit_price) * pip_multiplier

        # Risk Management: Maximum 1% risk per trade for Weekly timeframe
        max_risk_pct = 1.0  # 1% maximum risk (very conservative for position trading)
        max_risk_usd = (max_risk_pct / 100) * current_equity

        # Position sizing: $1.5 per pip for Weekly (larger but controlled positions)
        pnl_usd = pnl_pips * 1.5

        # Apply strict stop loss: Maximum loss of 1% per trade
        if pnl_usd < -max_risk_usd:
            pnl_usd = -max_risk_usd
            pnl_pips = pnl_usd / 1.5  # Recalculate pips for reporting

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
        }

        return {"trade": trade, "new_equity": new_equity}

    async def run_backtest_suite(self) -> Dict[str, Any]:
        """Run weekly backtest on all available pairs"""
        logger.info(
            f"🚀 Starting weekly-only backtest suite for {len(self.available_pairs)} pairs"
        )

        results = {}
        successful_backtests = []

        for i, pair in enumerate(self.available_pairs, 1):
            logger.info(f"[{i}/{len(self.available_pairs)}] Processing {pair}...")

            result = await self.backtest_pair(pair)
            if result:
                results[pair] = result
                successful_backtests.append(result)

            # Small delay between pairs
            await asyncio.sleep(0.1)

        # Calculate portfolio summary
        if successful_backtests:
            total_return = sum(r.total_return for r in successful_backtests) / len(
                successful_backtests
            )
            total_trades = sum(r.total_trades for r in successful_backtests)
            total_winning = sum(r.winning_trades for r in successful_backtests)
            portfolio_win_rate = (
                (total_winning / total_trades * 100) if total_trades > 0 else 0
            )
            avg_sharpe = sum(r.sharpe_ratio for r in successful_backtests) / len(
                successful_backtests
            )
            max_drawdown = max(r.max_drawdown for r in successful_backtests)

            # Sort results by performance
            top_performers = sorted(
                successful_backtests, key=lambda x: x.total_return, reverse=True
            )[:3]

            portfolio_summary = {
                "backtest_type": "weekly_only_ema_crossover",
                "strategy_name": "Weekly EMA Crossover (20/50) + RSI + ADX",
                "timeframe": "Weekly",
                "backtest_date": datetime.now(timezone.utc).isoformat(),
                "total_pairs": len(self.available_pairs),
                "successful_pairs": len(successful_backtests),
                "portfolio_return": total_return,
                "portfolio_win_rate": portfolio_win_rate,
                "portfolio_sharpe": avg_sharpe,
                "portfolio_max_drawdown": max_drawdown,
                "total_trades": total_trades,
                "risk_assessment": (
                    "High"
                    if max_drawdown > 50
                    else "Medium" if max_drawdown > 20 else "Low"
                ),
                "performance_grade": (
                    "A"
                    if total_return >= 20 and portfolio_win_rate >= 60
                    else (
                        "B" if total_return >= 10 else "C" if total_return >= 0 else "D"
                    )
                ),
                "top_performers": [
                    {
                        "pair": p.pair,
                        "return": p.total_return,
                        "win_rate": p.win_rate,
                        "sharpe": p.sharpe_ratio,
                        "trades": p.total_trades,
                        "grade": p.performance_grade,
                    }
                    for p in top_performers
                ],
            }
        else:
            portfolio_summary = {"error": "No successful backtests completed"}

        # Save results to JSON files for frontend
        await self._save_results_to_files(portfolio_summary, results)

        return {"portfolio_summary": portfolio_summary, "individual_results": results}

    async def _save_results_to_files(
        self, portfolio_summary: Dict[str, Any], individual_results: Dict[str, Any]
    ):
        """Save backtest results to JSON files for frontend consumption"""
        try:
            # Create output directory if it doesn't exist
            output_dir = "../4ex.ninja-frontend/public/data/strategy"
            os.makedirs(output_dir, exist_ok=True)

            # Save portfolio summary
            portfolio_file = os.path.join(output_dir, "weekly_portfolio_summary.json")
            with open(portfolio_file, "w") as f:
                json.dump(portfolio_summary, f, indent=2, default=str)

            # Save individual results
            individual_file = os.path.join(output_dir, "weekly_individual_results.json")
            # Convert dataclass results to dict for JSON serialization
            serializable_results = {}
            for pair, result in individual_results.items():
                serializable_results[pair] = {
                    "pair": result.pair,
                    "start_date": result.start_date,
                    "end_date": result.end_date,
                    "total_return": result.total_return,
                    "total_trades": result.total_trades,
                    "winning_trades": result.winning_trades,
                    "losing_trades": result.losing_trades,
                    "win_rate": result.win_rate,
                    "max_drawdown": result.max_drawdown,
                    "sharpe_ratio": result.sharpe_ratio,
                    "candles_analyzed": result.candles_analyzed,
                    "weekly_candles": result.weekly_candles,
                    "signals_generated": result.signals_generated,
                    "performance_grade": result.performance_grade,
                }

            with open(individual_file, "w") as f:
                json.dump(serializable_results, f, indent=2, default=str)

            logger.info(f"💾 Weekly results saved to:")
            logger.info(f"   Portfolio: {portfolio_file}")
            logger.info(f"   Individual: {individual_file}")

        except Exception as e:
            logger.error(f"❌ Error saving weekly results to files: {str(e)}")


async def main():
    """Main execution function"""
    backtester = WeeklyJSONBacktester()

    try:
        results = await backtester.run_backtest_suite()

        # Print results
        portfolio = results["portfolio_summary"]
        if "error" not in portfolio:
            print("\n" + "=" * 60)
            print("📊 WEEKLY-ONLY BACKTEST RESULTS")
            print("=" * 60)
            print(f"Strategy: {portfolio['strategy_name']}")
            print(f"Timeframe: {portfolio['timeframe']}")
            print(f"Portfolio Return: {portfolio['portfolio_return']:.2f}%")
            print(f"Portfolio Win Rate: {portfolio['portfolio_win_rate']:.1f}%")
            print(f"Sharpe Ratio: {portfolio['portfolio_sharpe']:.2f}")
            print(f"Max Drawdown: {portfolio['portfolio_max_drawdown']:.1f}%")
            print(f"Performance Grade: {portfolio['performance_grade']}")
            print(f"Risk Assessment: {portfolio['risk_assessment']}")
            print(f"Total Trades: {portfolio['total_trades']}")

            print(f"\n🏆 Top 3 Weekly Performers:")
            for i, performer in enumerate(portfolio["top_performers"], 1):
                print(
                    f"   {i}. {performer['pair']}: {performer['return']:.2f}% (Win Rate: {performer['win_rate']:.1f}%, Trades: {performer['trades']})"
                )

            print("\n📈 Individual Weekly Results:")
            for pair, result in results["individual_results"].items():
                print(
                    f"   {result.pair}: {result.total_return:.2f}% ({result.total_trades} trades, {result.win_rate:.1f}% win rate)"
                )
        else:
            print(f"❌ Error: {portfolio['error']}")

        print("=" * 60)

    except Exception as e:
        logger.error(f"❌ Fatal error during weekly backtest: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())

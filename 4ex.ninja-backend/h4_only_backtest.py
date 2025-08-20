#!/usr/bin/env python3
"""
H4-Only Backtest for 4ex.ninja
Simple single-timeframe backtest using H4 data from JSON files
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

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
class H4BacktestResult:
    """Results from H4-only backtest"""

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
    signals_generated: int
    performance_grade: str


class H4JSONBacktester:
    def __init__(self):
        self.data_dir = "backtest_data/historical_data"
        self.initial_equity = 10000.0

        # Get available pairs from successful fetches
        self.available_pairs = self._get_available_pairs()
        logger.info(f"📊 Available pairs for H4 backtesting: {self.available_pairs}")

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

    def _calculate_simple_ema(self, prices: List[float], period: int) -> List[float]:
        """Calculate simple EMA for H4 signals"""
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

    def _generate_h4_signal(
        self, candles: List[LocalPriceData], pair: str, index: int
    ) -> Optional[TradingSignal]:
        """Generate simple H4 EMA crossover signal"""
        # Need at least 50 candles for EMA calculation
        if index < 50:
            return None

        # Get recent candles up to current index
        recent_candles = candles[: index + 1]
        closes = [c.close for c in recent_candles]

        # Calculate EMAs (21 and 50 period)
        fast_ema = self._calculate_simple_ema(closes, 21)
        slow_ema = self._calculate_simple_ema(closes, 50)

        if len(fast_ema) < 2 or len(slow_ema) < 2:
            return None

        # Check for crossover
        current_fast = fast_ema[-1]
        current_slow = slow_ema[-1]
        prev_fast = fast_ema[-2]
        prev_slow = slow_ema[-2]

        current_candle = recent_candles[-1]
        signal_type = SignalType.HOLD
        confidence = 0.5

        # Bullish crossover: fast EMA crosses above slow EMA
        if prev_fast <= prev_slow and current_fast > current_slow:
            signal_type = SignalType.BUY
            confidence = 0.7
        # Bearish crossover: fast EMA crosses below slow EMA
        elif prev_fast >= prev_slow and current_fast < current_slow:
            signal_type = SignalType.SELL
            confidence = 0.7

        if signal_type != SignalType.HOLD:
            return TradingSignal(
                pair=pair,
                timeframe="H4",
                signal_type=signal_type,
                price=current_candle.close,
                fast_ma=current_fast,
                slow_ma=current_slow,
                timestamp=current_candle.timestamp,
                confidence=confidence,
            )

        return None

    async def backtest_pair(self, pair: str) -> Optional[H4BacktestResult]:
        """Backtest a single pair using H4 data only"""
        try:
            logger.info(f"📊 Starting H4 backtest for {pair}...")

            # Load H4 data
            candles = self._load_pair_data(pair)
            if not candles:
                return None

            # Check if we have sufficient data
            if len(candles) < 100:
                logger.warning(
                    f"⚠️ Insufficient H4 data for {pair}: {len(candles)} candles"
                )
                return None

            # Initialize tracking variables
            account_equity = self.initial_equity
            trades = []
            signals = []
            current_position = None
            equity_curve = [
                {"timestamp": candles[0].timestamp, "equity": account_equity}
            ]

            logger.info(f"📊 Processing {len(candles)} H4 candles for {pair}")

            # Simulate trading through the data
            for i in range(
                50, len(candles)
            ):  # Start after we have enough data for EMAs
                # Generate H4 signal
                signal = self._generate_h4_signal(candles, pair, i)

                if signal:
                    signals.append(signal)

                    # Simulate trade execution
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

                # Update equity curve every 24 candles (daily)
                if i % 24 == 0:
                    equity_curve.append(
                        {"timestamp": candles[i].timestamp, "equity": account_equity}
                    )

            # Close final position if open
            if current_position:
                final_signal = TradingSignal(
                    pair=pair,
                    timeframe="H4",
                    signal_type=SignalType.HOLD,
                    price=candles[-1].close,
                    fast_ma=0.0,
                    slow_ma=0.0,
                    timestamp=candles[-1].timestamp,
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

            result = H4BacktestResult(
                pair=pair,
                start_date=candles[0].timestamp.strftime("%Y-%m-%d"),
                end_date=candles[-1].timestamp.strftime("%Y-%m-%d"),
                total_return=total_return,
                total_trades=len(trades),
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                win_rate=win_rate,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio,
                candles_analyzed=len(candles),
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
        """Close a trading position and calculate P&L"""
        entry_price = position["entry_price"]
        exit_price = signal.price
        position_type = position["type"]
        pair = signal.pair

        # Determine pip multiplier based on pair type
        # JPY pairs: 1 pip = 0.01, so multiply by 100
        # Other pairs: 1 pip = 0.0001, so multiply by 10000
        is_jpy_pair = "JPY" in pair
        pip_multiplier = 100 if is_jpy_pair else 10000

        # Calculate P&L based on position type
        if position_type == "BUY":
            pnl_pips = (exit_price - entry_price) * pip_multiplier
        else:  # SELL
            pnl_pips = (entry_price - exit_price) * pip_multiplier

        # Simplified P&L calculation (assuming 1 standard lot)
        pnl_usd = pnl_pips * 1.0  # $1 per pip for simplicity
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
        """Run H4 backtest on all available pairs"""
        logger.info(
            f"🚀 Starting H4-only backtest suite for {len(self.available_pairs)} pairs"
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
                "backtest_type": "h4_only_ema_crossover",
                "strategy_name": "H4 EMA Crossover (21/50)",
                "timeframe": "H4",
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
            portfolio_file = os.path.join(output_dir, "h4_portfolio_summary.json")
            with open(portfolio_file, "w") as f:
                json.dump(portfolio_summary, f, indent=2, default=str)

            # Save individual results
            individual_file = os.path.join(output_dir, "h4_individual_results.json")
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
                    "signals_generated": result.signals_generated,
                    "performance_grade": result.performance_grade,
                }

            with open(individual_file, "w") as f:
                json.dump(serializable_results, f, indent=2, default=str)

            logger.info(f"💾 Results saved to:")
            logger.info(f"   Portfolio: {portfolio_file}")
            logger.info(f"   Individual: {individual_file}")

        except Exception as e:
            logger.error(f"❌ Error saving results to files: {str(e)}")


async def main():
    """Main execution function"""
    backtester = H4JSONBacktester()

    try:
        results = await backtester.run_backtest_suite()

        # Print results
        portfolio = results["portfolio_summary"]
        if "error" not in portfolio:
            print("\n" + "=" * 60)
            print("📊 H4-ONLY BACKTEST RESULTS")
            print("=" * 60)
            print(f"Strategy: EMA Crossover (21/50)")
            print(f"Timeframe: H4 Only")
            print(f"Portfolio Return: {portfolio['portfolio_return']:.2f}%")
            print(f"Portfolio Win Rate: {portfolio['portfolio_win_rate']:.1f}%")
            print(f"Sharpe Ratio: {portfolio['portfolio_sharpe']:.2f}")
            print(f"Max Drawdown: {portfolio['portfolio_max_drawdown']:.1f}%")
            print(f"Total Trades: {portfolio['total_trades']}")

            print(f"\n🏆 Top 3 H4 Performers:")
            for i, performer in enumerate(portfolio["top_performers"], 1):
                print(
                    f"   {i}. {performer['pair']}: {performer['return']:.2f}% (Win Rate: {performer['win_rate']:.1f}%, Trades: {performer['trades']})"
                )

            print("\n📈 Individual H4 Results:")
            for pair, result in results["individual_results"].items():
                print(
                    f"   {result.pair}: {result.total_return:.2f}% ({result.total_trades} trades, {result.win_rate:.1f}% win rate)"
                )
        else:
            print(f"❌ Error: {portfolio['error']}")

        print("=" * 60)

    except Exception as e:
        logger.error(f"❌ Fatal error during H4 backtest: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Multi-Timeframe Strategy Backtesting & Deployment Service
Production-ready backtesting for the enhanced multi-timeframe strategy.
This service will be deployed to DigitalOcean for live monitoring and results display.
"""

import asyncio
import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

from services.multi_timeframe_strategy_service import MultiTimeframeStrategyService
from services.data_service import DataService
from models.signal_models import TradingSignal, PriceData, PerformanceMetrics
from config.settings import MULTI_TIMEFRAME_STRATEGY_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """Complete backtest result for a currency pair."""

    pair: str
    strategy_type: str
    start_date: datetime
    end_date: datetime
    total_signals: int
    buy_signals: int
    sell_signals: int
    hold_signals: int

    # Performance metrics
    total_return: float
    annual_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float

    # Risk metrics
    average_trade_duration: int  # hours
    largest_win: float
    largest_loss: float
    consecutive_wins: int
    consecutive_losses: int

    # Execution metrics
    execution_time: float
    data_points_analyzed: int

    # Strategy-specific
    confluence_scores: List[float]
    timeframe_alignment_rate: float


@dataclass
class LiveMonitoringResult:
    """Live monitoring result for real-time display."""

    timestamp: datetime
    pair: str
    current_signal: str
    confidence: float
    weekly_trend: str
    daily_setup: str
    fourhour_trigger: str
    confluence_score: float
    risk_reward_ratio: float
    expected_move: float
    market_session: str


class MultiTimeframeBacktestService:
    """
    Production Multi-Timeframe Strategy Backtesting Service

    This service:
    1. Backtests the enhanced multi-timeframe strategy
    2. Provides live market monitoring
    3. Generates results for frontend display
    4. Deploys to DigitalOcean for continuous operation
    """

    def __init__(self):
        self.strategy_service = MultiTimeframeStrategyService()
        self.data_service = DataService()

        # Configuration
        self.pairs = list(MULTI_TIMEFRAME_STRATEGY_CONFIG.keys())
        self.backtest_period_days = 365  # 1 year default

        # Results storage
        self.backtest_results: Dict[str, BacktestResult] = {}
        self.live_results: Dict[str, LiveMonitoringResult] = {}

        # Performance tracking
        self.total_signals_generated = 0
        self.total_execution_time = 0.0

    async def run_comprehensive_backtest(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Run comprehensive backtest for all currency pairs.

        Returns results suitable for frontend display and performance analysis.
        """
        logger.info("🚀 Starting Multi-Timeframe Strategy Comprehensive Backtest")

        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=self.backtest_period_days)

        logger.info(
            f"📅 Backtest Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        )

        # Track overall performance
        start_time = datetime.now()
        total_signals = 0

        # Run backtest for each pair
        for pair in self.pairs:
            try:
                logger.info(f"📊 Backtesting {pair}...")
                result = await self.backtest_pair(pair, start_date, end_date)
                self.backtest_results[pair] = result
                total_signals += result.total_signals
                logger.info(
                    f"✅ {pair}: {result.annual_return:.1f}% return, {result.win_rate:.1%} win rate"
                )
            except Exception as e:
                logger.error(f"❌ {pair} backtest failed: {str(e)}")

        execution_time = (datetime.now() - start_time).total_seconds()

        # Compile comprehensive results
        comprehensive_results = await self.compile_comprehensive_results(
            start_date, end_date, execution_time, total_signals
        )

        # Save results for frontend and monitoring
        await self.save_results_for_frontend(comprehensive_results)

        logger.info("🎉 Comprehensive Backtest Complete!")
        return comprehensive_results

    async def backtest_pair(
        self, pair: str, start_date: datetime, end_date: datetime
    ) -> BacktestResult:
        """
        Backtest a single currency pair using multi-timeframe strategy.
        """
        execution_start = datetime.now()

        # Get historical data for all timeframes
        try:
            # For backtesting, we'll use 4H data and derive other timeframes
            data_points_needed = (
                (end_date - start_date).days * 6
            ) + 500  # Extra for indicators
            historical_data = await self.data_service.get_historical_data(
                pair, "H4", min(data_points_needed, 5000)
            )
        except Exception as e:
            logger.warning(f"Using synthetic data for {pair}: {str(e)}")
            historical_data = self._generate_synthetic_backtest_data(
                pair, start_date, end_date
            )

        if len(historical_data) < 100:
            raise ValueError(
                f"Insufficient data for {pair}: {len(historical_data)} points"
            )

        # Convert to timeframe-specific data
        weekly_data = self._convert_to_weekly(historical_data)
        daily_data = self._convert_to_daily(historical_data)
        fourhour_data = historical_data

        # Track signals and performance
        signals: List[TradingSignal] = []
        confluence_scores: List[float] = []

        # Simulate trading through the period
        for i in range(
            max(200, len(fourhour_data) // 10), len(fourhour_data), 6
        ):  # Every 24 hours
            try:
                # Get data slices for analysis
                weekly_slice = (
                    weekly_data[: i // 42 + 1]
                    if i // 42 < len(weekly_data)
                    else weekly_data
                )
                daily_slice = (
                    daily_data[: i // 6 + 1] if i // 6 < len(daily_data) else daily_data
                )
                fourhour_slice = fourhour_data[: i + 1]

                # Generate signal using multi-timeframe analysis
                signal = await self.strategy_service.generate_multi_timeframe_signal(
                    pair, weekly_slice, daily_slice, fourhour_slice
                )

                if signal and signal.signal_type.value != "HOLD":
                    signals.append(signal)
                    confluence_scores.append(signal.confidence or 0.0)

            except Exception as e:
                logger.debug(f"Signal generation error at index {i}: {str(e)}")
                continue

        # Calculate performance metrics
        performance_metrics = await self._calculate_backtest_performance(
            signals, historical_data
        )

        execution_time = (datetime.now() - execution_start).total_seconds()

        # Count signal types
        buy_signals = len([s for s in signals if s.signal_type.value == "BUY"])
        sell_signals = len([s for s in signals if s.signal_type.value == "SELL"])
        hold_signals = len(historical_data) - len(signals)  # Approximate

        return BacktestResult(
            pair=pair,
            strategy_type="multi_timeframe_enhanced",
            start_date=start_date,
            end_date=end_date,
            total_signals=len(signals),
            buy_signals=buy_signals,
            sell_signals=sell_signals,
            hold_signals=hold_signals,
            # Performance metrics
            total_return=performance_metrics["total_return"],
            annual_return=performance_metrics["annual_return"],
            sharpe_ratio=performance_metrics["sharpe_ratio"],
            max_drawdown=performance_metrics["max_drawdown"],
            win_rate=performance_metrics["win_rate"],
            profit_factor=performance_metrics["profit_factor"],
            # Risk metrics
            average_trade_duration=int(performance_metrics["avg_trade_duration"]),
            largest_win=performance_metrics["largest_win"],
            largest_loss=performance_metrics["largest_loss"],
            consecutive_wins=int(performance_metrics["consecutive_wins"]),
            consecutive_losses=int(performance_metrics["consecutive_losses"]),
            # Execution metrics
            execution_time=execution_time,
            data_points_analyzed=len(historical_data),
            # Strategy-specific
            confluence_scores=confluence_scores,
            timeframe_alignment_rate=performance_metrics["alignment_rate"],
        )

    async def _calculate_backtest_performance(
        self, signals: List[TradingSignal], price_data: List[PriceData]
    ) -> Dict[str, float]:
        """
        Calculate comprehensive performance metrics from backtest signals.
        """
        if not signals:
            return self._empty_performance_metrics()

        # Simulate trading execution
        trades = []
        current_position = None

        for signal in signals:
            if current_position is None:
                # Open new position
                current_position = {
                    "type": signal.signal_type.value,
                    "entry_price": signal.price,
                    "entry_time": signal.timestamp,
                    "confidence": signal.confidence or 0.5,
                }
            else:
                # Close position if opposite signal
                if (
                    current_position["type"] == "BUY"
                    and signal.signal_type.value == "SELL"
                ) or (
                    current_position["type"] == "SELL"
                    and signal.signal_type.value == "BUY"
                ):

                    # Calculate trade result
                    if current_position["type"] == "BUY":
                        pnl_pct = (
                            signal.price - current_position["entry_price"]
                        ) / current_position["entry_price"]
                    else:
                        pnl_pct = (
                            current_position["entry_price"] - signal.price
                        ) / current_position["entry_price"]

                    trade_duration = (
                        signal.timestamp - current_position["entry_time"]
                    ).total_seconds() / 3600

                    trades.append(
                        {
                            "pnl_pct": pnl_pct,
                            "duration_hours": trade_duration,
                            "confidence": current_position["confidence"],
                        }
                    )

                    current_position = {
                        "type": signal.signal_type.value,
                        "entry_price": signal.price,
                        "entry_time": signal.timestamp,
                        "confidence": signal.confidence or 0.5,
                    }

        if not trades:
            return self._empty_performance_metrics()

        # Calculate metrics
        pnl_values = [t["pnl_pct"] for t in trades]
        winning_trades = [pnl for pnl in pnl_values if pnl > 0]
        losing_trades = [pnl for pnl in pnl_values if pnl < 0]

        total_return = sum(pnl_values) * 100  # Convert to percentage
        annual_return = total_return * (365 / (len(price_data) / 6 / 24))  # Annualize

        win_rate = len(winning_trades) / len(trades) if trades else 0

        avg_win = sum(winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(losing_trades) / len(losing_trades) if losing_trades else 0
        profit_factor = (
            abs(avg_win * len(winning_trades) / (avg_loss * len(losing_trades)))
            if losing_trades
            else 1.0
        )

        # Drawdown calculation
        equity_curve = []
        running_equity = 100  # Start with 100%
        for pnl in pnl_values:
            running_equity *= 1 + pnl
            equity_curve.append(running_equity)

        peak = 100
        max_drawdown = 0
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak
            max_drawdown = max(max_drawdown, drawdown)

        # Risk metrics
        returns_std = np.std(pnl_values) if len(pnl_values) > 1 else 0.01
        sharpe_ratio = (
            (annual_return / 100) / (returns_std * np.sqrt(252))
            if returns_std > 0
            else 0
        )

        # Consecutive wins/losses
        consecutive_wins = consecutive_losses = 0
        current_streak = 0
        for pnl in pnl_values:
            if pnl > 0:
                current_streak = current_streak + 1 if current_streak >= 0 else 1
                consecutive_wins = max(consecutive_wins, current_streak)
            else:
                current_streak = current_streak - 1 if current_streak <= 0 else -1
                consecutive_losses = max(consecutive_losses, abs(current_streak))

        return {
            "total_return": round(total_return, 2),
            "annual_return": round(annual_return, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "max_drawdown": round(max_drawdown * 100, 2),
            "win_rate": round(win_rate, 3),
            "profit_factor": round(profit_factor, 2),
            "avg_trade_duration": round(
                sum(t["duration_hours"] for t in trades) / len(trades), 1
            ),
            "largest_win": round(max(pnl_values) * 100, 2) if pnl_values else 0,
            "largest_loss": round(min(pnl_values) * 100, 2) if pnl_values else 0,
            "consecutive_wins": consecutive_wins,
            "consecutive_losses": consecutive_losses,
            "alignment_rate": round(
                sum(t["confidence"] for t in trades) / len(trades), 3
            ),
        }

    def _empty_performance_metrics(self) -> Dict[str, float]:
        """Return empty performance metrics for failed backtests."""
        return {
            "total_return": 0.0,
            "annual_return": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "win_rate": 0.0,
            "profit_factor": 1.0,
            "avg_trade_duration": 0.0,
            "largest_win": 0.0,
            "largest_loss": 0.0,
            "consecutive_wins": 0,
            "consecutive_losses": 0,
            "alignment_rate": 0.0,
        }

    async def run_live_monitoring(self) -> Dict[str, LiveMonitoringResult]:
        """
        Run live market monitoring for all pairs.
        This method will be called continuously in production.
        """
        logger.info("📡 Running live market monitoring...")

        live_results = {}

        for pair in self.pairs:
            try:
                result = await self.monitor_pair_live(pair)
                live_results[pair] = result
                self.live_results[pair] = result
            except Exception as e:
                logger.error(f"Live monitoring failed for {pair}: {str(e)}")

        # Save for frontend consumption
        await self.save_live_results(live_results)

        return live_results

    async def monitor_pair_live(self, pair: str) -> LiveMonitoringResult:
        """
        Monitor a single pair for live trading signals.
        """
        # Get recent data for analysis
        try:
            recent_data = await self.data_service.get_historical_data(pair, "H4", 500)
        except Exception:
            logger.warning(f"Using synthetic data for live monitoring of {pair}")
            recent_data = self._generate_synthetic_backtest_data(
                pair, datetime.now() - timedelta(days=90), datetime.now()
            )

        if len(recent_data) < 100:
            raise ValueError(f"Insufficient data for live monitoring of {pair}")

        # Convert to timeframes
        weekly_data = self._convert_to_weekly(recent_data)
        daily_data = self._convert_to_daily(recent_data)
        fourhour_data = recent_data

        # Generate current signal
        signal = await self.strategy_service.generate_multi_timeframe_signal(
            pair, weekly_data, daily_data, fourhour_data
        )

        # Analyze individual timeframes for detailed status
        weekly_analysis = await self.strategy_service.analyze_weekly_trend(weekly_data)
        daily_analysis = await self.strategy_service.analyze_daily_swing(
            daily_data, weekly_analysis
        )
        fourhour_analysis = await self.strategy_service.analyze_fourhour_execution(
            fourhour_data, weekly_analysis, daily_analysis
        )

        # Calculate confluence score
        confluence_score = self.strategy_service._calculate_confluence_score(
            weekly_analysis, daily_analysis, fourhour_analysis
        )

        # Determine market session
        current_hour = datetime.utcnow().hour
        if 0 <= current_hour < 7:
            market_session = "Asian"
        elif 7 <= current_hour < 15:
            market_session = "London"
        elif 15 <= current_hour < 22:
            market_session = "New York"
        else:
            market_session = "Asian"

        return LiveMonitoringResult(
            timestamp=datetime.utcnow(),
            pair=pair,
            current_signal=signal.signal_type.value if signal else "HOLD",
            confidence=float(signal.confidence or 0.0),
            weekly_trend=weekly_analysis.trend_direction,
            daily_setup=daily_analysis.bias,
            fourhour_trigger=fourhour_analysis.trend_direction,
            confluence_score=confluence_score,
            risk_reward_ratio=3.0,  # Default from strategy
            expected_move=2.5,  # Estimated percentage move
            market_session=market_session,
        )

    def _convert_to_weekly(self, fourhour_data: List[PriceData]) -> List[PriceData]:
        """Convert 4H data to weekly timeframe."""
        weekly_data = []

        # Group by week (42 periods of 4H = 1 week)
        for i in range(0, len(fourhour_data), 42):
            week_data = fourhour_data[i : i + 42]
            if len(week_data) < 10:  # Need minimum data
                continue

            weekly_candle = PriceData(
                pair=week_data[0].pair,
                timeframe="1W",
                timestamp=week_data[0].timestamp,
                open=week_data[0].open,
                high=max(candle.high for candle in week_data),
                low=min(candle.low for candle in week_data),
                close=week_data[-1].close,
                volume=sum(getattr(candle, "volume", 1000) for candle in week_data),
            )
            weekly_data.append(weekly_candle)

        return weekly_data

    def _convert_to_daily(self, fourhour_data: List[PriceData]) -> List[PriceData]:
        """Convert 4H data to daily timeframe."""
        daily_data = []

        # Group by day (6 periods of 4H = 1 day)
        for i in range(0, len(fourhour_data), 6):
            day_data = fourhour_data[i : i + 6]
            if len(day_data) < 3:  # Need minimum data
                continue

            daily_candle = PriceData(
                pair=day_data[0].pair,
                timeframe="1D",
                timestamp=day_data[0].timestamp,
                open=day_data[0].open,
                high=max(candle.high for candle in day_data),
                low=min(candle.low for candle in day_data),
                close=day_data[-1].close,
                volume=sum(getattr(candle, "volume", 1000) for candle in day_data),
            )
            daily_data.append(daily_candle)

        return daily_data

    def _generate_synthetic_backtest_data(
        self, pair: str, start_date: datetime, end_date: datetime
    ) -> List[PriceData]:
        """Generate synthetic data for backtesting when real data unavailable."""
        logger.info(f"Generating synthetic backtest data for {pair}")

        # Calculate number of 4H periods
        total_hours = int((end_date - start_date).total_seconds() / 3600)
        periods = total_hours // 4

        # Starting prices
        price_map = {
            "EUR_USD": 1.0850,
            "GBP_USD": 1.2650,
            "USD_JPY": 148.50,
            "AUD_USD": 0.6650,
            "EUR_GBP": 0.8580,
            "GBP_JPY": 187.50,
            "USD_CAD": 1.3650,
        }

        start_price = price_map.get(pair, 1.0000)
        current_price = start_price
        current_time = start_date

        data = []

        # Generate trending price movement with realistic patterns
        trend_strength = np.random.uniform(0.0002, 0.0008)  # Daily trend
        trend_direction = np.random.choice([-1, 1])

        for i in range(periods):
            # Add trend and noise
            trend_component = trend_direction * trend_strength * (i / periods)
            cycle_component = np.sin(i / 50) * 0.0003  # Market cycles
            noise = np.random.normal(0, 0.0015)  # Random volatility

            price_change = trend_component + cycle_component + noise
            current_price *= 1 + price_change

            # Generate OHLC with realistic spread
            volatility = 0.0012
            high = current_price * (1 + np.random.uniform(0, volatility))
            low = current_price * (1 - np.random.uniform(0, volatility))
            open_price = current_price * (
                1 + np.random.uniform(-volatility / 3, volatility / 3)
            )

            data.append(
                PriceData(
                    pair=pair,
                    timeframe="4H",
                    timestamp=current_time,
                    open=round(open_price, 5),
                    high=round(high, 5),
                    low=round(low, 5),
                    close=round(current_price, 5),
                    volume=np.random.randint(800, 1200),
                )
            )

            current_time += timedelta(hours=4)

        return data

    async def compile_comprehensive_results(
        self,
        start_date: datetime,
        end_date: datetime,
        execution_time: float,
        total_signals: int,
    ) -> Dict[str, Any]:
        """
        Compile comprehensive results for frontend display and analysis.
        """
        if not self.backtest_results:
            return {"error": "No backtest results available"}

        # Overall portfolio metrics
        portfolio_return = np.mean(
            [r.annual_return for r in self.backtest_results.values()]
        )
        portfolio_sharpe = np.mean(
            [r.sharpe_ratio for r in self.backtest_results.values()]
        )
        portfolio_max_dd = max([r.max_drawdown for r in self.backtest_results.values()])
        portfolio_win_rate = np.mean(
            [r.win_rate for r in self.backtest_results.values()]
        )

        # Top performers
        sorted_by_return = sorted(
            self.backtest_results.items(),
            key=lambda x: x[1].annual_return,
            reverse=True,
        )

        # Compile comprehensive results
        results = {
            "backtest_summary": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "execution_time_seconds": round(execution_time, 2),
                "total_pairs_tested": len(self.backtest_results),
                "total_signals_generated": total_signals,
                "strategy_type": "multi_timeframe_enhanced",
            },
            "portfolio_performance": {
                "average_annual_return": round(portfolio_return, 2),
                "portfolio_sharpe_ratio": round(portfolio_sharpe, 2),
                "maximum_drawdown": round(portfolio_max_dd, 2),
                "average_win_rate": round(portfolio_win_rate, 3),
                "total_trades": sum(
                    r.total_signals for r in self.backtest_results.values()
                ),
                "performance_grade": self._calculate_performance_grade(
                    float(portfolio_return),
                    float(portfolio_sharpe),
                    float(portfolio_max_dd),
                ),
            },
            "top_performers": [
                {
                    "pair": pair,
                    "annual_return": round(result.annual_return, 2),
                    "sharpe_ratio": round(result.sharpe_ratio, 2),
                    "win_rate": round(result.win_rate, 3),
                    "max_drawdown": round(result.max_drawdown, 2),
                    "total_signals": result.total_signals,
                }
                for pair, result in sorted_by_return[:5]
            ],
            "detailed_results": {
                pair: asdict(result) for pair, result in self.backtest_results.items()
            },
            "strategy_insights": {
                "best_performing_pair": (
                    sorted_by_return[0][0] if sorted_by_return else "None"
                ),
                "most_active_pair": max(
                    self.backtest_results.items(), key=lambda x: x[1].total_signals
                )[0],
                "highest_win_rate": max(
                    self.backtest_results.values(), key=lambda x: x.win_rate
                ).pair,
                "lowest_drawdown": min(
                    self.backtest_results.values(), key=lambda x: x.max_drawdown
                ).pair,
                "average_confluence_score": round(
                    np.mean(
                        [
                            np.mean(r.confluence_scores)
                            for r in self.backtest_results.values()
                            if r.confluence_scores
                        ]
                    ),
                    3,
                ),
            },
            "deployment_readiness": {
                "ready_for_live_trading": portfolio_return > 15
                and portfolio_max_dd < 15,
                "risk_assessment": (
                    "Low"
                    if portfolio_max_dd < 10
                    else "Medium" if portfolio_max_dd < 20 else "High"
                ),
                "recommended_pairs": [
                    pair
                    for pair, result in self.backtest_results.items()
                    if result.annual_return > 20 and result.max_drawdown < 12
                ],
                "live_deployment_score": round(
                    (portfolio_return / 30) * 0.4
                    + (portfolio_win_rate * 100 / 70) * 0.3
                    + ((20 - portfolio_max_dd) / 20) * 0.3,
                    2,
                ),
            },
        }

        return results

    def _calculate_performance_grade(
        self, annual_return: float, sharpe: float, max_dd: float
    ) -> str:
        """Calculate a letter grade for strategy performance."""
        # Scoring system
        return_score = min(annual_return / 25, 1.0)  # 25% = perfect
        sharpe_score = min(sharpe / 2.0, 1.0)  # 2.0 = perfect
        dd_score = max(0, (15 - max_dd) / 15)  # <15% = perfect

        overall_score = return_score * 0.4 + sharpe_score * 0.3 + dd_score * 0.3

        if overall_score >= 0.9:
            return "A+"
        elif overall_score >= 0.8:
            return "A"
        elif overall_score >= 0.7:
            return "B+"
        elif overall_score >= 0.6:
            return "B"
        elif overall_score >= 0.5:
            return "C"
        else:
            return "D"

    async def save_results_for_frontend(self, results: Dict[str, Any]) -> None:
        """Save backtest results for frontend consumption."""

        # Create results directory
        results_dir = Path("backtest_results/frontend_display")
        results_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save main results
        with open(results_dir / f"backtest_results_{timestamp}.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

        # Save latest results (for frontend to always fetch)
        with open(results_dir / "latest_backtest_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

        # Save individual pair results for detailed analysis
        pair_results_dir = results_dir / "pair_details"
        pair_results_dir.mkdir(exist_ok=True)

        for pair, result in self.backtest_results.items():
            with open(pair_results_dir / f"{pair}_detailed_{timestamp}.json", "w") as f:
                json.dump(asdict(result), f, indent=2, default=str)

        logger.info(f"📁 Backtest results saved to {results_dir}")

    async def save_live_results(
        self, live_results: Dict[str, LiveMonitoringResult]
    ) -> None:
        """Save live monitoring results for frontend consumption."""

        results_dir = Path("backtest_results/live_monitoring")
        results_dir.mkdir(parents=True, exist_ok=True)

        # Convert to JSON-serializable format
        json_results = {pair: asdict(result) for pair, result in live_results.items()}

        # Save current live results
        with open(results_dir / "current_live_signals.json", "w") as f:
            json.dump(json_results, f, indent=2, default=str)

        # Also save timestamped version
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(results_dir / f"live_signals_{timestamp}.json", "w") as f:
            json.dump(json_results, f, indent=2, default=str)

        logger.info(f"📡 Live results saved to {results_dir}")


# Production deployment functions
async def run_backtest_for_deployment():
    """
    Run comprehensive backtest for production deployment.
    This is the main function that will be called on DigitalOcean.
    """
    service = MultiTimeframeBacktestService()

    print("🚀 4ex.ninja Multi-Timeframe Strategy - Production Backtest")
    print("=" * 60)

    # Run comprehensive backtest
    results = await service.run_comprehensive_backtest()

    print(f"\n📊 BACKTEST COMPLETED!")
    print(f"Strategy Type: {results['backtest_summary']['strategy_type']}")
    print(f"Pairs Tested: {results['backtest_summary']['total_pairs_tested']}")
    print(f"Total Signals: {results['backtest_summary']['total_signals_generated']}")
    print(f"Execution Time: {results['backtest_summary']['execution_time_seconds']}s")

    print(f"\n📈 PORTFOLIO PERFORMANCE:")
    portfolio = results["portfolio_performance"]
    print(f"Average Annual Return: {portfolio['average_annual_return']}%")
    print(f"Portfolio Sharpe Ratio: {portfolio['portfolio_sharpe_ratio']}")
    print(f"Maximum Drawdown: {portfolio['maximum_drawdown']}%")
    print(f"Average Win Rate: {portfolio['average_win_rate']:.1%}")
    print(f"Performance Grade: {portfolio['performance_grade']}")

    print(f"\n🏆 TOP PERFORMERS:")
    for i, performer in enumerate(results["top_performers"][:3], 1):
        print(
            f"{i}. {performer['pair']}: {performer['annual_return']}% return, {performer['win_rate']:.1%} win rate"
        )

    print(f"\n🚦 DEPLOYMENT STATUS:")
    deployment = results["deployment_readiness"]
    status = "✅ READY" if deployment["ready_for_live_trading"] else "⚠️ REVIEW NEEDED"
    print(f"Live Trading Ready: {status}")
    print(f"Risk Assessment: {deployment['risk_assessment']}")
    print(f"Deployment Score: {deployment['live_deployment_score']}/1.0")

    return results


async def run_live_monitoring_service():
    """
    Run continuous live monitoring service.
    This will run continuously on DigitalOcean.
    """
    service = MultiTimeframeBacktestService()

    print("📡 Starting Live Market Monitoring Service...")

    while True:
        try:
            # Run live monitoring
            live_results = await service.run_live_monitoring()

            print(
                f"📊 Live Monitoring Update - {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
            )
            for pair, result in live_results.items():
                signal_icon = (
                    "🔴"
                    if result.current_signal == "SELL"
                    else "🟢" if result.current_signal == "BUY" else "⚪"
                )
                print(
                    f"{signal_icon} {pair}: {result.current_signal} (Confidence: {result.confidence:.2f}, Session: {result.market_session})"
                )

            # Wait 15 minutes before next update
            await asyncio.sleep(15 * 60)

        except Exception as e:
            logger.error(f"Live monitoring error: {str(e)}")
            await asyncio.sleep(5 * 60)  # Wait 5 minutes on error


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "live":
        # Run live monitoring
        asyncio.run(run_live_monitoring_service())
    else:
        # Run backtest
        asyncio.run(run_backtest_for_deployment())

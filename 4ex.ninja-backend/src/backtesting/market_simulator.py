"""
Market Simulator for Universal Backtesting Framework.

This module simulates realistic market conditions for backtesting,
providing data feeds and market environment simulation for ANY strategy type.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from .strategy_interface import BaseStrategy, TradeSignal
from .models import Trade
from .regime_detector import RegimeDetector, MarketRegime
from .data_infrastructure import DataInfrastructure
from .data_quality_monitor import DataQualityMonitor

logger = logging.getLogger(__name__)


@dataclass
class MarketConditions:
    """Current market conditions for simulation."""

    regime: MarketRegime
    volatility_level: float  # 0.0 to 1.0
    trend_strength: float  # -1.0 to 1.0 (negative = downtrend)
    liquidity_level: float  # 0.0 to 1.0
    spread_multiplier: float  # Multiplier for normal spreads
    session_type: str  # "london", "newyork", "tokyo", "overlap", "quiet"


@dataclass
class SimulationConfig:
    """Market simulation configuration."""

    enable_news_events: bool = True
    enable_session_effects: bool = True
    enable_weekend_gaps: bool = True
    enable_holiday_effects: bool = True
    liquidity_model: str = "session_based"  # "session_based" or "constant"
    volatility_clustering: bool = True
    spread_variation: bool = True


@dataclass
class MultiPairBacktestResult:
    """Results from multi-pair backtesting simulation."""

    strategy_name: str
    pair_results: Dict[str, Any]
    portfolio_analysis: Dict[str, Any]
    regime_correlation: Dict[str, Any]
    total_trades: int = 0
    total_pnl: float = 0.0
    sharpe_ratio: Optional[float] = None
    max_drawdown: float = 0.0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class MarketSimulator:
    """
    Universal market simulator for backtesting.

    Provides realistic market environment simulation that works with
    ANY strategy type, including multi-pair and multi-timeframe scenarios.
    """

    def __init__(
        self,
        data_infrastructure: Optional[DataInfrastructure] = None,
        config: Optional[SimulationConfig] = None,
    ):
        """
        Initialize market simulator.

        Args:
            data_infrastructure: Data infrastructure for market data
            config: Simulation configuration
        """
        self.data_infrastructure = data_infrastructure or DataInfrastructure()
        self.config = config or SimulationConfig()
        self.regime_detector = RegimeDetector()
        # Note: DataQualityMonitor requires providers, so we'll skip it for now
        # self.quality_monitor = DataQualityMonitor([])

        logger.info("MarketSimulator initialized")

    def simulate_trading_session(
        self,
        strategy: BaseStrategy,
        start_date: datetime,
        end_date: datetime,
        pairs: List[str],
        timeframe: str = "4H",
    ) -> MultiPairBacktestResult:
        """
        Simulate a complete trading session across multiple pairs.

        Args:
            strategy: Strategy to test
            start_date: Simulation start date
            end_date: Simulation end date
            pairs: Currency pairs to trade
            timeframe: Chart timeframe

        Returns:
            Multi-pair backtest results
        """
        try:
            logger.info(f"Starting multi-pair simulation for {strategy.strategy_name}")
            logger.info(f"Pairs: {pairs}, Period: {start_date} to {end_date}")

            pair_results = {}
            total_trades = 0
            total_pnl = 0.0

            # Simulate each pair independently
            for pair in pairs:
                logger.info(f"Simulating {pair}")

                # Get market data for this pair
                market_data = self._get_market_data(
                    pair, timeframe, start_date, end_date
                )

                if market_data.empty:
                    logger.warning(f"No data available for {pair}")
                    continue

                # Run strategy simulation for this pair
                pair_result = self._simulate_pair_trading(
                    strategy, pair, market_data, start_date, end_date
                )

                pair_results[pair] = pair_result
                total_trades += pair_result.get("total_trades", 0)
                total_pnl += pair_result.get("total_pnl", 0.0)

            # Analyze portfolio performance
            portfolio_analysis = self._analyze_portfolio_performance(pair_results)

            # Analyze regime correlation across pairs
            regime_correlation = self._analyze_regime_correlation_across_pairs(
                pair_results
            )

            return MultiPairBacktestResult(
                strategy_name=strategy.strategy_name,
                pair_results=pair_results,
                portfolio_analysis=portfolio_analysis,
                regime_correlation=regime_correlation,
                total_trades=total_trades,
                total_pnl=total_pnl,
                sharpe_ratio=portfolio_analysis.get("sharpe_ratio"),
                max_drawdown=portfolio_analysis.get("max_drawdown", 0.0),
                start_date=start_date,
                end_date=end_date,
            )

        except Exception as e:
            logger.error(f"Error in trading session simulation: {e}")
            return MultiPairBacktestResult(
                strategy_name=strategy.strategy_name,
                pair_results={},
                portfolio_analysis={},
                regime_correlation={},
            )

    def simulate_market_conditions(
        self, market_data: pd.DataFrame, current_time: datetime
    ) -> MarketConditions:
        """
        Simulate realistic market conditions for a given time.

        Args:
            market_data: Current market data
            current_time: Current simulation time

        Returns:
            Simulated market conditions
        """
        try:
            # Detect current regime
            regime = self._detect_current_regime(market_data)

            # Calculate market metrics
            volatility_level = self._calculate_volatility_level(market_data)
            trend_strength = self._calculate_trend_strength(market_data)
            liquidity_level = self._calculate_liquidity_level(current_time)
            spread_multiplier = self._calculate_spread_multiplier(
                regime, volatility_level
            )
            session_type = self._determine_session_type(current_time)

            return MarketConditions(
                regime=regime,
                volatility_level=volatility_level,
                trend_strength=trend_strength,
                liquidity_level=liquidity_level,
                spread_multiplier=spread_multiplier,
                session_type=session_type,
            )

        except Exception as e:
            logger.error(f"Error simulating market conditions: {e}")
            # Return default conditions
            return MarketConditions(
                regime=MarketRegime.UNCERTAIN,
                volatility_level=0.5,
                trend_strength=0.0,
                liquidity_level=0.5,
                spread_multiplier=1.0,
                session_type="quiet",
            )

    def _get_market_data(
        self, pair: str, timeframe: str, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """
        Get market data for simulation.
        """
        try:
            # Use placeholder for data infrastructure (will be enhanced later)
            # data = self.data_infrastructure.get_historical_data(
            #     pair, timeframe, start_date, end_date
            # )

            # For now, generate synthetic data directly
            logger.info(f"Generating synthetic data for {pair}")
            data = self._generate_synthetic_data(pair, timeframe, start_date, end_date)

            if data.empty:
                # Generate synthetic data if real data unavailable
                logger.warning(f"No real data for {pair}, generating synthetic data")
                data = self._generate_synthetic_data(
                    pair, timeframe, start_date, end_date
                )

            return data

        except Exception as e:
            logger.warning(f"Error getting market data for {pair}: {e}")
            # Fallback to synthetic data
            return self._generate_synthetic_data(pair, timeframe, start_date, end_date)

    def _generate_synthetic_data(
        self, pair: str, timeframe: str, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """
        Generate synthetic market data for simulation.
        """
        # Determine frequency based on timeframe
        if timeframe == "4H":
            freq = "4H"
        elif timeframe == "1D":
            freq = "D"
        elif timeframe == "1H":
            freq = "H"
        else:
            freq = "4H"

        # Generate time series
        date_range = pd.date_range(start=start_date, end=end_date, freq=freq)

        # Base price (different for each pair)
        base_prices = {
            "EURUSD": 1.1000,
            "GBPUSD": 1.3000,
            "USDJPY": 110.00,
            "AUDUSD": 0.7500,
            "USDCAD": 1.2500,
            "NZDUSD": 0.7000,
            "USDCHF": 0.9200,
        }

        base_price = base_prices.get(pair, 1.1000)

        # Generate realistic price movement
        n_periods = len(date_range)
        returns = np.random.normal(0, 0.01, n_periods)  # 1% daily volatility

        # Add some trend and mean reversion
        trend = np.cumsum(np.random.normal(0, 0.001, n_periods))
        returns += trend * 0.1

        # Calculate prices
        prices = base_price * np.exp(np.cumsum(returns))

        # Generate OHLC data
        data = []
        for i, (timestamp, close) in enumerate(zip(date_range, prices)):
            # Generate realistic OHLC based on close price
            volatility = abs(returns[i])
            range_size = volatility * close * 2

            # Open is previous close (or base for first candle)
            open_price = prices[i - 1] if i > 0 else close

            # High and low around the range
            high = max(open_price, close) + np.random.uniform(0, range_size / 2)
            low = min(open_price, close) - np.random.uniform(0, range_size / 2)

            # Ensure OHLC consistency
            high = max(high, open_price, close)
            low = min(low, open_price, close)

            data.append(
                {
                    "timestamp": timestamp,
                    "open": round(open_price, 5),
                    "high": round(high, 5),
                    "low": round(low, 5),
                    "close": round(close, 5),
                    "volume": np.random.randint(1000, 10000),
                }
            )

        return pd.DataFrame(data)

    def _simulate_pair_trading(
        self,
        strategy: BaseStrategy,
        pair: str,
        market_data: pd.DataFrame,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """
        Simulate trading for a single currency pair.
        """
        try:
            # Placeholder regime detection (simplified for now)
            # regime_periods = self.regime_detector.detect_regime_periods_for_data(market_data)

            # Create a simple regime mapping based on volatility
            regime_periods = self._create_simple_regime_periods(market_data)

            all_trades = []
            total_pnl = 0.0

            # Process each regime period
            for regime in regime_periods:
                periods = regime_periods[regime]

                for period_start, period_end in periods:
                    # Get data for this period
                    period_mask = (market_data["timestamp"] >= period_start) & (
                        market_data["timestamp"] <= period_end
                    )
                    period_data = market_data[period_mask].copy()

                    if period_data.empty:
                        continue

                    # Generate signals for this period
                    signals = strategy.generate_signals(period_data, regime)

                    # Convert signals to trades (simplified simulation)
                    for signal in signals:
                        trade = self._create_trade_from_signal(signal, pair)

                        # Simulate trade execution in this period data
                        executed_trade = self._simulate_trade_in_period(
                            trade, period_data
                        )

                        if executed_trade.pnl is not None:
                            all_trades.append(executed_trade)
                            total_pnl += executed_trade.pnl

            # Calculate performance metrics
            return {
                "pair": pair,
                "total_trades": len(all_trades),
                "winning_trades": len([t for t in all_trades if t.pnl and t.pnl > 0]),
                "losing_trades": len([t for t in all_trades if t.pnl and t.pnl < 0]),
                "total_pnl": total_pnl,
                "win_rate": (
                    len([t for t in all_trades if t.pnl and t.pnl > 0])
                    / len(all_trades)
                    if all_trades
                    else 0
                ),
                "trades": all_trades,
                "regime_performance": self._analyze_regime_performance_for_pair(
                    all_trades, regime_periods
                ),
            }

        except Exception as e:
            logger.error(f"Error simulating trading for {pair}: {e}")
            return {
                "pair": pair,
                "total_trades": 0,
                "total_pnl": 0.0,
                "win_rate": 0.0,
                "trades": [],
                "error": str(e),
            }

    def _detect_current_regime(self, market_data: pd.DataFrame) -> MarketRegime:
        """
        Detect current market regime from data.
        """
        try:
            # Simplified regime detection for now
            # detection_result = self.regime_detector.detect_regime_periods_for_data(market_data)

            # Return a simple default regime
            return MarketRegime.TRENDING_LOW_VOL

        except Exception as e:
            logger.warning(f"Error detecting regime: {e}")
            return MarketRegime.UNCERTAIN

    def _calculate_volatility_level(self, market_data: pd.DataFrame) -> float:
        """
        Calculate current volatility level (0.0 to 1.0).
        """
        if market_data.empty or len(market_data) < 20:
            return 0.5

        # Calculate 20-period ATR
        high_low = market_data["high"] - market_data["low"]
        high_close = abs(market_data["high"] - market_data["close"].shift(1))
        low_close = abs(market_data["low"] - market_data["close"].shift(1))

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = (
            true_range.rolling(20).mean().iloc[-1]
            if len(true_range) >= 20
            else true_range.mean()
        )

        # Normalize to 0-1 scale (simplified)
        avg_price = market_data["close"].iloc[-1]
        volatility_ratio = atr / avg_price if avg_price > 0 else 0

        return min(1.0, max(0.0, volatility_ratio * 100))  # Scale appropriately

    def _calculate_trend_strength(self, market_data: pd.DataFrame) -> float:
        """
        Calculate trend strength (-1.0 to 1.0).
        """
        if market_data.empty or len(market_data) < 20:
            return 0.0

        # Simple trend calculation using moving averages
        ma_fast = market_data["close"].rolling(10).mean()
        ma_slow = market_data["close"].rolling(20).mean()

        if ma_fast.iloc[-1] > ma_slow.iloc[-1]:
            # Uptrend - calculate strength
            trend_strength = (ma_fast.iloc[-1] - ma_slow.iloc[-1]) / ma_slow.iloc[-1]
            return min(1.0, trend_strength * 100)
        else:
            # Downtrend - calculate strength
            trend_strength = (ma_slow.iloc[-1] - ma_fast.iloc[-1]) / ma_slow.iloc[-1]
            return max(-1.0, -trend_strength * 100)

    def _calculate_liquidity_level(self, current_time: datetime) -> float:
        """
        Calculate liquidity level based on trading session.
        """
        hour = current_time.hour

        # London session (8-16 GMT): High liquidity
        if 8 <= hour < 16:
            return 1.0
        # New York session (13-21 GMT): High liquidity
        elif 13 <= hour < 21:
            return 1.0
        # London-NY overlap (13-16 GMT): Maximum liquidity
        elif 13 <= hour < 16:
            return 1.0
        # Tokyo session (0-9 GMT): Medium liquidity
        elif 0 <= hour < 9:
            return 0.7
        # Quiet periods: Low liquidity
        else:
            return 0.3

    def _calculate_spread_multiplier(
        self, regime: MarketRegime, volatility: float
    ) -> float:
        """
        Calculate spread multiplier based on market conditions.
        """
        base_multiplier = 1.0

        # Increase spreads in high volatility regimes
        if regime in [MarketRegime.TRENDING_HIGH_VOL, MarketRegime.RANGING_HIGH_VOL]:
            base_multiplier *= 1.5

        # Additional volatility adjustment
        volatility_multiplier = 1.0 + (volatility * 0.5)

        return base_multiplier * volatility_multiplier

    def _determine_session_type(self, current_time: datetime) -> str:
        """
        Determine current trading session type.
        """
        hour = current_time.hour

        if 13 <= hour < 16:
            return "overlap"  # London-NY overlap
        elif 8 <= hour < 16:
            return "london"
        elif 13 <= hour < 21:
            return "newyork"
        elif 0 <= hour < 9:
            return "tokyo"
        else:
            return "quiet"

    def _create_trade_from_signal(self, signal: TradeSignal, pair: str) -> Trade:
        """
        Create a trade object from a trade signal.
        """
        return Trade(
            entry_time=signal.signal_time,
            exit_time=None,
            pair=pair,
            direction=signal.direction,
            entry_price=signal.entry_price,
            exit_price=None,
            position_size=10000,  # Default position size
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            strategy_name=signal.strategy_name,
        )

    def _simulate_trade_in_period(
        self, trade: Trade, period_data: pd.DataFrame
    ) -> Trade:
        """
        Simulate trade execution within a specific period.
        """
        # Find entry point
        entry_idx = None
        for i, row in period_data.iterrows():
            if row["timestamp"] >= trade.entry_time:
                entry_idx = i
                break

        if entry_idx is None:
            trade.exit_time = trade.entry_time
            trade.exit_price = trade.entry_price
            trade.pnl = 0.0
            trade.exit_reason = "NO_ENTRY"
            return trade

        # Simulate trade progression
        try:
            entry_idx_pos = period_data.index.get_loc(entry_idx)

            # Handle different return types from get_loc
            if isinstance(entry_idx_pos, int):
                start_pos = entry_idx_pos
            elif isinstance(entry_idx_pos, slice):
                start_pos = entry_idx_pos.start or 0
            else:
                # For boolean array or other types, find first True
                if hasattr(entry_idx_pos, "argmax"):
                    start_pos = int(entry_idx_pos.argmax())
                else:
                    start_pos = 0
        except (KeyError, ValueError):
            start_pos = 0

        for i in range(start_pos, len(period_data)):
            row = period_data.iloc[i]

            if trade.direction == "BUY":
                if row["low"] <= trade.stop_loss:
                    trade.exit_time = row["timestamp"]
                    trade.exit_price = trade.stop_loss
                    trade.exit_reason = "SL"
                    break
                elif row["high"] >= trade.take_profit:
                    trade.exit_time = row["timestamp"]
                    trade.exit_price = trade.take_profit
                    trade.exit_reason = "TP"
                    break
            else:  # SELL
                if row["high"] >= trade.stop_loss:
                    trade.exit_time = row["timestamp"]
                    trade.exit_price = trade.stop_loss
                    trade.exit_reason = "SL"
                    break
                elif row["low"] <= trade.take_profit:
                    trade.exit_time = row["timestamp"]
                    trade.exit_price = trade.take_profit
                    trade.exit_reason = "TP"
                    break

        # Calculate P&L if trade was closed
        if trade.exit_price is not None:
            if trade.direction == "BUY":
                price_diff = trade.exit_price - trade.entry_price
            else:
                price_diff = trade.entry_price - trade.exit_price

            trade.pnl = price_diff * trade.position_size
            trade.pnl_pips = price_diff / 0.0001  # Convert to pips
        else:
            # Trade still open at end of period
            last_price = period_data.iloc[-1]["close"]
            trade.exit_time = period_data.iloc[-1]["timestamp"]
            trade.exit_price = last_price
            trade.exit_reason = "TIME"

            if trade.direction == "BUY":
                price_diff = last_price - trade.entry_price
            else:
                price_diff = trade.entry_price - last_price

            trade.pnl = price_diff * trade.position_size
            trade.pnl_pips = price_diff / 0.0001

        return trade

    def _analyze_portfolio_performance(
        self, pair_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze performance across all pairs in the portfolio.
        """
        if not pair_results:
            return {}

        total_trades = sum(
            result.get("total_trades", 0) for result in pair_results.values()
        )
        total_pnl = sum(
            result.get("total_pnl", 0.0) for result in pair_results.values()
        )
        winning_trades = sum(
            result.get("winning_trades", 0) for result in pair_results.values()
        )

        portfolio_win_rate = winning_trades / total_trades if total_trades > 0 else 0

        return {
            "total_trades": total_trades,
            "total_pnl": total_pnl,
            "win_rate": portfolio_win_rate,
            "number_of_pairs": len(pair_results),
            "avg_pnl_per_pair": total_pnl / len(pair_results) if pair_results else 0,
            "pair_performance": {
                pair: result.get("total_pnl", 0)
                for pair, result in pair_results.items()
            },
        }

    def _analyze_regime_correlation_across_pairs(
        self, pair_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze how regimes correlate across different currency pairs.
        """
        regime_analysis = {}

        for pair, result in pair_results.items():
            if "regime_performance" in result:
                regime_analysis[pair] = result["regime_performance"]

        return {
            "pair_regime_analysis": regime_analysis,
            "cross_pair_correlation": "Analysis placeholder - requires more sophisticated correlation calculation",
        }

    def _analyze_regime_performance_for_pair(
        self,
        trades: List[Trade],
        regime_periods: Dict[MarketRegime, List[Tuple[datetime, datetime]]],
    ) -> Dict[str, Any]:
        """
        Analyze performance by regime for a specific pair.
        """
        regime_performance = {}

        for regime in regime_periods:
            regime_trades = []

            # Match trades to regime periods
            for trade in trades:
                for period_start, period_end in regime_periods[regime]:
                    if (
                        trade.entry_time >= period_start
                        and trade.entry_time <= period_end
                    ):
                        regime_trades.append(trade)
                        break

            if regime_trades:
                regime_pnl = sum(t.pnl for t in regime_trades if t.pnl)
                regime_performance[regime.value] = {
                    "trades": len(regime_trades),
                    "pnl": regime_pnl,
                    "win_rate": len([t for t in regime_trades if t.pnl and t.pnl > 0])
                    / len(regime_trades),
                }

        return regime_performance

    def _create_simple_regime_periods(
        self, market_data: pd.DataFrame
    ) -> Dict[MarketRegime, List[Tuple[datetime, datetime]]]:
        """
        Create simple regime periods based on basic market analysis.
        This is a placeholder until full regime detection is integrated.
        """
        if market_data.empty:
            return {}

        # For simplicity, create one regime period covering the entire dataset
        start_time = market_data["timestamp"].min()
        end_time = market_data["timestamp"].max()

        # Simple volatility analysis to determine regime
        if len(market_data) > 20:
            returns = market_data["close"].pct_change().dropna()
            volatility = returns.std()

            if volatility > 0.02:  # High volatility threshold
                regime = MarketRegime.TRENDING_HIGH_VOL
            else:
                regime = MarketRegime.TRENDING_LOW_VOL
        else:
            regime = MarketRegime.UNCERTAIN

        return {regime: [(start_time, end_time)]}

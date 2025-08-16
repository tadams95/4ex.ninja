"""
Universal Backtesting Engine for 4ex.ninja Framework.

This module provides a strategy-agnostic backtesting engine that can work with
ANY strategy implementing the BaseStrategy interface, integrating with existing
Phase 2 infrastructure for regime detection and performance analysis.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import pandas as pd

from .strategy_interface import BaseStrategy, TradeSignal, AccountInfo
from .regime_detector import RegimeDetector, MarketRegime, RegimeDetectionResult
from .data_infrastructure import DataInfrastructure
from .data_quality_monitor import DataQualityMonitor, DataValidationReport, QualityIssue

logger = logging.getLogger(__name__)


@dataclass
class BacktestDataset:
    """Prepared dataset for backtesting."""

    data: pd.DataFrame
    quality_report: DataValidationReport
    provider_info: Dict[str, Any]
    regime_periods: Optional[Dict[MarketRegime, List[Tuple[datetime, datetime]]]] = None


@dataclass
class Trade:
    """Executed trade record."""

    entry_time: datetime
    exit_time: Optional[datetime]
    pair: str
    direction: str
    entry_price: float
    exit_price: Optional[float]
    position_size: float
    stop_loss: float
    take_profit: float
    pnl: Optional[float] = None
    pnl_pips: Optional[float] = None
    exit_reason: Optional[str] = None  # "TP", "SL", "TIME", "MANUAL"
    strategy_name: str = ""
    regime: Optional[MarketRegime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BacktestResult:
    """Results from backtesting a strategy."""

    trades: List[Trade]
    strategy_name: str
    pair: str
    timeframe: str
    start_date: datetime
    end_date: datetime
    initial_balance: float
    final_balance: float
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    regime_analysis: Optional[Dict[str, Any]] = None
    data_quality: Optional[DataValidationReport] = None


@dataclass
class MultiPairBacktestResult:
    """Results from multi-pair backtesting."""

    strategy_name: str
    pair_results: Dict[str, BacktestResult]
    portfolio_analysis: Dict[str, Any] = field(default_factory=dict)
    regime_correlation: Dict[str, Any] = field(default_factory=dict)


class BacktestDataManager:
    """
    Data manager that leverages existing Phase 2 infrastructure.
    """

    def __init__(self):
        """Initialize with existing infrastructure components."""
        self.data_infrastructure = DataInfrastructure()
        # Initialize quality monitor with empty provider list for now
        # Will be enhanced when actual providers are available
        self.quality_monitor = None
        self.regime_detector = RegimeDetector()

    async def prepare_backtest_data(
        self, pair: str, timeframe: str, start_date: datetime, end_date: datetime
    ) -> BacktestDataset:
        """
        Prepare and validate data for backtesting using existing infrastructure.

        Args:
            pair: Currency pair (e.g., "EURUSD")
            timeframe: Timeframe (e.g., "4H", "1D")
            start_date: Start date for data
            end_date: End date for data

        Returns:
            BacktestDataset with validated data and quality report
        """
        try:
            # Use existing data infrastructure to get historical data
            logger.info(
                f"Preparing backtest data for {pair} {timeframe} from {start_date} to {end_date}"
            )

            # For now, create simulated data structure until actual method is available
            raw_data = await self._get_historical_data_wrapper(
                pair=pair, timeframe=timeframe, start_date=start_date, end_date=end_date
            )

            # Create basic quality report
            quality_report = self._create_basic_quality_report(
                raw_data, pair, timeframe
            )

            # Handle quality issues
            cleaned_data = self._handle_quality_issues(raw_data, quality_report)

            # Get provider status (simplified)
            provider_info = {"status": "active", "provider": "simulated"}

            return BacktestDataset(
                data=cleaned_data,
                quality_report=quality_report,
                provider_info=provider_info,
            )

        except Exception as e:
            logger.error(f"Error preparing backtest data: {e}")
            raise

    async def _get_historical_data_wrapper(
        self, pair: str, timeframe: str, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """
        Wrapper to get historical data - adapts to existing infrastructure.
        """
        # TODO: Integrate with actual data infrastructure methods once available
        # For now, create a basic structure that matches expected format

        # Generate time series for the period
        if timeframe == "4H":
            freq = "4H"
        elif timeframe == "1D":
            freq = "D"
        elif timeframe == "1H":
            freq = "H"
        else:
            freq = "4H"  # Default

        date_range = pd.date_range(start=start_date, end=end_date, freq=freq)

        # Create basic OHLCV structure (will be replaced with real data)
        data = pd.DataFrame(
            {
                "timestamp": date_range,
                "open": 1.1000 + pd.Series(range(len(date_range))) * 0.0001,
                "high": 1.1010 + pd.Series(range(len(date_range))) * 0.0001,
                "low": 1.0990 + pd.Series(range(len(date_range))) * 0.0001,
                "close": 1.1005 + pd.Series(range(len(date_range))) * 0.0001,
                "volume": 1000,
            }
        )

        return data

    def _create_basic_quality_report(
        self, data: pd.DataFrame, pair: str, timeframe: str
    ) -> DataValidationReport:
        """
        Create a basic quality report.
        """
        return DataValidationReport(
            pair=pair,
            timeframe=timeframe,
            period_start=data["timestamp"].min() if not data.empty else datetime.now(),
            period_end=data["timestamp"].max() if not data.empty else datetime.now(),
            total_candles=len(data),
            expected_candles=len(data),
            missing_candles=0,
            gap_percentage=0.0,
            outlier_count=0,
            price_anomalies=[],
            volume_anomalies=[],
            spread_consistency=1.0,
            provider_comparison={},
            issues=[],
            overall_quality_score=1.0,
        )

    def _handle_quality_issues(
        self, data: pd.DataFrame, quality_report: DataValidationReport
    ) -> pd.DataFrame:
        """
        Handle data quality issues identified by quality monitor.

        Args:
            data: Raw market data
            quality_report: Quality validation report

        Returns:
            Cleaned market data
        """
        cleaned_data = data.copy()

        # Handle gaps in data
        if quality_report.issues:
            for issue in quality_report.issues:
                if (
                    hasattr(issue, "alert_level")
                    and issue.alert_level.value == "critical"
                ):
                    logger.warning(f"Critical data issue: {issue.description}")
                    # For now, just log issues - could implement specific fixes

        return cleaned_data


class UniversalBacktestingEngine:
    """
    Strategy-agnostic backtesting engine that works with ANY strategy.

    This engine integrates with existing Phase 2 infrastructure for regime
    detection, data management, and performance analysis.
    """

    def __init__(self):
        """Initialize with existing infrastructure components."""
        self.data_manager = BacktestDataManager()
        self.regime_detector = RegimeDetector()

    async def run_backtest(
        self,
        strategy: BaseStrategy,
        pair: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        initial_balance: float = 10000.0,
    ) -> BacktestResult:
        """
        Run universal backtesting that works with ANY strategy implementation.

        Args:
            strategy: Strategy implementing BaseStrategy interface
            pair: Currency pair to backtest
            timeframe: Timeframe for backtesting
            start_date: Start date for backtest
            end_date: End date for backtest
            initial_balance: Starting account balance

        Returns:
            BacktestResult with trade history and performance metrics
        """
        try:
            logger.info(
                f"Starting backtest for {strategy.strategy_name} on {pair} {timeframe}"
            )

            # Prepare data using existing infrastructure
            dataset = await self.data_manager.prepare_backtest_data(
                pair, timeframe, start_date, end_date
            )

            # Detect regimes using existing engine
            regime_periods = await self._detect_regime_periods(
                dataset.data, start_date, end_date
            )
            dataset.regime_periods = regime_periods

            # Initialize account
            account_info = AccountInfo(
                balance=initial_balance,
                equity=initial_balance,
                margin_used=0.0,
                free_margin=initial_balance,
                max_position_size=initial_balance * 0.1,  # Max 10% per trade
            )

            all_trades = []
            current_balance = initial_balance

            # Process each regime period
            for regime, periods in regime_periods.items():
                logger.info(f"Processing {regime} regime with {len(periods)} periods")

                for period_start, period_end in periods:
                    period_data = self._get_period_data(
                        dataset.data, period_start, period_end
                    )

                    if period_data.empty:
                        continue

                    # Generate signals using the strategy's implementation
                    signals = strategy.generate_signals(period_data, regime)

                    # Execute trades using universal execution engine
                    period_trades = await self._execute_signals(
                        signals, period_data, strategy, account_info, regime
                    )

                    # Update account balance
                    for trade in period_trades:
                        if trade.pnl is not None:
                            current_balance += trade.pnl
                            account_info.balance = current_balance
                            account_info.equity = current_balance

                    all_trades.extend(period_trades)

            # Calculate performance metrics
            performance_metrics = self._calculate_performance_metrics(
                all_trades, initial_balance
            )

            # Analyze regime performance
            regime_analysis = self._analyze_regime_performance(
                all_trades, regime_periods
            )

            return BacktestResult(
                trades=all_trades,
                strategy_name=strategy.strategy_name,
                pair=pair,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                initial_balance=initial_balance,
                final_balance=current_balance,
                performance_metrics=performance_metrics,
                regime_analysis=regime_analysis,
                data_quality=dataset.quality_report,
            )

        except Exception as e:
            logger.error(f"Error in backtesting: {e}")
            raise

    async def _detect_regime_periods(
        self, data: pd.DataFrame, start_date: datetime, end_date: datetime
    ) -> Dict[MarketRegime, List[Tuple[datetime, datetime]]]:
        """
        Detect regime periods using existing regime detector.

        Args:
            data: Market data
            start_date: Start date
            end_date: End date

        Returns:
            Dictionary mapping regimes to time periods
        """
        try:
            # Use existing regime detector - simplified for now
            # TODO: Integrate with actual regime detector methods when available
            logger.info("Detecting regime periods")

            # For now, create a single uncertain period until actual implementation
            return {MarketRegime.UNCERTAIN: [(start_date, end_date)]}

        except Exception as e:
            logger.warning(f"Error detecting regimes: {e}, using single period")
            # Fallback to single period if regime detection fails
            return {MarketRegime.UNCERTAIN: [(start_date, end_date)]}

    async def _execute_signals(
        self,
        signals: List[TradeSignal],
        market_data: pd.DataFrame,
        strategy: BaseStrategy,
        account_info: AccountInfo,
        regime: MarketRegime,
    ) -> List[Trade]:
        """
        Execute signals using universal execution logic.

        Args:
            signals: List of trade signals
            market_data: Market data for execution
            strategy: Strategy instance
            account_info: Account information
            regime: Current market regime

        Returns:
            List of executed trades
        """
        executed_trades = []

        for signal in signals:
            try:
                # Validate signal using strategy's validation logic
                if not strategy.validate_signal(signal, market_data):
                    logger.debug(
                        f"Signal validation failed for {signal.pair} at {signal.signal_time}"
                    )
                    continue

                # Calculate position size using strategy's logic
                position_size = strategy.calculate_position_size(signal, account_info)

                if position_size <= 0:
                    logger.debug(f"Position size <= 0 for signal: {position_size}")
                    continue

                # Create trade record
                trade = Trade(
                    entry_time=signal.signal_time,
                    exit_time=None,
                    pair=signal.pair,
                    direction=signal.direction,
                    entry_price=signal.entry_price,
                    exit_price=None,
                    position_size=position_size,
                    stop_loss=signal.stop_loss,
                    take_profit=signal.take_profit,
                    strategy_name=strategy.strategy_name,
                    regime=regime,
                    metadata=signal.metadata or {},
                )

                # Simulate trade execution (simplified for swing trading)
                executed_trade = self._simulate_trade_execution(trade, market_data)
                executed_trades.append(executed_trade)

            except Exception as e:
                logger.error(f"Error executing signal: {e}")
                continue

        return executed_trades

    def _simulate_trade_execution(
        self, trade: Trade, market_data: pd.DataFrame
    ) -> Trade:
        """
        Simulate trade execution for swing trading (simplified model).

        Args:
            trade: Trade to simulate
            market_data: Market data

        Returns:
            Trade with execution results
        """
        # Find data after entry time
        entry_idx = None
        for i, row in market_data.iterrows():
            if row["timestamp"] >= trade.entry_time:
                entry_idx = i
                break

        if entry_idx is None:
            # No data after entry time
            trade.exit_time = trade.entry_time
            trade.exit_price = trade.entry_price
            trade.pnl = 0.0
            trade.pnl_pips = 0.0
            trade.exit_reason = "NO_DATA"
            return trade

        # Simulate trade progression
        entry_idx_int = entry_idx if isinstance(entry_idx, int) else 0
        for i in range(entry_idx_int, len(market_data)):
            row = market_data.iloc[i]

            if trade.direction == "BUY":
                # Check stop loss
                if row["low"] <= trade.stop_loss:
                    trade.exit_time = row["timestamp"]
                    trade.exit_price = trade.stop_loss
                    trade.exit_reason = "SL"
                    break
                # Check take profit
                elif row["high"] >= trade.take_profit:
                    trade.exit_time = row["timestamp"]
                    trade.exit_price = trade.take_profit
                    trade.exit_reason = "TP"
                    break
            else:  # SELL
                # Check stop loss
                if row["high"] >= trade.stop_loss:
                    trade.exit_time = row["timestamp"]
                    trade.exit_price = trade.stop_loss
                    trade.exit_reason = "SL"
                    break
                # Check take profit
                elif row["low"] <= trade.take_profit:
                    trade.exit_time = row["timestamp"]
                    trade.exit_price = trade.take_profit
                    trade.exit_reason = "TP"
                    break

        # If trade didn't exit, close at last available price
        if trade.exit_time is None:
            last_row = market_data.iloc[-1]
            trade.exit_time = last_row["timestamp"]
            trade.exit_price = last_row["close"]
            trade.exit_reason = "TIME"

        # Calculate P&L
        if trade.exit_price is not None:
            if trade.direction == "BUY":
                trade.pnl = (trade.exit_price - trade.entry_price) * trade.position_size
                trade.pnl_pips = (
                    trade.exit_price - trade.entry_price
                ) * 10000  # Assuming 4-digit quotes
            else:
                trade.pnl = (trade.entry_price - trade.exit_price) * trade.position_size
                trade.pnl_pips = (trade.entry_price - trade.exit_price) * 10000

        return trade

    def _get_period_data(
        self, data: pd.DataFrame, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """
        Extract data for specific time period.

        Args:
            data: Full dataset
            start_date: Period start
            end_date: Period end

        Returns:
            Data for the specified period
        """
        mask = (data["timestamp"] >= start_date) & (data["timestamp"] <= end_date)
        return data[mask].copy()

    def _calculate_performance_metrics(
        self, trades: List[Trade], initial_balance: float
    ) -> Dict[str, Any]:
        """
        Calculate basic performance metrics.

        Args:
            trades: List of executed trades
            initial_balance: Initial account balance

        Returns:
            Dictionary of performance metrics
        """
        if not trades:
            return {"total_trades": 0, "total_pnl": 0.0}

        # Filter trades with valid P&L and extract the values
        valid_pnl_values = [trade.pnl for trade in trades if trade.pnl is not None]
        total_pnl = sum(valid_pnl_values) if valid_pnl_values else 0.0

        winning_pnl = [pnl for pnl in valid_pnl_values if pnl > 0]
        losing_pnl = [pnl for pnl in valid_pnl_values if pnl < 0]

        # Calculate averages safely
        avg_win = sum(winning_pnl) / len(winning_pnl) if winning_pnl else 0
        avg_loss = sum(losing_pnl) / len(losing_pnl) if losing_pnl else 0

        # Calculate profit factor safely
        total_wins = sum(winning_pnl) if winning_pnl else 0
        total_losses = abs(sum(losing_pnl)) if losing_pnl else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else 0

        return {
            "total_trades": len(trades),
            "winning_trades": len(winning_pnl),
            "losing_trades": len(losing_pnl),
            "win_rate": (
                len(winning_pnl) / len(valid_pnl_values) if valid_pnl_values else 0
            ),
            "total_pnl": total_pnl,
            "total_return": total_pnl / initial_balance if initial_balance > 0 else 0,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": profit_factor,
        }

    def _analyze_regime_performance(
        self,
        trades: List[Trade],
        regime_periods: Dict[MarketRegime, List[Tuple[datetime, datetime]]],
    ) -> Dict[str, Any]:
        """
        Analyze performance by market regime.

        Args:
            trades: List of trades
            regime_periods: Regime periods

        Returns:
            Regime performance analysis
        """
        regime_performance = {}

        for regime in regime_periods.keys():
            regime_trades = [t for t in trades if t.regime == regime]
            if regime_trades:
                regime_performance[regime.value] = self._calculate_performance_metrics(
                    regime_trades,
                    0,  # Don't calculate return percentage for regime analysis
                )

        return regime_performance

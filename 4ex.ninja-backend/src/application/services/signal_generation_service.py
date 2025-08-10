"""
Signal generation service using repository pattern.

This service migrates the existing signal generation logic to use the new
repository pattern for clean separation of concerns and dependency injection.
"""

from ...infrastructure.logging import get_logger
import pandas as pd
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Optional, List
from uuid import uuid4

from ...core.entities.signal import Signal, SignalType, SignalStatus, CrossoverType
from ...core.entities.market_data import MarketData, Candle
from ...core.interfaces.signal_repository import ISignalRepository
from ...core.interfaces.market_data_repository import IMarketDataRepository
from ...infrastructure.configuration.repository_config import RepositoryServiceProvider

# Import existing monitoring and error handling
from ...infrastructure.monitoring.alerts import (
    alert_signal_processing_failure,
    alert_database_connectivity,
)
from ...infrastructure.monitoring.dashboards import (
    metrics_collector,
    record_signal_generated,
)
from ...strategies.error_handling import (
    validate_market_data,
    validate_signal_data,
)

logger = get_logger(__name__)


class SignalGenerationService:
    """
    Signal generation service using repository pattern.

    This service provides signal generation functionality using the repository
    pattern for data access, replacing direct database operations.
    """

    def __init__(self, repository_provider: RepositoryServiceProvider):
        """
        Initialize the signal generation service.

        Args:
            repository_provider: Repository service provider for DI
        """
        self.repository_provider = repository_provider

    async def generate_signals_for_strategy(
        self,
        pair: str,
        timeframe: str,
        strategy_name: str,
        fast_ma: int,
        slow_ma: int,
        atr_multiplier_sl: float = 2.0,
        atr_multiplier_tp: float = 3.0,
    ) -> List[Signal]:
        """
        Generate signals for a trading strategy using repository pattern.

        Args:
            pair: Currency pair (e.g., "EUR_USD")
            timeframe: Timeframe (e.g., "H4", "D")
            strategy_name: Name of the strategy
            fast_ma: Fast moving average period
            slow_ma: Slow moving average period
            atr_multiplier_sl: ATR multiplier for stop loss
            atr_multiplier_tp: ATR multiplier for take profit

        Returns:
            List of generated signals
        """
        try:
            logger.info(
                "Starting signal generation",
                extra={
                    "pair": pair,
                    "timeframe": timeframe,
                    "strategy": strategy_name,
                    "fast_ma": fast_ma,
                    "slow_ma": slow_ma,
                    "atr_multiplier_sl": atr_multiplier_sl,
                    "atr_multiplier_tp": atr_multiplier_tp,
                },
            )

            # Get market data repository
            market_data_repo = (
                await self.repository_provider.get_market_data_repository()
            )

            # Fetch market data for the pair and timeframe
            criteria = {"instrument": pair, "granularity": timeframe}
            market_data_list = await market_data_repo.find_by_criteria(
                criteria, limit=500
            )

            if not market_data_list:
                logger.warning(
                    "No market data found",
                    extra={"pair": pair, "timeframe": timeframe, "data_count": 0},
                )
                return []

            logger.debug(
                "Market data retrieved",
                extra={
                    "pair": pair,
                    "timeframe": timeframe,
                    "data_count": len(market_data_list),
                },
            )

            # Convert market data to DataFrame for signal calculation
            df = self._convert_market_data_to_dataframe(market_data_list)

            if df.empty:
                logger.warning(
                    "No candle data available after conversion",
                    extra={"pair": pair, "timeframe": timeframe},
                )
                return []

            logger.debug(
                "Market data converted to DataFrame",
                extra={
                    "pair": pair,
                    "timeframe": timeframe,
                    "df_shape": df.shape,
                    "date_range": {
                        "start": str(df.index.min()) if not df.empty else None,
                        "end": str(df.index.max()) if not df.empty else None,
                    },
                },
            )

            # Calculate moving averages and signals
            df = self._calculate_moving_averages(df, fast_ma, slow_ma)
            df = self._calculate_atr(df)
            df = self._generate_crossover_signals(df)
            df = self._calculate_stop_loss_take_profit(
                df, atr_multiplier_sl, atr_multiplier_tp
            )

            # Convert DataFrame signals to Signal entities
            signals = await self._convert_signals_to_entities(
                df,
                pair,
                timeframe,
                strategy_name,
                fast_ma,
                slow_ma,
                atr_multiplier_sl,
                atr_multiplier_tp,
            )

            # Store signals using repository
            await self._store_signals(signals)

            logger.info(
                "Signal generation completed successfully",
                extra={
                    "pair": pair,
                    "timeframe": timeframe,
                    "strategy": strategy_name,
                    "signals_generated": len(signals),
                    "signal_types": (
                        [s.signal_type.value for s in signals] if signals else []
                    ),
                },
            )

            # Track metrics
            metrics_collector.set_gauge(
                "signals_generated_current",
                len(signals),
                {"pair": pair, "timeframe": timeframe, "strategy": strategy_name},
            )

            return signals

        except Exception as e:
            error_msg = f"Error generating signals for {pair} {timeframe}: {str(e)}"
            logger.error(
                "Signal generation failed",
                extra={
                    "pair": pair,
                    "timeframe": timeframe,
                    "strategy": strategy_name,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            await alert_signal_processing_failure(error_msg)

            metrics_collector.increment_counter(
                "signal_generation_errors",
                1,
                {"pair": pair, "timeframe": timeframe, "strategy": strategy_name},
            )
            return []

    def _convert_market_data_to_dataframe(
        self, market_data_list: List[MarketData]
    ) -> pd.DataFrame:
        """
        Convert MarketData entities to pandas DataFrame.

        Args:
            market_data_list: List of MarketData entities

        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Collect all candles from all market data
            candles_data = []
            for market_data in market_data_list:
                for candle in market_data.candles:
                    candles_data.append(
                        {
                            "time": candle.time,
                            "open": float(candle.open),
                            "high": float(candle.high),
                            "low": float(candle.low),
                            "close": float(candle.close),
                            "volume": candle.volume,
                        }
                    )

            if not candles_data:
                return pd.DataFrame()

            # Create DataFrame and set time as index
            df = pd.DataFrame(candles_data)
            df.set_index("time", inplace=True)
            df.sort_index(inplace=True)

            return df

        except Exception as e:
            logger.error(f"Error converting market data to DataFrame: {e}")
            return pd.DataFrame()

    def _calculate_moving_averages(
        self, df: pd.DataFrame, fast_ma: int, slow_ma: int
    ) -> pd.DataFrame:
        """Calculate moving averages."""
        try:
            df["fast_ma"] = df["close"].rolling(window=fast_ma).mean()
            df["slow_ma"] = df["close"].rolling(window=slow_ma).mean()
            return df
        except Exception as e:
            logger.error(f"Error calculating moving averages: {e}")
            return df

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Calculate Average True Range."""
        try:
            df["prev_close"] = df["close"].shift(1)
            df["tr1"] = df["high"] - df["low"]
            df["tr2"] = abs(df["high"] - df["prev_close"])
            df["tr3"] = abs(df["low"] - df["prev_close"])
            df["tr"] = df[["tr1", "tr2", "tr3"]].max(axis=1)
            df["atr"] = df["tr"].rolling(window=period).mean()

            # Clean up intermediate columns
            df.drop(["prev_close", "tr1", "tr2", "tr3", "tr"], axis=1, inplace=True)

            return df
        except Exception as e:
            logger.error(f"Error calculating ATR: {e}")
            return df

    def _generate_crossover_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate crossover signals based on moving averages."""
        try:
            # Initialize signal column
            df["signal"] = 0
            df["crossover_type"] = ""

            # Calculate crossovers
            df["fast_above_slow"] = df["fast_ma"] > df["slow_ma"]
            df["prev_fast_above_slow"] = df["fast_above_slow"].shift(1)

            # Bullish crossover (fast MA crosses above slow MA)
            bullish_crossover = (df["fast_above_slow"] == True) & (
                df["prev_fast_above_slow"] == False
            )
            df.loc[bullish_crossover, "signal"] = 1
            df.loc[bullish_crossover, "crossover_type"] = "BULLISH"

            # Bearish crossover (fast MA crosses below slow MA)
            bearish_crossover = (df["fast_above_slow"] == False) & (
                df["prev_fast_above_slow"] == True
            )
            df.loc[bearish_crossover, "signal"] = -1
            df.loc[bearish_crossover, "crossover_type"] = "BEARISH"

            # Clean up intermediate columns
            df.drop(["fast_above_slow", "prev_fast_above_slow"], axis=1, inplace=True)

            return df
        except Exception as e:
            logger.error(f"Error generating crossover signals: {e}")
            return df

    def _calculate_stop_loss_take_profit(
        self, df: pd.DataFrame, atr_multiplier_sl: float, atr_multiplier_tp: float
    ) -> pd.DataFrame:
        """Calculate stop loss and take profit levels."""
        try:
            # Initialize columns
            df["stop_loss"] = 0.0
            df["take_profit"] = 0.0
            df["risk_reward_ratio"] = 0.0

            # Calculate for buy signals
            buy_signals = df["signal"] == 1
            df.loc[buy_signals, "stop_loss"] = df.loc[buy_signals, "close"] - (
                df.loc[buy_signals, "atr"] * atr_multiplier_sl
            )
            df.loc[buy_signals, "take_profit"] = df.loc[buy_signals, "close"] + (
                df.loc[buy_signals, "atr"] * atr_multiplier_tp
            )

            # Calculate for sell signals
            sell_signals = df["signal"] == -1
            df.loc[sell_signals, "stop_loss"] = df.loc[sell_signals, "close"] + (
                df.loc[sell_signals, "atr"] * atr_multiplier_sl
            )
            df.loc[sell_signals, "take_profit"] = df.loc[sell_signals, "close"] - (
                df.loc[sell_signals, "atr"] * atr_multiplier_tp
            )

            # Calculate risk reward ratio
            has_signal = df["signal"] != 0
            risk = abs(df.loc[has_signal, "close"] - df.loc[has_signal, "stop_loss"])
            reward = abs(
                df.loc[has_signal, "take_profit"] - df.loc[has_signal, "close"]
            )
            df.loc[has_signal, "risk_reward_ratio"] = reward / risk.replace(
                0, 1
            )  # Avoid division by zero

            return df
        except Exception as e:
            logger.error(f"Error calculating stop loss and take profit: {e}")
            return df

    async def _convert_signals_to_entities(
        self,
        df: pd.DataFrame,
        pair: str,
        timeframe: str,
        strategy_name: str,
        fast_ma: int,
        slow_ma: int,
        atr_multiplier_sl: float,
        atr_multiplier_tp: float,
    ) -> List[Signal]:
        """Convert DataFrame signals to Signal entities."""
        signals = []

        try:
            # Filter rows with signals
            signal_rows = df[df["signal"] != 0]

            for timestamp, row in signal_rows.iterrows():
                # Determine signal type
                signal_type = SignalType.BUY if row["signal"] == 1 else SignalType.SELL
                crossover_type = (
                    CrossoverType.BULLISH
                    if row["crossover_type"] == "BULLISH"
                    else CrossoverType.BEARISH
                )

                # Create Signal entity
                signal = Signal(
                    signal_id=str(uuid4()),
                    pair=pair,
                    timeframe=timeframe,
                    signal_type=signal_type,
                    crossover_type=crossover_type,
                    entry_price=Decimal(str(row["close"])),
                    current_price=Decimal(str(row["close"])),
                    fast_ma=fast_ma,
                    slow_ma=slow_ma,
                    timestamp=(
                        timestamp
                        if isinstance(timestamp, datetime)
                        else datetime.now(timezone.utc)
                    ),
                    stop_loss=(
                        Decimal(str(row["stop_loss"]))
                        if row["stop_loss"] != 0
                        else None
                    ),
                    take_profit=(
                        Decimal(str(row["take_profit"]))
                        if row["take_profit"] != 0
                        else None
                    ),
                    atr_value=(
                        Decimal(str(row["atr"])) if not pd.isna(row["atr"]) else None
                    ),
                    atr_multiplier_sl=atr_multiplier_sl,
                    atr_multiplier_tp=atr_multiplier_tp,
                    risk_reward_ratio=(
                        float(row["risk_reward_ratio"])
                        if not pd.isna(row["risk_reward_ratio"])
                        else None
                    ),
                    strategy_name=strategy_name,
                    status=SignalStatus.ACTIVE,
                )

                signals.append(signal)

        except Exception as e:
            logger.error(f"Error converting signals to entities: {e}")

        return signals

    async def _store_signals(self, signals: List[Signal]) -> None:
        """Store signals using repository pattern."""
        try:
            signal_repository = await self.repository_provider.get_signal_repository()

            signals_stored = 0
            for signal in signals:
                try:
                    # Validate signal data
                    signal_dict = signal.to_dict()
                    if validate_signal_data(signal_dict):
                        # Store using repository
                        stored_signal = await signal_repository.create(signal)
                        if stored_signal:
                            signals_stored += 1
                            logger.info(
                                f"Stored signal {signal.signal_id} for {signal.pair} {signal.timeframe}"
                            )

                            # Record metrics
                            record_signal_generated(
                                signal.pair, signal.risk_reward_ratio or 1.0
                            )
                        else:
                            logger.error(f"Failed to store signal {signal.signal_id}")
                    else:
                        logger.warning(f"Invalid signal data for {signal.signal_id}")
                        metrics_collector.increment_counter(
                            "signal_validation_failures",
                            1,
                            {"pair": signal.pair, "timeframe": signal.timeframe},
                        )

                except Exception as e:
                    error_msg = f"Error storing signal {signal.signal_id}: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    await alert_database_connectivity(error_msg)

            # Track storage success rate
            if signals:
                success_rate = signals_stored / len(signals)
                metrics_collector.set_gauge(
                    "signal_storage_success_rate",
                    success_rate,
                    {"operation": "repository_storage"},
                )

            logger.info(f"Successfully stored {signals_stored}/{len(signals)} signals")

        except Exception as e:
            error_msg = f"Error in signal storage process: {str(e)}"
            logger.error(error_msg, exc_info=True)
            await alert_database_connectivity(error_msg)

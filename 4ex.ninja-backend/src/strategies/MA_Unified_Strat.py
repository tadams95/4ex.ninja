import pandas as pd
from config.settings import MONGO_CONNECTION_STRING
from pymongo import MongoClient
import asyncio
import logging
import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Optional
from config.strat_settings import STRATEGIES

# Import our comprehensive error handling and monitoring infrastructure
from infrastructure.monitoring.alerts import (
    alert_signal_processing_failure,
    alert_database_connectivity,
    alert_external_api_downtime,
)
from infrastructure.monitoring.dashboards import (
    metrics_collector,
    track_requests,
    record_signal_generated,
)
from strategies.error_handling import (
    signal_error_handler,
    validate_market_data,
    validate_signal_data,
    detect_data_corruption,
)
from infrastructure.repositories.error_handling import database_operation

# Import Discord notification infrastructure
from infrastructure.monitoring.discord_alerts import send_signal_to_discord
from core.entities.signal import Signal, SignalType, CrossoverType, SignalStatus
from config.discord_config import (
    should_send_discord_notification,
    get_discord_channel_tier,
)

# Import AsyncNotificationService for non-blocking Discord delivery
from infrastructure.services.notification_integration import (
    send_signal_async,
    NotificationPriority,
    UserTier,
)
from infrastructure.services.async_notification_startup import on_strategy_start

# Set up database connections
client = MongoClient(
    MONGO_CONNECTION_STRING, tls=True, tlsAllowInvalidCertificates=True
)
price_db = client["streamed_prices"]
signals_db = client["signals"]

# Logging setup
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class MovingAverageCrossStrategy:
    def __init__(
        self,
        pair: str,
        timeframe: str,
        slow_ma: int,
        fast_ma: int,
        atr_period: int,
        sl_atr_multiplier: float,
        tp_atr_multiplier: float,
        min_atr_value: float,
        min_rr_ratio: float,
        sleep_seconds: int,
        min_candles: int,
    ):
        self.pair = pair
        self.timeframe = timeframe
        self.collection = price_db[f"{pair}_{timeframe}"]
        self.signals_collection = signals_db["trades"]
        self.slow_ma = slow_ma
        self.fast_ma = fast_ma
        self.atr_period = atr_period
        self.sl_atr_multiplier = sl_atr_multiplier
        self.tp_atr_multiplier = tp_atr_multiplier
        self.min_atr_value = min_atr_value
        self.min_rr_ratio = min_rr_ratio
        self.sleep_seconds = sleep_seconds
        self.min_candles = min_candles  # Kept but unused with 200-candle fetch
        self.is_jpy_pair = pair.endswith("JPY")

        # Discord configuration
        self.discord_enabled = True  # Set to False to disable Discord notifications
        logging.info(
            f"Discord notifications {'enabled' if self.discord_enabled else 'disabled'} for {self.pair} {self.timeframe}"
        )

        # Initialize AsyncNotificationService for non-blocking Discord delivery
        try:
            on_strategy_start()
            logging.info(
                f"AsyncNotificationService initialized for {self.pair} {self.timeframe}"
            )
        except Exception as e:
            logging.error(f"Failed to initialize AsyncNotificationService: {str(e)}")
            logging.info("Falling back to legacy Discord notifications")

    def validate_signal(
        self, signal: int, atr: float, risk_reward_ratio: float
    ) -> bool:
        """Validate if a signal meets the minimum criteria."""
        try:
            is_valid = (
                signal != 0
                and atr >= self.min_atr_value
                and risk_reward_ratio >= self.min_rr_ratio
            )
            logging.debug(
                f"Validating signal for {self.pair}: signal={signal}, atr={atr}, rr={risk_reward_ratio}, valid={is_valid}"
            )
            return is_valid
        except Exception as e:
            logging.error(f"Error validating signal for {self.pair}: {e}")
            return False

    def calculate_atr(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Average True Range."""
        try:
            high = df["high"]
            low = df["low"]
            close = df["close"].shift(1)
            tr = pd.concat(
                [high - low, abs(high - close), abs(low - close)], axis=1
            ).max(axis=1)
            return tr.rolling(window=self.atr_period).mean()
        except Exception as e:
            logging.error(f"Error calculating ATR for {self.pair}: {e}")
            return pd.Series(index=df.index)

    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate trading signals based on moving average crossovers."""
        try:
            # Create an explicit deep copy to avoid SettingWithCopyWarning
            df = df.copy(deep=True)

            # Calculate moving averages and ATR
            df["slow_ma"] = df["close"].rolling(window=self.slow_ma).mean()
            df["fast_ma"] = df["close"].rolling(window=self.fast_ma).mean()
            df["atr"] = self.calculate_atr(df)
            df["signal"] = 0

            # Determine crossovers
            buy_crossover = (df["fast_ma"] > df["slow_ma"]) & (
                df["fast_ma"].shift(1) <= df["slow_ma"].shift(1)
            )
            sell_crossover = (df["fast_ma"] < df["slow_ma"]) & (
                df["fast_ma"].shift(1) >= df["slow_ma"].shift(1)
            )
            df.loc[buy_crossover, "signal"] = 1
            df.loc[sell_crossover, "signal"] = -1
            logging.info(
                f"Detected {len(df[df['signal'] != 0])} crossovers for {self.pair} {self.timeframe}"
            )

            # Calculate stop loss and take profit
            df["stop_loss"] = pd.NA
            df["take_profit"] = pd.NA
            df["risk_reward_ratio"] = pd.NA

            # For buy signals
            buy_signals = df["signal"] == 1
            df.loc[buy_signals, "stop_loss"] = df.loc[buy_signals, "close"] - (
                df.loc[buy_signals, "atr"] * self.sl_atr_multiplier
            )
            df.loc[buy_signals, "take_profit"] = df.loc[buy_signals, "close"] + (
                df.loc[buy_signals, "atr"] * self.tp_atr_multiplier
            )
            df.loc[buy_signals, "risk_reward_ratio"] = (
                df.loc[buy_signals, "take_profit"] - df.loc[buy_signals, "close"]
            ) / (df.loc[buy_signals, "close"] - df.loc[buy_signals, "stop_loss"])

            # For sell signals
            sell_signals = df["signal"] == -1
            df.loc[sell_signals, "stop_loss"] = df.loc[sell_signals, "close"] + (
                df.loc[sell_signals, "atr"] * self.sl_atr_multiplier
            )
            df.loc[sell_signals, "take_profit"] = df.loc[sell_signals, "close"] - (
                df.loc[sell_signals, "atr"] * self.tp_atr_multiplier
            )
            df.loc[sell_signals, "risk_reward_ratio"] = (
                df.loc[sell_signals, "close"] - df.loc[sell_signals, "take_profit"]
            ) / (df.loc[sell_signals, "stop_loss"] - df.loc[sell_signals, "close"])

            # Ensure numeric types after calculations
            df["stop_loss"] = pd.to_numeric(df["stop_loss"], errors="coerce")
            df["take_profit"] = pd.to_numeric(df["take_profit"], errors="coerce")
            df["risk_reward_ratio"] = pd.to_numeric(
                df["risk_reward_ratio"], errors="coerce"
            )

            # Filter signals based on validation criteria
            invalid_indices = []
            for index, row in df[df["signal"] != 0].iterrows():
                if not self.validate_signal(
                    row["signal"], row["atr"], row["risk_reward_ratio"]
                ):
                    invalid_indices.append(index)

            if invalid_indices:
                df.loc[invalid_indices, "signal"] = 0
                logging.info(
                    f"Filtered {len(invalid_indices)} signals for {self.pair} {self.timeframe}"
                )

            return df
        except Exception as e:
            logging.error(
                f"Error calculating signals for {self.pair}: {e}", exc_info=True
            )
            return df

    def generate_trade_dict(self, row: pd.Series) -> Optional[Dict]:
        """Generate a dictionary of trade data from a signal row."""
        try:
            close_price = Decimal(str(row["close"]))
            stop_loss = Decimal(str(row["stop_loss"]))
            take_profit = Decimal(str(row["take_profit"]))
            pip_multiplier = Decimal("100") if self.is_jpy_pair else Decimal("10000")
            sl_pips = abs(close_price - stop_loss) * pip_multiplier
            tp_pips = abs(take_profit - close_price) * pip_multiplier
            signal_data = {
                "time": row.name,
                "instrument": self.pair,
                "timeframe": self.timeframe,
                "close": float(row["close"]),
                "slow_ma": float(row["slow_ma"]),
                "fast_ma": float(row["fast_ma"]),
                "signal": int(row["signal"]),
                "stop_loss": float(stop_loss),
                "take_profit": float(take_profit),
                "sl_pips": float(sl_pips),
                "tp_pips": float(tp_pips),
                "atr": float(row["atr"]),
                "risk_reward_ratio": float(row["risk_reward_ratio"]),
                "created_at": datetime.now(timezone.utc),
            }
            logging.info(
                f"Generated signal for {self.pair} {self.timeframe}: {signal_data}"
            )
            return signal_data
        except Exception as e:
            logging.error(
                f"Error generating trade dict for {self.pair}: {e}", exc_info=True
            )
            return None

    async def send_signal_to_discord(self, signal_data: Dict, row: pd.Series) -> None:
        """
        Send trading signal to Discord using the existing Discord infrastructure.

        This method converts our signal_data dictionary to a Signal entity
        and sends it to Discord through the comprehensive notification system.
        """
        try:
            # Convert signal_data to Signal entity for Discord notification
            signal_entity = Signal(
                signal_id=f"{self.pair}_{self.timeframe}_{signal_data['time'].strftime('%Y%m%d_%H%M%S')}",
                pair=self.pair,
                timeframe=self.timeframe,
                signal_type=(
                    SignalType.BUY if signal_data["signal"] == 1 else SignalType.SELL
                ),
                crossover_type=(
                    CrossoverType.BULLISH
                    if signal_data["signal"] == 1
                    else CrossoverType.BEARISH
                ),
                entry_price=Decimal(str(signal_data["close"])),
                current_price=Decimal(str(signal_data["close"])),
                fast_ma=signal_data["fast_ma"],
                slow_ma=signal_data["slow_ma"],
                timestamp=signal_data["time"],
                stop_loss=(
                    Decimal(str(signal_data["stop_loss"]))
                    if signal_data["stop_loss"]
                    else None
                ),
                take_profit=(
                    Decimal(str(signal_data["take_profit"]))
                    if signal_data["take_profit"]
                    else None
                ),
                atr_value=(
                    Decimal(str(signal_data["atr"])) if signal_data["atr"] else None
                ),
                risk_reward_ratio=signal_data.get("risk_reward_ratio"),
                strategy_name="MA Unified Strategy",
                status=SignalStatus.ACTIVE,
                confidence_score=0.85,  # You can calculate this based on ATR, volume, etc.
            )

            # Send to Discord using AsyncNotificationService for non-blocking delivery
            channel_tier = get_discord_channel_tier(signal_data)

            # Determine priority and user tier based on signal quality
            priority = (
                NotificationPriority.HIGH
                if channel_tier == "premium"
                else NotificationPriority.NORMAL
            )
            user_tier = UserTier.PREMIUM if channel_tier == "premium" else UserTier.FREE

            try:
                # Use async notification service for non-blocking delivery
                discord_success = await send_signal_async(
                    signal=signal_entity,
                    priority=priority,
                    user_tier=user_tier,
                    additional_context={
                        "market_conditions": "Live Trading Signal",
                        "sl_pips": signal_data.get("sl_pips", 0),
                        "tp_pips": signal_data.get("tp_pips", 0),
                        "atr_value": signal_data.get("atr", 0),
                        "volatility": (
                            "Medium" if signal_data.get("atr", 0) < 50 else "High"
                        ),
                        "session": self._get_trading_session(),
                        "strategy_confidence": (
                            "High"
                            if signal_data.get("risk_reward_ratio", 0) > 1.5
                            else "Medium"
                        ),
                        "channel_tier": channel_tier,
                        "notification_priority": priority.value,
                    },
                )

                if discord_success:
                    logging.info(
                        f"✅ Discord notification queued for {self.pair} {self.timeframe} signal"
                    )
                    # Track Discord notification success
                    metrics_collector.increment_counter(
                        "discord_notifications_sent",
                        1,
                        {
                            "pair": self.pair,
                            "timeframe": self.timeframe,
                            "signal_type": "crossover",
                        },
                    )
                else:
                    logging.warning(
                        f"⚠️ Failed to queue Discord notification for {self.pair} {self.timeframe}"
                    )
                    # Track Discord notification failure
                    metrics_collector.increment_counter(
                        "discord_notifications_failed",
                        1,
                        {
                            "pair": self.pair,
                            "timeframe": self.timeframe,
                            "reason": "queue_failure",
                        },
                    )

            except Exception as e:
                logging.error(
                    f"⚠️ AsyncNotificationService failed for {self.pair} {self.timeframe}: {str(e)}"
                )

                # Fallback to legacy Discord notification
                try:
                    logging.info(
                        f"Attempting legacy Discord notification for {self.pair} {self.timeframe}"
                    )
                    discord_success = await send_signal_to_discord(
                        signal=signal_entity,
                        alert_type="crossover_signal",
                        additional_context={
                            "market_conditions": "Live Trading Signal (Fallback)",
                            "sl_pips": signal_data.get("sl_pips", 0),
                            "tp_pips": signal_data.get("tp_pips", 0),
                            "atr_value": signal_data.get("atr", 0),
                            "volatility": (
                                "Medium" if signal_data.get("atr", 0) < 50 else "High"
                            ),
                            "session": self._get_trading_session(),
                            "strategy_confidence": (
                                "High"
                                if signal_data.get("risk_reward_ratio", 0) > 1.5
                                else "Medium"
                            ),
                            "channel_tier": channel_tier,
                            "notification_priority": (
                                "HIGH" if channel_tier == "premium" else "NORMAL"
                            ),
                        },
                    )

                    if discord_success:
                        logging.info(
                            f"✅ Legacy Discord notification sent for {self.pair} {self.timeframe} signal"
                        )
                        # Track Discord notification success
                        metrics_collector.increment_counter(
                            "discord_notifications_sent",
                            1,
                            {
                                "pair": self.pair,
                                "timeframe": self.timeframe,
                                "signal_type": "crossover_fallback",
                            },
                        )
                    else:
                        logging.warning(
                            f"⚠️ Legacy Discord notification also failed for {self.pair} {self.timeframe}"
                        )
                        # Track Discord notification failure
                        metrics_collector.increment_counter(
                            "discord_notifications_failed",
                            1,
                            {
                                "pair": self.pair,
                                "timeframe": self.timeframe,
                                "reason": "fallback_failure",
                            },
                        )

                except Exception as fallback_e:
                    logging.error(
                        f"❌ Legacy Discord notification also failed for {self.pair} {self.timeframe}: {str(fallback_e)}",
                        exc_info=True,
                    )
                    # Track Discord notification errors
                    metrics_collector.increment_counter(
                        "discord_notifications_failed",
                        1,
                        {
                            "pair": self.pair,
                            "timeframe": self.timeframe,
                            "reason": "exception",
                        },
                    )

        except Exception as e:
            logging.error(
                f"❌ Error in send_signal_to_discord for {self.pair} {self.timeframe}: {str(e)}",
                exc_info=True,
            )

    def _get_trading_session(self) -> str:
        """Determine current trading session for context."""
        from datetime import datetime
        import pytz

        utc_now = datetime.now(pytz.UTC)
        london_time = utc_now.astimezone(pytz.timezone("Europe/London"))
        ny_time = utc_now.astimezone(pytz.timezone("America/New_York"))
        tokyo_time = utc_now.astimezone(pytz.timezone("Asia/Tokyo"))

        hour = utc_now.hour

        if 0 <= hour < 7:  # Tokyo session
            return "Tokyo Open"
        elif 7 <= hour < 15:  # London session
            return "London Open"
        elif 15 <= hour < 22:  # New York session
            return "New York Open"
        else:  # Overlap or quiet periods
            return "Market Overlap"

    async def process_dataframe(self, df: pd.DataFrame) -> None:
        """Process a dataframe of price data to generate and store signals."""
        if df.empty:
            logging.info(f"No data found for {self.pair} {self.timeframe}")
            # Track empty data event
            metrics_collector.increment_counter(
                "signal_processing_warnings",
                1,
                {"pair": self.pair, "timeframe": self.timeframe, "reason": "no_data"},
            )
            return

        # Set time as index
        df.set_index("time", inplace=True)

        # Prepare OHLC data - create a new DataFrame
        df = df[["open", "high", "low", "close"]].copy(deep=True)

        # Validate market data using our error handling infrastructure
        try:
            # Convert DataFrame to list of dictionaries for validation
            candle_data = []
            for index, row in df.iterrows():
                # Handle timestamp conversion safely - use current time as fallback
                try:
                    timestamp = int(pd.Timestamp(str(index)).timestamp())
                except:
                    timestamp = int(datetime.now().timestamp())

                candle_dict = {
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "timestamp": timestamp,
                }
                candle_data.append(candle_dict)

            # Detect data corruption
            if detect_data_corruption(candle_data):
                error_msg = f"Data corruption detected for {self.pair} {self.timeframe}"
                logging.error(error_msg)
                await alert_signal_processing_failure(error_msg)
                metrics_collector.increment_counter(
                    "signal_processing_errors",
                    1,
                    {
                        "pair": self.pair,
                        "timeframe": self.timeframe,
                        "error_type": "data_corruption",
                    },
                )
                return

        except Exception as e:
            error_msg = f"Market data validation failed for {self.pair} {self.timeframe}: {str(e)}"
            logging.error(error_msg)
            await alert_signal_processing_failure(error_msg)
            metrics_collector.increment_counter(
                "signal_processing_errors",
                1,
                {
                    "pair": self.pair,
                    "timeframe": self.timeframe,
                    "error_type": "validation_failure",
                },
            )
            return

        # Ensure numeric types
        for col in ["open", "high", "low", "close"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Clean the data
        df = df.dropna(subset=["open", "high", "low", "close"])
        logging.info(
            f"After NaN removal: {len(df)} valid candles for {self.pair} {self.timeframe}"
        )

        # Remove duplicates
        df = df[~df.index.duplicated(keep="last")].copy(deep=True)

        # Calculate signals with error handling
        try:
            df = self.calculate_signals(df)
        except Exception as e:
            error_msg = (
                f"Signal calculation failed for {self.pair} {self.timeframe}: {str(e)}"
            )
            logging.error(error_msg, exc_info=True)
            await alert_signal_processing_failure(error_msg)
            metrics_collector.increment_counter(
                "signal_processing_errors",
                1,
                {
                    "pair": self.pair,
                    "timeframe": self.timeframe,
                    "error_type": "calculation_failure",
                },
            )
            return

        # Log signal count
        signal_count = len(df[df["signal"] != 0])
        logging.info(f"Found {signal_count} signals for {self.pair} {self.timeframe}")

        # Track signal generation metrics
        metrics_collector.set_gauge(
            "signals_generated_current",
            signal_count,
            {"pair": self.pair, "timeframe": self.timeframe},
        )

        # Store valid signals with database error handling
        signals_stored = 0
        for index, row in df[df["signal"] != 0].iterrows():
            try:
                signal_data = self.generate_trade_dict(row)
                if signal_data:
                    # Validate signal data before storing
                    if validate_signal_data(signal_data):
                        # Store signal with error handling
                        try:
                            result = self.signals_collection.update_one(
                                {"time": index}, {"$set": signal_data}, upsert=True
                            )
                            if result:
                                signals_stored += 1
                                logging.info(
                                    f"Saved signal to signals.trades for {self.pair} {self.timeframe}"
                                )

                                # Record successful signal generation
                                record_signal_generated(
                                    self.pair, signal_data.get("risk_reward_ratio", 1.0)
                                )

                                # 🚀 DISCORD INTEGRATION: Send signal to Discord immediately after storage
                                if (
                                    self.discord_enabled
                                    and should_send_discord_notification(signal_data)
                                ):
                                    await self.send_signal_to_discord(signal_data, row)

                            else:
                                error_msg = f"Failed to store signal for {self.pair} {self.timeframe}"
                                logging.error(error_msg)
                                await alert_database_connectivity(error_msg)
                        except Exception as db_e:
                            error_msg = f"Database error storing signal for {self.pair} {self.timeframe}: {str(db_e)}"
                            logging.error(error_msg, exc_info=True)
                            await alert_database_connectivity(error_msg)
                    else:
                        logging.warning(
                            f"Invalid signal data for {self.pair} {self.timeframe}"
                        )
                        metrics_collector.increment_counter(
                            "signal_validation_failures",
                            1,
                            {"pair": self.pair, "timeframe": self.timeframe},
                        )
            except Exception as e:
                error_msg = (
                    f"Error storing signal for {self.pair} {self.timeframe}: {str(e)}"
                )
                logging.error(error_msg, exc_info=True)
                await alert_database_connectivity(error_msg)
                metrics_collector.increment_counter(
                    "database_errors",
                    1,
                    {
                        "pair": self.pair,
                        "timeframe": self.timeframe,
                        "operation": "signal_storage",
                    },
                )

        # Track storage success rate
        if signal_count > 0:
            success_rate = signals_stored / signal_count
            metrics_collector.set_gauge(
                "signal_storage_success_rate",
                success_rate,
                {"pair": self.pair, "timeframe": self.timeframe},
            )

            if success_rate < 0.8:  # Alert if less than 80% success rate
                await alert_database_connectivity(
                    f"Low signal storage success rate ({success_rate:.1%}) for {self.pair} {self.timeframe}"
                )

    async def monitor_prices(self):
        """Main monitoring loop that fetches data and processes it periodically."""
        logging.info(f"Starting monitoring for {self.pair} {self.timeframe}")

        # Track monitoring start
        metrics_collector.increment_counter(
            "strategy_monitoring_started",
            1,
            {"pair": self.pair, "timeframe": self.timeframe},
        )

        consecutive_errors = 0
        max_consecutive_errors = 5

        while True:
            start_time = time.time()

            try:
                # Track API request timing
                fetch_start = time.time()

                # Fetch last 200 candles
                df = pd.DataFrame(
                    list(self.collection.find().sort("time", -1).limit(200))
                )
                logging.info(
                    f"Retrieved {len(df)} candles for {self.pair} {self.timeframe}"
                )

                # Record fetch duration
                fetch_duration = time.time() - fetch_start
                metrics_collector.record_histogram(
                    "data_fetch_duration",
                    fetch_duration,
                    {"pair": self.pair, "timeframe": self.timeframe},
                )

                # Process the dataframe with comprehensive error handling
                await self.process_dataframe(df)

                # Reset consecutive error count on success
                consecutive_errors = 0

                # Track successful monitoring cycle
                metrics_collector.increment_counter(
                    "monitoring_cycles_completed",
                    1,
                    {"pair": self.pair, "timeframe": self.timeframe},
                )

                # Track cycle duration
                cycle_duration = time.time() - start_time
                metrics_collector.record_histogram(
                    "monitoring_cycle_duration",
                    cycle_duration,
                    {"pair": self.pair, "timeframe": self.timeframe},
                )

                # Clean up and wait for next cycle
                del df
                await asyncio.sleep(self.sleep_seconds)

            except Exception as e:
                consecutive_errors += 1
                error_msg = f"Error monitoring {self.pair} {self.timeframe}: {str(e)}"
                logging.error(error_msg, exc_info=True)

                # Track monitoring errors
                metrics_collector.increment_counter(
                    "monitoring_errors",
                    1,
                    {
                        "pair": self.pair,
                        "timeframe": self.timeframe,
                        "consecutive_errors": str(consecutive_errors),
                    },
                )

                # Alert on critical errors or consecutive failures
                if consecutive_errors >= max_consecutive_errors:
                    critical_msg = f"Critical: {consecutive_errors} consecutive monitoring failures for {self.pair} {self.timeframe}"
                    logging.critical(critical_msg)
                    await alert_signal_processing_failure(critical_msg)

                    # Longer sleep on consecutive failures
                    await asyncio.sleep(1800)  # 30 minutes
                elif consecutive_errors >= 3:
                    # Alert on multiple consecutive errors
                    warning_msg = f"Warning: {consecutive_errors} consecutive monitoring errors for {self.pair} {self.timeframe}"
                    await alert_signal_processing_failure(warning_msg)
                    await asyncio.sleep(900)  # 15 minutes
                else:
                    # Regular error handling
                    await alert_signal_processing_failure(error_msg)
                    await asyncio.sleep(300)  # 5 minutes

                # Track error recovery attempts
                metrics_collector.increment_counter(
                    "error_recovery_attempts",
                    1,
                    {"pair": self.pair, "timeframe": self.timeframe},
                )


async def run_strategies():
    """Start all strategies concurrently."""
    strategies = [MovingAverageCrossStrategy(**cfg) for cfg in STRATEGIES.values()]
    tasks = [asyncio.create_task(strategy.monitor_prices()) for strategy in strategies]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    logging.info("Starting multi-strategy monitoring...")
    asyncio.run(run_strategies())

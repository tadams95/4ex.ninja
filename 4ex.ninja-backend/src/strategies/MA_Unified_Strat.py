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

# ═══ EMERGENCY RISK MANAGEMENT FRAMEWORK ═══
from risk.emergency_risk_manager import (
    EmergencyRiskManager,
    EmergencyLevel,
    create_emergency_risk_manager,
)
import pytz

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

# Import Redis-powered incremental signal processor for 80-90% performance improvement
import sys
import aiohttp

sys.path.append("/root")
from infrastructure.services.incremental_signal_processor import (
    create_incremental_processor,
)
from infrastructure.cache.redis_cache_service import (
    get_cache_service as initialize_cache_service,
)

# Import Discord webhook sender for direct webhook notifications
try:
    from infrastructure.services.discord_webhook_sender import get_webhook_sender
    import aiohttp

    WEBHOOK_AVAILABLE = True
except ImportError:
    WEBHOOK_AVAILABLE = False
    logging.warning(
        "Discord webhook sender not available, using fallback notifications"
    )

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
        portfolio_initial_value: float = 100000.0,  # NEW: Portfolio value for emergency protocols
        enable_emergency_management: bool = True,  # NEW: Enable/disable emergency management
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

        # ═══ EMERGENCY RISK MANAGEMENT INITIALIZATION ═══
        self.portfolio_initial_value = portfolio_initial_value
        self.portfolio_current_value = portfolio_initial_value
        self.enable_emergency_management = enable_emergency_management
        self.emergency_manager = None

        logging.info(
            f"Emergency Risk Management {'ENABLED' if enable_emergency_management else 'DISABLED'} for {self.pair}"
        )

        # Initialize emergency manager if enabled
        if self.enable_emergency_management:
            try:
                # This will be called asynchronously in the main execution loop
                self.emergency_manager_initialized = False
                logging.info(
                    f"Emergency Risk Manager will be initialized for {self.pair}"
                )
            except Exception as e:
                logging.error(f"Error preparing emergency manager for {self.pair}: {e}")
                self.enable_emergency_management = False

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
            logging.warning(f"AsyncNotificationService initialization failed: {e}")

        # Initialize Redis-powered incremental processor for 80-90% performance improvement
        self.incremental_processor = None
        self.optimization_enabled = True  # Set to False to disable Redis optimization

    async def initialize_emergency_manager(self):
        """Initialize the Emergency Risk Manager (call this once at startup)"""
        try:
            if self.enable_emergency_management and not self.emergency_manager:
                self.emergency_manager = await create_emergency_risk_manager(
                    portfolio_value=self.portfolio_initial_value
                )
                self.emergency_manager_initialized = True
                logging.info(
                    f"🚨 Emergency Risk Manager ACTIVATED for {self.pair} - 4-level protocols enabled"
                )
            else:
                logging.info(f"Emergency Risk Manager disabled for {self.pair}")
        except Exception as e:
            logging.error(
                f"Failed to initialize Emergency Risk Manager for {self.pair}: {e}"
            )
            self.enable_emergency_management = False

    def validate_signal(
        self, signal: int, atr: float, risk_reward_ratio: float
    ) -> bool:
        """Enhanced signal validation with Emergency Risk Management protocols."""
        try:
            # ═══ ORIGINAL VALIDATION ═══
            original_valid = (
                signal != 0
                and atr >= self.min_atr_value
                and risk_reward_ratio >= self.min_rr_ratio
            )

            if not original_valid:
                logging.debug(f"Signal rejected by original validation for {self.pair}")
                return False

            # ═══ EMERGENCY RISK MANAGEMENT VALIDATION ═══
            if self.enable_emergency_management and self.emergency_manager:
                try:
                    emergency_status = self.emergency_manager.get_emergency_status()

                    # 🛑 EMERGENCY STOP CHECK (Level 4 - 25% drawdown)
                    if emergency_status.get("trading_halted", False):
                        logging.critical(
                            f"🛑 SIGNAL REJECTED for {self.pair}: EMERGENCY STOP ACTIVATED "
                            f"(Level {emergency_status.get('emergency_level')})"
                        )
                        return False

                    # 🚨 CRISIS MODE VALIDATION (Level 3 - 20% drawdown)
                    emergency_level = emergency_status.get("emergency_level")
                    if emergency_level == "LEVEL_3":
                        # In crisis mode, require higher standards
                        if risk_reward_ratio < 3.0:
                            logging.warning(
                                f"🚨 SIGNAL REJECTED for {self.pair}: Insufficient RR ({risk_reward_ratio:.2f}) "
                                f"during CRISIS MODE (requires 3.0+)"
                            )
                            return False

                        if atr < self.min_atr_value * 1.5:
                            logging.warning(
                                f"🚨 SIGNAL REJECTED for {self.pair}: Insufficient ATR ({atr:.4f}) "
                                f"during CRISIS MODE"
                            )
                            return False

                    # ⚠️ ELEVATED RISK VALIDATION (Level 1-2)
                    elif emergency_level in ["LEVEL_1", "LEVEL_2"]:
                        active_stress_events = emergency_status.get(
                            "active_stress_events", 0
                        )
                        if active_stress_events > 0:
                            logging.warning(
                                f"⚠️ Signal evaluation during stress: {active_stress_events} active events"
                            )

                            # Require higher RR during stress
                            if risk_reward_ratio < 2.0:
                                logging.warning(
                                    f"⚠️ SIGNAL REJECTED for {self.pair}: Insufficient RR during stress event"
                                )
                                return False

                    # Log successful validation with emergency context
                    if emergency_level != "NORMAL":
                        logging.info(
                            f"✅ SIGNAL ACCEPTED for {self.pair} under Emergency Level {emergency_level} "
                            f"(RR: {risk_reward_ratio:.2f}, ATR: {atr:.4f})"
                        )

                    return True

                except Exception as e:
                    logging.error(f"Error in emergency validation for {self.pair}: {e}")
                    # Conservative approach: reject signal during emergency system errors
                    return False

            # If emergency management is disabled, use original validation
            logging.debug(
                f"Signal validated for {self.pair} (Emergency Management disabled)"
            )
            return original_valid

        except Exception as e:
            logging.error(f"Error validating signal for {self.pair}: {e}")
            return False

    def calculate_emergency_position_size(
        self, base_size: float, current_volatility: Optional[float] = None
    ) -> float:
        """Calculate position size with Emergency Risk Management adjustments."""
        try:
            if not self.enable_emergency_management or not self.emergency_manager:
                return base_size

            # Use Emergency Risk Manager for dynamic position sizing
            adjusted_size = self.emergency_manager.calculate_position_size(
                base_size=base_size,
                pair=self.pair,
                current_volatility=current_volatility,
                portfolio_correlation=0.0,  # TODO: Implement portfolio correlation tracking
            )

            # Log position sizing adjustment
            emergency_status = self.emergency_manager.get_emergency_status()
            multiplier = emergency_status.get("position_size_multiplier", 1.0)

            if abs(adjusted_size - base_size) > 0.01:  # Log if significant change
                logging.info(
                    f"💰 Position sizing for {self.pair}: ${base_size:.2f} → ${adjusted_size:.2f} "
                    f"(Emergency Level: {emergency_status.get('emergency_level')}, "
                    f"Multiplier: {multiplier:.1%})"
                )

            return adjusted_size

        except Exception as e:
            logging.error(
                f"Error calculating emergency position size for {self.pair}: {e}"
            )
            return base_size * 0.5  # Conservative fallback

    async def update_portfolio_value(self, new_value: float):
        """Update portfolio value for Emergency Risk Management monitoring."""
        try:
            if self.enable_emergency_management and self.emergency_manager:
                previous_value = self.portfolio_current_value
                self.portfolio_current_value = new_value

                # Update emergency manager
                await self.emergency_manager.update_portfolio_value(new_value)

                # Calculate and log drawdown
                drawdown = (
                    self.portfolio_initial_value - new_value
                ) / self.portfolio_initial_value

                if abs(new_value - previous_value) > (
                    previous_value * 0.01
                ):  # Log significant changes
                    logging.info(
                        f"📊 Portfolio update for {self.pair}: ${new_value:,.2f} "
                        f"(Drawdown: {drawdown:.2%})"
                    )

                    # Log emergency level changes
                    emergency_status = self.emergency_manager.get_emergency_status()
                    emergency_level = emergency_status.get("emergency_level")
                    if emergency_level != "NORMAL":
                        logging.warning(
                            f"⚠️ Emergency Level {emergency_level} active for {self.pair}"
                        )

        except Exception as e:
            logging.error(f"Error updating portfolio value for {self.pair}: {e}")

    async def monitor_market_stress(self, current_df: pd.DataFrame):
        """Monitor for stress events using 2x volatility threshold."""
        try:
            if self.enable_emergency_management and self.emergency_manager:
                # Prepare market data for stress detection
                market_data = {self.pair: current_df}

                # Monitor stress events
                stress_events = await self.emergency_manager.monitor_stress_events(
                    market_data
                )

                if stress_events:
                    logging.warning(
                        f"🚨 STRESS EVENTS DETECTED for {self.pair}: {len(stress_events)} events"
                    )

                    # Log critical stress events
                    for event in stress_events[:2]:  # Log first 2 events
                        logging.warning(
                            f"  - {event.event_type.value}: Severity {event.severity:.2f}x "
                            f"| Action: {event.recommended_action}"
                        )

                    # Send stress alerts if severe
                    for event in stress_events:
                        if event.severity > 3.0:  # Critical severity
                            logging.critical(
                                f"🔥 CRITICAL STRESS EVENT for {self.pair}: "
                                f"{event.event_type.value} (Severity: {event.severity:.2f}x)"
                            )

                return stress_events

        except Exception as e:
            logging.error(f"Error monitoring market stress for {self.pair}: {e}")
            return []

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

            # Get emergency risk context if available
            emergency_context = {}
            if self.enable_emergency_management and self.emergency_manager:
                try:
                    emergency_status = self.emergency_manager.get_emergency_status()
                    emergency_context = {
                        "emergency_level": emergency_status.get(
                            "emergency_level", "NORMAL"
                        ),
                        "portfolio_drawdown": emergency_status.get(
                            "portfolio_drawdown", 0.0
                        ),
                        "position_size_multiplier": emergency_status.get(
                            "position_size_multiplier", 1.0
                        ),
                        "active_stress_events": emergency_status.get(
                            "active_stress_events", 0
                        ),
                        "trading_halted": emergency_status.get("trading_halted", False),
                    }
                except Exception as e:
                    logging.warning(
                        f"Could not get emergency context for {self.pair}: {e}"
                    )

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
                # 💾 EMERGENCY RISK CONTEXT
                "emergency_context": emergency_context,
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
        Send trading signal to Discord using direct webhook call with rate limiting.

        This method sends signals directly to Discord webhooks for immediate notifications.
        """
        try:
            # Check if webhook sender is available
            if WEBHOOK_AVAILABLE:
                try:
                    webhook_sender = await get_webhook_sender()

                    # Prepare signal data for webhook
                    webhook_signal_data = {
                        "instrument": self.pair,
                        "timeframe": self.timeframe,
                        "signal": signal_data["signal"],
                        "close": signal_data["close"],
                        "stop_loss": signal_data["stop_loss"],
                        "take_profit": signal_data["take_profit"],
                        "sl_pips": signal_data["sl_pips"],
                        "tp_pips": signal_data["tp_pips"],
                        "risk_reward_ratio": signal_data["risk_reward_ratio"],
                    }

                    # Determine channel based on signal quality
                    channel = (
                        "signals_premium"
                        if signal_data["risk_reward_ratio"] > 2.0
                        else "signals_free"
                    )

                    # Retry logic for rate limiting
                    max_retries = 3
                    base_delay = 2  # Base delay in seconds

                    for attempt in range(max_retries):
                        try:
                            # Send webhook notification
                            webhook_success = await webhook_sender.send_signal_webhook(
                                webhook_signal_data, channel
                            )

                            if webhook_success:
                                logging.info(
                                    f"🚀 Direct Discord webhook sent to {channel} for {self.pair} {self.timeframe}"
                                )
                                return
                            else:
                                # If it failed but didn't raise an exception, break and use fallback
                                logging.warning(
                                    f"⚠️ Direct webhook failed (attempt {attempt + 1}/{max_retries}), falling back to infrastructure"
                                )
                                break

                        except aiohttp.ClientResponseError as e:
                            if e.status == 429:  # Rate limited
                                if attempt < max_retries - 1:
                                    # Exponential backoff: 2s, 4s, 8s
                                    delay = base_delay * (2**attempt)
                                    logging.warning(
                                        f"🕒 Discord rate limited (429), retrying in {delay}s (attempt {attempt + 1}/{max_retries})"
                                    )
                                    await asyncio.sleep(delay)
                                    continue
                                else:
                                    logging.warning(
                                        f"🚫 Discord rate limit exceeded after {max_retries} attempts, using fallback"
                                    )
                                    break
                            else:
                                # Other HTTP errors
                                logging.warning(
                                    f"⚠️ Discord webhook HTTP error {e.status}: {e.message}"
                                )
                                break
                        except Exception as retry_e:
                            logging.warning(
                                f"⚠️ Discord webhook error (attempt {attempt + 1}/{max_retries}): {retry_e}"
                            )
                            if attempt < max_retries - 1:
                                delay = base_delay * (2**attempt)
                                await asyncio.sleep(delay)
                                continue
                            else:
                                break

                except Exception as webhook_e:
                    logging.warning(
                        f"Direct webhook error: {webhook_e}, using fallback"
                    )

            # Fallback to existing comprehensive Discord infrastructure
            signal_entity = Signal(
                signal_id=f"{self.pair}_{self.timeframe}_{pd.Timestamp(signal_data['time']).strftime('%Y%m%d_%H%M%S')}",
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
                confidence_score=0.85,
            )

            # Send to Discord using AsyncNotificationService for non-blocking delivery
            channel_tier = get_discord_channel_tier(signal_data)
            priority = (
                NotificationPriority.HIGH
                if channel_tier == "premium"
                else NotificationPriority.NORMAL
            )
            user_tier = UserTier.PREMIUM if channel_tier == "premium" else UserTier.FREE

            try:
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
                else:
                    logging.warning(
                        f"⚠️ Failed to queue Discord notification for {self.pair} {self.timeframe}"
                    )

            except Exception as e:
                logging.error(
                    f"⚠️ AsyncNotificationService failed for {self.pair} {self.timeframe}: {str(e)}"
                )

                # Final fallback to legacy Discord notification
                try:
                    discord_success = await send_signal_to_discord(
                        signal=signal_entity,
                        alert_type="crossover_signal",
                        additional_context={
                            "market_conditions": "Live Trading Signal (Fallback)",
                            "sl_pips": signal_data.get("sl_pips", 0),
                            "tp_pips": signal_data.get("tp_pips", 0),
                            "session": self._get_trading_session(),
                        },
                    )

                    if discord_success:
                        logging.info(
                            f"✅ Legacy Discord notification sent for {self.pair} {self.timeframe} signal"
                        )
                    else:
                        logging.warning(
                            f"⚠️ All Discord notification methods failed for {self.pair} {self.timeframe}"
                        )

                except Exception as fallback_e:
                    logging.error(
                        f"❌ All Discord notification methods failed for {self.pair} {self.timeframe}: {str(fallback_e)}"
                    )

        except Exception as e:
            logging.error(
                f"❌ Error in send_signal_to_discord for {self.pair} {self.timeframe}: {str(e)}",
                exc_info=True,
            )

    async def process_optimized_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process signals from optimized data (MA already calculated by incremental processor).

        This method handles the remaining signal logic after incremental MA calculation.
        """
        try:
            if df.empty:
                return df

            # Create an explicit deep copy to avoid SettingWithCopyWarning
            df = df.copy(deep=True)

            # Calculate ATR (not cached yet, but could be optimized later)
            df["atr"] = self.calculate_atr(df)
            df["signal"] = 0

            # Determine crossovers using pre-calculated MAs
            buy_crossover = (df["fast_ma"] > df["slow_ma"]) & (
                df["fast_ma"].shift(1) <= df["slow_ma"].shift(1)
            )
            sell_crossover = (df["fast_ma"] < df["slow_ma"]) & (
                df["fast_ma"].shift(1) >= df["slow_ma"].shift(1)
            )
            df.loc[buy_crossover, "signal"] = 1
            df.loc[sell_crossover, "signal"] = -1

            # Calculate stop loss and take profit
            df["stop_loss"] = pd.NA
            df["take_profit"] = pd.NA
            df["risk_reward_ratio"] = pd.NA

            # For buy signals
            buy_signals = df["signal"] == 1
            if buy_signals.any():
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
            if sell_signals.any():
                df.loc[sell_signals, "stop_loss"] = df.loc[sell_signals, "close"] + (
                    df.loc[sell_signals, "atr"] * self.sl_atr_multiplier
                )
                df.loc[sell_signals, "take_profit"] = df.loc[sell_signals, "close"] - (
                    df.loc[sell_signals, "atr"] * self.tp_atr_multiplier
                )
                df.loc[sell_signals, "risk_reward_ratio"] = (
                    df.loc[sell_signals, "close"] - df.loc[sell_signals, "take_profit"]
                ) / (df.loc[sell_signals, "stop_loss"] - df.loc[sell_signals, "close"])

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
                f"Error processing optimized signals for {self.pair}: {e}",
                exc_info=True,
            )
            return df

    async def _process_original_method(self):
        """
        Fallback method: Original 200-candle fetch + full MA calculation.

        Used when Redis optimization is unavailable or fails.
        """
        try:
            # Track API request timing
            fetch_start = time.time()

            # Fetch last 200 candles (original method)
            df = pd.DataFrame(list(self.collection.find().sort("time", -1).limit(200)))
            logging.info(
                f"🔄 Fallback: Retrieved {len(df)} candles for {self.pair} {self.timeframe}"
            )

            # Record fetch duration
            fetch_duration = time.time() - fetch_start
            metrics_collector.record_histogram(
                "data_fetch_duration_fallback",
                fetch_duration,
                {"pair": self.pair, "timeframe": self.timeframe},
            )

            # ═══ EMERGENCY RISK MANAGEMENT: STRESS MONITORING (FALLBACK) ═══
            if (
                self.enable_emergency_management
                and self.emergency_manager
                and not df.empty
            ):
                try:
                    # Set time as index for stress monitoring
                    df_for_stress = df.copy()
                    if "time" in df_for_stress.columns:
                        df_for_stress.set_index("time", inplace=True)
                    stress_events = await self.monitor_market_stress(df_for_stress)
                    if stress_events:
                        logging.info(
                            f"🚨 Stress monitoring (fallback) completed for {self.pair}: {len(stress_events)} events detected"
                        )
                except Exception as stress_e:
                    logging.error(
                        f"Error in fallback stress monitoring for {self.pair}: {stress_e}"
                    )

            # Process the dataframe with comprehensive error handling
            await self.process_dataframe(df)

        except Exception as e:
            logging.error(
                f"Error in original method fallback for {self.pair}: {e}", exc_info=True
            )
            raise  # Re-raise to trigger error handling in main loop

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

        # ═══ EMERGENCY RISK MANAGEMENT INITIALIZATION ═══
        # Initialize Emergency Risk Manager first
        if self.enable_emergency_management:
            try:
                await self.initialize_emergency_manager()
                if self.emergency_manager:
                    logging.info(
                        f"🚨 Emergency Risk Management ACTIVATED for {self.pair}"
                    )
                else:
                    logging.warning(
                        f"⚠️ Emergency Risk Management failed to initialize for {self.pair}"
                    )
            except Exception as e:
                logging.error(
                    f"Failed to initialize Emergency Risk Manager for {self.pair}: {e}"
                )
                self.enable_emergency_management = False

        # Initialize Redis cache service for performance optimization
        try:
            cache_service = await initialize_cache_service()
            logging.info(
                f"✅ Redis cache service initialized for {self.pair} {self.timeframe}"
            )
        except Exception as e:
            logging.warning(f"⚠️ Redis cache initialization failed: {e}")
            logging.info("Continuing with fallback mode (no cache optimization)")

        # Initialize incremental processor for 80-90% performance improvement
        if self.optimization_enabled:
            try:
                self.incremental_processor = await create_incremental_processor(
                    pair=self.pair,
                    timeframe=self.timeframe,
                    slow_ma=self.slow_ma,
                    fast_ma=self.fast_ma,
                    atr_period=self.atr_period,
                    collection=self.collection,
                )
                logging.info(
                    f"🚀 Incremental processor initialized for {self.pair} {self.timeframe}"
                )
            except Exception as e:
                logging.warning(f"⚠️ Incremental processor initialization failed: {e}")
                logging.info("Falling back to original processing method")
                self.optimization_enabled = False

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
                # 🚀 REDIS OPTIMIZATION: Use incremental processing for 80-90% performance improvement
                if self.optimization_enabled and self.incremental_processor:
                    try:
                        # Process with incremental optimization (1-5 candles vs 200)
                        df = await self.incremental_processor.process_signals_optimized(
                            self.collection
                        )

                        if not df.empty:
                            # Set time as index for compatibility with existing code
                            df.set_index("time", inplace=True)

                            # Prepare OHLC data
                            df = df[
                                ["open", "high", "low", "close", "fast_ma", "slow_ma"]
                            ].copy(deep=True)

                            # Calculate remaining signals using optimized data
                            df = await self.process_optimized_signals(df)

                            # ═══ EMERGENCY RISK MANAGEMENT: STRESS MONITORING ═══
                            if (
                                self.enable_emergency_management
                                and self.emergency_manager
                            ):
                                try:
                                    stress_events = await self.monitor_market_stress(df)
                                    if stress_events:
                                        logging.info(
                                            f"🚨 Stress monitoring completed for {self.pair}: {len(stress_events)} events detected"
                                        )
                                except Exception as stress_e:
                                    logging.error(
                                        f"Error in stress monitoring for {self.pair}: {stress_e}"
                                    )

                            # Process the optimized dataframe
                            await self.process_dataframe(df)

                            logging.info(
                                f"⚡ Optimized processing completed for {self.pair} {self.timeframe}"
                            )
                        else:
                            logging.debug(
                                f"📊 No new signals to process for {self.pair} {self.timeframe}"
                            )

                    except Exception as opt_e:
                        logging.warning(
                            f"Optimization failed for {self.pair} {self.timeframe}: {opt_e}"
                        )
                        logging.info("Falling back to original method for this cycle")
                        await self._process_original_method()
                else:
                    # 🔄 FALLBACK: Original method (200-candle fetch + full MA calculation)
                    await self._process_original_method()

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

                # Log performance metrics periodically
                if (
                    hasattr(self, "incremental_processor")
                    and self.incremental_processor
                ):
                    try:
                        stats = await self.incremental_processor.get_performance_stats()
                        if stats.get("cache_hit_rate", 0) > 0:
                            logging.info(
                                f"📊 Performance stats for {self.pair}_{self.timeframe}: "
                                f"Cache hit rate: {stats['cache_hit_rate']:.1%}, "
                                f"Incremental rate: {stats['incremental_rate']:.1%}"
                            )
                    except Exception:
                        pass  # Don't let stats collection break the main loop

                # Clean up and wait for next cycle
                if "df" in locals():
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

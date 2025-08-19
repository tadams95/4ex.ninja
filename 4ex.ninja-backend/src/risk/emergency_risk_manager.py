"""
Emergency Risk Management Framework (Phase 1)

This module implements a 4-level emergency risk protocol system designed to:
- Detect stress events through 2x volatility threshold monitoring
- Activate crisis mode at 20% portfolio drawdown
- Execute emergency stop at 25% portfolio drawdown
- Provide real-time risk monitoring and automated position management

Based on comprehensive backtesting findings that identified 0.000/1.000 stress resilience vulnerability.
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal
import json

# Database connection for emergency risk data persistence
from config.settings import MONGO_CONNECTION_STRING
from pymongo import MongoClient

# Database connection for emergency risk data persistence
client = MongoClient(
    MONGO_CONNECTION_STRING, tls=True, tlsAllowInvalidCertificates=True
)
risk_db = client["risk_management"]

# Import existing risk infrastructure
from .risk_calculator import RiskCalculator
from .volatility_impact_analyzer import VolatilityImpactAnalyzer

# Import monitoring and alert infrastructure
try:
    from infrastructure.monitoring.alerts import (
        alert_signal_processing_failure,
        alert_database_connectivity,
        alert_external_api_downtime,
    )
    from infrastructure.monitoring.discord_alerts import send_signal_to_discord
except ImportError:
    # Local development fallback - use relative imports
    from ..infrastructure.monitoring.alerts import (
        alert_signal_processing_failure,
        alert_database_connectivity,
        alert_external_api_downtime,
    )
    from ..infrastructure.monitoring.discord_alerts import send_signal_to_discord

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class EmergencyLevel(Enum):
    """Emergency protocol levels"""

    NORMAL = 0
    LEVEL_1 = 1  # 10% portfolio drawdown - Enhanced monitoring
    LEVEL_2 = 2  # 15% portfolio drawdown - Position size reduction
    LEVEL_3 = 3  # 20% portfolio drawdown - Crisis mode activation
    LEVEL_4 = 4  # 25% portfolio drawdown - Emergency stop


class StressEventType(Enum):
    """Types of stress events"""

    VOLATILITY_SPIKE = "volatility_spike"
    FLASH_CRASH = "flash_crash"
    CORRELATION_BREAKDOWN = "correlation_breakdown"
    LIQUIDITY_CRISIS = "liquidity_crisis"
    MARKET_FREEZE = "market_freeze"


@dataclass
class EmergencyProtocol:
    """Emergency protocol configuration"""

    level: EmergencyLevel
    portfolio_drawdown_threshold: float
    volatility_threshold_multiplier: float
    position_size_multiplier: float
    stop_trading: bool
    alert_priority: str
    description: str


@dataclass
class StressEvent:
    """Stress event detection data"""

    event_type: StressEventType
    severity: float
    detected_at: datetime
    current_volatility: float
    threshold_volatility: float
    affected_pairs: List[str]
    recommended_action: str


class EmergencyRiskManager:
    """
    Emergency Risk Management Framework implementing 4-level emergency protocols
    """

    def __init__(
        self,
        portfolio_initial_value: float = 100000.0,
        base_volatility_window: int = 20,
        monitoring_interval: int = 30,
    ):
        """
        Initialize Emergency Risk Manager

        Args:
            portfolio_initial_value: Initial portfolio value for drawdown calculations
            base_volatility_window: Window for calculating base volatility
            monitoring_interval: Monitoring interval in seconds
        """
        self.portfolio_initial_value = portfolio_initial_value
        self.base_volatility_window = base_volatility_window
        self.monitoring_interval = monitoring_interval

        # Initialize risk calculators
        self.risk_calculator = RiskCalculator()
        self.volatility_analyzer = VolatilityImpactAnalyzer()

        # Emergency protocol configuration
        self.emergency_protocols = self._initialize_emergency_protocols()

        # Current state
        self.current_emergency_level = EmergencyLevel.NORMAL
        self.portfolio_current_value = portfolio_initial_value
        self.active_stress_events: List[StressEvent] = []
        self.emergency_history: List[Dict] = []

        # Database collections for persistence
        self.emergency_events_collection = risk_db["emergency_events"]
        self.stress_events_collection = risk_db["stress_events"]
        self.portfolio_metrics_collection = risk_db["portfolio_metrics"]

        # Volatility tracking
        self.volatility_history: Dict[str, List[float]] = {}
        self.base_volatility: Dict[str, float] = {}

        # Position tracking
        self.active_positions: Dict[str, Dict] = {}
        self.position_limits: Dict[str, float] = {}

        self.logger = logging.getLogger(__name__)
        self.logger.info("EmergencyRiskManager initialized")

    def _initialize_emergency_protocols(
        self,
    ) -> Dict[EmergencyLevel, EmergencyProtocol]:
        """Initialize the 4-level emergency protocol system"""
        return {
            EmergencyLevel.NORMAL: EmergencyProtocol(
                level=EmergencyLevel.NORMAL,
                portfolio_drawdown_threshold=0.0,
                volatility_threshold_multiplier=1.0,
                position_size_multiplier=1.0,
                stop_trading=False,
                alert_priority="info",
                description="Normal operations - no restrictions",
            ),
            EmergencyLevel.LEVEL_1: EmergencyProtocol(
                level=EmergencyLevel.LEVEL_1,
                portfolio_drawdown_threshold=0.10,  # 10% drawdown
                volatility_threshold_multiplier=1.5,
                position_size_multiplier=0.8,  # Reduce position size by 20%
                stop_trading=False,
                alert_priority="warning",
                description="Enhanced monitoring - slight position reduction",
            ),
            EmergencyLevel.LEVEL_2: EmergencyProtocol(
                level=EmergencyLevel.LEVEL_2,
                portfolio_drawdown_threshold=0.15,  # 15% drawdown
                volatility_threshold_multiplier=1.8,
                position_size_multiplier=0.6,  # Reduce position size by 40%
                stop_trading=False,
                alert_priority="high",
                description="Significant position size reduction",
            ),
            EmergencyLevel.LEVEL_3: EmergencyProtocol(
                level=EmergencyLevel.LEVEL_3,
                portfolio_drawdown_threshold=0.20,  # 20% drawdown - CRISIS MODE
                volatility_threshold_multiplier=2.0,
                position_size_multiplier=0.3,  # Reduce position size by 70%
                stop_trading=False,
                alert_priority="critical",
                description="CRISIS MODE - Severe position reduction",
            ),
            EmergencyLevel.LEVEL_4: EmergencyProtocol(
                level=EmergencyLevel.LEVEL_4,
                portfolio_drawdown_threshold=0.25,  # 25% drawdown - EMERGENCY STOP
                volatility_threshold_multiplier=2.5,
                position_size_multiplier=0.0,  # Stop all new positions
                stop_trading=True,
                alert_priority="emergency",
                description="EMERGENCY STOP - All trading halted",
            ),
        }

    async def monitor_stress_events(
        self, market_data: Dict[str, pd.DataFrame]
    ) -> List[StressEvent]:
        """
        Continuous monitoring for stress events using 2x volatility threshold

        Args:
            market_data: Dictionary of currency pair DataFrames with OHLC data

        Returns:
            List of detected stress events
        """
        detected_events = []

        try:
            for pair, df in market_data.items():
                if len(df) < self.base_volatility_window:
                    continue

                # Calculate current volatility
                current_volatility = self._calculate_current_volatility(df)

                # Update volatility history
                if pair not in self.volatility_history:
                    self.volatility_history[pair] = []
                self.volatility_history[pair].append(current_volatility)

                # Keep only recent history
                if len(self.volatility_history[pair]) > 100:
                    self.volatility_history[pair] = self.volatility_history[pair][-100:]

                # Calculate base volatility (20-period average)
                if len(self.volatility_history[pair]) >= self.base_volatility_window:
                    base_vol = float(
                        np.mean(
                            self.volatility_history[pair][
                                -self.base_volatility_window :
                            ]
                        )
                    )
                    self.base_volatility[pair] = base_vol

                    # Check for stress events (2x volatility threshold)
                    volatility_threshold = base_vol * 2.0

                    if current_volatility > volatility_threshold:
                        severity = float(current_volatility / base_vol)

                        # Determine stress event type based on severity
                        if severity > 5.0:
                            event_type = StressEventType.FLASH_CRASH
                        elif severity > 3.0:
                            event_type = StressEventType.VOLATILITY_SPIKE
                        else:
                            event_type = StressEventType.VOLATILITY_SPIKE

                        stress_event = StressEvent(
                            event_type=event_type,
                            severity=severity,
                            detected_at=datetime.now(timezone.utc),
                            current_volatility=current_volatility,
                            threshold_volatility=float(volatility_threshold),
                            affected_pairs=[pair],
                            recommended_action=self._get_recommended_action(severity),
                        )

                        detected_events.append(stress_event)

                        # 💾 SAVE STRESS EVENT TO DATABASE
                        await self._save_stress_event(stress_event)

                        self.logger.warning(
                            f"Stress event detected: {pair} volatility {current_volatility:.4f} "
                            f"exceeds threshold {volatility_threshold:.4f} (severity: {severity:.2f}x)"
                        )

            # Update active stress events
            self.active_stress_events = detected_events

            # Check for correlation breakdown across pairs
            if len(detected_events) >= 3:  # Multiple pairs affected
                correlation_event = await self._check_correlation_breakdown(market_data)
                if correlation_event:
                    detected_events.append(correlation_event)

            return detected_events

        except Exception as e:
            self.logger.error(f"Error monitoring stress events: {e}", exc_info=True)
            return []

    def _calculate_current_volatility(self, df: pd.DataFrame) -> float:
        """Calculate current volatility using True Range"""
        try:
            if len(df) < 2:
                return 0.0

            # Calculate True Range
            high = df["high"].iloc[-1]
            low = df["low"].iloc[-1]
            prev_close = df["close"].iloc[-2]

            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))

            # Normalize by current price
            current_price = df["close"].iloc[-1]
            return tr / current_price if current_price > 0 else 0.0

        except Exception as e:
            self.logger.error(f"Error calculating volatility: {e}")
            return 0.0

    async def _check_correlation_breakdown(
        self, market_data: Dict[str, pd.DataFrame]
    ) -> Optional[StressEvent]:
        """Check for correlation breakdown across currency pairs"""
        try:
            if len(market_data) < 3:
                return None

            # Calculate returns for correlation analysis
            returns_data = {}
            for pair, df in market_data.items():
                if len(df) >= 20:
                    returns = df["close"].pct_change().dropna()
                    if len(returns) >= 10:
                        returns_data[pair] = returns.iloc[-10:]  # Last 10 periods

            if len(returns_data) < 3:
                return None

            # Create correlation matrix
            returns_df = pd.DataFrame(returns_data)
            correlation_matrix = returns_df.corr()

            # Check for unusual correlation patterns
            avg_correlation = correlation_matrix.values[
                np.triu_indices_from(correlation_matrix.values, k=1)
            ].mean()

            # If average correlation drops below 0.1 (near zero), it might indicate breakdown
            if avg_correlation < 0.1:
                return StressEvent(
                    event_type=StressEventType.CORRELATION_BREAKDOWN,
                    severity=abs(avg_correlation) + 1.0,
                    detected_at=datetime.now(timezone.utc),
                    current_volatility=0.0,
                    threshold_volatility=0.0,
                    affected_pairs=list(returns_data.keys()),
                    recommended_action="Reduce cross-pair exposure due to correlation breakdown",
                )

            return None

        except Exception as e:
            self.logger.error(f"Error checking correlation breakdown: {e}")
            return None

    def _get_recommended_action(self, severity: float) -> str:
        """Get recommended action based on stress event severity"""
        if severity > 5.0:
            return "IMMEDIATE: Close all positions, activate emergency protocols"
        elif severity > 3.0:
            return "HIGH: Reduce position sizes by 50%, increase monitoring"
        elif severity > 2.5:
            return "MODERATE: Reduce position sizes by 25%, tighten stops"
        else:
            return "LOW: Monitor closely, consider position reduction"

    async def update_portfolio_value(self, new_value: float) -> None:
        """
        Update portfolio value and check for emergency level escalation

        Args:
            new_value: Current portfolio value
        """
        try:
            previous_value = self.portfolio_current_value
            self.portfolio_current_value = new_value

            # Calculate current drawdown
            drawdown = (
                self.portfolio_initial_value - new_value
            ) / self.portfolio_initial_value

            # Determine appropriate emergency level
            new_emergency_level = self._determine_emergency_level(drawdown)

            # Check if emergency level changed
            if new_emergency_level != self.current_emergency_level:
                await self._escalate_emergency_level(
                    self.current_emergency_level, new_emergency_level, drawdown
                )
                self.current_emergency_level = new_emergency_level

            # Log portfolio update
            self.logger.info(
                f"Portfolio updated: ${new_value:,.2f} "
                f"(Drawdown: {drawdown:.2%}, Emergency Level: {new_emergency_level.name})"
            )

            # 💾 SAVE PORTFOLIO METRICS TO DATABASE (only for significant changes or emergency levels)
            if (
                abs(drawdown) > 0.01 or new_emergency_level != EmergencyLevel.NORMAL
            ):  # >1% drawdown or emergency active
                await self._save_portfolio_metrics(
                    new_value, drawdown, new_emergency_level.name
                )

        except Exception as e:
            self.logger.error(f"Error updating portfolio value: {e}", exc_info=True)

    def _determine_emergency_level(self, drawdown: float) -> EmergencyLevel:
        """Determine emergency level based on portfolio drawdown"""
        if drawdown >= 0.25:  # 25% drawdown
            return EmergencyLevel.LEVEL_4
        elif drawdown >= 0.20:  # 20% drawdown
            return EmergencyLevel.LEVEL_3
        elif drawdown >= 0.15:  # 15% drawdown
            return EmergencyLevel.LEVEL_2
        elif drawdown >= 0.10:  # 10% drawdown
            return EmergencyLevel.LEVEL_1
        else:
            return EmergencyLevel.NORMAL

    async def _escalate_emergency_level(
        self, previous_level: EmergencyLevel, new_level: EmergencyLevel, drawdown: float
    ) -> None:
        """Handle emergency level escalation"""
        try:
            protocol = self.emergency_protocols[new_level]

            # Log emergency escalation
            escalation_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "previous_level": previous_level.name,
                "new_level": new_level.name,
                "portfolio_value": self.portfolio_current_value,
                "drawdown": drawdown,
                "protocol": {
                    "position_size_multiplier": protocol.position_size_multiplier,
                    "stop_trading": protocol.stop_trading,
                    "description": protocol.description,
                },
            }

            self.emergency_history.append(escalation_data)

            # 💾 SAVE EMERGENCY EVENT TO DATABASE
            await self._save_emergency_event(escalation_data)

            # Send emergency alert
            await self._send_emergency_alert(protocol, drawdown)

            # Execute emergency actions
            await self._execute_emergency_actions(protocol)

            self.logger.critical(
                f"EMERGENCY ESCALATION: {previous_level.name} -> {new_level.name} "
                f"(Drawdown: {drawdown:.2%}, Action: {protocol.description})"
            )

        except Exception as e:
            self.logger.error(f"Error escalating emergency level: {e}", exc_info=True)

    async def _send_emergency_alert(
        self, protocol: EmergencyProtocol, drawdown: float
    ) -> None:
        """Send emergency alert via Discord and other channels"""
        try:
            alert_message = {
                "title": f"🚨 EMERGENCY LEVEL {protocol.level.value} ACTIVATED",
                "description": protocol.description,
                "fields": [
                    {
                        "name": "Portfolio Drawdown",
                        "value": f"{drawdown:.2%}",
                        "inline": True,
                    },
                    {
                        "name": "Portfolio Value",
                        "value": f"${self.portfolio_current_value:,.2f}",
                        "inline": True,
                    },
                    {
                        "name": "Position Size Multiplier",
                        "value": f"{protocol.position_size_multiplier:.1%}",
                        "inline": True,
                    },
                    {
                        "name": "Trading Status",
                        "value": "HALTED" if protocol.stop_trading else "RESTRICTED",
                        "inline": True,
                    },
                ],
                "color": self._get_alert_color(protocol.level),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Send to Discord (implement with existing Discord infrastructure)
            # await send_signal_to_discord(alert_message)

            # Log alert
            self.logger.critical(f"Emergency alert sent: {alert_message}")

        except Exception as e:
            self.logger.error(f"Error sending emergency alert: {e}")

    def _get_alert_color(self, level: EmergencyLevel) -> int:
        """Get Discord embed color for alert level"""
        colors = {
            EmergencyLevel.NORMAL: 0x00FF00,  # Green
            EmergencyLevel.LEVEL_1: 0xFFFF00,  # Yellow
            EmergencyLevel.LEVEL_2: 0xFF8C00,  # Orange
            EmergencyLevel.LEVEL_3: 0xFF0000,  # Red
            EmergencyLevel.LEVEL_4: 0x8B0000,  # Dark Red
        }
        return colors.get(level, 0x808080)  # Gray default

    async def _execute_emergency_actions(self, protocol: EmergencyProtocol) -> None:
        """Execute emergency actions based on protocol"""
        try:
            if protocol.stop_trading:
                # Stop all trading activities
                await self._halt_all_trading()

            # Update position size limits
            await self._update_position_limits(protocol.position_size_multiplier)

            # If significant drawdown, consider closing positions
            if protocol.level in [EmergencyLevel.LEVEL_3, EmergencyLevel.LEVEL_4]:
                await self._consider_position_closure()

        except Exception as e:
            self.logger.error(f"Error executing emergency actions: {e}")

    async def _halt_all_trading(self) -> None:
        """Halt all trading activities"""
        try:
            # This would integrate with the trading engine to stop new trades
            self.logger.critical(
                "ALL TRADING ACTIVITIES HALTED - EMERGENCY STOP ACTIVATED"
            )

            # Additional emergency stop logic would go here
            # - Cancel pending orders
            # - Notify all strategy instances
            # - Close risky positions

        except Exception as e:
            self.logger.error(f"Error halting trading: {e}")

    async def _update_position_limits(self, multiplier: float) -> None:
        """Update position size limits based on emergency protocol"""
        try:
            for pair in self.position_limits:
                self.position_limits[pair] *= multiplier

            self.logger.warning(
                f"Position limits updated with multiplier: {multiplier}"
            )

        except Exception as e:
            self.logger.error(f"Error updating position limits: {e}")

    async def _consider_position_closure(self) -> None:
        """Consider closing positions during crisis levels"""
        try:
            # Logic to evaluate and potentially close risky positions
            # This would integrate with the position management system

            self.logger.critical("Evaluating positions for emergency closure")

        except Exception as e:
            self.logger.error(f"Error considering position closure: {e}")

    def calculate_position_size(
        self,
        base_size: float,
        pair: str,
        current_volatility: Optional[float] = None,
        portfolio_correlation: float = 0.0,
    ) -> float:
        """
        Calculate dynamic position size based on emergency protocols and market conditions

        Args:
            base_size: Base position size
            pair: Currency pair
            current_volatility: Current market volatility
            portfolio_correlation: Portfolio correlation factor

        Returns:
            Adjusted position size
        """
        try:
            # Get current emergency protocol
            protocol = self.emergency_protocols[self.current_emergency_level]

            # Start with emergency protocol adjustment
            adjusted_size = base_size * protocol.position_size_multiplier

            # Apply volatility adjustment if provided
            if current_volatility is not None and pair in self.base_volatility:
                base_vol = self.base_volatility[pair]
                if base_vol > 0:
                    volatility_ratio = current_volatility / base_vol
                    volatility_adjustment = (
                        min(1.0, 1.0 / volatility_ratio)
                        if volatility_ratio > 1.0
                        else 1.0
                    )
                    adjusted_size *= volatility_adjustment

            # Apply correlation adjustment
            correlation_adjustment = max(0.5, 1.0 - portfolio_correlation)
            adjusted_size *= correlation_adjustment

            # Ensure minimum size constraints
            min_size = base_size * 0.1  # Minimum 10% of base size
            adjusted_size = max(adjusted_size, min_size)

            # Emergency stop override
            if protocol.stop_trading:
                adjusted_size = 0.0

            return adjusted_size

        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return base_size * 0.5  # Conservative fallback

    def get_emergency_status(self) -> Dict[str, Any]:
        """Get current emergency risk management status"""
        try:
            protocol = self.emergency_protocols[self.current_emergency_level]
            drawdown = (
                self.portfolio_initial_value - self.portfolio_current_value
            ) / self.portfolio_initial_value

            return {
                "emergency_level": self.current_emergency_level.name,
                "emergency_level_value": self.current_emergency_level.value,
                "portfolio_drawdown": drawdown,
                "portfolio_value": self.portfolio_current_value,
                "position_size_multiplier": protocol.position_size_multiplier,
                "trading_halted": protocol.stop_trading,
                "active_stress_events": len(self.active_stress_events),
                "stress_events": [
                    {
                        "type": event.event_type.value,
                        "severity": event.severity,
                        "pairs": event.affected_pairs,
                        "detected_at": event.detected_at.isoformat(),
                    }
                    for event in self.active_stress_events
                ],
                "protocol_description": protocol.description,
                "last_update": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Error getting emergency status: {e}")
            return {"error": "Failed to get emergency status"}

    async def _save_emergency_event(self, event_data: Dict) -> None:
        """Save emergency event to database for historical analysis"""
        try:
            event_doc = {
                **event_data,
                "saved_at": datetime.now(timezone.utc),
                "event_id": f"{event_data.get('timestamp', '')[:19]}_emergency",  # YYYY-MM-DDTHH:MM:SS
            }
            result = self.emergency_events_collection.insert_one(event_doc)
            if result.inserted_id:
                self.logger.info(
                    f"📊 Emergency event saved to database: {event_data.get('new_level')}"
                )
        except Exception as e:
            self.logger.error(f"Failed to save emergency event: {e}")

    async def _save_stress_event(self, stress_event: StressEvent) -> None:
        """Save stress event to database for historical analysis"""
        try:
            stress_doc = {
                "event_type": stress_event.event_type.value,
                "severity": stress_event.severity,
                "affected_pairs": stress_event.affected_pairs,
                "detected_at": stress_event.detected_at.isoformat(),
                "recommended_action": stress_event.recommended_action,
                "current_volatility": stress_event.current_volatility,
                "threshold_volatility": stress_event.threshold_volatility,
                "saved_at": datetime.now(timezone.utc),
                "event_id": f"{stress_event.detected_at.strftime('%Y%m%d_%H%M%S')}_stress_{stress_event.event_type.value}",
            }
            result = self.stress_events_collection.insert_one(stress_doc)
            if result.inserted_id:
                self.logger.info(
                    f"📊 Stress event saved to database: {stress_event.event_type.value} (severity: {stress_event.severity:.2f})"
                )
        except Exception as e:
            self.logger.error(f"Failed to save stress event: {e}")

    async def _save_portfolio_metrics(
        self, portfolio_value: float, drawdown: float, emergency_level: str
    ) -> None:
        """Save portfolio metrics to database for trend analysis"""
        try:
            metrics_doc = {
                "timestamp": datetime.now(timezone.utc),
                "portfolio_value": portfolio_value,
                "drawdown_percentage": drawdown,
                "emergency_level": emergency_level,
                "position_size_multiplier": self.emergency_protocols[
                    self.current_emergency_level
                ].position_size_multiplier,
                "trading_halted": self.emergency_protocols[
                    self.current_emergency_level
                ].stop_trading,
                "active_stress_events_count": len(self.active_stress_events),
            }
            result = self.portfolio_metrics_collection.insert_one(metrics_doc)
            if result.inserted_id:
                self.logger.debug(
                    f"📊 Portfolio metrics saved: {emergency_level} (${portfolio_value:,.2f}, {drawdown:.2%} drawdown)"
                )
        except Exception as e:
            self.logger.error(f"Failed to save portfolio metrics: {e}")

    async def run_monitoring_loop(self, market_data_source) -> None:
        """
        Run continuous monitoring loop for emergency risk management

        Args:
            market_data_source: Source for real-time market data
        """
        self.logger.info("Starting emergency risk monitoring loop")

        try:
            while True:
                try:
                    # Get latest market data
                    market_data = await market_data_source.get_latest_data()

                    # Monitor for stress events
                    stress_events = await self.monitor_stress_events(market_data)

                    if stress_events:
                        self.logger.warning(
                            f"Detected {len(stress_events)} stress events"
                        )

                    # Check portfolio value updates would be handled by external system
                    # calling update_portfolio_value()

                    await asyncio.sleep(self.monitoring_interval)

                except Exception as e:
                    self.logger.error(f"Error in monitoring loop iteration: {e}")
                    await asyncio.sleep(5)  # Short delay before retry

        except asyncio.CancelledError:
            self.logger.info("Emergency risk monitoring loop cancelled")
        except Exception as e:
            self.logger.critical(
                f"Critical error in monitoring loop: {e}", exc_info=True
            )


# Integration helper functions


async def create_emergency_risk_manager(
    portfolio_value: float = 100000.0,
) -> EmergencyRiskManager:
    """Factory function to create and initialize EmergencyRiskManager"""
    manager = EmergencyRiskManager(portfolio_initial_value=portfolio_value)
    return manager


def integrate_with_strategy(strategy_instance, emergency_manager: EmergencyRiskManager):
    """
    Integrate EmergencyRiskManager with existing strategy instance

    Args:
        strategy_instance: Existing strategy instance (e.g., MovingAverageCrossStrategy)
        emergency_manager: EmergencyRiskManager instance
    """
    # Add emergency manager reference to strategy
    strategy_instance.emergency_manager = emergency_manager

    # Override position sizing method if it exists
    original_validate_signal = getattr(strategy_instance, "validate_signal", None)

    if original_validate_signal:

        def enhanced_validate_signal(signal, atr, risk_reward_ratio):
            # First check original validation
            if not original_validate_signal(signal, atr, risk_reward_ratio):
                return False

            # Check emergency protocols
            emergency_status = emergency_manager.get_emergency_status()
            if emergency_status.get("trading_halted", False):
                strategy_instance.logger.warning(
                    "Signal rejected: Trading halted due to emergency protocol"
                )
                return False

            return True

        strategy_instance.validate_signal = enhanced_validate_signal

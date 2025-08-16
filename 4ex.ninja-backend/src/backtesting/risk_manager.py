"""
Universal Risk Manager for Multi-Strategy Portfolio Management.

This module provides comprehensive risk management that works across
all strategy types and handles portfolio-level risk controls.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .strategy_interface import TradeSignal, AccountInfo
from .portfolio_manager import PortfolioState, StrategyAllocation

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk severity levels."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class RiskCheckResult:
    """Result of a risk check."""

    approved: bool
    risk_level: RiskLevel
    failed_checks: List[str]
    risk_adjustments: Dict[str, float]
    recommended_size: float = 0.0
    warnings: Optional[List[str]] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


@dataclass
class RiskLimits:
    """Universal risk limits configuration."""

    max_portfolio_risk: float = 0.10  # 10% max total portfolio risk
    max_position_risk: float = 0.02  # 2% max risk per position
    max_correlation_exposure: float = 0.30  # 30% max correlated exposure
    max_currency_exposure: float = 0.40  # 40% max exposure to any single currency
    max_strategies_per_pair: int = 2  # Max strategies trading same pair
    max_daily_trades: int = 10  # Max trades per day across all strategies
    max_consecutive_losses: int = 5  # Max consecutive losses before pause
    min_account_balance: float = 1000.0  # Minimum account balance to continue
    drawdown_limit: float = 0.20  # 20% max drawdown
    concentration_limit: float = 0.25  # 25% max concentration in any asset


class UniversalRiskManager:
    """
    Risk management that works across all strategy types.

    Provides portfolio-level risk controls, position sizing validation,
    and real-time risk monitoring for any strategy implementation.
    """

    def __init__(self, risk_limits: Optional[RiskLimits] = None):
        """
        Initialize risk manager.

        Args:
            risk_limits: Custom risk limits, uses defaults if None
        """
        self.risk_limits = risk_limits or RiskLimits()
        self.daily_trade_count = 0
        self.consecutive_losses = 0
        self.last_trade_date: Optional[datetime] = None
        self.risk_events_log: List[Dict[str, Any]] = []

        logger.info("Universal risk manager initialized")

    def _max_risk_level(self, level1: RiskLevel, level2: Any) -> RiskLevel:
        """
        Safely compare risk levels, handling cases where level2 might not be RiskLevel.

        Args:
            level1: First risk level (RiskLevel enum)
            level2: Second risk level (could be RiskLevel or Any)

        Returns:
            The higher risk level
        """
        if not isinstance(level2, RiskLevel):
            return level1
        return level1 if level1.value >= level2.value else level2

    def check_portfolio_risk_limits(
        self,
        portfolio_state: PortfolioState,
        new_signal: TradeSignal,
        strategy_name: str,
    ) -> RiskCheckResult:
        """
        Universal risk checking for any strategy type.

        Args:
            portfolio_state: Current portfolio state
            new_signal: Proposed trade signal
            strategy_name: Name of strategy generating signal

        Returns:
            Comprehensive risk check result
        """
        failed_checks = []
        warnings = []
        risk_adjustments = {}
        overall_risk_level = RiskLevel.LOW

        # 1. Check total portfolio risk
        portfolio_risk_check = self._check_total_portfolio_risk(
            portfolio_state, new_signal
        )
        if not portfolio_risk_check["approved"]:
            failed_checks.append("total_portfolio_risk")
            overall_risk_level = self._max_risk_level(
                overall_risk_level, portfolio_risk_check["risk_level"]
            )

        # 2. Check position-level risk
        position_risk_check = self._check_position_risk(new_signal, portfolio_state)
        if not position_risk_check["approved"]:
            failed_checks.append("position_risk")
            overall_risk_level = self._max_risk_level(
                overall_risk_level, position_risk_check["risk_level"]
            )
        else:
            risk_adjustments["position_size"] = position_risk_check.get(
                "adjustment", 1.0
            )

        # 3. Check correlation risk
        correlation_risk_check = self._check_correlation_risk(
            portfolio_state, new_signal
        )
        if not correlation_risk_check["approved"]:
            if correlation_risk_check["risk_level"] == RiskLevel.HIGH:
                failed_checks.append("correlation_risk")
            else:
                warnings.append(correlation_risk_check["warning"])
                risk_adjustments["correlation"] = correlation_risk_check.get(
                    "adjustment", 0.8
                )
            overall_risk_level = self._max_risk_level(
                overall_risk_level, correlation_risk_check["risk_level"]
            )

        # 4. Check currency concentration
        currency_risk_check = self._check_currency_concentration(
            portfolio_state, new_signal
        )
        if not currency_risk_check["approved"]:
            if currency_risk_check["risk_level"] == RiskLevel.HIGH:
                failed_checks.append("currency_concentration")
            else:
                warnings.append(currency_risk_check["warning"])
                risk_adjustments["currency"] = currency_risk_check.get(
                    "adjustment", 0.7
                )
            overall_risk_level = self._max_risk_level(
                overall_risk_level, currency_risk_check["risk_level"]
            )

        # 5. Check strategy limits
        strategy_risk_check = self._check_strategy_limits(
            portfolio_state, new_signal, strategy_name
        )
        if not strategy_risk_check["approved"]:
            failed_checks.append("strategy_limits")
            overall_risk_level = self._max_risk_level(
                overall_risk_level, strategy_risk_check["risk_level"]
            )

        # 6. Check daily trading limits
        daily_limit_check = self._check_daily_limits()
        if not daily_limit_check["approved"]:
            failed_checks.append("daily_limits")
            overall_risk_level = self._max_risk_level(
                overall_risk_level, daily_limit_check["risk_level"]
            )

        # Calculate recommended position size
        recommended_size = self._calculate_risk_adjusted_size(
            new_signal, portfolio_state, risk_adjustments
        )

        # Final approval decision
        approved = len(failed_checks) == 0

        # Log risk event
        self._log_risk_event(
            new_signal, strategy_name, failed_checks, warnings, approved
        )

        return RiskCheckResult(
            approved=approved,
            risk_level=overall_risk_level,
            failed_checks=failed_checks,
            risk_adjustments=risk_adjustments,
            recommended_size=recommended_size,
            warnings=warnings,
        )

    def _check_total_portfolio_risk(
        self, portfolio_state: PortfolioState, new_signal: TradeSignal
    ) -> Dict[str, Any]:
        """Check total portfolio risk limits."""
        current_risk = portfolio_state.total_risk

        # Estimate additional risk from new signal
        signal_risk = self._estimate_signal_risk(
            new_signal, portfolio_state.total_balance
        )
        total_risk_after = current_risk + signal_risk

        if total_risk_after <= self.risk_limits.max_portfolio_risk:
            return {
                "approved": True,
                "risk_level": RiskLevel.LOW,
                "current_risk": current_risk,
                "projected_risk": total_risk_after,
            }
        elif total_risk_after <= self.risk_limits.max_portfolio_risk * 1.2:
            return {
                "approved": False,
                "risk_level": RiskLevel.MEDIUM,
                "reason": f"Portfolio risk would be {total_risk_after:.1%}, exceeds limit {self.risk_limits.max_portfolio_risk:.1%}",
            }
        else:
            return {
                "approved": False,
                "risk_level": RiskLevel.HIGH,
                "reason": f"Portfolio risk would be {total_risk_after:.1%}, significantly exceeds limit",
            }

    def _check_position_risk(
        self, signal: TradeSignal, portfolio_state: PortfolioState
    ) -> Dict[str, Any]:
        """Check individual position risk limits."""
        signal_risk = self._estimate_signal_risk(signal, portfolio_state.total_balance)

        if signal_risk <= self.risk_limits.max_position_risk:
            return {"approved": True, "risk_level": RiskLevel.LOW, "adjustment": 1.0}
        elif signal_risk <= self.risk_limits.max_position_risk * 1.5:
            # Adjust position size to meet limit
            adjustment = self.risk_limits.max_position_risk / signal_risk
            return {
                "approved": True,
                "risk_level": RiskLevel.MEDIUM,
                "adjustment": adjustment,
                "warning": f"Position size adjusted to meet risk limit",
            }
        else:
            return {
                "approved": False,
                "risk_level": RiskLevel.HIGH,
                "reason": f"Position risk {signal_risk:.1%} exceeds maximum {self.risk_limits.max_position_risk:.1%}",
            }

    def _check_correlation_risk(
        self, portfolio_state: PortfolioState, new_signal: TradeSignal
    ) -> Dict[str, Any]:
        """Check correlation risk with existing positions."""
        active_pairs = list(portfolio_state.active_positions.keys())
        if not active_pairs:
            return {"approved": True, "risk_level": RiskLevel.LOW}

        # Simple correlation check based on currency overlap
        correlated_pairs = []
        for pair in active_pairs:
            if self._pairs_share_currency(new_signal.pair, pair):
                correlated_pairs.append(pair)

        correlation_count = len(correlated_pairs)

        if correlation_count == 0:
            return {"approved": True, "risk_level": RiskLevel.LOW}
        elif correlation_count <= 2:
            return {
                "approved": True,
                "risk_level": RiskLevel.MEDIUM,
                "adjustment": 0.8,
                "warning": f"Moderate correlation with {correlation_count} pairs",
            }
        else:
            return {
                "approved": False,
                "risk_level": RiskLevel.HIGH,
                "reason": f"High correlation with {correlation_count} active pairs",
            }

    def _check_currency_concentration(
        self, portfolio_state: PortfolioState, new_signal: TradeSignal
    ) -> Dict[str, Any]:
        """Check currency concentration limits."""
        if len(new_signal.pair) != 6:
            return {"approved": True, "risk_level": RiskLevel.LOW}

        base_currency = new_signal.pair[:3]
        quote_currency = new_signal.pair[3:]

        # Count exposure to these currencies
        base_exposure = 0
        quote_exposure = 0

        for position in portfolio_state.active_positions.values():
            if len(position.pair) == 6:
                pos_base = position.pair[:3]
                pos_quote = position.pair[3:]

                if pos_base == base_currency or pos_quote == base_currency:
                    base_exposure += 1
                if pos_base == quote_currency or pos_quote == quote_currency:
                    quote_exposure += 1

        max_exposure = max(base_exposure, quote_exposure)
        exposure_ratio = max_exposure / max(1, len(portfolio_state.active_positions))

        if exposure_ratio <= 0.3:  # 30% or less
            return {"approved": True, "risk_level": RiskLevel.LOW}
        elif exposure_ratio <= 0.5:  # 50% or less
            return {
                "approved": True,
                "risk_level": RiskLevel.MEDIUM,
                "adjustment": 0.7,
                "warning": f"Moderate currency concentration: {max_exposure} positions",
            }
        else:
            return {
                "approved": False,
                "risk_level": RiskLevel.HIGH,
                "reason": f"High currency concentration: {max_exposure} positions ({exposure_ratio:.1%})",
            }

    def _check_strategy_limits(
        self,
        portfolio_state: PortfolioState,
        new_signal: TradeSignal,
        strategy_name: str,
    ) -> Dict[str, Any]:
        """Check strategy-specific limits."""
        if strategy_name not in portfolio_state.strategy_allocations:
            return {"approved": True, "risk_level": RiskLevel.LOW}

        strategy_allocation = portfolio_state.strategy_allocations[strategy_name]

        # Check if strategy is active
        if not strategy_allocation.active:
            return {
                "approved": False,
                "risk_level": RiskLevel.HIGH,
                "reason": f"Strategy '{strategy_name}' is inactive",
            }

        # Check strategy allocation limits
        current_positions = len(strategy_allocation.positions)
        max_positions_per_strategy = 3  # Configurable limit

        if current_positions < max_positions_per_strategy:
            return {"approved": True, "risk_level": RiskLevel.LOW}
        else:
            return {
                "approved": False,
                "risk_level": RiskLevel.MEDIUM,
                "reason": f"Strategy has maximum positions: {current_positions}",
            }

    def _check_daily_limits(self) -> Dict[str, Any]:
        """Check daily trading limits."""
        current_date = datetime.now()

        # Reset counter if new day
        if self.last_trade_date and self.last_trade_date.date() != current_date.date():
            self.daily_trade_count = 0

        if self.daily_trade_count < self.risk_limits.max_daily_trades:
            return {"approved": True, "risk_level": RiskLevel.LOW}
        else:
            return {
                "approved": False,
                "risk_level": RiskLevel.MEDIUM,
                "reason": f"Daily trade limit reached: {self.daily_trade_count}",
            }

    def _estimate_signal_risk(self, signal: TradeSignal, balance: float) -> float:
        """Estimate risk percentage for a signal."""
        if balance <= 0:
            return 1.0  # 100% risk if no balance

        stop_distance = abs(signal.entry_price - signal.stop_loss)
        risk_amount = stop_distance * 1000  # Assume minimum position size

        return risk_amount / balance

    def _calculate_risk_adjusted_size(
        self,
        signal: TradeSignal,
        portfolio_state: PortfolioState,
        risk_adjustments: Dict[str, float],
    ) -> float:
        """Calculate risk-adjusted position size."""
        base_size = 1000  # Base position size

        # Apply all risk adjustments
        final_adjustment = 1.0
        for adjustment in risk_adjustments.values():
            final_adjustment *= adjustment

        return base_size * final_adjustment

    def _pairs_share_currency(self, pair1: str, pair2: str) -> bool:
        """Check if two pairs share a common currency."""
        if len(pair1) != 6 or len(pair2) != 6:
            return False

        pair1_currencies = [pair1[:3], pair1[3:]]
        pair2_currencies = [pair2[:3], pair2[3:]]

        return any(curr in pair2_currencies for curr in pair1_currencies)

    def _log_risk_event(
        self,
        signal: TradeSignal,
        strategy_name: str,
        failed_checks: List[str],
        warnings: List[str],
        approved: bool,
    ):
        """Log risk management event."""
        event = {
            "timestamp": datetime.now(),
            "signal": {
                "pair": signal.pair,
                "direction": signal.direction,
                "strategy": strategy_name,
            },
            "approved": approved,
            "failed_checks": failed_checks,
            "warnings": warnings,
        }

        self.risk_events_log.append(event)

        # Keep only last 100 events
        if len(self.risk_events_log) > 100:
            self.risk_events_log = self.risk_events_log[-100:]

    def update_trade_outcome(self, strategy_name: str, was_profitable: bool):
        """Update consecutive loss tracking."""
        current_date = datetime.now()
        self.last_trade_date = current_date
        self.daily_trade_count += 1

        if was_profitable:
            self.consecutive_losses = 0
        else:
            self.consecutive_losses += 1

        # Log if approaching consecutive loss limit
        if self.consecutive_losses >= self.risk_limits.max_consecutive_losses - 1:
            logger.warning(
                f"Approaching consecutive loss limit: {self.consecutive_losses}"
            )

    def get_risk_summary(self) -> Dict[str, Any]:
        """Get comprehensive risk management summary."""
        return {
            "risk_limits": {
                "max_portfolio_risk": self.risk_limits.max_portfolio_risk,
                "max_position_risk": self.risk_limits.max_position_risk,
                "max_correlation_exposure": self.risk_limits.max_correlation_exposure,
                "max_daily_trades": self.risk_limits.max_daily_trades,
            },
            "current_status": {
                "daily_trade_count": self.daily_trade_count,
                "consecutive_losses": self.consecutive_losses,
                "last_trade_date": self.last_trade_date,
            },
            "recent_events": len(self.risk_events_log),
            "risk_events_summary": self._summarize_risk_events(),
        }

    def _summarize_risk_events(self) -> Dict[str, Any]:
        """Summarize recent risk events."""
        if not self.risk_events_log:
            return {"total_events": 0}

        recent_events = self.risk_events_log[-20:]  # Last 20 events

        total_events = len(recent_events)
        approved_events = sum(1 for event in recent_events if event["approved"])
        rejected_events = total_events - approved_events

        # Count failure reasons
        failure_reasons = {}
        for event in recent_events:
            for reason in event["failed_checks"]:
                failure_reasons[reason] = failure_reasons.get(reason, 0) + 1

        return {
            "total_events": total_events,
            "approved": approved_events,
            "rejected": rejected_events,
            "approval_rate": approved_events / total_events if total_events > 0 else 0,
            "common_failures": failure_reasons,
        }

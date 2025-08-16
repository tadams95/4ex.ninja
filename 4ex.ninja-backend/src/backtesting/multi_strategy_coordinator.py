"""
Multi-Strategy Coordinator for Portfolio Management.

This module coordinates multiple strategies running simultaneously,
preventing conflicts and optimizing portfolio-level performance.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import pandas as pd

from .strategy_interface import BaseStrategy, TradeSignal
from .portfolio_manager import UniversalPortfolioManager, PortfolioDecision, Action
from .risk_manager import UniversalRiskManager, RiskCheckResult
from .correlation_manager import CorrelationManager
from .regime_detector import MarketRegime

logger = logging.getLogger(__name__)


class CoordinationAction(Enum):
    """Actions for signal coordination."""

    EXECUTE = "execute"
    REJECT = "reject"
    DELAY = "delay"
    MODIFY = "modify"


@dataclass
class CoordinatedSignal:
    """Signal after coordination processing."""

    original_signal: TradeSignal
    strategy_name: str
    action: CoordinationAction
    modified_size: Optional[float] = None
    delay_until: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    priority_score: float = 0.0


@dataclass
class SignalConflict:
    """Represents a conflict between multiple strategy signals."""

    pair: str
    conflicting_signals: List[Tuple[str, TradeSignal]]  # (strategy_name, signal)
    conflict_type: str  # "same_direction", "opposite_direction", "timing"
    resolution_method: str
    chosen_signal: Optional[Tuple[str, TradeSignal]] = None


class MultiStrategyCoordinator:
    """
    Coordinates multiple strategies running simultaneously.
    Prevents conflicts and optimizes portfolio-level performance.
    """

    def __init__(
        self,
        portfolio_manager: UniversalPortfolioManager,
        risk_manager: Optional[UniversalRiskManager] = None,
        correlation_manager: Optional[CorrelationManager] = None,
    ):
        """
        Initialize multi-strategy coordinator.

        Args:
            portfolio_manager: Portfolio management instance
            risk_manager: Risk management instance (optional)
            correlation_manager: Correlation analysis instance (optional)
        """
        self.portfolio_manager = portfolio_manager
        self.risk_manager = risk_manager or UniversalRiskManager()
        self.correlation_manager = correlation_manager or CorrelationManager()

        # Coordination settings
        self.max_signals_per_session = 10
        self.min_signal_spacing_minutes = 15
        self.conflict_resolution_method = "priority_score"

        # State tracking
        self.recent_signals: List[CoordinatedSignal] = []
        self.signal_conflicts: List[SignalConflict] = []
        self.execution_history: List[Dict[str, Any]] = []

        logger.info("Multi-strategy coordinator initialized")

    def coordinate_strategies(
        self,
        market_data: Dict[str, pd.DataFrame],
        current_regime: Optional[MarketRegime] = None,
    ) -> Dict[str, List[CoordinatedSignal]]:
        """
        Run all strategies and coordinate their signals for optimal portfolio performance.

        Args:
            market_data: Market data for all pairs
            current_regime: Current market regime

        Returns:
            Coordinated signals by strategy
        """
        # Generate signals from all active strategies
        all_signals = self._generate_all_signals(market_data, current_regime)

        # Detect and resolve conflicts
        coordinated_signals = self._coordinate_signal_conflicts(
            all_signals, current_regime
        )

        # Apply portfolio-level risk management
        final_signals = self._apply_portfolio_risk_management(coordinated_signals)

        # Apply timing coordination
        timed_signals = self._apply_timing_coordination(final_signals)

        # Log coordination results
        self._log_coordination_results(all_signals, timed_signals)

        return timed_signals

    def _generate_all_signals(
        self,
        market_data: Dict[str, pd.DataFrame],
        current_regime: Optional[MarketRegime],
    ) -> Dict[str, List[TradeSignal]]:
        """Generate signals from all active strategies."""
        all_signals = {}

        for (
            strategy_name,
            strategy_allocation,
        ) in self.portfolio_manager.strategy_allocations.items():
            if not strategy_allocation.active:
                continue

            strategy = strategy_allocation.strategy
            strategy_signals = []

            # Generate signals for all pairs
            for pair, data in market_data.items():
                try:
                    pair_signals = strategy.generate_signals(data, current_regime)
                    # Add strategy name to signals
                    for signal in pair_signals:
                        signal.strategy_name = strategy_name
                    strategy_signals.extend(pair_signals)
                except Exception as e:
                    logger.warning(
                        f"Failed to generate signals for {strategy_name} on {pair}: {e}"
                    )

            all_signals[strategy_name] = strategy_signals

        return all_signals

    def _coordinate_signal_conflicts(
        self,
        all_signals: Dict[str, List[TradeSignal]],
        current_regime: Optional[MarketRegime],
    ) -> Dict[str, List[CoordinatedSignal]]:
        """
        Handle conflicts when multiple strategies signal the same pair.

        Args:
            all_signals: All signals by strategy
            current_regime: Current market regime

        Returns:
            Coordinated signals by strategy
        """
        # Group signals by currency pair
        signals_by_pair = self._group_signals_by_pair(all_signals)

        coordinated = {}
        conflicts_detected = []

        for pair, pair_signals in signals_by_pair.items():
            if len(pair_signals) == 1:
                # No conflict, process normally
                strategy_name = list(pair_signals.keys())[0]
                signal = pair_signals[strategy_name][0]

                coordinated_signal = CoordinatedSignal(
                    original_signal=signal,
                    strategy_name=strategy_name,
                    action=CoordinationAction.EXECUTE,
                    priority_score=self._calculate_signal_priority(
                        signal, strategy_name, current_regime
                    ),
                )

                coordinated.setdefault(strategy_name, []).append(coordinated_signal)

            else:
                # Multiple strategies signaling same pair - need coordination
                conflict = self._detect_signal_conflict(pair, pair_signals)
                conflicts_detected.append(conflict)

                resolved_signals = self._resolve_signal_conflict(
                    conflict, current_regime
                )

                for strategy_name, coordinated_signal in resolved_signals.items():
                    coordinated.setdefault(strategy_name, []).append(coordinated_signal)

        self.signal_conflicts.extend(conflicts_detected)
        return coordinated

    def _group_signals_by_pair(
        self, all_signals: Dict[str, List[TradeSignal]]
    ) -> Dict[str, Dict[str, List[TradeSignal]]]:
        """Group all signals by currency pair."""
        signals_by_pair = {}

        for strategy_name, signals in all_signals.items():
            for signal in signals:
                pair = signal.pair
                if pair not in signals_by_pair:
                    signals_by_pair[pair] = {}
                if strategy_name not in signals_by_pair[pair]:
                    signals_by_pair[pair][strategy_name] = []
                signals_by_pair[pair][strategy_name].append(signal)

        return signals_by_pair

    def _detect_signal_conflict(
        self, pair: str, pair_signals: Dict[str, List[TradeSignal]]
    ) -> SignalConflict:
        """Detect the type of conflict between signals."""
        conflicting_signals = []
        directions = set()

        for strategy_name, signals in pair_signals.items():
            for signal in signals:
                conflicting_signals.append((strategy_name, signal))
                directions.add(signal.direction)

        # Determine conflict type
        if len(directions) == 1:
            conflict_type = "same_direction"
        else:
            conflict_type = "opposite_direction"

        return SignalConflict(
            pair=pair,
            conflicting_signals=conflicting_signals,
            conflict_type=conflict_type,
            resolution_method=self.conflict_resolution_method,
        )

    def _resolve_signal_conflict(
        self, conflict: SignalConflict, current_regime: Optional[MarketRegime]
    ) -> Dict[str, CoordinatedSignal]:
        """
        Resolve conflicts when multiple strategies want to trade the same pair.

        Args:
            conflict: Signal conflict details
            current_regime: Current market regime

        Returns:
            Resolved signals by strategy
        """
        resolved_signals = {}

        if conflict.conflict_type == "same_direction":
            # Multiple strategies agreeing - choose best one or combine
            resolved_signals = self._resolve_same_direction_conflict(
                conflict, current_regime
            )
        else:
            # Opposite directions - more complex resolution needed
            resolved_signals = self._resolve_opposite_direction_conflict(
                conflict, current_regime
            )

        return resolved_signals

    def _resolve_same_direction_conflict(
        self, conflict: SignalConflict, current_regime: Optional[MarketRegime]
    ) -> Dict[str, CoordinatedSignal]:
        """Resolve conflicts where strategies agree on direction."""
        # Score all signals
        scored_signals = []
        for strategy_name, signal in conflict.conflicting_signals:
            priority_score = self._calculate_signal_priority(
                signal, strategy_name, current_regime
            )
            scored_signals.append((strategy_name, signal, priority_score))

        # Sort by priority score
        scored_signals.sort(key=lambda x: x[2], reverse=True)

        resolved = {}

        # Execute highest priority signal
        best_strategy, best_signal, best_score = scored_signals[0]
        resolved[best_strategy] = CoordinatedSignal(
            original_signal=best_signal,
            strategy_name=best_strategy,
            action=CoordinationAction.EXECUTE,
            priority_score=best_score,
        )

        # Reject or delay others
        for strategy_name, signal, score in scored_signals[1:]:
            # Delay lower priority signals for potential later execution
            resolved[strategy_name] = CoordinatedSignal(
                original_signal=signal,
                strategy_name=strategy_name,
                action=CoordinationAction.DELAY,
                delay_until=datetime.now() + timedelta(minutes=30),
                rejection_reason="Lower priority in same-direction conflict",
                priority_score=score,
            )

        conflict.chosen_signal = (best_strategy, best_signal)
        return resolved

    def _resolve_opposite_direction_conflict(
        self, conflict: SignalConflict, current_regime: Optional[MarketRegime]
    ) -> Dict[str, CoordinatedSignal]:
        """Resolve conflicts where strategies disagree on direction."""
        # Score all signals
        scored_signals = []
        for strategy_name, signal in conflict.conflicting_signals:
            priority_score = self._calculate_signal_priority(
                signal, strategy_name, current_regime
            )
            scored_signals.append((strategy_name, signal, priority_score))

        # Sort by priority score
        scored_signals.sort(key=lambda x: x[2], reverse=True)

        resolved = {}

        # For opposite directions, be more conservative
        best_strategy, best_signal, best_score = scored_signals[0]

        # Only execute if significantly better than competing signals
        score_threshold = 0.2  # 20% better
        second_best_score = scored_signals[1][2] if len(scored_signals) > 1 else 0

        if best_score > second_best_score + score_threshold:
            # Clear winner - execute best signal
            resolved[best_strategy] = CoordinatedSignal(
                original_signal=best_signal,
                strategy_name=best_strategy,
                action=CoordinationAction.EXECUTE,
                priority_score=best_score,
            )

            # Reject others
            for strategy_name, signal, score in scored_signals[1:]:
                resolved[strategy_name] = CoordinatedSignal(
                    original_signal=signal,
                    strategy_name=strategy_name,
                    action=CoordinationAction.REJECT,
                    rejection_reason="Opposite direction conflict - clear winner",
                    priority_score=score,
                )

            conflict.chosen_signal = (best_strategy, best_signal)
        else:
            # No clear winner - reject all to avoid risk
            for strategy_name, signal, score in scored_signals:
                resolved[strategy_name] = CoordinatedSignal(
                    original_signal=signal,
                    strategy_name=strategy_name,
                    action=CoordinationAction.REJECT,
                    rejection_reason="Opposite direction conflict - no clear winner",
                    priority_score=score,
                )

        return resolved

    def _calculate_signal_priority(
        self,
        signal: TradeSignal,
        strategy_name: str,
        current_regime: Optional[MarketRegime],
    ) -> float:
        """
        Calculate priority score for a signal.

        Higher score = higher priority
        """
        priority = signal.signal_strength  # Base score from signal strength

        # Adjust for strategy performance
        if strategy_name in self.portfolio_manager.strategy_allocations:
            strategy_perf = self.portfolio_manager.strategy_allocations[
                strategy_name
            ].performance_tracker
            win_rate = strategy_perf.get("win_rate", 0.5)
            priority *= 0.5 + win_rate  # Boost for better performing strategies

        # Adjust for regime appropriateness
        if current_regime:
            regime_score = self._calculate_regime_appropriateness(
                strategy_name, current_regime
            )
            priority *= regime_score

        # Adjust for timing (recent signals get lower priority to prevent overtrading)
        timing_penalty = self._calculate_timing_penalty(signal.pair)
        priority *= timing_penalty

        return min(1.0, max(0.0, priority))  # Clamp to [0, 1]

    def _calculate_regime_appropriateness(
        self, strategy_name: str, regime: MarketRegime
    ) -> float:
        """Calculate how appropriate a strategy is for current regime."""
        # This would ideally be configured per strategy
        # For now, use simple heuristics

        if not hasattr(regime, "type"):
            return 1.0

        # Example regime scoring (would be strategy-specific in real implementation)
        if "ma" in strategy_name.lower():
            # MA strategies better in trending markets
            if hasattr(regime, "type") and getattr(regime, "type", None) == "TRENDING":
                return 1.2
            else:
                return 0.8
        elif "rsi" in strategy_name.lower():
            # RSI strategies better in ranging markets
            if hasattr(regime, "type") and getattr(regime, "type", None) == "RANGING":
                return 1.2
            else:
                return 0.8

        return 1.0  # Neutral score

    def _calculate_timing_penalty(self, pair: str) -> float:
        """Calculate timing penalty for pair based on recent activity."""
        recent_signals = [
            s
            for s in self.recent_signals
            if s.original_signal.pair == pair
            and (datetime.now() - s.original_signal.signal_time).total_seconds() < 3600
        ]  # Last hour

        if len(recent_signals) == 0:
            return 1.0
        elif len(recent_signals) <= 2:
            return 0.8
        else:
            return 0.5  # Heavy penalty for overtrading

    def _apply_portfolio_risk_management(
        self, coordinated_signals: Dict[str, List[CoordinatedSignal]]
    ) -> Dict[str, List[CoordinatedSignal]]:
        """Apply portfolio-level risk management to coordinated signals."""
        risk_managed_signals = {}

        for strategy_name, signals in coordinated_signals.items():
            risk_managed_signals[strategy_name] = []

            for coord_signal in signals:
                if coord_signal.action != CoordinationAction.EXECUTE:
                    # Already rejected/delayed, keep as is
                    risk_managed_signals[strategy_name].append(coord_signal)
                    continue

                # Check with portfolio risk manager
                portfolio_state = self.portfolio_manager._get_current_portfolio_state()
                risk_result = self.risk_manager.check_portfolio_risk_limits(
                    portfolio_state, coord_signal.original_signal, strategy_name
                )

                if risk_result.approved:
                    # Approved but may need size adjustment
                    if risk_result.recommended_size > 0:
                        coord_signal.modified_size = risk_result.recommended_size
                    risk_managed_signals[strategy_name].append(coord_signal)
                else:
                    # Rejected by risk manager
                    coord_signal.action = CoordinationAction.REJECT
                    coord_signal.rejection_reason = (
                        f"Risk management: {', '.join(risk_result.failed_checks)}"
                    )
                    risk_managed_signals[strategy_name].append(coord_signal)

        return risk_managed_signals

    def _apply_timing_coordination(
        self, signals: Dict[str, List[CoordinatedSignal]]
    ) -> Dict[str, List[CoordinatedSignal]]:
        """Apply timing coordination to prevent signal clustering."""
        timed_signals = {}
        all_execute_signals = []

        # Collect all signals marked for execution
        for strategy_name, strategy_signals in signals.items():
            for signal in strategy_signals:
                if signal.action == CoordinationAction.EXECUTE:
                    all_execute_signals.append((strategy_name, signal))

        # Sort by priority
        all_execute_signals.sort(key=lambda x: x[1].priority_score, reverse=True)

        # Apply spacing between signals
        executed_count = 0
        last_execution_time = datetime.now()

        for strategy_name, strategy_signals in signals.items():
            timed_signals[strategy_name] = []

            for signal in strategy_signals:
                if signal.action != CoordinationAction.EXECUTE:
                    timed_signals[strategy_name].append(signal)
                    continue

                # Check if we should execute this signal based on timing
                time_since_last = (
                    datetime.now() - last_execution_time
                ).total_seconds() / 60

                if (
                    executed_count < self.max_signals_per_session
                    and time_since_last >= self.min_signal_spacing_minutes
                ):
                    # Execute signal
                    timed_signals[strategy_name].append(signal)
                    executed_count += 1
                    last_execution_time = datetime.now()
                else:
                    # Delay signal
                    signal.action = CoordinationAction.DELAY
                    signal.delay_until = last_execution_time + timedelta(
                        minutes=self.min_signal_spacing_minutes
                    )
                    signal.rejection_reason = (
                        "Timing coordination - spacing requirements"
                    )
                    timed_signals[strategy_name].append(signal)

        return timed_signals

    def _log_coordination_results(
        self,
        original_signals: Dict[str, List[TradeSignal]],
        final_signals: Dict[str, List[CoordinatedSignal]],
    ):
        """Log coordination results for analysis."""
        original_count = sum(len(signals) for signals in original_signals.values())

        final_count = 0
        executed_count = 0
        rejected_count = 0
        delayed_count = 0

        for strategy_signals in final_signals.values():
            final_count += len(strategy_signals)
            for signal in strategy_signals:
                if signal.action == CoordinationAction.EXECUTE:
                    executed_count += 1
                elif signal.action == CoordinationAction.REJECT:
                    rejected_count += 1
                elif signal.action == CoordinationAction.DELAY:
                    delayed_count += 1

        coordination_result = {
            "timestamp": datetime.now(),
            "original_signals": original_count,
            "final_signals": final_count,
            "executed": executed_count,
            "rejected": rejected_count,
            "delayed": delayed_count,
            "conflicts_detected": len(self.signal_conflicts),
        }

        self.execution_history.append(coordination_result)

        # Keep only last 50 coordination sessions
        if len(self.execution_history) > 50:
            self.execution_history = self.execution_history[-50:]

        logger.info(
            f"Coordination completed: {executed_count}/{original_count} signals executed"
        )

    def get_coordination_summary(self) -> Dict[str, Any]:
        """Get comprehensive coordination summary."""
        if not self.execution_history:
            return {"status": "no_activity"}

        recent_sessions = self.execution_history[-10:]  # Last 10 sessions

        total_original = sum(session["original_signals"] for session in recent_sessions)
        total_executed = sum(session["executed"] for session in recent_sessions)
        total_rejected = sum(session["rejected"] for session in recent_sessions)
        total_delayed = sum(session["delayed"] for session in recent_sessions)

        execution_rate = total_executed / total_original if total_original > 0 else 0

        return {
            "recent_sessions": len(recent_sessions),
            "total_signals_processed": total_original,
            "execution_rate": execution_rate,
            "signals_executed": total_executed,
            "signals_rejected": total_rejected,
            "signals_delayed": total_delayed,
            "total_conflicts": len(self.signal_conflicts),
            "current_coordination_settings": {
                "max_signals_per_session": self.max_signals_per_session,
                "min_signal_spacing_minutes": self.min_signal_spacing_minutes,
                "conflict_resolution_method": self.conflict_resolution_method,
            },
        }

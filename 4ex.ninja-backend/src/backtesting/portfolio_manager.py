"""
Universal Portfolio Manager for Multi-Strategy Backtesting.

This module manages multiple strategies simultaneously, handling portfolio-level
risk management, allocation management, and strategy coordination.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .strategy_interface import BaseStrategy, TradeSignal, AccountInfo
from .position_manager import Position, PositionManager
from .factor_analysis import FactorAnalyzer

logger = logging.getLogger(__name__)


class Action(Enum):
    """Portfolio decision actions."""

    ACCEPT = "accept"
    REJECT = "reject"
    REDUCE = "reduce"
    DELAY = "delay"


@dataclass
class PortfolioDecision:
    """Portfolio decision for a trade signal."""

    action: Action
    size: float = 0.0
    reason: str = ""
    strategy_allocation_adjustment: float = 1.0
    risk_adjustment: float = 1.0


@dataclass
class StrategyAllocation:
    """Strategy allocation within the portfolio."""

    strategy: BaseStrategy
    allocation: float  # Percentage of portfolio allocated (0.0 to 1.0)
    positions: Dict[str, Position] = field(default_factory=dict)
    performance_tracker: Dict[str, Any] = field(default_factory=dict)
    last_signal_time: Optional[datetime] = None
    active: bool = True


@dataclass
class PortfolioState:
    """Current state of the portfolio."""

    total_balance: float
    available_balance: float
    total_risk: float
    active_positions: Dict[str, Position]
    strategy_allocations: Dict[str, StrategyAllocation]
    correlation_matrix: Dict[str, Dict[str, float]] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)


class UniversalPortfolioManager:
    """
    Portfolio manager that can handle multiple strategies simultaneously.
    Works with ANY strategy type that implements BaseStrategy interface.
    """

    def __init__(self, initial_balance: float, currency_pairs: List[str]):
        """Initialize portfolio manager."""
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.currency_pairs = currency_pairs

        # Strategy management
        self.strategy_allocations: Dict[str, StrategyAllocation] = {}
        self.position_manager = PositionManager()

        # Risk and correlation analysis
        self.correlation_analyzer = FactorAnalyzer()

        # Portfolio limits
        self.max_total_risk = 0.10  # 10% max total portfolio risk
        self.max_correlation_exposure = 0.30  # 30% max correlated exposure
        self.max_strategies_per_pair = 2  # Max strategies trading same pair
        self.min_strategy_allocation = 0.05  # 5% minimum strategy allocation

        # Performance tracking
        self.portfolio_history: List[Dict[str, Any]] = []

        logger.info(f"Portfolio manager initialized with {initial_balance} balance")

    def add_strategy(
        self, strategy_name: str, strategy: BaseStrategy, allocation: float
    ):
        """
        Add any strategy type to the portfolio.

        Args:
            strategy_name: Unique name for this strategy instance
            strategy: Strategy implementing BaseStrategy interface
            allocation: Percentage of portfolio allocated (0.0 to 1.0)
        """
        if allocation < self.min_strategy_allocation:
            raise ValueError(
                f"Strategy allocation must be at least {self.min_strategy_allocation}"
            )

        if (
            sum(alloc.allocation for alloc in self.strategy_allocations.values())
            + allocation
            > 1.0
        ):
            raise ValueError("Total strategy allocations cannot exceed 100%")

        self.strategy_allocations[strategy_name] = StrategyAllocation(
            strategy=strategy,
            allocation=allocation,
            performance_tracker={
                "total_signals": 0,
                "accepted_signals": 0,
                "rejected_signals": 0,
                "total_pnl": 0.0,
                "win_rate": 0.0,
                "avg_risk_reward": 0.0,
            },
        )

        logger.info(
            f"Added strategy '{strategy_name}' with {allocation:.1%} allocation"
        )

    def remove_strategy(self, strategy_name: str):
        """Remove a strategy from the portfolio."""
        if strategy_name not in self.strategy_allocations:
            raise ValueError(f"Strategy '{strategy_name}' not found in portfolio")

        # Close any open positions for this strategy
        strategy_allocation = self.strategy_allocations[strategy_name]
        for position in strategy_allocation.positions.values():
            self.position_manager.close_position(
                position.position_id, position.entry_price, "Strategy removed"
            )

        del self.strategy_allocations[strategy_name]
        logger.info(f"Removed strategy '{strategy_name}' from portfolio")

    def evaluate_signal_portfolio_impact(
        self, signal: TradeSignal, strategy_name: str
    ) -> PortfolioDecision:
        """
        Evaluate any signal type in portfolio context.
        Works with MA, RSI, Bollinger, ICT, or any other strategy signals.
        """
        if strategy_name not in self.strategy_allocations:
            return PortfolioDecision(
                action=Action.REJECT,
                reason=f"Strategy '{strategy_name}' not found in portfolio",
            )

        strategy_allocation = self.strategy_allocations[strategy_name]
        if not strategy_allocation.active:
            return PortfolioDecision(
                action=Action.REJECT, reason=f"Strategy '{strategy_name}' is inactive"
            )

        # Check portfolio-level constraints
        portfolio_state = self._get_current_portfolio_state()

        # 1. Check total portfolio risk
        total_risk_check = self._check_total_portfolio_risk(
            portfolio_state, signal, strategy_name
        )
        if not total_risk_check.approved:
            return PortfolioDecision(
                action=Action.REJECT,
                reason=f"Portfolio risk limit exceeded: {total_risk_check.reason}",
            )

        # 2. Check correlation limits
        correlation_check = self._check_correlation_limits(portfolio_state, signal)
        if not correlation_check.approved:
            return PortfolioDecision(
                action=(
                    Action.REJECT
                    if correlation_check.severity == "high"
                    else Action.REDUCE
                ),
                reason=f"Correlation limit issue: {correlation_check.reason}",
                size=(
                    correlation_check.suggested_size
                    if correlation_check.severity == "medium"
                    else 0.0
                ),
            )

        # 3. Check strategy allocation limits
        allocation_check = self._check_strategy_allocation_limits(strategy_name, signal)
        if not allocation_check.approved:
            return PortfolioDecision(
                action=Action.REDUCE,
                reason=f"Strategy allocation limit: {allocation_check.reason}",
                size=allocation_check.suggested_size,
            )

        # 4. Check pair exposure limits
        pair_check = self._check_pair_exposure_limits(portfolio_state, signal)
        if not pair_check.approved:
            return PortfolioDecision(
                action=(
                    Action.REJECT if pair_check.severity == "high" else Action.REDUCE
                ),
                reason=f"Pair exposure limit: {pair_check.reason}",
                size=(
                    pair_check.suggested_size
                    if pair_check.severity == "medium"
                    else 0.0
                ),
            )

        # Calculate optimal position size
        optimal_size = self._calculate_portfolio_optimal_size(signal, strategy_name)

        return PortfolioDecision(
            action=Action.ACCEPT,
            size=optimal_size,
            reason="Signal approved for portfolio",
            strategy_allocation_adjustment=1.0,
            risk_adjustment=1.0,
        )

    def _calculate_portfolio_optimal_size(
        self, signal: TradeSignal, strategy_name: str
    ) -> float:
        """
        Calculate position size considering:
        - Strategy-specific sizing from the strategy itself
        - Portfolio-level correlation limits
        - Strategy allocation limits
        - Total portfolio risk limits
        """
        strategy_allocation = self.strategy_allocations[strategy_name]

        # Get strategy-specific size recommendation
        account_info = self._get_account_info()
        strategy_size = strategy_allocation.strategy.calculate_position_size(
            signal, account_info
        )

        # Apply strategy allocation limit
        allocation_percentage = strategy_allocation.allocation
        max_strategy_size = (
            self.current_balance * allocation_percentage * 0.1
        )  # Max 10% per trade

        # Apply correlation adjustment
        correlation_adjustment = self._calculate_correlation_adjustment(signal.pair)

        # Apply portfolio risk adjustment
        portfolio_risk_adjustment = self._calculate_portfolio_risk_adjustment()

        # Final size calculation
        final_size = min(
            strategy_size,
            max_strategy_size * correlation_adjustment * portfolio_risk_adjustment,
        )

        return max(1000, final_size)  # Minimum position size

    def _get_current_portfolio_state(self) -> PortfolioState:
        """Get current portfolio state."""
        all_positions = {}
        total_risk = 0.0

        # Collect all positions from all strategies
        for strategy_name, allocation in self.strategy_allocations.items():
            for position_id, position in allocation.positions.items():
                all_positions[position_id] = position
                # Calculate risk for this position
                risk = (
                    abs(position.entry_price - position.stop_loss)
                    * position.position_size
                )
                total_risk += risk

        return PortfolioState(
            total_balance=self.current_balance,
            available_balance=self.current_balance - total_risk,
            total_risk=(
                total_risk / self.current_balance if self.current_balance > 0 else 0.0
            ),
            active_positions=all_positions,
            strategy_allocations=self.strategy_allocations,
            last_updated=datetime.now(),
        )

    def _get_all_active_pairs(self) -> List[str]:
        """Get all currency pairs with active positions across all strategies."""
        all_pairs = set()
        for strategy_allocation in self.strategy_allocations.values():
            all_pairs.update(strategy_allocation.positions.keys())
        return list(all_pairs)

    def _check_total_portfolio_risk(
        self, portfolio_state: PortfolioState, signal: TradeSignal, strategy_name: str
    ) -> Any:
        """Check if adding this signal would exceed total portfolio risk limits."""
        current_risk = portfolio_state.total_risk

        # Estimate risk for new signal
        signal_risk = (
            abs(signal.entry_price - signal.stop_loss) * 1000
        )  # Assume minimum size
        signal_risk_percentage = signal_risk / self.current_balance

        total_risk_after = current_risk + signal_risk_percentage

        class RiskCheck:
            def __init__(self, approved: bool, reason: str = ""):
                self.approved = approved
                self.reason = reason

        if total_risk_after <= self.max_total_risk:
            return RiskCheck(True)
        else:
            return RiskCheck(
                False,
                f"Total risk would be {total_risk_after:.1%}, exceeds limit {self.max_total_risk:.1%}",
            )

    def _check_correlation_limits(
        self, portfolio_state: PortfolioState, signal: TradeSignal
    ) -> Any:
        """Check correlation limits for the signal pair."""
        active_pairs = self._get_all_active_pairs()

        class CorrelationCheck:
            def __init__(
                self,
                approved: bool,
                severity: str = "low",
                reason: str = "",
                suggested_size: float = 0.0,
            ):
                self.approved = approved
                self.severity = severity
                self.reason = reason
                self.suggested_size = suggested_size

        if not active_pairs:
            return CorrelationCheck(True)

        # Simple correlation check based on currency pair overlaps
        overlapping_pairs = [
            pair
            for pair in active_pairs
            if self._pairs_share_currency(signal.pair, pair)
        ]

        if len(overlapping_pairs) == 0:
            return CorrelationCheck(True)
        elif len(overlapping_pairs) <= 2:
            return CorrelationCheck(True, "medium", "Some currency overlap", 0.7)
        else:
            return CorrelationCheck(
                False, "high", f"Too many overlapping pairs: {overlapping_pairs}"
            )

    def _check_strategy_allocation_limits(
        self, strategy_name: str, signal: TradeSignal
    ) -> Any:
        """Check if strategy is within its allocation limits."""
        strategy_allocation = self.strategy_allocations[strategy_name]

        # Calculate current strategy exposure
        current_strategy_value = sum(
            pos.position_size * pos.entry_price
            for pos in strategy_allocation.positions.values()
        )

        strategy_limit = self.current_balance * strategy_allocation.allocation

        class AllocationCheck:
            def __init__(
                self, approved: bool, reason: str = "", suggested_size: float = 0.0
            ):
                self.approved = approved
                self.reason = reason
                self.suggested_size = suggested_size

        if current_strategy_value < strategy_limit * 0.8:  # 80% of allocation
            return AllocationCheck(True)
        elif current_strategy_value < strategy_limit:
            remaining = strategy_limit - current_strategy_value
            return AllocationCheck(
                True,
                f"Near allocation limit, {remaining:.0f} remaining",
                remaining * 0.1,  # Conservative size
            )
        else:
            return AllocationCheck(
                False,
                f"Strategy allocation exceeded: {current_strategy_value:.0f} > {strategy_limit:.0f}",
            )

    def _check_pair_exposure_limits(
        self, portfolio_state: PortfolioState, signal: TradeSignal
    ) -> Any:
        """Check pair exposure limits."""
        strategies_trading_pair = sum(
            1
            for alloc in self.strategy_allocations.values()
            if signal.pair in alloc.positions
        )

        class PairCheck:
            def __init__(
                self,
                approved: bool,
                severity: str = "low",
                reason: str = "",
                suggested_size: float = 0.0,
            ):
                self.approved = approved
                self.severity = severity
                self.reason = reason
                self.suggested_size = suggested_size

        if strategies_trading_pair < self.max_strategies_per_pair:
            return PairCheck(True)
        else:
            return PairCheck(
                False,
                "high",
                f"Too many strategies trading {signal.pair}: {strategies_trading_pair}",
            )

    def _calculate_correlation_adjustment(self, pair: str) -> float:
        """Calculate correlation-based position size adjustment."""
        active_pairs = self._get_all_active_pairs()
        if not active_pairs:
            return 1.0

        # Count overlapping currencies
        overlaps = sum(
            1
            for active_pair in active_pairs
            if self._pairs_share_currency(pair, active_pair)
        )

        # Reduce size based on overlaps
        if overlaps == 0:
            return 1.0
        elif overlaps <= 2:
            return 0.8
        else:
            return 0.5

    def _calculate_portfolio_risk_adjustment(self) -> float:
        """Calculate portfolio-level risk adjustment."""
        portfolio_state = self._get_current_portfolio_state()

        # Reduce position sizes as portfolio risk increases
        if portfolio_state.total_risk < 0.05:  # Less than 5% risk
            return 1.0
        elif portfolio_state.total_risk < 0.08:  # Less than 8% risk
            return 0.8
        else:  # Approaching limit
            return 0.5

    def _pairs_share_currency(self, pair1: str, pair2: str) -> bool:
        """Check if two currency pairs share a common currency."""
        if len(pair1) != 6 or len(pair2) != 6:
            return False

        pair1_base, pair1_quote = pair1[:3], pair1[3:]
        pair2_base, pair2_quote = pair2[:3], pair2[3:]

        return (
            pair1_base == pair2_base
            or pair1_base == pair2_quote
            or pair1_quote == pair2_base
            or pair1_quote == pair2_quote
        )

    def _get_account_info(self) -> AccountInfo:
        """Get account information for strategy position sizing."""
        return AccountInfo(
            balance=self.current_balance,
            equity=self.current_balance,
            margin_used=0.0,  # Simplified for backtesting
            free_margin=self.current_balance,
            max_position_size=self.current_balance * 0.1,  # Max 10% per position
        )

    def update_strategy_performance(
        self, strategy_name: str, trade_result: Dict[str, Any]
    ):
        """Update performance tracking for a strategy."""
        if strategy_name not in self.strategy_allocations:
            return

        strategy_allocation = self.strategy_allocations[strategy_name]
        performance = strategy_allocation.performance_tracker

        performance["total_signals"] += 1
        if trade_result.get("executed", False):
            performance["accepted_signals"] += 1
            performance["total_pnl"] += trade_result.get("pnl", 0.0)
        else:
            performance["rejected_signals"] += 1

        # Update win rate and other metrics
        if performance["accepted_signals"] > 0:
            winning_trades = trade_result.get("winning_trades", 0)
            performance["win_rate"] = winning_trades / performance["accepted_signals"]

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get comprehensive portfolio summary."""
        portfolio_state = self._get_current_portfolio_state()

        strategy_summaries = {}
        for strategy_name, allocation in self.strategy_allocations.items():
            strategy_summaries[strategy_name] = {
                "allocation": allocation.allocation,
                "active_positions": len(allocation.positions),
                "performance": allocation.performance_tracker,
                "strategy_type": allocation.strategy.__class__.__name__,
            }

        return {
            "total_balance": portfolio_state.total_balance,
            "available_balance": portfolio_state.available_balance,
            "total_risk": portfolio_state.total_risk,
            "active_positions": len(portfolio_state.active_positions),
            "active_pairs": self._get_all_active_pairs(),
            "strategies": strategy_summaries,
            "last_updated": portfolio_state.last_updated,
        }

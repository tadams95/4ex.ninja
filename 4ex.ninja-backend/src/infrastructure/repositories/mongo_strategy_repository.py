"""
MongoDB Strategy Repository Implementation

Concrete implementation of IStrategyRepository for MongoDB database operations.
Provides optimized queries and strategy-specific operations including
performance tracking, lifecycle management, and validation.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
import copy

from .mongo_base_repository import MongoBaseRepository
from ...core.interfaces.strategy_repository import IStrategyRepository
from ...core.entities.strategy import Strategy, StrategyType, StrategyStatus
from ...core.interfaces.repository import RepositoryError

# Set up logging
logger = logging.getLogger(__name__)


class MongoStrategyRepository(MongoBaseRepository[Strategy], IStrategyRepository):
    """
    MongoDB implementation of strategy repository.

    Provides optimized queries for strategy-specific operations including
    filtering by type, status, performance metrics, and lifecycle management.
    """

    def __init__(self, database: Any, session: Optional[Any] = None):
        """
        Initialize the strategy repository.

        Args:
            database: MongoDB database instance
            session: Optional MongoDB session for transactions
        """
        super().__init__(database, "strategies", Strategy, session)

    async def get_by_name(self, name: str) -> Optional[Strategy]:
        """Get a strategy by its name."""
        try:
            filters = {"name": name}
            results = await self.find_by_criteria(filters, limit=1)
            return results[0] if results else None
        except Exception as e:
            raise RepositoryError(
                f"Failed to get strategy by name {name}", original_error=e
            )

    async def get_by_type(
        self, strategy_type: StrategyType, limit: Optional[int] = None
    ) -> List[Strategy]:
        """Get all strategies of a specific type."""
        try:
            filters = {"strategy_type": strategy_type.value}
            return await self.find_by_criteria(
                filters=filters, limit=limit, sort_by="created_at", sort_order="desc"
            )
        except Exception as e:
            raise RepositoryError(
                f"Failed to get strategies by type {strategy_type.value}",
                original_error=e,
            )

    async def get_by_status(
        self, status: StrategyStatus, limit: Optional[int] = None
    ) -> List[Strategy]:
        """Get all strategies with a specific status."""
        try:
            filters = {"status": status.value}
            return await self.find_by_criteria(
                filters=filters, limit=limit, sort_by="updated_at", sort_order="desc"
            )
        except Exception as e:
            raise RepositoryError(
                f"Failed to get strategies by status {status.value}", original_error=e
            )

    async def get_active_strategies(
        self, limit: Optional[int] = None
    ) -> List[Strategy]:
        """Get all currently active strategies."""
        try:
            filters = {"status": StrategyStatus.ACTIVE.value}
            return await self.find_by_criteria(
                filters=filters, limit=limit, sort_by="updated_at", sort_order="desc"
            )
        except Exception as e:
            raise RepositoryError("Failed to get active strategies", original_error=e)

    async def get_by_pair(
        self, pair: str, limit: Optional[int] = None
    ) -> List[Strategy]:
        """Get all strategies for a specific currency pair."""
        try:
            filters = {"pair": pair}
            return await self.find_by_criteria(
                filters=filters, limit=limit, sort_by="created_at", sort_order="desc"
            )
        except Exception as e:
            raise RepositoryError(
                f"Failed to get strategies by pair {pair}", original_error=e
            )

    async def get_by_timeframe(
        self, timeframe: str, limit: Optional[int] = None
    ) -> List[Strategy]:
        """Get all strategies for a specific timeframe."""
        try:
            filters = {"timeframe": timeframe}
            return await self.find_by_criteria(
                filters=filters, limit=limit, sort_by="created_at", sort_order="desc"
            )
        except Exception as e:
            raise RepositoryError(
                f"Failed to get strategies by timeframe {timeframe}", original_error=e
            )

    async def get_by_creator(
        self, creator: str, limit: Optional[int] = None
    ) -> List[Strategy]:
        """Get all strategies created by a specific user."""
        try:
            filters = {"creator": creator}
            return await self.find_by_criteria(
                filters=filters, limit=limit, sort_by="created_at", sort_order="desc"
            )
        except Exception as e:
            raise RepositoryError(
                f"Failed to get strategies by creator {creator}", original_error=e
            )

    async def search_by_tags(
        self, tags: List[str], limit: Optional[int] = None
    ) -> List[Strategy]:
        """Search strategies by tags."""
        try:
            # MongoDB query to find strategies that have any of the specified tags
            filters = {"tags": {"$in": tags}}
            return await self.find_by_criteria(
                filters=filters, limit=limit, sort_by="updated_at", sort_order="desc"
            )
        except Exception as e:
            raise RepositoryError(
                f"Failed to search strategies by tags {tags}", original_error=e
            )

    async def get_top_performing(
        self,
        metric: str = "total_pnl",
        limit: int = 10,
        time_period_days: Optional[int] = None,
    ) -> List[Strategy]:
        """Get top performing strategies based on a specific metric."""
        try:
            filters = {}

            # Add time period filter if specified
            if time_period_days:
                cutoff_date = datetime.utcnow() - timedelta(days=time_period_days)
                filters["updated_at"] = {"gte": cutoff_date}

            # Get strategies and sort by the specified metric
            strategies = await self.find_by_criteria(
                filters=filters,
                limit=limit * 2,  # Get more to sort properly
                sort_by="updated_at",
                sort_order="desc",
            )

            # Sort by the performance metric
            if metric == "total_pnl":
                strategies.sort(
                    key=lambda s: float(s.performance.total_pnl), reverse=True
                )
            elif metric == "win_rate":
                strategies.sort(key=lambda s: s.performance.win_rate, reverse=True)
            elif metric == "profit_factor":
                strategies.sort(key=lambda s: s.performance.profit_factor, reverse=True)
            else:
                # Default to total PnL
                strategies.sort(
                    key=lambda s: float(s.performance.total_pnl), reverse=True
                )

            return strategies[:limit]

        except Exception as e:
            raise RepositoryError(
                f"Failed to get top performing strategies by {metric}", original_error=e
            )

    async def update_performance(
        self, strategy_id: str, performance_data: Dict[str, Any]
    ) -> bool:
        """Update performance metrics for a strategy."""
        try:
            strategy = await self.get_by_id(strategy_id)
            if not strategy:
                return False

            # Update performance fields
            for key, value in performance_data.items():
                if hasattr(strategy.performance, key):
                    if key in [
                        "total_pnl",
                        "average_win",
                        "average_loss",
                        "max_drawdown",
                        "last_30_days_pnl",
                    ]:
                        setattr(strategy.performance, key, Decimal(str(value)))
                    else:
                        setattr(strategy.performance, key, value)

            strategy.performance.update_metrics()
            strategy.updated_at = datetime.utcnow()

            await self.update(strategy)

            logger.info(f"Updated performance for strategy {strategy_id}")
            return True

        except Exception as e:
            raise RepositoryError(
                f"Failed to update performance for strategy {strategy_id}",
                original_error=e,
            )

    async def activate_strategy(self, strategy_id: str) -> bool:
        """Activate a strategy."""
        try:
            strategy = await self.get_by_id(strategy_id)
            if not strategy:
                return False

            strategy.activate()
            await self.update(strategy)

            logger.info(f"Activated strategy {strategy_id}")
            return True

        except Exception as e:
            raise RepositoryError(
                f"Failed to activate strategy {strategy_id}", original_error=e
            )

    async def deactivate_strategy(self, strategy_id: str) -> bool:
        """Deactivate a strategy."""
        try:
            strategy = await self.get_by_id(strategy_id)
            if not strategy:
                return False

            strategy.deactivate()
            await self.update(strategy)

            logger.info(f"Deactivated strategy {strategy_id}")
            return True

        except Exception as e:
            raise RepositoryError(
                f"Failed to deactivate strategy {strategy_id}", original_error=e
            )

    async def archive_strategy(self, strategy_id: str) -> bool:
        """Archive a strategy."""
        try:
            strategy = await self.get_by_id(strategy_id)
            if not strategy:
                return False

            strategy.archive()
            await self.update(strategy)

            logger.info(f"Archived strategy {strategy_id}")
            return True

        except Exception as e:
            raise RepositoryError(
                f"Failed to archive strategy {strategy_id}", original_error=e
            )

    async def clone_strategy(
        self,
        strategy_id: str,
        new_name: str,
        modifications: Optional[Dict[str, Any]] = None,
    ) -> Optional[Strategy]:
        """Clone an existing strategy with optional modifications."""
        try:
            original = await self.get_by_id(strategy_id)
            if not original:
                return None

            # Create a copy of the original strategy
            cloned_data = original.to_dict()

            # Update with new name and ID
            cloned_data["strategy_id"] = (
                f"{strategy_id}_clone_{int(datetime.utcnow().timestamp())}"
            )
            cloned_data["name"] = new_name
            cloned_data["created_at"] = datetime.utcnow()
            cloned_data["updated_at"] = datetime.utcnow()
            cloned_data["status"] = StrategyStatus.INACTIVE.value

            # Reset performance metrics for the clone
            cloned_data["performance"] = {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "total_pnl": "0",
                "average_win": "0",
                "average_loss": "0",
                "profit_factor": 0.0,
                "max_drawdown": "0",
                "sharpe_ratio": None,
                "sortino_ratio": None,
                "last_30_days_pnl": "0",
                "last_7_days_trades": 0,
                "performance_start_date": None,
                "last_updated": datetime.utcnow(),
            }

            # Apply modifications if provided
            if modifications:
                for key, value in modifications.items():
                    if key in cloned_data:
                        cloned_data[key] = value

            # Create new strategy from modified data
            # Remove the MongoDB _id if present
            cloned_data.pop("_id", None)

            cloned_strategy = Strategy(**cloned_data)
            created_strategy = await self.create(cloned_strategy)

            logger.info(
                f"Cloned strategy {strategy_id} to {created_strategy.strategy_id}"
            )
            return created_strategy

        except Exception as e:
            raise RepositoryError(
                f"Failed to clone strategy {strategy_id}", original_error=e
            )

    async def get_strategy_statistics(self, strategy_id: str) -> Dict[str, Any]:
        """Get comprehensive statistics for a strategy."""
        try:
            strategy = await self.get_by_id(strategy_id)
            if not strategy:
                return {}

            stats = {
                "strategy_id": strategy.strategy_id,
                "name": strategy.name,
                "type": strategy.strategy_type.value,
                "status": strategy.status.value,
                "pair": strategy.pair,
                "timeframe": strategy.timeframe,
                "created_at": strategy.created_at,
                "updated_at": strategy.updated_at,
                "last_signal_time": strategy.last_signal_time,
                "performance": strategy.performance.to_dict(),
                "parameters": strategy.parameters.to_dict(),
                "tags": strategy.tags,
                "required_data_periods": strategy.get_required_data_periods(),
                "is_active": strategy.is_active(),
                "is_testing": strategy.is_testing(),
            }

            return stats

        except Exception as e:
            raise RepositoryError(
                f"Failed to get strategy statistics for {strategy_id}", original_error=e
            )

    async def validate_strategy_parameters(self, strategy: Strategy) -> Dict[str, Any]:
        """Validate strategy parameters and configuration."""
        try:
            issues = []
            warnings = []

            # Validate strategy type specific parameters
            if strategy.strategy_type == StrategyType.MOVING_AVERAGE_CROSSOVER:
                if not strategy.parameters.fast_ma_period:
                    issues.append(
                        "Fast MA period is required for Moving Average Crossover strategy"
                    )
                if not strategy.parameters.slow_ma_period:
                    issues.append(
                        "Slow MA period is required for Moving Average Crossover strategy"
                    )
                if (
                    strategy.parameters.fast_ma_period
                    and strategy.parameters.slow_ma_period
                    and strategy.parameters.fast_ma_period
                    >= strategy.parameters.slow_ma_period
                ):
                    issues.append("Fast MA period must be less than slow MA period")

            # Validate risk management parameters
            if strategy.parameters.atr_period and strategy.parameters.atr_period < 1:
                issues.append("ATR period must be positive")

            if (
                strategy.parameters.sl_atr_multiplier
                and strategy.parameters.sl_atr_multiplier <= 0
            ):
                issues.append("Stop loss ATR multiplier must be positive")

            if (
                strategy.parameters.tp_atr_multiplier
                and strategy.parameters.tp_atr_multiplier <= 0
            ):
                issues.append("Take profit ATR multiplier must be positive")

            if (
                strategy.parameters.min_rr_ratio
                and strategy.parameters.min_rr_ratio <= 0
            ):
                warnings.append("Minimum risk-reward ratio should be positive")

            # Validate position sizing
            if (
                strategy.parameters.position_size_value
                and strategy.parameters.position_size_value <= 0
            ):
                issues.append("Position size must be positive")

            if strategy.parameters.max_risk_per_trade and (
                strategy.parameters.max_risk_per_trade <= 0
                or strategy.parameters.max_risk_per_trade > 100
            ):
                warnings.append(
                    "Max risk per trade should be between 0 and 100 percent"
                )

            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "warnings": warnings,
                "strategy_id": strategy.strategy_id,
                "validation_time": datetime.utcnow(),
            }

        except Exception as e:
            raise RepositoryError(
                f"Failed to validate strategy parameters for {strategy.strategy_id}",
                original_error=e,
            )

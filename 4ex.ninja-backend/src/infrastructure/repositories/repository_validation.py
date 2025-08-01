"""
Repository Validation Utilities

Provides validation utilities and health checks for repository implementations.
Includes interface compliance checking, data integrity validation, and
performance monitoring capabilities.
"""

import logging
from typing import Dict, Any, List, Optional, Type, TypeVar
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import inspect
import asyncio

from ...core.interfaces.repository import IBaseRepository
from ...core.interfaces.signal_repository import ISignalRepository
from ...core.interfaces.market_data_repository import IMarketDataRepository
from ...core.interfaces.strategy_repository import IStrategyRepository
from ...core.interfaces.repository import RepositoryError

# Set up logging
logger = logging.getLogger(__name__)

T = TypeVar("T")


class IRepositoryValidator(ABC):
    """Abstract base class for repository validators."""

    @abstractmethod
    async def validate_interface_compliance(
        self, repository: IBaseRepository[T]
    ) -> Dict[str, Any]:
        """Validate that repository implements interface correctly."""
        pass

    @abstractmethod
    async def validate_data_integrity(
        self, repository: IBaseRepository[T]
    ) -> Dict[str, Any]:
        """Validate data integrity within repository."""
        pass

    @abstractmethod
    async def check_performance_metrics(
        self, repository: IBaseRepository[T]
    ) -> Dict[str, Any]:
        """Check repository performance metrics."""
        pass


class BaseRepositoryValidator(IRepositoryValidator):
    """Base validator for common repository validation logic."""

    def __init__(self, timeout_seconds: int = 30):
        """
        Initialize the validator.

        Args:
            timeout_seconds: Maximum time to wait for operations
        """
        self.timeout_seconds = timeout_seconds

    async def validate_interface_compliance(
        self, repository: IBaseRepository[T]
    ) -> Dict[str, Any]:
        """Validate that repository implements interface correctly."""
        try:
            issues = []

            # Check if repository implements required interface
            if not isinstance(repository, IBaseRepository):
                issues.append("Repository does not implement IBaseRepository interface")
                return {"valid": False, "issues": issues}

            # Check required methods exist and are callable
            required_methods = [
                "create",
                "get_by_id",
                "update",
                "delete",
                "get_all",
                "find_by_criteria",
                "count",
                "exists",
            ]

            for method_name in required_methods:
                if not hasattr(repository, method_name):
                    issues.append(f"Missing required method: {method_name}")
                elif not callable(getattr(repository, method_name)):
                    issues.append(f"Method {method_name} is not callable")
                else:
                    # Check if method is async
                    method = getattr(repository, method_name)
                    if not inspect.iscoroutinefunction(method):
                        issues.append(f"Method {method_name} is not async")

            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "checked_methods": required_methods,
                "validation_time": datetime.utcnow(),
            }

        except Exception as e:
            logger.error(f"Interface compliance validation failed: {e}")
            return {
                "valid": False,
                "issues": [f"Validation error: {str(e)}"],
                "validation_time": datetime.utcnow(),
            }

    async def validate_data_integrity(
        self, repository: IBaseRepository[T]
    ) -> Dict[str, Any]:
        """Validate basic data integrity."""
        try:
            issues = []

            # Test basic CRUD operations
            try:
                # Test count operation
                total_count = await asyncio.wait_for(
                    repository.count(), timeout=self.timeout_seconds
                )

                if total_count < 0:
                    issues.append("Count returned negative value")

            except asyncio.TimeoutError:
                issues.append("Count operation timed out")
            except Exception as e:
                issues.append(f"Count operation failed: {str(e)}")

            # Test pagination
            try:
                first_page = await asyncio.wait_for(
                    repository.get_all(limit=5, offset=0), timeout=self.timeout_seconds
                )

                if len(first_page) > 5:
                    issues.append("Limit parameter not respected")

            except asyncio.TimeoutError:
                issues.append("Pagination test timed out")
            except Exception as e:
                issues.append(f"Pagination test failed: {str(e)}")

            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "total_records": total_count if "total_count" in locals() else 0,
                "validation_time": datetime.utcnow(),
            }

        except Exception as e:
            logger.error(f"Data integrity validation failed: {e}")
            return {
                "valid": False,
                "issues": [f"Validation error: {str(e)}"],
                "validation_time": datetime.utcnow(),
            }

    async def check_performance_metrics(
        self, repository: IBaseRepository[T]
    ) -> Dict[str, Any]:
        """Check basic performance metrics."""
        try:
            metrics = {}

            # Test query performance
            start_time = datetime.utcnow()

            try:
                await asyncio.wait_for(repository.count(), timeout=self.timeout_seconds)

                count_duration = (datetime.utcnow() - start_time).total_seconds()
                metrics["count_query_duration_seconds"] = count_duration

                if count_duration > 5.0:  # 5 second threshold
                    metrics["performance_warnings"] = ["Count query is slow (>5s)"]

            except asyncio.TimeoutError:
                metrics["count_query_duration_seconds"] = self.timeout_seconds
                metrics["performance_warnings"] = ["Count query timed out"]

            # Test retrieval performance
            start_time = datetime.utcnow()

            try:
                await asyncio.wait_for(
                    repository.get_all(limit=10), timeout=self.timeout_seconds
                )

                retrieval_duration = (datetime.utcnow() - start_time).total_seconds()
                metrics["retrieval_query_duration_seconds"] = retrieval_duration

                if retrieval_duration > 3.0:  # 3 second threshold
                    if "performance_warnings" not in metrics:
                        metrics["performance_warnings"] = []
                    metrics["performance_warnings"].append(
                        "Retrieval query is slow (>3s)"
                    )

            except asyncio.TimeoutError:
                metrics["retrieval_query_duration_seconds"] = self.timeout_seconds
                if "performance_warnings" not in metrics:
                    metrics["performance_warnings"] = []
                metrics["performance_warnings"].append("Retrieval query timed out")

            metrics["validation_time"] = datetime.utcnow()

            return metrics

        except Exception as e:
            logger.error(f"Performance metrics check failed: {e}")
            return {
                "error": f"Performance check error: {str(e)}",
                "validation_time": datetime.utcnow(),
            }


class SignalRepositoryValidator(BaseRepositoryValidator):
    """Validator specific to signal repositories."""

    async def validate_interface_compliance(
        self, repository: ISignalRepository
    ) -> Dict[str, Any]:
        """Validate signal repository interface compliance."""
        # First run base validation
        base_result = await super().validate_interface_compliance(repository)

        if not base_result["valid"]:
            return base_result

        try:
            # Check signal-specific methods
            signal_methods = [
                "get_by_strategy_id",
                "get_by_pair",
                "get_by_status",
                "get_by_type",
                "get_active_signals",
                "get_recent_signals",
                "get_signals_by_performance",
                "update_signal_status",
                "close_signal",
                "calculate_strategy_performance",
            ]

            issues = base_result["issues"].copy()

            for method_name in signal_methods:
                if not hasattr(repository, method_name):
                    issues.append(f"Missing signal-specific method: {method_name}")
                elif not callable(getattr(repository, method_name)):
                    issues.append(f"Signal method {method_name} is not callable")
                elif not inspect.iscoroutinefunction(getattr(repository, method_name)):
                    issues.append(f"Signal method {method_name} is not async")

            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "checked_methods": base_result["checked_methods"] + signal_methods,
                "validation_time": datetime.utcnow(),
            }

        except Exception as e:
            logger.error(f"Signal repository validation failed: {e}")
            return {
                "valid": False,
                "issues": [f"Validation error: {str(e)}"],
                "validation_time": datetime.utcnow(),
            }


class MarketDataRepositoryValidator(BaseRepositoryValidator):
    """Validator specific to market data repositories."""

    async def validate_interface_compliance(
        self, repository: IMarketDataRepository
    ) -> Dict[str, Any]:
        """Validate market data repository interface compliance."""
        # First run base validation
        base_result = await super().validate_interface_compliance(repository)

        if not base_result["valid"]:
            return base_result

        try:
            # Check market data specific methods
            market_data_methods = [
                "get_by_pair_and_timeframe",
                "get_latest_candles",
                "get_candles_by_date_range",
                "add_candles",
                "update_latest_candle",
                "get_pairs_with_data",
                "get_available_timeframes",
                "get_data_coverage",
                "calculate_technical_indicators",
                "cleanup_old_data",
                "validate_data_integrity",
                "get_price_at_time",
            ]

            issues = base_result["issues"].copy()

            for method_name in market_data_methods:
                if not hasattr(repository, method_name):
                    issues.append(f"Missing market data method: {method_name}")
                elif not callable(getattr(repository, method_name)):
                    issues.append(f"Market data method {method_name} is not callable")
                elif not inspect.iscoroutinefunction(getattr(repository, method_name)):
                    issues.append(f"Market data method {method_name} is not async")

            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "checked_methods": base_result["checked_methods"] + market_data_methods,
                "validation_time": datetime.utcnow(),
            }

        except Exception as e:
            logger.error(f"Market data repository validation failed: {e}")
            return {
                "valid": False,
                "issues": [f"Validation error: {str(e)}"],
                "validation_time": datetime.utcnow(),
            }


class StrategyRepositoryValidator(BaseRepositoryValidator):
    """Validator specific to strategy repositories."""

    async def validate_interface_compliance(
        self, repository: IStrategyRepository
    ) -> Dict[str, Any]:
        """Validate strategy repository interface compliance."""
        # First run base validation
        base_result = await super().validate_interface_compliance(repository)

        if not base_result["valid"]:
            return base_result

        try:
            # Check strategy-specific methods
            strategy_methods = [
                "get_by_name",
                "get_by_type",
                "get_by_status",
                "get_active_strategies",
                "get_by_pair",
                "get_by_timeframe",
                "get_by_creator",
                "search_by_tags",
                "get_top_performing",
                "update_performance",
                "activate_strategy",
                "deactivate_strategy",
                "archive_strategy",
                "clone_strategy",
                "get_strategy_statistics",
                "validate_strategy_parameters",
            ]

            issues = base_result["issues"].copy()

            for method_name in strategy_methods:
                if not hasattr(repository, method_name):
                    issues.append(f"Missing strategy method: {method_name}")
                elif not callable(getattr(repository, method_name)):
                    issues.append(f"Strategy method {method_name} is not callable")
                elif not inspect.iscoroutinefunction(getattr(repository, method_name)):
                    issues.append(f"Strategy method {method_name} is not async")

            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "checked_methods": base_result["checked_methods"] + strategy_methods,
                "validation_time": datetime.utcnow(),
            }

        except Exception as e:
            logger.error(f"Strategy repository validation failed: {e}")
            return {
                "valid": False,
                "issues": [f"Validation error: {str(e)}"],
                "validation_time": datetime.utcnow(),
            }


class RepositoryHealthChecker:
    """Health checker for repository systems."""

    def __init__(self):
        """Initialize the health checker."""
        self.validators = {
            "signal": SignalRepositoryValidator(),
            "market_data": MarketDataRepositoryValidator(),
            "strategy": StrategyRepositoryValidator(),
        }

    async def run_full_health_check(
        self, repositories: Dict[str, IBaseRepository[Any]]
    ) -> Dict[str, Any]:
        """
        Run comprehensive health check on all repositories.

        Args:
            repositories: Dictionary of repository name to repository instance

        Returns:
            Health check results
        """
        try:
            results = {
                "overall_health": "healthy",
                "check_time": datetime.utcnow(),
                "repository_results": {},
                "summary": {
                    "total_repositories": len(repositories),
                    "healthy_repositories": 0,
                    "unhealthy_repositories": 0,
                    "total_issues": 0,
                },
            }

            for repo_name, repository in repositories.items():
                logger.info(f"Running health check for {repo_name} repository")

                validator = self.validators.get(repo_name, BaseRepositoryValidator())

                # Run all validation checks
                interface_result = await validator.validate_interface_compliance(
                    repository
                )
                integrity_result = await validator.validate_data_integrity(repository)
                performance_result = await validator.check_performance_metrics(
                    repository
                )

                repo_result = {
                    "interface_compliance": interface_result,
                    "data_integrity": integrity_result,
                    "performance_metrics": performance_result,
                    "overall_healthy": (
                        interface_result.get("valid", False)
                        and integrity_result.get("valid", False)
                    ),
                }

                results["repository_results"][repo_name] = repo_result

                # Update summary
                if repo_result["overall_healthy"]:
                    results["summary"]["healthy_repositories"] += 1
                else:
                    results["summary"]["unhealthy_repositories"] += 1
                    results["overall_health"] = "unhealthy"

                # Count total issues
                total_issues = len(interface_result.get("issues", [])) + len(
                    integrity_result.get("issues", [])
                )
                results["summary"]["total_issues"] += total_issues

            logger.info(
                f"Health check completed. Overall status: {results['overall_health']}"
            )
            return results

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "overall_health": "critical",
                "error": str(e),
                "check_time": datetime.utcnow(),
            }

    async def run_quick_health_check(
        self, repositories: Dict[str, IBaseRepository[Any]]
    ) -> Dict[str, Any]:
        """
        Run quick health check focusing on basic connectivity.

        Args:
            repositories: Dictionary of repository name to repository instance

        Returns:
            Quick health check results
        """
        try:
            results = {
                "overall_health": "healthy",
                "check_time": datetime.utcnow(),
                "repository_status": {},
                "response_times": {},
            }

            for repo_name, repository in repositories.items():
                start_time = datetime.utcnow()

                try:
                    # Quick connectivity test
                    await asyncio.wait_for(repository.count(), timeout=5)

                    response_time = (datetime.utcnow() - start_time).total_seconds()
                    results["repository_status"][repo_name] = "healthy"
                    results["response_times"][repo_name] = response_time

                except asyncio.TimeoutError:
                    results["repository_status"][repo_name] = "timeout"
                    results["response_times"][repo_name] = 5.0
                    results["overall_health"] = "degraded"

                except Exception as e:
                    results["repository_status"][repo_name] = f"error: {str(e)}"
                    results["overall_health"] = "unhealthy"

            return results

        except Exception as e:
            logger.error(f"Quick health check failed: {e}")
            return {
                "overall_health": "critical",
                "error": str(e),
                "check_time": datetime.utcnow(),
            }


# Utility functions for easy access
async def validate_repository_interface(
    repository: IBaseRepository[T], repository_type: str = "base"
) -> Dict[str, Any]:
    """
    Validate repository interface compliance.

    Args:
        repository: Repository instance to validate
        repository_type: Type of repository ("base", "signal", "market_data", "strategy")

    Returns:
        Validation results
    """
    validators = {
        "base": BaseRepositoryValidator(),
        "signal": SignalRepositoryValidator(),
        "market_data": MarketDataRepositoryValidator(),
        "strategy": StrategyRepositoryValidator(),
    }

    validator = validators.get(repository_type, BaseRepositoryValidator())
    return await validator.validate_interface_compliance(repository)


async def check_repository_health(
    repositories: Dict[str, IBaseRepository[Any]], quick: bool = False
) -> Dict[str, Any]:
    """
    Check health of repository system.

    Args:
        repositories: Dictionary of repository instances
        quick: Whether to run quick check only

    Returns:
        Health check results
    """
    health_checker = RepositoryHealthChecker()

    if quick:
        return await health_checker.run_quick_health_check(repositories)
    else:
        return await health_checker.run_full_health_check(repositories)

"""
Streamlined data infrastructure for swing trading backtesting.

This module provides a unified interface for managing multiple data providers
with focus on swing trading requirements (4H, Daily, Weekly timeframes).
"""

import asyncio
from typing import List, Dict, Optional, Tuple, Union
from datetime import datetime, timedelta
from decimal import Decimal
import logging
from dataclasses import dataclass, field
from enum import Enum

from .data_providers.base_provider import (
    BaseDataProvider,
    SwingCandleData,
    DataQualityMetrics,
)
from .data_providers.oanda_provider import OandaProvider
from .data_providers.alpha_vantage_provider import AlphaVantageProvider

logger = logging.getLogger(__name__)


class DataSourceStatus(Enum):
    """Data source status enumeration."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass
class DataSourceHealth:
    """Data source health information."""

    provider_name: str
    status: DataSourceStatus
    last_check: datetime
    error_message: Optional[str] = None
    response_time_ms: Optional[float] = None


@dataclass
class SwingTradingCosts:
    """
    Simplified transaction cost model for swing trading.

    This model focuses on the major cost components that impact swing trading
    strategies over longer holding periods.
    """

    def calculate_costs(
        self,
        position_size: Decimal,
        hold_days: int,
        pair: str,
        provider: Optional[BaseDataProvider] = None,
    ) -> Dict[str, Decimal]:
        """
        Calculate total trading costs for a swing trade.

        Args:
            position_size: Position size in base currency units
            hold_days: Number of days to hold the position
            pair: Currency pair
            provider: Data provider for spread/swap rates (optional)

        Returns:
            Dictionary with cost breakdown
        """
        costs = {}

        # Spread cost (entry + exit) - use synchronous approach for simplicity
        if provider:
            # For swing trading, use default spreads to avoid async complications
            spread_pips = self._get_default_spread(pair)
        else:
            spread_pips = self._get_default_spread(pair)

        pip_value = self._calculate_pip_value(pair, position_size)
        spread_cost = spread_pips * pip_value * 2  # Entry + Exit
        costs["spread_cost"] = spread_cost

        # Financing cost (swap/rollover)
        if provider:
            # Use default swap rates for simplicity in swing trading
            daily_swap = self._get_default_swap_rate(pair)
        else:
            daily_swap = self._get_default_swap_rate(pair)

        financing_cost = (
            position_size * hold_days * daily_swap / Decimal("10000")
        )  # Convert from pips
        costs["financing_cost"] = financing_cost

        # Commission (basic assumption for swing trading)
        commission = position_size * Decimal("0.00002")  # 0.002% of position size
        costs["commission"] = commission

        # Total cost
        total_cost = spread_cost + abs(financing_cost) + commission
        costs["total_cost"] = total_cost

        return costs

    def _get_default_spread(self, pair: str) -> Decimal:
        """Get default spread assumptions for swing trading."""
        default_spreads = {
            "EUR_USD": Decimal("1.5"),
            "GBP_USD": Decimal("2.0"),
            "USD_JPY": Decimal("1.8"),
            "USD_CHF": Decimal("2.2"),
            "AUD_USD": Decimal("2.5"),
            "USD_CAD": Decimal("2.8"),
            "NZD_USD": Decimal("3.0"),
        }
        return default_spreads.get(pair, Decimal("3.0"))

    def _get_default_swap_rate(self, pair: str) -> Decimal:
        """Get default swap rate assumptions (daily, in pips)."""
        default_swaps = {
            "EUR_USD": Decimal("-0.5"),
            "GBP_USD": Decimal("-0.8"),
            "USD_JPY": Decimal("0.3"),
            "USD_CHF": Decimal("0.2"),
            "AUD_USD": Decimal("-0.6"),
            "USD_CAD": Decimal("0.1"),
            "NZD_USD": Decimal("-0.7"),
        }
        return default_swaps.get(pair, Decimal("0.0"))

    def _calculate_pip_value(self, pair: str, position_size: Decimal) -> Decimal:
        """Calculate pip value for position sizing."""
        if pair.endswith("JPY"):
            pip_size = Decimal("0.01")
        else:
            pip_size = Decimal("0.0001")

        return position_size * pip_size


class DataInfrastructure:
    """
    Main data infrastructure class for swing trading backtesting.

    This class manages multiple data providers with automatic failover,
    data validation, and cost calculation capabilities.
    """

    def __init__(self, alpha_vantage_key: Optional[str] = None):
        """
        Initialize data infrastructure.

        Args:
            alpha_vantage_key: Alpha Vantage API key (optional)
        """
        self.providers: List[BaseDataProvider] = []
        self.primary_provider: Optional[BaseDataProvider] = None
        self.cost_calculator = SwingTradingCosts()
        self._provider_health: Dict[str, DataSourceHealth] = {}

        # Initialize providers
        self._initialize_providers(alpha_vantage_key)

    def _initialize_providers(self, alpha_vantage_key: Optional[str] = None):
        """Initialize data providers in priority order."""
        try:
            # Primary provider: OANDA
            oanda_provider = OandaProvider()
            self.providers.append(oanda_provider)

            # Secondary provider: Alpha Vantage
            av_provider = AlphaVantageProvider(alpha_vantage_key)
            self.providers.append(av_provider)

            # Sort by priority
            self.providers.sort(key=lambda p: p.priority)

            logger.info(f"Initialized {len(self.providers)} data providers")

        except Exception as e:
            logger.error(f"Failed to initialize providers: {str(e)}")

    async def connect_all(self) -> bool:
        """
        Connect to all data providers.

        Returns:
            True if at least one provider connected successfully
        """
        connection_tasks = []
        for provider in self.providers:
            task = asyncio.create_task(self._connect_provider(provider))
            connection_tasks.append(task)

        results = await asyncio.gather(*connection_tasks, return_exceptions=True)

        # Find primary provider (first healthy provider by priority)
        for provider in self.providers:
            if provider.is_available:
                if not self.primary_provider:
                    self.primary_provider = provider
                    logger.info(f"Primary provider set to: {provider.name}")
                break

        connected_count = sum(1 for provider in self.providers if provider.is_available)
        logger.info(f"Connected to {connected_count}/{len(self.providers)} providers")

        return connected_count > 0

    async def _connect_provider(self, provider: BaseDataProvider) -> bool:
        """Connect to a single provider."""
        try:
            start_time = datetime.utcnow()
            connected = await provider.connect()
            end_time = datetime.utcnow()

            response_time = (end_time - start_time).total_seconds() * 1000

            if connected:
                status = DataSourceStatus.HEALTHY
                error_message = None
                logger.info(f"Connected to {provider.name}")
            else:
                status = DataSourceStatus.UNAVAILABLE
                error_message = "Connection failed"
                logger.warning(f"Failed to connect to {provider.name}")

            self._provider_health[provider.name] = DataSourceHealth(
                provider_name=provider.name,
                status=status,
                last_check=end_time,
                error_message=error_message,
                response_time_ms=response_time,
            )

            return connected

        except Exception as e:
            logger.error(f"Error connecting to {provider.name}: {str(e)}")
            self._provider_health[provider.name] = DataSourceHealth(
                provider_name=provider.name,
                status=DataSourceStatus.UNAVAILABLE,
                last_check=datetime.utcnow(),
                error_message=str(e),
            )
            return False

    async def get_candles(
        self,
        pair: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        count: Optional[int] = None,
        validate: bool = True,
    ) -> List[SwingCandleData]:
        """
        Get historical candle data with automatic provider fallback.

        Args:
            pair: Currency pair
            timeframe: Timeframe ('4H', 'D', 'W')
            start_time: Start datetime
            end_time: End datetime
            count: Maximum number of candles
            validate: Whether to validate data quality

        Returns:
            List of candle data
        """
        if not self.providers:
            logger.error("No data providers available")
            return []

        # Try providers in priority order
        for provider in self.providers:
            if not provider.is_available:
                continue

            try:
                logger.info(
                    f"Fetching candles from {provider.name} for {pair} {timeframe}"
                )

                candles = await provider.get_candles(
                    pair, timeframe, start_time, end_time, count
                )

                if candles:
                    logger.info(
                        f"Retrieved {len(candles)} candles from {provider.name}"
                    )

                    # Validate data quality if requested
                    if validate:
                        quality = await provider.validate_data_quality(
                            pair, timeframe, start_time, end_time
                        )

                        if quality.gap_percentage > 50:  # More than 50% missing data
                            logger.warning(
                                f"Poor data quality from {provider.name}: {quality.gap_percentage:.1f}% gaps"
                            )
                            continue

                    return candles
                else:
                    logger.warning(f"No candles returned from {provider.name}")

            except Exception as e:
                logger.error(f"Error fetching candles from {provider.name}: {str(e)}")
                # Mark provider as degraded
                if provider.name in self._provider_health:
                    self._provider_health[provider.name].status = (
                        DataSourceStatus.DEGRADED
                    )
                continue

        logger.error("Failed to fetch candles from all providers")
        return []

    async def get_current_spread(self, pair: str) -> Optional[Decimal]:
        """
        Get current spread with provider fallback.

        Args:
            pair: Currency pair

        Returns:
            Current spread in pips
        """
        for provider in self.providers:
            if provider.is_available:
                try:
                    spread = await provider.get_current_spread(pair)
                    if spread:
                        return spread
                except Exception as e:
                    logger.warning(
                        f"Failed to get spread from {provider.name}: {str(e)}"
                    )
                    continue

        # Fallback to default spreads
        return self.cost_calculator._get_default_spread(pair)

    def calculate_trading_costs(
        self, position_size: Decimal, hold_days: int, pair: str
    ) -> Dict[str, Decimal]:
        """
        Calculate total trading costs for a swing trade.

        Args:
            position_size: Position size in base currency units
            hold_days: Number of days to hold position
            pair: Currency pair

        Returns:
            Cost breakdown dictionary
        """
        provider = self.primary_provider if self.primary_provider else None

        return self.cost_calculator.calculate_costs(
            position_size, hold_days, pair, provider
        )

    async def validate_data_across_providers(
        self, pair: str, timeframe: str, start_time: datetime, end_time: datetime
    ) -> Dict[str, DataQualityMetrics]:
        """
        Validate data quality across all available providers.

        Args:
            pair: Currency pair
            timeframe: Timeframe
            start_time: Start datetime
            end_time: End datetime

        Returns:
            Dictionary of quality metrics by provider
        """
        validation_tasks = []
        provider_names = []

        for provider in self.providers:
            if provider.is_available:
                task = asyncio.create_task(
                    provider.validate_data_quality(
                        pair, timeframe, start_time, end_time
                    )
                )
                validation_tasks.append(task)
                provider_names.append(provider.name)

        if not validation_tasks:
            return {}

        results = await asyncio.gather(*validation_tasks, return_exceptions=True)

        quality_metrics = {}
        for i, result in enumerate(results):
            if isinstance(result, DataQualityMetrics):
                quality_metrics[provider_names[i]] = result
            else:
                logger.error(
                    f"Validation failed for {provider_names[i]}: {str(result)}"
                )

        return quality_metrics

    async def health_check_all(self) -> Dict[str, DataSourceHealth]:
        """
        Perform health check on all providers.

        Returns:
            Dictionary of health status by provider name
        """
        health_tasks = []

        for provider in self.providers:
            task = asyncio.create_task(provider.health_check())
            health_tasks.append(task)

        results = await asyncio.gather(*health_tasks, return_exceptions=True)

        for i, result in enumerate(results):
            provider = self.providers[i]

            if isinstance(result, bool) and result:
                status = DataSourceStatus.HEALTHY
                error_message = None
            elif isinstance(result, bool):
                status = DataSourceStatus.UNAVAILABLE
                error_message = "Health check failed"
            else:
                status = DataSourceStatus.UNAVAILABLE
                error_message = str(result)

            self._provider_health[provider.name] = DataSourceHealth(
                provider_name=provider.name,
                status=status,
                last_check=datetime.utcnow(),
                error_message=error_message,
            )

        return self._provider_health.copy()

    async def close_all(self):
        """Close all provider connections."""
        for provider in self.providers:
            # Check if provider has a close method (e.g., AlphaVantageProvider)
            if hasattr(provider, "close") and callable(getattr(provider, "close")):
                try:
                    close_method = getattr(provider, "close")
                    await close_method()
                except Exception as e:
                    logger.warning(f"Error closing {provider.name}: {str(e)}")

        logger.info("All data provider connections closed")

    def get_provider_status(self) -> Dict[str, Dict]:
        """
        Get status summary of all providers.

        Returns:
            Dictionary with provider status information
        """
        status = {}

        for provider in self.providers:
            health = self._provider_health.get(provider.name)

            status[provider.name] = {
                "priority": provider.priority,
                "available": provider.is_available,
                "health_status": health.status.value if health else "unknown",
                "last_check": health.last_check.isoformat() if health else None,
                "error_message": health.error_message if health else None,
                "response_time_ms": health.response_time_ms if health else None,
            }

        return status

    def get_supported_pairs(self) -> List[str]:
        """Get list of supported currency pairs."""
        if self.providers:
            return self.providers[0].MAJOR_PAIRS
        return []

    def get_supported_timeframes(self) -> List[str]:
        """Get list of supported timeframes."""
        if self.providers:
            return self.providers[0].SWING_TIMEFRAMES
        return []

"""
Performance Tracker

Tracks strategy performance metrics and provides real-time performance
monitoring for the 4ex.ninja monitoring dashboard.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import redis
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""

    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    avg_trade_duration: float
    total_trades: int
    current_positions: int


class PerformanceTracker:
    """
    Real-time strategy performance tracking system

    Monitors and tracks strategy performance metrics in real-time
    for the monitoring dashboard.
    """

    def __init__(self, redis_host="localhost", redis_port=6379):
        try:
            self.redis_client = redis.Redis(
                host=redis_host, port=redis_port, decode_responses=True
            )
            self.redis_client.ping()
        except:
            logger.warning("Redis connection failed, using in-memory storage")
            self.redis_client = None

        # Configuration
        self.performance_key = "strategy_performance"
        self.regime_performance_key = "regime_performance"
        self.trades_key = "strategy_trades"

        # In-memory storage fallback
        self._memory_storage = {
            "performance": None,
            "regime_performance": [],
            "trades": [],
            "last_update": None,
        }

        self.is_initialized = False

    async def initialize(self):
        """Initialize the performance tracker"""
        try:
            logger.info("Initializing Performance Tracker...")

            # Initialize performance data if not exists
            await self._initialize_performance_data()

            self.is_initialized = True
            logger.info("Performance Tracker initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Performance Tracker: {e}")
            raise

    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the performance tracker"""
        try:
            # Test Redis connection if available
            redis_health = True
            if self.redis_client:
                try:
                    redis_health = self.redis_client.ping()
                except:
                    redis_health = False

            # Check last update time
            last_update = None
            if self.redis_client:
                try:
                    last_update = self.redis_client.get("performance_last_update")
                except:
                    pass

            if not last_update:
                last_update = self._memory_storage.get("last_update")

            if last_update:
                try:
                    if isinstance(last_update, str):
                        last_update_time = datetime.fromisoformat(last_update)
                    elif isinstance(last_update, datetime):
                        last_update_time = last_update
                    else:
                        # Handle unknown types
                        last_update_time = datetime.now() - timedelta(hours=1)

                    time_since_update = (
                        datetime.now() - last_update_time
                    ).total_seconds()
                    is_recent = time_since_update < 1800  # 30 minutes
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error parsing last_update time: {e}")
                    is_recent = False
            else:
                is_recent = False

            return {
                "status": "healthy" if redis_health and is_recent else "degraded",
                "redis_connected": redis_health,
                "last_update_recent": is_recent,
                "initialized": self.is_initialized,
            }

        except Exception as e:
            logger.error(f"Performance tracker health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall strategy performance summary"""
        try:
            # Get cached performance data
            cached_performance = None
            if self.redis_client:
                try:
                    cached_performance = self.redis_client.get(self.performance_key)
                except:
                    pass

            if not cached_performance:
                cached_performance = self._memory_storage.get("performance")

            if cached_performance:
                try:
                    if isinstance(cached_performance, str):
                        performance_data = json.loads(cached_performance)
                    elif isinstance(cached_performance, dict):
                        performance_data = cached_performance
                    else:
                        # Handle unknown types, generate fresh data
                        return await self._calculate_performance_summary()

                    return performance_data
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Error parsing cached performance data: {e}")
                    return await self._calculate_performance_summary()
            else:
                # Generate fresh performance data
                return await self._calculate_performance_summary()

        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return await self._get_default_performance_summary()

    async def get_performance_by_regime(self) -> List[Dict[str, Any]]:
        """Get performance breakdown by market regime"""
        try:
            # Get cached regime performance data
            cached_data = None
            if self.redis_client:
                try:
                    cached_data = self.redis_client.get(self.regime_performance_key)
                except:
                    pass

            if not cached_data:
                cached_data = self._memory_storage.get("regime_performance")

            if cached_data:
                try:
                    if isinstance(cached_data, str):
                        regime_performance = json.loads(cached_data)
                    elif isinstance(cached_data, list):
                        regime_performance = cached_data
                    else:
                        # Handle unknown types, generate fresh data
                        return await self._calculate_regime_performance()

                    return regime_performance
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Error parsing cached regime performance data: {e}")
                    return await self._calculate_regime_performance()
            else:
                # Generate fresh regime performance data
                return await self._calculate_regime_performance()

        except Exception as e:
            logger.error(f"Error getting performance by regime: {e}")
            return []

    async def get_chart_data(
        self, timeframe: str = "1d", chart_type: str = "equity_curve"
    ) -> Dict[str, Any]:
        """Get performance chart data"""
        try:
            # Simulate chart data (replace with actual implementation)
            if chart_type == "equity_curve":
                return await self._generate_equity_curve_data(timeframe)
            elif chart_type == "drawdown":
                return await self._generate_drawdown_data(timeframe)
            elif chart_type == "regime_returns":
                return await self._generate_regime_returns_data(timeframe)
            else:
                return {"error": f"Unknown chart type: {chart_type}"}

        except Exception as e:
            logger.error(f"Error getting chart data: {e}")
            return {"error": str(e)}

    async def get_strategy_health(self) -> Dict[str, Any]:
        """Get strategy health indicators"""
        try:
            performance = await self.get_performance_summary()

            # Calculate health indicators
            health_score = self._calculate_health_score(performance)
            warnings = self._check_performance_warnings(performance)

            return {
                "health_score": health_score,
                "status": self._get_health_status(health_score),
                "warnings": warnings,
                "last_update": datetime.now().isoformat(),
                "performance_metrics": performance,
            }

        except Exception as e:
            logger.error(f"Error getting strategy health: {e}")
            return {
                "health_score": 0.5,
                "status": "unknown",
                "warnings": ["Unable to calculate health metrics"],
                "error": str(e),
            }

    async def check_strategy_health(self) -> Optional[Dict[str, Any]]:
        """Check for strategy health issues"""
        try:
            health_data = await self.get_strategy_health()

            # Check for critical issues
            health_score = health_data.get("health_score", 0.5)
            warnings = health_data.get("warnings", [])

            if health_score < 0.3 or len(warnings) > 3:
                return {
                    "severity": "critical" if health_score < 0.2 else "warning",
                    "health_score": health_score,
                    "issues": warnings,
                    "timestamp": datetime.now().isoformat(),
                }

            return None

        except Exception as e:
            logger.error(f"Error checking strategy health: {e}")
            return None

    async def _initialize_performance_data(self):
        """Initialize performance data if not exists"""
        try:
            # Check if performance data exists
            existing_data = None
            if self.redis_client:
                try:
                    existing_data = self.redis_client.get(self.performance_key)
                except:
                    pass

            if not existing_data:
                # Create initial performance data
                initial_performance = await self._get_default_performance_summary()
                await self._cache_performance_data(initial_performance)

        except Exception as e:
            logger.error(f"Error initializing performance data: {e}")

    async def _calculate_performance_summary(self) -> Dict[str, Any]:
        """Calculate fresh performance summary"""
        try:
            # Simulate performance calculation (replace with actual implementation)
            import random

            # Generate realistic performance metrics
            total_return = (random.random() - 0.4) * 0.5  # -40% to +10% range
            sharpe_ratio = 0.5 + random.random() * 1.5  # 0.5 to 2.0
            max_drawdown = random.random() * 0.25  # 0% to 25%
            win_rate = 0.4 + random.random() * 0.4  # 40% to 80%
            avg_trade_duration = 2 + random.random() * 8  # 2 to 10 days
            total_trades = 50 + int(random.random() * 200)  # 50 to 250 trades
            current_positions = int(random.random() * 5)  # 0 to 4 positions

            performance_data = {
                "total_return": round(total_return, 4),
                "sharpe_ratio": round(sharpe_ratio, 2),
                "max_drawdown": round(max_drawdown, 4),
                "win_rate": round(win_rate, 3),
                "avg_trade_duration": round(avg_trade_duration, 1),
                "total_trades": total_trades,
                "current_positions": current_positions,
                "last_updated": datetime.now().isoformat(),
            }

            # Cache the result
            await self._cache_performance_data(performance_data)

            return performance_data

        except Exception as e:
            logger.error(f"Error calculating performance summary: {e}")
            return await self._get_default_performance_summary()

    async def _calculate_regime_performance(self) -> List[Dict[str, Any]]:
        """Calculate performance by regime"""
        try:
            # Simulate regime performance data
            import random

            regimes = [
                "trending_high_vol",
                "trending_low_vol",
                "ranging_high_vol",
                "ranging_low_vol",
            ]

            regime_performance = []
            for regime in regimes:
                performance = {
                    "regime_name": regime,
                    "return_pct": round((random.random() - 0.4) * 0.3, 4),
                    "sharpe_ratio": round(0.3 + random.random() * 1.5, 2),
                    "win_rate": round(0.3 + random.random() * 0.5, 3),
                    "avg_duration_days": round(2 + random.random() * 6, 1),
                    "trade_count": 10 + int(random.random() * 50),
                    "drawdown": round(random.random() * 0.15, 4),
                }
                regime_performance.append(performance)

            # Cache the result
            await self._cache_regime_performance(regime_performance)

            return regime_performance

        except Exception as e:
            logger.error(f"Error calculating regime performance: {e}")
            return []

    async def _generate_equity_curve_data(self, timeframe: str) -> Dict[str, Any]:
        """Generate equity curve chart data"""
        try:
            import random
            from datetime import timedelta

            # Parse timeframe
            hours = self._parse_timeframe(timeframe)
            points = min(100, hours)  # Max 100 data points

            # Generate time series
            end_time = datetime.now()
            time_step = timedelta(hours=hours / points)

            equity_data = []
            current_equity = 10000  # Starting equity

            for i in range(points):
                timestamp = end_time - timedelta(hours=hours) + (i * time_step)

                # Simulate equity movement
                change = (random.random() - 0.48) * 100  # Slight upward bias
                current_equity += change

                equity_data.append(
                    {
                        "timestamp": timestamp.isoformat(),
                        "equity": round(current_equity, 2),
                    }
                )

            return {
                "chart_type": "equity_curve",
                "timeframe": timeframe,
                "data": equity_data,
            }

        except Exception as e:
            logger.error(f"Error generating equity curve data: {e}")
            return {"error": str(e)}

    async def _generate_drawdown_data(self, timeframe: str) -> Dict[str, Any]:
        """Generate drawdown chart data"""
        try:
            import random
            from datetime import timedelta

            hours = self._parse_timeframe(timeframe)
            points = min(100, hours)

            end_time = datetime.now()
            time_step = timedelta(hours=hours / points)

            drawdown_data = []
            current_drawdown = 0

            for i in range(points):
                timestamp = end_time - timedelta(hours=hours) + (i * time_step)

                # Simulate drawdown (always negative or zero)
                change = random.random() * 0.02 - 0.01  # Small changes
                current_drawdown = min(0, current_drawdown + change)

                drawdown_data.append(
                    {
                        "timestamp": timestamp.isoformat(),
                        "drawdown": round(current_drawdown, 4),
                    }
                )

            return {
                "chart_type": "drawdown",
                "timeframe": timeframe,
                "data": drawdown_data,
            }

        except Exception as e:
            logger.error(f"Error generating drawdown data: {e}")
            return {"error": str(e)}

    async def _generate_regime_returns_data(self, timeframe: str) -> Dict[str, Any]:
        """Generate regime returns chart data"""
        try:
            import random

            regimes = [
                "trending_high_vol",
                "trending_low_vol",
                "ranging_high_vol",
                "ranging_low_vol",
            ]

            regime_returns = []
            for regime in regimes:
                returns = round((random.random() - 0.4) * 0.3, 4)
                regime_returns.append({"regime": regime, "returns": returns})

            return {
                "chart_type": "regime_returns",
                "timeframe": timeframe,
                "data": regime_returns,
            }

        except Exception as e:
            logger.error(f"Error generating regime returns data: {e}")
            return {"error": str(e)}

    def _calculate_health_score(self, performance: Dict[str, Any]) -> float:
        """Calculate overall strategy health score (0-1)"""
        try:
            # Simple health scoring based on key metrics
            score_components = []

            # Sharpe ratio component (0-1)
            sharpe = performance.get("sharpe_ratio", 0)
            sharpe_score = min(1.0, max(0.0, sharpe / 2.0))
            score_components.append(sharpe_score * 0.3)

            # Return component (0-1)
            total_return = performance.get("total_return", 0)
            return_score = min(1.0, max(0.0, (total_return + 0.2) / 0.4))
            score_components.append(return_score * 0.3)

            # Drawdown component (0-1) - inverted
            max_drawdown = performance.get("max_drawdown", 0.5)
            drawdown_score = max(0.0, 1.0 - (max_drawdown / 0.3))
            score_components.append(drawdown_score * 0.25)

            # Win rate component (0-1)
            win_rate = performance.get("win_rate", 0.5)
            win_rate_score = win_rate
            score_components.append(win_rate_score * 0.15)

            return sum(score_components)

        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return 0.5

    def _check_performance_warnings(self, performance: Dict[str, Any]) -> List[str]:
        """Check for performance warnings"""
        warnings = []

        try:
            # Check various performance metrics
            if performance.get("total_return", 0) < -0.2:
                warnings.append("High negative returns detected")

            if performance.get("max_drawdown", 0) > 0.15:
                warnings.append("High drawdown detected")

            if performance.get("sharpe_ratio", 1) < 0.5:
                warnings.append("Low Sharpe ratio")

            if performance.get("win_rate", 0.5) < 0.3:
                warnings.append("Low win rate")

            if performance.get("current_positions", 0) > 10:
                warnings.append("High number of open positions")

        except Exception as e:
            logger.error(f"Error checking performance warnings: {e}")
            warnings.append("Unable to analyze performance metrics")

        return warnings

    def _get_health_status(self, health_score: float) -> str:
        """Get health status from score"""
        if health_score >= 0.8:
            return "excellent"
        elif health_score >= 0.6:
            return "good"
        elif health_score >= 0.4:
            return "fair"
        elif health_score >= 0.2:
            return "poor"
        else:
            return "critical"

    async def _get_default_performance_summary(self) -> Dict[str, Any]:
        """Get default performance summary"""
        return {
            "total_return": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "win_rate": 0.0,
            "avg_trade_duration": 0.0,
            "total_trades": 0,
            "current_positions": 0,
            "last_updated": datetime.now().isoformat(),
        }

    async def _cache_performance_data(self, performance_data: Dict[str, Any]):
        """Cache performance data"""
        try:
            performance_json = json.dumps(performance_data, default=str)

            if self.redis_client:
                try:
                    self.redis_client.setex(
                        self.performance_key, 1800, performance_json
                    )  # 30 minutes
                    self.redis_client.set(
                        "performance_last_update", datetime.now().isoformat()
                    )
                except:
                    pass

            # Fallback to memory storage
            self._memory_storage["performance"] = performance_json
            self._memory_storage["last_update"] = datetime.now().isoformat()

        except Exception as e:
            logger.error(f"Error caching performance data: {e}")

    async def _cache_regime_performance(self, regime_performance: List[Dict[str, Any]]):
        """Cache regime performance data"""
        try:
            regime_json = json.dumps(regime_performance, default=str)

            if self.redis_client:
                try:
                    self.redis_client.setex(
                        self.regime_performance_key, 1800, regime_json
                    )
                except:
                    pass

            # Fallback to memory storage
            self._memory_storage["regime_performance"] = regime_json

        except Exception as e:
            logger.error(f"Error caching regime performance data: {e}")

    def _parse_timeframe(self, timeframe: str) -> int:
        """Parse timeframe string to hours"""
        timeframe_map = {"1h": 1, "4h": 4, "1d": 24, "1w": 168, "1m": 720}
        return timeframe_map.get(timeframe, 24)

    async def cleanup(self):
        """Cleanup resources"""
        try:
            logger.info("Cleaning up Performance Tracker...")
            # Close Redis connection if needed
            if self.redis_client:
                try:
                    self.redis_client.close()
                except:
                    pass

        except Exception as e:
            logger.error(f"Error during Performance Tracker cleanup: {e}")

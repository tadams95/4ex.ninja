"""
Real-Time Regime Monitor

Provides real-time market regime detection and monitoring capabilities
for the 4ex.ninja monitoring dashboard.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import redis
import pandas as pd
from dataclasses import dataclass

# For now, create a simplified version that doesn't depend on the complex backtesting modules
# This can be enhanced later to integrate with the actual regime detection system

logger = logging.getLogger(__name__)


@dataclass
class RegimeChangeEvent:
    """Represents a regime change event"""

    old_regime: str
    new_regime: str
    confidence: float
    timestamp: datetime
    strength: float
    volatility_level: str


class RegimeMonitor:
    """
    Real-time market regime monitoring system

    Continuously monitors market conditions and detects regime changes
    in real-time for strategy adjustment and alert generation.
    """

    def __init__(self, redis_host="localhost", redis_port=6379):
        try:
            self.redis_client = redis.Redis(
                host=redis_host, port=redis_port, decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
        except:
            logger.warning("Redis connection failed, using in-memory storage")
            self.redis_client = None

        # Configuration
        self.monitoring_pairs = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD"]
        self.update_interval = 300  # 5 minutes
        self.regime_history_key = "regime_history"
        self.current_regime_key = "current_regime"

        # State tracking
        self.last_regime = "ranging_low_vol"  # Default regime
        self.regime_start_time = datetime.now()
        self.is_initialized = False

        # In-memory storage fallback
        self._memory_storage = {
            "current_regime": None,
            "regime_history": [],
            "last_update": None,
        }

    async def initialize(self):
        """Initialize the regime monitor"""
        try:
            logger.info("Initializing Regime Monitor...")

            # Load initial regime state
            await self._load_current_regime()

            self.is_initialized = True
            logger.info("Regime Monitor initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Regime Monitor: {e}")
            raise

    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the regime monitor"""
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
                    last_update = self.redis_client.get("regime_last_update")
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
                    is_recent = time_since_update < 600  # 10 minutes
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error parsing last_update time: {e}")
                    is_recent = False
            else:
                is_recent = False

            return {
                "status": "healthy" if redis_health and is_recent else "degraded",
                "redis_connected": redis_health,
                "data_provider_healthy": True,  # Simplified for now
                "last_update_recent": is_recent,
                "monitoring_pairs": len(self.monitoring_pairs),
                "initialized": self.is_initialized,
            }

        except Exception as e:
            logger.error(f"Regime monitor health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def get_current_regime(self) -> Dict[str, Any]:
        """Get the current market regime status"""
        try:
            # Get cached regime data
            cached_regime = None
            if self.redis_client:
                try:
                    cached_regime = self.redis_client.get(self.current_regime_key)
                except:
                    pass

            if not cached_regime:
                cached_regime = self._memory_storage.get("current_regime")

            if cached_regime:
                try:
                    if isinstance(cached_regime, str):
                        regime_data = json.loads(cached_regime)
                    elif isinstance(cached_regime, dict):
                        regime_data = cached_regime
                    else:
                        # Handle unknown types, return default
                        return await self._get_default_regime_data()

                    # Calculate time in regime
                    if self.regime_start_time:
                        time_in_regime = int(
                            (datetime.now() - self.regime_start_time).total_seconds()
                            / 60
                        )
                        regime_data["time_in_regime"] = time_in_regime

                    return regime_data
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Error parsing cached regime data: {e}")
                    return await self._get_default_regime_data()
            else:
                # Return default regime data
                return await self._get_default_regime_data()

        except Exception as e:
            logger.error(f"Error getting current regime: {e}")
            return await self._get_default_regime_data()

    async def _get_default_regime_data(self) -> Dict[str, Any]:
        """Get default regime data"""
        return {
            "current_regime": self.last_regime,
            "confidence": 0.75,
            "regime_strength": 0.6,
            "time_in_regime": int(
                (datetime.now() - self.regime_start_time).total_seconds() / 60
            ),
            "last_change": self.regime_start_time,
            "volatility_level": "medium",
            "trend_direction": "sideways",
        }

    async def get_regime_history(
        self, timeframe: str = "1d", limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get historical regime changes"""
        try:
            # Parse timeframe
            hours = self._parse_timeframe(timeframe)
            cutoff_time = datetime.now() - timedelta(hours=hours)

            # Get regime history
            history_data = []
            if self.redis_client:
                try:
                    history_data = self.redis_client.lrange(
                        self.regime_history_key, 0, limit
                    )
                except:
                    pass

            if not history_data:
                history_data = self._memory_storage.get("regime_history", [])

            regime_history = []
            # Ensure history_data is iterable
            if isinstance(history_data, list):
                for item in history_data:
                    try:
                        if isinstance(item, str):
                            regime_event = json.loads(item)
                        elif isinstance(item, dict):
                            regime_event = item
                        else:
                            continue  # Skip unknown types

                        event_time = datetime.fromisoformat(regime_event["timestamp"])

                        if event_time >= cutoff_time:
                            regime_history.append(regime_event)
                    except (json.JSONDecodeError, ValueError, KeyError) as e:
                        logger.warning(f"Error parsing regime history item: {e}")
                        continue

            return regime_history[:limit]

        except Exception as e:
            logger.error(f"Error getting regime history: {e}")
            return []

    async def check_for_regime_change(self) -> Optional[Dict[str, Any]]:
        """Check if there has been a regime change"""
        try:
            # Simulate regime detection (replace with actual analysis later)
            current_analysis = await self._simulate_regime_analysis()
            current_regime = current_analysis["current_regime"]

            # Check if regime has changed
            if self.last_regime and current_regime != self.last_regime:
                regime_change = {
                    "old_regime": self.last_regime,
                    "new_regime": current_regime,
                    "confidence": current_analysis["confidence"],
                    "timestamp": datetime.now().isoformat(),
                    "strength": current_analysis["regime_strength"],
                    "volatility_level": current_analysis["volatility_level"],
                }

                # Store regime change
                await self._store_regime_change(regime_change)

                # Update current regime
                self.last_regime = current_regime
                self.regime_start_time = datetime.now()

                logger.info(
                    f"Regime change detected: {regime_change['old_regime']} -> {current_regime}"
                )
                return regime_change

            return None

        except Exception as e:
            logger.error(f"Error checking for regime change: {e}")
            return None

    async def _simulate_regime_analysis(self) -> Dict[str, Any]:
        """Simulate regime analysis (placeholder for actual implementation)"""
        try:
            # This is a simplified simulation
            # In the full implementation, this would use the actual regime detection components

            import random

            regimes = [
                "trending_high_vol",
                "trending_low_vol",
                "ranging_high_vol",
                "ranging_low_vol",
            ]
            volatility_levels = ["low", "medium", "high"]
            trend_directions = ["bullish", "bearish", "sideways"]

            # Add some persistence to avoid constant regime changes
            if random.random() < 0.95:  # 95% chance to stay in current regime
                current_regime = self.last_regime
            else:
                current_regime = random.choice(regimes)

            regime_data = {
                "current_regime": current_regime,
                "confidence": 0.70 + random.random() * 0.25,  # 0.70-0.95
                "regime_strength": 0.50 + random.random() * 0.40,  # 0.50-0.90
                "time_in_regime": int(
                    (datetime.now() - self.regime_start_time).total_seconds() / 60
                ),
                "last_change": datetime.now(),
                "volatility_level": random.choice(volatility_levels),
                "trend_direction": random.choice(trend_directions),
            }

            # Cache the result
            await self._cache_regime_data(regime_data)

            return regime_data

        except Exception as e:
            logger.error(f"Error in regime analysis simulation: {e}")
            return await self._get_default_regime_data()

    async def _cache_regime_data(self, regime_data: Dict[str, Any]):
        """Cache regime data"""
        try:
            regime_json = json.dumps(regime_data, default=str)

            if self.redis_client:
                try:
                    self.redis_client.setex(self.current_regime_key, 300, regime_json)
                    self.redis_client.set(
                        "regime_last_update", datetime.now().isoformat()
                    )
                except:
                    pass

            # Fallback to memory storage
            self._memory_storage["current_regime"] = regime_json
            self._memory_storage["last_update"] = datetime.now().isoformat()

        except Exception as e:
            logger.error(f"Error caching regime data: {e}")

    async def _store_regime_change(self, regime_change: Dict[str, Any]):
        """Store regime change in history"""
        try:
            regime_json = json.dumps(regime_change, default=str)

            if self.redis_client:
                try:
                    self.redis_client.lpush(self.regime_history_key, regime_json)
                    self.redis_client.ltrim(self.regime_history_key, 0, 999)
                except:
                    pass

            # Fallback to memory storage
            if "regime_history" not in self._memory_storage:
                self._memory_storage["regime_history"] = []

            self._memory_storage["regime_history"].insert(0, regime_change)
            if len(self._memory_storage["regime_history"]) > 1000:
                self._memory_storage["regime_history"] = self._memory_storage[
                    "regime_history"
                ][:1000]

        except Exception as e:
            logger.error(f"Error storing regime change: {e}")

    async def _load_current_regime(self):
        """Load current regime state from cache"""
        try:
            cached_regime = None
            if self.redis_client:
                try:
                    cached_regime = self.redis_client.get(self.current_regime_key)
                except:
                    pass

            if cached_regime and isinstance(cached_regime, str):
                regime_data = json.loads(cached_regime)
                self.last_regime = regime_data.get("current_regime", "ranging_low_vol")

                # Estimate regime start time
                history = await self.get_regime_history(timeframe="7d", limit=10)
                if history:
                    self.regime_start_time = datetime.fromisoformat(
                        history[0]["timestamp"]
                    )
                else:
                    self.regime_start_time = datetime.now()
            else:
                # Set defaults
                self.last_regime = "ranging_low_vol"
                self.regime_start_time = datetime.now()

                # Perform initial analysis
                initial_analysis = await self._simulate_regime_analysis()
                self.last_regime = initial_analysis["current_regime"]

        except Exception as e:
            logger.error(f"Error loading current regime: {e}")
            self.last_regime = "ranging_low_vol"
            self.regime_start_time = datetime.now()

    def _parse_timeframe(self, timeframe: str) -> int:
        """Parse timeframe string to hours"""
        timeframe_map = {"1h": 1, "4h": 4, "1d": 24, "1w": 168, "1m": 720}
        return timeframe_map.get(timeframe, 24)

    async def cleanup(self):
        """Cleanup resources"""
        try:
            logger.info("Cleaning up Regime Monitor...")
            # Close Redis connection if needed
            if self.redis_client:
                try:
                    self.redis_client.close()
                except:
                    pass

        except Exception as e:
            logger.error(f"Error during Regime Monitor cleanup: {e}")

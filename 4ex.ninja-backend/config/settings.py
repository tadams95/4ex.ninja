"""
Optimal MA Strategy Configuration
Production settings for achieving 18.0-19.8% returns.
Parameters extracted from batch_1_results.json validation.
"""

from typing import Dict, Any
import os
from dataclasses import dataclass


@dataclass
class Settings:
    """Application settings."""

    environment: str
    mongodb_url: str
    discord_webhook_url: str
    oanda_api_key: str
    oanda_account_id: str
    oanda_environment: str
    redis_url: str


def get_settings() -> Settings:
    """Get application settings from environment variables."""
    return Settings(
        environment=os.getenv("ENVIRONMENT", "production"),
        mongodb_url=os.getenv("MONGODB_URL", "mongodb://localhost:27017/4ex_ninja"),
        discord_webhook_url=os.getenv("DISCORD_WEBHOOK_URL", ""),
        oanda_api_key=os.getenv("OANDA_API_KEY", ""),
        oanda_account_id=os.getenv("OANDA_ACCOUNT_ID", ""),
        oanda_environment=os.getenv("OANDA_ENVIRONMENT", "practice"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
    )


# OPTIMAL MA STRATEGY CONFIGURATION
# Based on validation backtest results showing 18.0-19.8% returns
# Parameters: conservative_moderate_daily (fast_ma=50, slow_ma=200)

OPTIMAL_STRATEGY_CONFIG = {
    "EUR_USD_D": {
        "pair": "EUR_USD",
        "timeframe": "D",
        "slow_ma": 200,
        "fast_ma": 50,
        "source": "close",
        "strategy_type": "conservative_moderate_daily",
        "expected_return": "18.0%",
        "validated": True,
    },
    "GBP_USD_D": {
        "pair": "GBP_USD",
        "timeframe": "D",
        "slow_ma": 200,
        "fast_ma": 50,
        "source": "close",
        "strategy_type": "conservative_moderate_daily",
        "expected_return": "19.8%",
        "validated": True,
    },
    "USD_JPY_D": {
        "pair": "USD_JPY",
        "timeframe": "D",
        "slow_ma": 200,
        "fast_ma": 50,
        "source": "close",
        "strategy_type": "conservative_moderate_daily",
        "expected_return": "18.5%",
        "validated": True,
    },
    "AUD_USD_D": {
        "pair": "AUD_USD",
        "timeframe": "D",
        "slow_ma": 200,
        "fast_ma": 50,
        "source": "close",
        "strategy_type": "conservative_moderate_daily",
        "expected_return": "18.2%",
        "validated": True,
    },
    "EUR_GBP_D": {
        "pair": "EUR_GBP",
        "timeframe": "D",
        "slow_ma": 200,
        "fast_ma": 50,
        "source": "close",
        "strategy_type": "conservative_moderate_daily",
        "expected_return": "18.7%",
        "validated": True,
    },
    "GBP_JPY_D": {
        "pair": "GBP_JPY",
        "timeframe": "D",
        "slow_ma": 200,
        "fast_ma": 50,
        "source": "close",
        "strategy_type": "conservative_moderate_daily",
        "expected_return": "19.1%",
        "validated": True,
    },
    "NZD_USD_D": {
        "pair": "NZD_USD",
        "timeframe": "D",
        "slow_ma": 200,
        "fast_ma": 50,
        "source": "close",
        "strategy_type": "conservative_moderate_daily",
        "expected_return": "18.3%",
        "validated": True,
    },
    "USD_CAD_D": {
        "pair": "USD_CAD",
        "timeframe": "D",
        "slow_ma": 200,
        "fast_ma": 50,
        "source": "close",
        "strategy_type": "conservative_moderate_daily",
        "expected_return": "18.9%",
        "validated": True,
    },
}

# Performance targets based on validation results
PERFORMANCE_TARGETS = {
    "overall_return_range": "18.0-19.8%",
    "strategy_type": "conservative_moderate_daily",
    "parameters": {"fast_ma": 50, "slow_ma": 200},
    "validation_source": "batch_1_results.json",
    "total_validated_strategies": 8,
    "all_profitable": True,
}

# Trading pairs we support
SUPPORTED_PAIRS = list(OPTIMAL_STRATEGY_CONFIG.keys())

# MA calculation settings
MA_SETTINGS = {
    "fast_ma_period": 50,
    "slow_ma_period": 200,
    "source": "close",
    "method": "simple",  # Simple Moving Average
}


def get_strategy_config(pair_key: str) -> Dict[str, Any]:
    """Get strategy configuration for a specific pair."""
    if pair_key not in OPTIMAL_STRATEGY_CONFIG:
        raise ValueError(f"Unsupported pair: {pair_key}")

    return OPTIMAL_STRATEGY_CONFIG[pair_key]


def get_all_strategy_configs() -> Dict[str, Dict[str, Any]]:
    """Get all optimal strategy configurations."""
    return OPTIMAL_STRATEGY_CONFIG.copy()


def is_optimal_configuration() -> bool:
    """Verify we're using the validated optimal configuration."""
    # Check that all strategies use the optimal parameters
    for config in OPTIMAL_STRATEGY_CONFIG.values():
        if config["fast_ma"] != 50 or config["slow_ma"] != 200:
            return False
    return True

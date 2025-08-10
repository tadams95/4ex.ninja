"""
Discord Configuration for Live Signal Notifications

This module contains configuration settings for Discord integration
with the MA Unified Strategy signal generation.
"""

import os
from typing import Dict, List

# Discord notification settings
DISCORD_NOTIFICATIONS_ENABLED = (
    os.getenv("DISCORD_NOTIFICATIONS_ENABLED", "true").lower() == "true"
)

# Signal filtering settings
DISCORD_SIGNAL_FILTERS = {
    "min_risk_reward_ratio": float(os.getenv("DISCORD_MIN_RR_RATIO", "1.0")),
    "min_confidence_score": float(os.getenv("DISCORD_MIN_CONFIDENCE", "0.7")),
    "enabled_pairs": os.getenv(
        "DISCORD_ENABLED_PAIRS",
        "EUR/USD,GBP/USD,USD/JPY,AUD/USD,USD/CAD,USD/CHF,NZD/USD",
    ).split(","),
    "enabled_timeframes": os.getenv("DISCORD_ENABLED_TIMEFRAMES", "H1,H4,D").split(","),
}

# Notification channels mapping
DISCORD_CHANNEL_CONFIG = {
    "high_confidence": {
        "min_confidence": 0.8,
        "min_rr_ratio": 2.0,
        "channel_type": "premium",
    },
    "medium_confidence": {
        "min_confidence": 0.6,
        "min_rr_ratio": 1.5,
        "channel_type": "standard",
    },
    "low_confidence": {
        "min_confidence": 0.0,
        "min_rr_ratio": 1.0,
        "channel_type": "free",
    },
}

# Rate limiting for Discord (prevent spam)
DISCORD_RATE_LIMITS = {
    "max_signals_per_minute": int(os.getenv("DISCORD_MAX_SIGNALS_PER_MINUTE", "5")),
    "max_signals_per_hour": int(os.getenv("DISCORD_MAX_SIGNALS_PER_HOUR", "30")),
    "cooldown_between_same_pair": int(os.getenv("DISCORD_PAIR_COOLDOWN_MINUTES", "15")),
}


def should_send_discord_notification(signal_data: Dict) -> bool:
    """
    Determine if a signal should be sent to Discord based on filters.

    Args:
        signal_data: Dictionary containing signal information

    Returns:
        bool: True if signal should be sent to Discord
    """
    if not DISCORD_NOTIFICATIONS_ENABLED:
        return False

    # Check pair filter
    pair = signal_data.get("instrument", "")
    if pair not in DISCORD_SIGNAL_FILTERS["enabled_pairs"]:
        return False

    # Check timeframe filter
    timeframe = signal_data.get("timeframe", "")
    if timeframe not in DISCORD_SIGNAL_FILTERS["enabled_timeframes"]:
        return False

    # Check risk/reward ratio
    rr_ratio = signal_data.get("risk_reward_ratio", 0)
    if rr_ratio < DISCORD_SIGNAL_FILTERS["min_risk_reward_ratio"]:
        return False

    return True


def get_discord_channel_tier(signal_data: Dict) -> str:
    """
    Determine which Discord channel tier to use based on signal quality.

    Args:
        signal_data: Dictionary containing signal information

    Returns:
        str: Channel tier (premium, standard, free)
    """
    confidence = signal_data.get("confidence_score", 0.5)
    rr_ratio = signal_data.get("risk_reward_ratio", 1.0)

    for tier, config in DISCORD_CHANNEL_CONFIG.items():
        if (
            confidence >= config["min_confidence"]
            and rr_ratio >= config["min_rr_ratio"]
        ):
            return config["channel_type"]

    return "free"  # Default to free tier

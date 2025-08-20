"""
Support/Resistance Detection Service for 4ex.ninja

Identifies key support and resistance levels using multiple confluence factors:
- Daily/Weekly highs and lows
- Fibonacci retracements
- Round number psychology
- Previous significant levels
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging


class SupportResistanceService:
    """Detects and manages support/resistance levels for enhanced trade confluence."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Fibonacci retracement levels
        self.fib_levels = [0.0, 0.236, 0.382, 0.500, 0.618, 0.786, 1.0]

        # Round number intervals by pair type
        self.round_number_intervals = {
            "major": 0.0050,  # EUR_USD, GBP_USD, etc. (50 pips)
            "jpy": 0.5000,  # USD_JPY, EUR_JPY, etc. (50 pips for JPY)
            "minor": 0.0020,  # EUR_GBP, etc. (20 pips)
        }

        # JPY pairs have different decimal places
        self.jpy_pairs = [
            "USD_JPY",
            "EUR_JPY",
            "GBP_JPY",
            "AUD_JPY",
            "CHF_JPY",
            "CAD_JPY",
        ]

    def detect_key_levels(
        self, data: pd.DataFrame, pair: str, lookback_days: int = 30
    ) -> Dict:
        """
        Detect comprehensive support/resistance levels.

        Args:
            data: OHLC data with datetime index
            pair: Currency pair name
            lookback_days: Days to look back for level detection

        Returns:
            Dict with support/resistance levels and confluence scores
        """
        if len(data) < 20:
            return {"error": "Insufficient data for level detection"}

        try:
            # Get recent data for analysis
            cutoff_date = data.index[-1] - timedelta(days=lookback_days)
            recent_data = data[data.index >= cutoff_date].copy()

            levels = {
                "pair": pair,
                "analysis_date": str(data.index[-1])[:10],
                "current_price": float(data["close"].iloc[-1]),
                "support_levels": [],
                "resistance_levels": [],
                "fibonacci_levels": [],
                "round_numbers": [],
                "confluence_zones": [],
            }

            # 1. Daily/Weekly Highs and Lows
            daily_levels = self._get_daily_weekly_levels(data, recent_data)

            # 2. Fibonacci Retracements
            fib_levels = self._calculate_fibonacci_levels(recent_data, pair)
            levels["fibonacci_levels"] = fib_levels

            # 3. Round Number Levels
            round_levels = self._get_round_number_levels(levels["current_price"], pair)
            levels["round_numbers"] = round_levels

            # 4. Swing Highs/Lows
            swing_levels = self._identify_swing_levels(recent_data)

            # 5. Combine and score all levels
            all_levels = daily_levels + fib_levels + round_levels + swing_levels
            support, resistance = self._categorize_levels(
                all_levels, levels["current_price"]
            )

            levels["support_levels"] = support
            levels["resistance_levels"] = resistance

            # 6. Identify confluence zones (multiple levels close together)
            levels["confluence_zones"] = self._identify_confluence_zones(
                all_levels, pair
            )

            return levels

        except Exception as e:
            self.logger.error(f"Error detecting levels for {pair}: {str(e)}")
            return {"error": f"Level detection failed: {str(e)}"}

    def _get_daily_weekly_levels(
        self, full_data: pd.DataFrame, recent_data: pd.DataFrame
    ) -> List[Dict]:
        """Extract daily and weekly significant highs and lows."""
        levels = []

        # Daily levels (last 5 days)
        daily_data = recent_data.tail(5)
        for i, (date, row) in enumerate(daily_data.iterrows()):
            date_str = str(date)[:10]  # Simple string conversion
            levels.extend(
                [
                    {
                        "price": float(row["high"]),
                        "type": "daily_high",
                        "date": date_str,
                        "strength": 0.7,
                        "source": "daily",
                    },
                    {
                        "price": float(row["low"]),
                        "type": "daily_low",
                        "date": date_str,
                        "strength": 0.7,
                        "source": "daily",
                    },
                ]
            )

        # Weekly levels (resample to weekly)
        if len(full_data) >= 7:
            weekly_data = (
                full_data.resample("W")
                .agg({"open": "first", "high": "max", "low": "min", "close": "last"})
                .dropna()
                .tail(4)
            )  # Last 4 weeks

            for date, row in weekly_data.iterrows():
                date_str = str(date)[:10]  # Simple string conversion
                levels.extend(
                    [
                        {
                            "price": float(row["high"]),
                            "type": "weekly_high",
                            "date": date_str,
                            "strength": 1.0,
                            "source": "weekly",
                        },
                        {
                            "price": float(row["low"]),
                            "type": "weekly_low",
                            "date": date_str,
                            "strength": 1.0,
                            "source": "weekly",
                        },
                    ]
                )

        return levels

    def _calculate_fibonacci_levels(self, data: pd.DataFrame, pair: str) -> List[Dict]:
        """Calculate Fibonacci retracement levels."""
        if len(data) < 10:
            return []

        # Find swing high and low in the recent period
        swing_high = data["high"].max()
        swing_low = data["low"].min()

        # Find the dates
        high_date = data[data["high"] == swing_high].index[0]
        low_date = data[data["low"] == swing_low].index[0]

        # Determine trend direction
        if high_date > low_date:
            # Uptrend: low to high
            trend_direction = "uptrend"
            range_size = swing_high - swing_low
        else:
            # Downtrend: high to low
            trend_direction = "downtrend"
            range_size = swing_high - swing_low

        fib_levels = []
        for level in self.fib_levels:
            if trend_direction == "uptrend":
                price = swing_low + (range_size * level)
            else:
                price = swing_high - (range_size * level)

            fib_levels.append(
                {
                    "price": float(price),
                    "type": f"fibonacci_{level}",
                    "level": level,
                    "trend": trend_direction,
                    "strength": 0.8 if level in [0.382, 0.5, 0.618] else 0.6,
                    "source": "fibonacci",
                }
            )

        return fib_levels

    def _get_round_number_levels(self, current_price: float, pair: str) -> List[Dict]:
        """Identify psychologically significant round number levels."""
        levels = []

        # Determine interval based on pair type
        if any(jpy in pair for jpy in self.jpy_pairs):
            interval = self.round_number_intervals["jpy"]
            decimal_places = 2
        elif pair in ["EUR_GBP", "AUD_NZD"]:
            interval = self.round_number_intervals["minor"]
            decimal_places = 4
        else:
            interval = self.round_number_intervals["major"]
            decimal_places = 4

        # Find round numbers above and below current price
        for i in range(-3, 4):  # 3 levels above and below
            if i == 0:
                continue

            round_price = round(current_price / interval) * interval + (i * interval)

            levels.append(
                {
                    "price": round(float(round_price), decimal_places),
                    "type": "round_number",
                    "distance": abs(round_price - current_price),
                    "strength": 0.6,
                    "source": "psychology",
                }
            )

        return levels

    def _identify_swing_levels(self, data: pd.DataFrame, window: int = 5) -> List[Dict]:
        """Identify swing highs and lows as potential S/R levels."""
        levels = []

        if len(data) < window * 2:
            return levels

        # Find swing highs
        for i in range(window, len(data) - window):
            current_high = data["high"].iloc[i]
            is_swing_high = True

            # Check if current high is higher than surrounding highs
            for j in range(i - window, i + window + 1):
                if j != i and data["high"].iloc[j] >= current_high:
                    is_swing_high = False
                    break

            if is_swing_high:
                levels.append(
                    {
                        "price": float(current_high),
                        "type": "swing_high",
                        "date": str(data.index[i])[:10],
                        "strength": 0.8,
                        "source": "swing",
                    }
                )

        # Find swing lows
        for i in range(window, len(data) - window):
            current_low = data["low"].iloc[i]
            is_swing_low = True

            # Check if current low is lower than surrounding lows
            for j in range(i - window, i + window + 1):
                if j != i and data["low"].iloc[j] <= current_low:
                    is_swing_low = False
                    break

            if is_swing_low:
                levels.append(
                    {
                        "price": float(current_low),
                        "type": "swing_low",
                        "date": str(data.index[i])[:10],
                        "strength": 0.8,
                        "source": "swing",
                    }
                )

        return levels

    def _categorize_levels(
        self, all_levels: List[Dict], current_price: float
    ) -> Tuple[List[Dict], List[Dict]]:
        """Categorize levels into support and resistance based on current price."""
        support = []
        resistance = []

        for level in all_levels:
            level_data = level.copy()
            level_data["distance"] = abs(level["price"] - current_price)
            level_data["distance_pips"] = self._calculate_pips_distance(
                level["price"], current_price
            )

            if level["price"] < current_price:
                support.append(level_data)
            else:
                resistance.append(level_data)

        # Sort by distance from current price
        support.sort(key=lambda x: x["distance"])
        resistance.sort(key=lambda x: x["distance"])

        return support[:10], resistance[:10]  # Return top 10 closest levels

    def _identify_confluence_zones(
        self, all_levels: List[Dict], pair: str
    ) -> List[Dict]:
        """Identify zones where multiple S/R levels converge."""
        if not all_levels:
            return []

        # Determine proximity threshold based on pair type
        if any(jpy in pair for jpy in self.jpy_pairs):
            proximity_threshold = 0.20  # 20 pips for JPY pairs
        else:
            proximity_threshold = 0.0020  # 20 pips for other pairs

        confluence_zones = []
        processed_levels = set()

        for i, level1 in enumerate(all_levels):
            if i in processed_levels:
                continue

            zone_levels = [level1]
            zone_strength = level1["strength"]

            # Find nearby levels
            for j, level2 in enumerate(all_levels[i + 1 :], i + 1):
                if j in processed_levels:
                    continue

                distance = abs(level1["price"] - level2["price"])
                if distance <= proximity_threshold:
                    zone_levels.append(level2)
                    zone_strength += level2["strength"]
                    processed_levels.add(j)

            # Create confluence zone if multiple levels found
            if len(zone_levels) >= 2:
                avg_price = sum(l["price"] for l in zone_levels) / len(zone_levels)

                confluence_zones.append(
                    {
                        "price": float(avg_price),
                        "level_count": len(zone_levels),
                        "total_strength": zone_strength,
                        "confluence_score": zone_strength * len(zone_levels),
                        "levels": zone_levels,
                        "zone_width": max(l["price"] for l in zone_levels)
                        - min(l["price"] for l in zone_levels),
                    }
                )

                processed_levels.add(i)

        # Sort by confluence score
        confluence_zones.sort(key=lambda x: x["confluence_score"], reverse=True)

        return confluence_zones[:5]  # Return top 5 confluence zones

    def _calculate_pips_distance(self, price1: float, price2: float) -> float:
        """Calculate distance in pips between two prices."""
        distance = abs(price1 - price2)

        # JPY pairs have different pip value (0.01 = 1 pip)
        # Other pairs: 0.0001 = 1 pip
        if any(jpy in str(price1) for jpy in self.jpy_pairs):
            return distance * 100  # JPY pairs
        else:
            return distance * 10000  # Non-JPY pairs

    def get_level_confluence_score(
        self, entry_price: float, levels_data: Dict
    ) -> float:
        """
        Calculate confluence score for a potential entry price.

        Args:
            entry_price: Proposed entry price
            levels_data: Output from detect_key_levels()

        Returns:
            Confluence score (0.0 - 3.0)
        """
        if "error" in levels_data:
            return 0.0

        confluence_score = 0.0
        proximity_threshold = 0.0020  # 20 pips

        # Check proximity to confluence zones (highest weight)
        for zone in levels_data.get("confluence_zones", []):
            distance = abs(entry_price - zone["price"])
            if distance <= proximity_threshold:
                confluence_score += zone["confluence_score"] * 0.5

        # Check proximity to individual S/R levels
        all_levels = levels_data.get("support_levels", []) + levels_data.get(
            "resistance_levels", []
        )
        for level in all_levels:
            distance = abs(entry_price - level["price"])
            if distance <= proximity_threshold:
                confluence_score += level["strength"] * 0.3

        # Check proximity to Fibonacci levels
        for fib_level in levels_data.get("fibonacci_levels", []):
            distance = abs(entry_price - fib_level["price"])
            if distance <= proximity_threshold:
                confluence_score += fib_level["strength"] * 0.4

        return min(confluence_score, 3.0)  # Cap at 3.0

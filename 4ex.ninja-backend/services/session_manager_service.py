"""
Session Manager Service for 4ex.ninja

Provides session-based trading filters optimized for different currency pairs.
Implements market session logic to enhance trade quality and timing.
"""

from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional
from enum import Enum


class MarketSession(Enum):
    SYDNEY = "Sydney"
    TOKYO = "Tokyo"
    LONDON = "London"
    NEW_YORK = "New_York"
    OVERLAP_LONDON_NY = "London_NY_Overlap"
    OVERLAP_TOKYO_LONDON = "Tokyo_London_Overlap"


class SessionManagerService:
    """Manages forex market sessions and optimal trading times."""

    def __init__(self):
        self.session_times = {
            # All times in UTC
            MarketSession.SYDNEY: (21, 6),  # 21:00 - 06:00 UTC
            MarketSession.TOKYO: (23, 8),  # 23:00 - 08:00 UTC
            MarketSession.LONDON: (8, 16),  # 08:00 - 16:00 UTC
            MarketSession.NEW_YORK: (13, 22),  # 13:00 - 22:00 UTC
            MarketSession.OVERLAP_LONDON_NY: (13, 16),  # 13:00 - 16:00 UTC
            MarketSession.OVERLAP_TOKYO_LONDON: (8, 8),  # 08:00 - 08:00 UTC (brief)
        }

        # Optimal sessions for currency pairs based on backtesting results
        self.pair_optimal_sessions = {
            # JPY pairs - Best during Asian session (proven 36% avg returns)
            "USD_JPY": [MarketSession.TOKYO, MarketSession.OVERLAP_TOKYO_LONDON],
            "EUR_JPY": [MarketSession.TOKYO, MarketSession.OVERLAP_TOKYO_LONDON],
            "GBP_JPY": [MarketSession.TOKYO, MarketSession.OVERLAP_TOKYO_LONDON],
            "AUD_JPY": [MarketSession.TOKYO, MarketSession.SYDNEY],
            # USD pairs - Best during NY session
            "EUR_USD": [MarketSession.NEW_YORK, MarketSession.OVERLAP_LONDON_NY],
            "GBP_USD": [MarketSession.NEW_YORK, MarketSession.OVERLAP_LONDON_NY],
            "AUD_USD": [MarketSession.NEW_YORK, MarketSession.SYDNEY],
            "USD_CAD": [MarketSession.NEW_YORK, MarketSession.OVERLAP_LONDON_NY],
            "USD_CHF": [MarketSession.NEW_YORK, MarketSession.OVERLAP_LONDON_NY],
            # EUR pairs - Best during London session
            "EUR_GBP": [MarketSession.LONDON, MarketSession.OVERLAP_LONDON_NY],
        }

        # Session quality multipliers (based on volatility and liquidity)
        self.session_quality = {
            MarketSession.TOKYO: 1.2,  # High for JPY pairs
            MarketSession.LONDON: 1.1,  # Good for EUR pairs
            MarketSession.NEW_YORK: 1.1,  # Good for USD pairs
            MarketSession.OVERLAP_LONDON_NY: 1.3,  # Best liquidity
            MarketSession.OVERLAP_TOKYO_LONDON: 1.15,
            MarketSession.SYDNEY: 0.8,  # Lower liquidity
        }

    def get_current_session(
        self, current_time: Optional[datetime] = None
    ) -> List[MarketSession]:
        """Get currently active market sessions."""
        if current_time is None:
            current_time = datetime.now(timezone.utc)

        current_hour = current_time.hour
        active_sessions = []

        for session, (start, end) in self.session_times.items():
            if self._is_time_in_session(current_hour, start, end):
                active_sessions.append(session)

        return active_sessions

    def _is_time_in_session(self, current_hour: int, start: int, end: int) -> bool:
        """Check if current hour falls within session times."""
        if start <= end:
            # Same day session (e.g., London 8-16)
            return start <= current_hour < end
        else:
            # Overnight session (e.g., Tokyo 23-8)
            return current_hour >= start or current_hour < end

    def is_optimal_session_for_pair(
        self, pair: str, current_time: Optional[datetime] = None
    ) -> Tuple[bool, float]:
        """
        Check if current time is optimal for trading the given pair.

        Returns:
            Tuple[bool, float]: (is_optimal, quality_multiplier)
        """
        if pair not in self.pair_optimal_sessions:
            return False, 0.8  # Default conservative multiplier for unknown pairs

        current_sessions = self.get_current_session(current_time)
        optimal_sessions = self.pair_optimal_sessions[pair]

        # Check if any current session is optimal for this pair
        active_optimal_sessions = [s for s in current_sessions if s in optimal_sessions]

        if not active_optimal_sessions:
            return False, 0.7  # Reduce signal strength outside optimal sessions

        # Calculate quality multiplier based on best active session
        max_quality = max(
            self.session_quality[session] for session in active_optimal_sessions
        )
        return True, max_quality

    def get_session_filter_for_pair(self, pair: str) -> Dict:
        """Get comprehensive session filter information for a pair."""
        current_time = datetime.now(timezone.utc)
        is_optimal, quality = self.is_optimal_session_for_pair(pair, current_time)
        current_sessions = self.get_current_session(current_time)

        return {
            "pair": pair,
            "current_time_utc": current_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "current_sessions": [s.value for s in current_sessions],
            "is_optimal_session": is_optimal,
            "session_quality_multiplier": quality,
            "optimal_sessions": [
                s.value for s in self.pair_optimal_sessions.get(pair, [])
            ],
            "recommendation": (
                "TRADE"
                if is_optimal and quality >= 1.0
                else "WAIT" if quality >= 0.8 else "AVOID"
            ),
        }

    def get_next_optimal_session(self, pair: str) -> Dict:
        """Get information about the next optimal trading session for a pair."""
        if pair not in self.pair_optimal_sessions:
            return {"error": f"No optimal sessions defined for {pair}"}

        current_time = datetime.now(timezone.utc)
        current_hour = current_time.hour
        optimal_sessions = self.pair_optimal_sessions[pair]

        # Find next optimal session
        next_sessions = []
        for session in optimal_sessions:
            start_hour, _ = self.session_times[session]

            if start_hour > current_hour:
                hours_until = start_hour - current_hour
            else:
                hours_until = (24 - current_hour) + start_hour

            next_sessions.append(
                {
                    "session": session.value,
                    "hours_until": hours_until,
                    "start_hour_utc": start_hour,
                }
            )

        # Return the soonest optimal session
        next_session = min(next_sessions, key=lambda x: x["hours_until"])

        return {
            "pair": pair,
            "next_optimal_session": next_session,
            "current_time_utc": current_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
        }

    def is_major_overlap_active(self, current_time: Optional[datetime] = None) -> bool:
        """Check if a major session overlap is currently active."""
        current_sessions = self.get_current_session(current_time)
        return (
            MarketSession.OVERLAP_LONDON_NY in current_sessions
            or MarketSession.OVERLAP_TOKYO_LONDON in current_sessions
        )

    def get_session_analysis(self) -> Dict:
        """Get comprehensive session analysis for all pairs."""
        analysis = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "current_sessions": [s.value for s in self.get_current_session()],
            "major_overlap_active": self.is_major_overlap_active(),
            "pair_analysis": {},
        }

        for pair in self.pair_optimal_sessions.keys():
            analysis["pair_analysis"][pair] = self.get_session_filter_for_pair(pair)

        return analysis

"""
Signal Service
Manages trading signal generation, storage, and processing.
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from models.signal_models import TradingSignal, SignalStatus, PriceData
from services.ma_strategy_service import MAStrategyService


class SignalService:
    """Service for managing trading signals."""

    def __init__(self):
        self.ma_strategy_service = MAStrategyService()
        self.signals_cache: Dict[str, List[TradingSignal]] = {}
        self.logger = logging.getLogger(__name__)

    async def generate_signal_for_pair(
        self, pair: str, price_data: List[PriceData], force_recalculate: bool = False
    ) -> TradingSignal:
        """
        Generate a trading signal for a specific pair.

        Args:
            pair: Currency pair (e.g., "EUR_USD_D")
            price_data: Historical price data
            force_recalculate: Force recalculation even if recent signal exists

        Returns:
            TradingSignal object
        """
        try:
            # Check if we have a recent signal (unless forced)
            if not force_recalculate:
                recent_signal = await self._get_recent_signal(pair)
                if recent_signal:
                    self.logger.info(f"Using recent signal for {pair}")
                    return recent_signal

            # Generate new signal
            signal = await self.ma_strategy_service.generate_signal(pair, price_data)

            # Store signal
            await self._store_signal(signal)

            self.logger.info(
                f"Generated {signal.signal_type} signal for {pair} at {signal.price}"
            )

            return signal

        except Exception as e:
            self.logger.error(f"Error generating signal for {pair}: {str(e)}")
            raise

    async def generate_signals_for_all_pairs(
        self, price_data_dict: Dict[str, List[PriceData]]
    ) -> List[TradingSignal]:
        """
        Generate signals for all supported pairs.

        Args:
            price_data_dict: Dictionary mapping pair names to price data

        Returns:
            List of TradingSignal objects
        """
        signals = []
        supported_pairs = await self.ma_strategy_service.get_all_supported_pairs()

        for pair in supported_pairs:
            if pair in price_data_dict:
                try:
                    signal = await self.generate_signal_for_pair(
                        pair, price_data_dict[pair]
                    )
                    signals.append(signal)
                except Exception as e:
                    self.logger.error(f"Failed to generate signal for {pair}: {str(e)}")
                    continue

        return signals

    async def get_signals_by_pair(
        self, pair: str, limit: int = 50
    ) -> List[TradingSignal]:
        """Get recent signals for a specific pair."""
        if pair in self.signals_cache:
            return self.signals_cache[pair][-limit:]
        return []

    async def get_all_recent_signals(self, limit: int = 100) -> List[TradingSignal]:
        """Get all recent signals across all pairs."""
        all_signals = []
        for signals in self.signals_cache.values():
            all_signals.extend(signals)

        # Sort by timestamp and return most recent
        all_signals.sort(key=lambda x: x.timestamp, reverse=True)
        return all_signals[:limit]

    async def get_active_signals(self) -> List[TradingSignal]:
        """Get signals that are currently active (BUY/SELL)."""
        all_signals = await self.get_all_recent_signals()

        # Get latest signal per pair
        latest_signals = {}
        for signal in all_signals:
            pair_key = f"{signal.pair}_{signal.timeframe}"
            if pair_key not in latest_signals:
                latest_signals[pair_key] = signal

        # Return only BUY/SELL signals
        return [
            signal
            for signal in latest_signals.values()
            if signal.signal_type in ["BUY", "SELL"]
        ]

    async def mark_signal_processed(self, signal_id: str) -> bool:
        """Mark a signal as processed."""
        try:
            # Find and update signal status
            for pair_signals in self.signals_cache.values():
                for signal in pair_signals:
                    if signal.id == signal_id:
                        signal.status = SignalStatus.PROCESSED
                        return True
            return False
        except Exception as e:
            self.logger.error(
                f"Error marking signal {signal_id} as processed: {str(e)}"
            )
            return False

    async def mark_signal_sent(self, signal_id: str) -> bool:
        """Mark a signal as sent to Discord."""
        try:
            for pair_signals in self.signals_cache.values():
                for signal in pair_signals:
                    if signal.id == signal_id:
                        signal.status = SignalStatus.SENT
                        return True
            return False
        except Exception as e:
            self.logger.error(f"Error marking signal {signal_id} as sent: {str(e)}")
            return False

    async def _get_recent_signal(
        self, pair: str, max_age_minutes: int = 60
    ) -> Optional[TradingSignal]:
        """Get recent signal if it exists and is not too old."""
        if pair not in self.signals_cache:
            return None

        pair_signals = self.signals_cache[pair]
        if not pair_signals:
            return None

        latest_signal = pair_signals[-1]
        age = datetime.utcnow() - latest_signal.timestamp

        if age.total_seconds() / 60 <= max_age_minutes:
            return latest_signal

        return None

    async def _store_signal(self, signal: TradingSignal) -> None:
        """Store signal in cache."""
        # Generate ID if not present
        if not signal.id:
            signal.id = (
                f"{signal.pair}_{signal.timeframe}_{int(signal.timestamp.timestamp())}"
            )

        pair_key = f"{signal.pair}_{signal.timeframe}"

        if pair_key not in self.signals_cache:
            self.signals_cache[pair_key] = []

        self.signals_cache[pair_key].append(signal)

        # Keep only recent signals (last 100 per pair)
        if len(self.signals_cache[pair_key]) > 100:
            self.signals_cache[pair_key] = self.signals_cache[pair_key][-100:]

    async def cleanup_old_signals(self, max_age_days: int = 7) -> int:
        """Clean up old signals to prevent memory bloat."""
        cutoff_time = datetime.utcnow() - timedelta(days=max_age_days)
        cleaned_count = 0

        for pair in list(self.signals_cache.keys()):
            original_count = len(self.signals_cache[pair])
            self.signals_cache[pair] = [
                signal
                for signal in self.signals_cache[pair]
                if signal.timestamp > cutoff_time
            ]
            cleaned_count += original_count - len(self.signals_cache[pair])

            # Remove empty entries
            if not self.signals_cache[pair]:
                del self.signals_cache[pair]

        self.logger.info(f"Cleaned up {cleaned_count} old signals")
        return cleaned_count

    async def get_signal_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored signals."""
        total_signals = sum(len(signals) for signals in self.signals_cache.values())

        signal_counts_by_pair = {
            pair: len(signals) for pair, signals in self.signals_cache.items()
        }

        # Get signal type distribution
        signal_types = {"BUY": 0, "SELL": 0, "HOLD": 0}
        for signals in self.signals_cache.values():
            for signal in signals:
                signal_types[signal.signal_type] += 1

        # Get latest signal time
        latest_signal_time = None
        for signals in self.signals_cache.values():
            if signals:
                latest = signals[-1].timestamp
                if latest_signal_time is None or latest > latest_signal_time:
                    latest_signal_time = latest

        return {
            "total_signals": total_signals,
            "signals_by_pair": signal_counts_by_pair,
            "signal_type_distribution": signal_types,
            "latest_signal_time": latest_signal_time,
            "pairs_tracked": len(self.signals_cache),
        }

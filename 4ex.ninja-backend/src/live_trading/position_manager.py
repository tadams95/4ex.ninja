"""
Position Manager

Manages trading positions, including opening, closing, and tracking trades
with proper risk management and position sizing.
"""

import sys
import os
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from api.oanda_api import OandaAPI
from src.backtesting.strategy_interface import TradeSignal


class PositionStatus(Enum):
    """Position status enumeration."""

    OPEN = "open"
    CLOSED = "closed"
    PENDING = "pending"
    CANCELLED = "cancelled"


@dataclass
class Position:
    """Represents a trading position."""

    position_id: str
    instrument: str
    direction: str  # 'BUY' or 'SELL'
    units: int
    entry_price: float
    current_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    timestamp: Optional[datetime] = None
    status: PositionStatus = PositionStatus.PENDING
    strategy_name: str = ""
    unrealized_pnl: float = 0.0

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def update_current_price(self, price: float):
        """Update current price and calculate unrealized P&L."""
        self.current_price = price

        if self.direction == "BUY":
            self.unrealized_pnl = (self.current_price - self.entry_price) * abs(
                self.units
            )
        else:  # SELL
            self.unrealized_pnl = (self.entry_price - self.current_price) * abs(
                self.units
            )


class PositionManager:
    """
    Manages trading positions with proper risk management and execution.
    """

    def __init__(
        self, max_positions_per_instrument: int = 1, max_total_positions: int = 5
    ):
        """
        Initialize position manager.

        Args:
            max_positions_per_instrument: Maximum positions per instrument
            max_total_positions: Maximum total open positions
        """
        self.api = OandaAPI()
        self.positions: Dict[str, Position] = {}
        self.max_positions_per_instrument = max_positions_per_instrument
        self.max_total_positions = max_total_positions

    def can_open_position(self, instrument: str) -> bool:
        """
        Check if we can open a new position for an instrument.

        Args:
            instrument: Trading instrument

        Returns:
            True if position can be opened
        """
        # Count open positions for this instrument
        instrument_positions = sum(
            1
            for pos in self.positions.values()
            if pos.instrument == instrument and pos.status == PositionStatus.OPEN
        )

        # Count total open positions
        total_positions = sum(
            1 for pos in self.positions.values() if pos.status == PositionStatus.OPEN
        )

        return (
            instrument_positions < self.max_positions_per_instrument
            and total_positions < self.max_total_positions
        )

    def calculate_position_size(
        self,
        instrument: str,
        signal: TradeSignal,
        account_balance: float,
        risk_per_trade: float = 0.02,
    ) -> int:
        """
        Calculate position size based on risk management rules.

        Args:
            instrument: Trading instrument
            signal: Trade signal with entry and stop loss
            account_balance: Current account balance
            risk_per_trade: Risk per trade as fraction of balance (default 2%)

        Returns:
            Position size in units
        """
        try:
            if not signal.stop_loss or signal.stop_loss <= 0:
                # Default risk if no stop loss provided
                risk_amount = account_balance * risk_per_trade
                # Use 1% of balance as default position size
                current_price = signal.entry_price
                position_size = int((risk_amount * 0.01) / current_price)
            else:
                # Calculate based on stop loss distance
                risk_amount = account_balance * risk_per_trade
                stop_distance = abs(signal.entry_price - signal.stop_loss)

                if stop_distance > 0:
                    position_size = int(risk_amount / stop_distance)
                else:
                    position_size = int(account_balance * 0.001 / signal.entry_price)

            # Apply position size limits
            min_size = 1
            max_size = int(
                account_balance * 0.1 / signal.entry_price
            )  # Max 10% of balance

            position_size = max(min_size, min(position_size, max_size))

            # Make negative for sell orders
            if signal.direction == "SELL":
                position_size = -position_size

            return position_size

        except Exception as e:
            print(f"Error calculating position size: {e}")
            return 1 if signal.direction == "BUY" else -1

    def open_position(
        self,
        signal: TradeSignal,
        strategy_name: str = "",
        account_balance: float = 10000.0,
    ) -> Optional[Position]:
        """
        Open a new trading position based on a signal.

        Args:
            signal: Trade signal to execute
            strategy_name: Name of strategy generating signal
            account_balance: Current account balance

        Returns:
            Position object if successful, None otherwise
        """
        try:
            if not self.can_open_position(signal.pair):
                print(
                    f"Cannot open position for {signal.pair}: position limits exceeded"
                )
                return None

            # Calculate position size
            units = self.calculate_position_size(signal.pair, signal, account_balance)

            # Place trade with OANDA
            trade_response = self.api.place_trade(
                instrument=signal.pair,
                units=units,
                take_profit=signal.take_profit,
                stop_loss=signal.stop_loss,
            )

            if not trade_response:
                print(f"Failed to execute trade for {signal.pair}")
                return None

            # Handle different response types from OANDA API
            response_dict = None
            try:
                if isinstance(trade_response, dict):
                    response_dict = trade_response
                elif hasattr(trade_response, "__iter__"):
                    # Try to convert generator/iterator to dict
                    response_dict = dict(trade_response)
                else:
                    print(
                        f"Unexpected response type for {signal.pair}: {type(trade_response)}"
                    )
                    return None
            except Exception as e:
                print(f"Failed to process trade response for {signal.pair}: {e}")
                return None

            if not response_dict or "orderFillTransaction" not in response_dict:
                print(f"No orderFillTransaction in response for {signal.pair}")
                print(
                    f"Response keys: {list(response_dict.keys()) if response_dict else 'None'}"
                )
                return None

            # Extract trade info from response
            fill_transaction = response_dict["orderFillTransaction"]
            trade_id = fill_transaction["id"]

            # Create position object
            position = Position(
                position_id=trade_id,
                instrument=signal.pair,
                direction=signal.direction,
                units=units,
                entry_price=float(fill_transaction["price"]),
                current_price=float(fill_transaction["price"]),
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit,
                strategy_name=strategy_name,
                status=PositionStatus.OPEN,
            )

            # Store position
            self.positions[trade_id] = position

            print(
                f"✅ Position opened: {signal.direction} {abs(units)} units of {signal.pair} at {position.entry_price}"
            )

            return position

        except Exception as e:
            print(f"Error opening position: {e}")
            return None

    def close_position(self, position_id: str) -> bool:
        """
        Close an existing position.

        Args:
            position_id: ID of position to close

        Returns:
            True if position was closed successfully
        """
        try:
            if position_id not in self.positions:
                print(f"Position {position_id} not found")
                return False

            position = self.positions[position_id]

            if position.status != PositionStatus.OPEN:
                print(f"Position {position_id} is not open")
                return False

            # Close trade with OANDA
            close_response = self.api.close_trade(position_id)

            if not close_response:
                print(f"Failed to close position {position_id}")
                return False

            # Handle different response types from OANDA API
            response_dict = None
            try:
                if isinstance(close_response, dict):
                    response_dict = close_response
                elif hasattr(close_response, "__iter__"):
                    # Try to convert generator/iterator to dict
                    response_dict = dict(close_response)
                else:
                    print(
                        f"Unexpected close response type for {position_id}: {type(close_response)}"
                    )
                    return False
            except Exception as e:
                print(f"Failed to process close response for {position_id}: {e}")
                return False

            if response_dict and "orderFillTransaction" in response_dict:
                # Update position status
                position.status = PositionStatus.CLOSED
                fill_transaction = response_dict["orderFillTransaction"]
                position.current_price = float(fill_transaction["price"])

                print(
                    f"✅ Position closed: {position.instrument} at {position.current_price}"
                )
                return True
            else:
                print(
                    f"Failed to close position {position_id} - no orderFillTransaction"
                )
                if response_dict:
                    print(f"Response keys: {list(response_dict.keys())}")
                return False

        except Exception as e:
            print(f"Error closing position {position_id}: {e}")
            return False

    def update_positions(self):
        """Update all open positions with current market prices."""
        try:
            # Get all open trades from OANDA
            open_trades_response = self.api.get_open_trades()

            if not open_trades_response:
                return

            # Handle response type
            open_trades = None
            try:
                if isinstance(open_trades_response, list):
                    open_trades = open_trades_response
                elif (
                    isinstance(open_trades_response, dict)
                    and "trades" in open_trades_response
                ):
                    open_trades = open_trades_response["trades"]
                elif hasattr(open_trades_response, "__iter__"):
                    # Try to convert generator/iterator
                    response_dict = dict(open_trades_response)
                    open_trades = response_dict.get("trades", [])
                else:
                    print(
                        f"Unexpected open trades response type: {type(open_trades_response)}"
                    )
                    return
            except Exception as e:
                print(f"Failed to process open trades response: {e}")
                return

            if not open_trades:
                return

            # Update positions with current data
            for trade in open_trades:
                trade_id = trade["id"]

                if trade_id in self.positions:
                    position = self.positions[trade_id]
                    position.current_price = float(trade["price"])
                    position.update_current_price(position.current_price)

                    # Check if trade was closed externally
                    if trade["state"] != "OPEN":
                        position.status = PositionStatus.CLOSED

            # Mark positions as closed if they're not in open trades
            oanda_trade_ids = {trade["id"] for trade in open_trades}

            for position_id, position in self.positions.items():
                if (
                    position.status == PositionStatus.OPEN
                    and position_id not in oanda_trade_ids
                ):
                    position.status = PositionStatus.CLOSED

        except Exception as e:
            print(f"Error updating positions: {e}")

    def get_open_positions(self) -> List[Position]:
        """Get all open positions."""
        return [
            pos for pos in self.positions.values() if pos.status == PositionStatus.OPEN
        ]

    def get_positions_for_instrument(self, instrument: str) -> List[Position]:
        """Get all positions for a specific instrument."""
        return [pos for pos in self.positions.values() if pos.instrument == instrument]

    def get_total_unrealized_pnl(self) -> float:
        """Calculate total unrealized P&L across all open positions."""
        return sum(pos.unrealized_pnl for pos in self.get_open_positions())

    def get_position_summary(self) -> Dict:
        """Get summary of all positions."""
        open_positions = self.get_open_positions()

        return {
            "total_positions": len(open_positions),
            "total_unrealized_pnl": self.get_total_unrealized_pnl(),
            "positions_by_instrument": {
                instrument: len(self.get_positions_for_instrument(instrument))
                for instrument in set(pos.instrument for pos in open_positions)
            },
            "positions_by_strategy": {
                strategy: len(
                    [pos for pos in open_positions if pos.strategy_name == strategy]
                )
                for strategy in set(pos.strategy_name for pos in open_positions)
            },
        }


if __name__ == "__main__":
    # Test position manager
    print("🧪 Testing Position Manager...")

    pm = PositionManager()

    # Test position limits
    print(f"✅ Can open EUR_USD position: {pm.can_open_position('EUR_USD')}")

    # Create test signal
    from datetime import datetime

    test_signal = TradeSignal(
        pair="EUR_USD",
        direction="BUY",
        entry_price=1.1000,
        stop_loss=1.0950,
        take_profit=1.1100,
        signal_strength=0.8,
        signal_time=datetime.utcnow(),
        strategy_name="test",
    )

    # Test position size calculation
    position_size = pm.calculate_position_size("EUR_USD", test_signal, 10000.0)
    print(f"✅ Calculated position size: {position_size} units")

    # Test position summary
    summary = pm.get_position_summary()
    print(f"✅ Position summary: {summary}")

    print("🎯 Position Manager test completed!")

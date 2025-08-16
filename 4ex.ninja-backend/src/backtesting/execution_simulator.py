"""
Execution Simulator for Universal Backtesting Framework.

This module simulates realistic trade execution for ANY strategy type,
including slippage, spread costs, and market impact modeling.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from .strategy_interface import BaseStrategy, TradeSignal, AccountInfo
from .models import Trade
from .regime_detector import MarketRegime

logger = logging.getLogger(__name__)


@dataclass
class ExecutionConfig:
    """Execution simulation configuration."""

    spread_pips: float = 1.0  # Average spread in pips
    slippage_pips: float = 0.5  # Average slippage in pips
    commission_per_lot: float = 7.0  # Commission per lot (USD)
    max_slippage_pips: float = 3.0  # Maximum slippage in volatile conditions
    execution_delay_ms: int = 100  # Execution delay in milliseconds
    partial_fill_probability: float = 0.05  # Probability of partial fills
    rejection_probability: float = 0.01  # Probability of order rejection


@dataclass
class ExecutionResult:
    """Result of trade execution simulation."""

    executed: bool
    executed_price: Optional[float] = None
    executed_size: Optional[float] = None
    slippage_pips: Optional[float] = None
    spread_cost: Optional[float] = None
    commission: Optional[float] = None
    rejection_reason: Optional[str] = None
    execution_time: Optional[datetime] = None


class ExecutionSimulator:
    """
    Universal execution simulator for backtesting.

    Simulates realistic market conditions including:
    - Bid/ask spreads
    - Slippage based on market conditions
    - Commission costs
    - Order rejections
    - Partial fills
    - Market impact
    """

    def __init__(self, config: Optional[ExecutionConfig] = None):
        """
        Initialize execution simulator.

        Args:
            config: Execution configuration parameters
        """
        self.config = config or ExecutionConfig()
        logger.info("ExecutionSimulator initialized")

    def execute_signal(
        self,
        signal: TradeSignal,
        position_size: float,
        market_data: pd.DataFrame,
        regime: MarketRegime,
    ) -> ExecutionResult:
        """
        Simulate execution of a trade signal.

        Args:
            signal: Trade signal to execute
            position_size: Position size to execute
            market_data: Current market data
            regime: Current market regime

        Returns:
            ExecutionResult with simulation details
        """
        try:
            # Check for order rejection
            if self._should_reject_order(signal, market_data, regime):
                return ExecutionResult(
                    executed=False, rejection_reason="MARKET_CONDITIONS"
                )

            # Calculate execution price with spread and slippage
            executed_price = self._calculate_execution_price(
                signal, market_data, regime
            )

            # Calculate costs
            spread_cost = self._calculate_spread_cost(signal, position_size)
            slippage_pips = self._calculate_slippage(signal, market_data, regime)
            commission = self._calculate_commission(position_size)

            # Check for partial fills
            executed_size = self._simulate_partial_fill(position_size, regime)

            return ExecutionResult(
                executed=True,
                executed_price=executed_price,
                executed_size=executed_size,
                slippage_pips=slippage_pips,
                spread_cost=spread_cost,
                commission=commission,
                execution_time=signal.signal_time
                + timedelta(milliseconds=self.config.execution_delay_ms),
            )

        except Exception as e:
            logger.error(f"Error executing signal: {e}")
            return ExecutionResult(
                executed=False, rejection_reason=f"EXECUTION_ERROR: {str(e)}"
            )

    def simulate_trade_execution(
        self, trade: Trade, market_data: pd.DataFrame
    ) -> Trade:
        """
        Simulate the complete lifecycle of a trade.

        Args:
            trade: Trade to simulate
            market_data: Market data for simulation

        Returns:
            Trade with simulated execution results
        """
        try:
            # Find entry point in data
            entry_idx = self._find_entry_index(trade.entry_time, market_data)
            if entry_idx is None:
                trade.exit_time = trade.entry_time
                trade.exit_price = trade.entry_price
                trade.pnl = 0.0
                trade.pnl_pips = 0.0
                trade.exit_reason = "NO_DATA"
                return trade

            # Simulate trade progression with realistic execution
            exit_data = self._simulate_trade_progression(trade, market_data, entry_idx)

            # Update trade with exit information
            trade.exit_time = exit_data.get("exit_time")
            trade.exit_price = exit_data.get("exit_price")
            trade.exit_reason = exit_data.get("exit_reason", "TIME")

            # Calculate P&L with execution costs
            trade.pnl = self._calculate_realistic_pnl(trade)
            trade.pnl_pips = self._calculate_pips(trade)

            return trade

        except Exception as e:
            logger.error(f"Error simulating trade execution: {e}")
            trade.exit_time = trade.entry_time
            trade.exit_price = trade.entry_price
            trade.pnl = 0.0
            trade.pnl_pips = 0.0
            trade.exit_reason = "SIMULATION_ERROR"
            return trade

    def _should_reject_order(
        self, signal: TradeSignal, market_data: pd.DataFrame, regime: MarketRegime
    ) -> bool:
        """
        Determine if order should be rejected based on market conditions.
        """
        # Base rejection probability
        rejection_prob = self.config.rejection_probability

        # Increase rejection probability in volatile conditions
        if (
            regime
            and regime == MarketRegime.TRENDING_HIGH_VOL
            or regime == MarketRegime.RANGING_HIGH_VOL
        ):
            rejection_prob *= 2.0

        # Check for extreme market conditions
        if not market_data.empty:
            latest_data = market_data.iloc[-1]
            price_change = (
                abs(latest_data["close"] - latest_data["open"]) / latest_data["open"]
            )

            # Reject if price moved too much (>2% in one candle)
            if price_change > 0.02:
                rejection_prob *= 3.0

        return np.random.random() < min(rejection_prob, 0.1)  # Max 10% rejection

    def _calculate_execution_price(
        self, signal: TradeSignal, market_data: pd.DataFrame, regime: MarketRegime
    ) -> float:
        """
        Calculate realistic execution price including spread and slippage.
        """
        base_price = signal.entry_price

        # Add spread
        spread_adjustment = self.config.spread_pips * 0.0001  # Convert pips to price
        if signal.direction == "BUY":
            # Buy at ask price (higher)
            spread_price = base_price + spread_adjustment
        else:
            # Sell at bid price (lower)
            spread_price = base_price - spread_adjustment

        # Add slippage
        slippage_pips = self._calculate_slippage(signal, market_data, regime)
        slippage_adjustment = slippage_pips * 0.0001

        if signal.direction == "BUY":
            executed_price = spread_price + slippage_adjustment
        else:
            executed_price = spread_price - slippage_adjustment

        return executed_price

    def _calculate_slippage(
        self, signal: TradeSignal, market_data: pd.DataFrame, regime: MarketRegime
    ) -> float:
        """
        Calculate slippage based on market conditions and regime.
        """
        base_slippage = self.config.slippage_pips

        # Adjust based on market regime volatility
        if regime:
            if regime in [
                MarketRegime.TRENDING_HIGH_VOL,
                MarketRegime.RANGING_HIGH_VOL,
            ]:
                base_slippage *= 2.0
            elif regime in [
                MarketRegime.TRENDING_LOW_VOL,
                MarketRegime.RANGING_LOW_VOL,
            ]:
                base_slippage *= 0.5

        # Add random component
        random_factor = np.random.normal(1.0, 0.3)  # 30% standard deviation
        slippage = base_slippage * max(0.1, random_factor)  # Minimum 10% of base

        return min(slippage, self.config.max_slippage_pips)

    def _calculate_spread_cost(
        self, signal: TradeSignal, position_size: float
    ) -> float:
        """
        Calculate spread cost for the trade.
        """
        spread_pips = self.config.spread_pips
        pip_value = position_size * 0.0001  # Simplified pip value calculation
        return spread_pips * pip_value

    def _calculate_commission(self, position_size: float) -> float:
        """
        Calculate commission cost for the trade.
        """
        lots = position_size / 100000  # Convert units to lots
        return lots * self.config.commission_per_lot

    def _simulate_partial_fill(
        self, position_size: float, regime: MarketRegime
    ) -> float:
        """
        Simulate partial fills in volatile market conditions.
        """
        if np.random.random() < self.config.partial_fill_probability:
            # Partial fill between 70-95% of requested size
            fill_percentage = np.random.uniform(0.7, 0.95)
            return position_size * fill_percentage

        return position_size

    def _find_entry_index(
        self, entry_time: datetime, market_data: pd.DataFrame
    ) -> Optional[int]:
        """
        Find the index in market data for trade entry.
        """
        matching_indices = market_data[market_data["timestamp"] >= entry_time].index
        if len(matching_indices) > 0:
            return int(matching_indices[0])
        return None

    def _simulate_trade_progression(
        self, trade: Trade, market_data: pd.DataFrame, entry_idx: int
    ) -> Dict[str, Any]:
        """
        Simulate how a trade progresses through market data.
        """
        entry_idx_int = entry_idx if isinstance(entry_idx, int) else 0

        for i in range(entry_idx_int, len(market_data)):
            row = market_data.iloc[i]

            if trade.direction == "BUY":
                # Check stop loss with realistic execution
                if row["low"] <= trade.stop_loss:
                    exit_price = self._apply_exit_slippage(
                        trade.stop_loss, "SL", trade.direction
                    )
                    return {
                        "exit_time": row["timestamp"],
                        "exit_price": exit_price,
                        "exit_reason": "SL",
                    }
                # Check take profit with realistic execution
                elif row["high"] >= trade.take_profit:
                    exit_price = self._apply_exit_slippage(
                        trade.take_profit, "TP", trade.direction
                    )
                    return {
                        "exit_time": row["timestamp"],
                        "exit_price": exit_price,
                        "exit_reason": "TP",
                    }
            else:  # SELL
                # Check stop loss with realistic execution
                if row["high"] >= trade.stop_loss:
                    exit_price = self._apply_exit_slippage(
                        trade.stop_loss, "SL", trade.direction
                    )
                    return {
                        "exit_time": row["timestamp"],
                        "exit_price": exit_price,
                        "exit_reason": "SL",
                    }
                # Check take profit with realistic execution
                elif row["low"] <= trade.take_profit:
                    exit_price = self._apply_exit_slippage(
                        trade.take_profit, "TP", trade.direction
                    )
                    return {
                        "exit_time": row["timestamp"],
                        "exit_price": exit_price,
                        "exit_reason": "TP",
                    }

        # No exit conditions met - close at last available price
        if not market_data.empty:
            last_row = market_data.iloc[-1]
            return {
                "exit_time": last_row["timestamp"],
                "exit_price": last_row["close"],
                "exit_reason": "TIME",
            }

        return {
            "exit_time": trade.entry_time,
            "exit_price": trade.entry_price,
            "exit_reason": "NO_DATA",
        }

    def _apply_exit_slippage(
        self, target_price: float, exit_type: str, direction: str
    ) -> float:
        """
        Apply realistic slippage to exit orders.
        """
        # Stop losses typically have more slippage than take profits
        if exit_type == "SL":
            slippage_pips = np.random.uniform(0.5, 2.0)  # 0.5-2 pips slippage on stops
        else:  # TP
            slippage_pips = np.random.uniform(
                0.1, 0.5
            )  # 0.1-0.5 pips slippage on limits

        slippage_adjustment = slippage_pips * 0.0001

        # Apply slippage in unfavorable direction
        if exit_type == "SL":
            if direction == "BUY":
                return target_price - slippage_adjustment  # Worse exit for buy
            else:
                return target_price + slippage_adjustment  # Worse exit for sell
        else:  # TP
            if direction == "BUY":
                return target_price - slippage_adjustment  # Slightly worse fill
            else:
                return target_price + slippage_adjustment  # Slightly worse fill

    def _calculate_realistic_pnl(self, trade: Trade) -> float:
        """
        Calculate P&L including all execution costs.
        """
        if trade.exit_price is None:
            return 0.0

        # Base P&L calculation
        if trade.direction == "BUY":
            price_diff = trade.exit_price - trade.entry_price
        else:
            price_diff = trade.entry_price - trade.exit_price

        # Calculate P&L in account currency (assuming USD)
        base_pnl = price_diff * trade.position_size

        # Subtract execution costs (spread cost is already factored into entry price)
        commission = self._calculate_commission(trade.position_size)
        total_pnl = base_pnl - commission

        return total_pnl

    def _calculate_pips(self, trade: Trade) -> float:
        """
        Calculate P&L in pips.
        """
        if trade.exit_price is None:
            return 0.0

        if trade.direction == "BUY":
            price_diff = trade.exit_price - trade.entry_price
        else:
            price_diff = trade.entry_price - trade.exit_price

        # Convert to pips (assuming 4-decimal currency pairs)
        return price_diff / 0.0001

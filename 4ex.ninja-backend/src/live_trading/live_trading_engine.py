"""
Live Trading Engine

Main engine that coordinates strategies, data feeds, position management,
and risk management for live trading with OANDA.
"""

import sys
import os
import time
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.backtesting.strategies import StrategyFactory, strategy_registry
from src.backtesting.strategy_interface import TradeSignal, AccountInfo
from src.backtesting.regime_detector import MarketRegime
from api.oanda_api import OandaAPI
from .oanda_data_feed import OandaDataFeed
from .position_manager import PositionManager
from .risk_manager import RiskManager


class LiveTradingEngine:
    """
    Main live trading engine that coordinates all components for automated trading.
    """

    def __init__(
        self,
        update_interval: int = 300,  # 5 minutes
        max_positions: int = 5,
        risk_per_trade: float = 0.02,
    ):
        """
        Initialize the live trading engine.

        Args:
            update_interval: How often to check for signals (seconds)
            max_positions: Maximum number of open positions
            risk_per_trade: Risk per trade as fraction of balance
        """
        # Core components
        self.api = OandaAPI()
        self.data_feed = OandaDataFeed()
        self.position_manager = PositionManager(max_total_positions=max_positions)
        self.risk_manager = RiskManager(max_risk_per_trade=risk_per_trade)

        # Engine settings
        self.update_interval = update_interval
        self.is_running = False
        self.is_trading_enabled = True

        # Strategy management
        self.active_strategies: Dict[str, Any] = {}
        self.strategy_configs: Dict[str, Dict] = {}

        # Performance tracking
        self.signals_generated = 0
        self.trades_executed = 0
        self.last_update = None
        self.engine_start_time = None

        print("🚀 Live Trading Engine initialized")

    def add_strategy(
        self,
        strategy_name: str,
        instrument: str,
        timeframe: str,
        config: Optional[Dict] = None,
    ) -> bool:
        """
        Add a strategy to the live trading engine.

        Args:
            strategy_name: Name of strategy to add
            instrument: Trading instrument (e.g., 'EUR_USD')
            timeframe: Timeframe for signals (e.g., 'M5', 'H1')
            config: Strategy configuration

        Returns:
            True if strategy was added successfully
        """
        try:
            # Validate inputs
            if not self.data_feed.validate_instrument(instrument):
                print(f"❌ Invalid instrument: {instrument}")
                return False

            if not self.data_feed.validate_granularity(timeframe):
                print(f"❌ Invalid timeframe: {timeframe}")
                return False

            # Create strategy instance
            strategy = StrategyFactory.create_strategy(strategy_name, config or {})

            if not strategy:
                print(f"❌ Failed to create strategy: {strategy_name}")
                return False

            # Create unique key for this strategy instance
            strategy_key = f"{strategy_name}_{instrument}_{timeframe}"

            # Store strategy and config
            self.active_strategies[strategy_key] = {
                "strategy": strategy,
                "instrument": instrument,
                "timeframe": timeframe,
                "config": config or {},
                "last_signal_time": None,
                "total_signals": 0,
            }

            print(f"✅ Added strategy: {strategy_key}")
            return True

        except Exception as e:
            print(f"❌ Error adding strategy {strategy_name}: {e}")
            return False

    def remove_strategy(
        self, strategy_name: str, instrument: str, timeframe: str
    ) -> bool:
        """
        Remove a strategy from the engine.

        Args:
            strategy_name: Name of strategy to remove
            instrument: Trading instrument
            timeframe: Timeframe

        Returns:
            True if strategy was removed
        """
        strategy_key = f"{strategy_name}_{instrument}_{timeframe}"

        if strategy_key in self.active_strategies:
            del self.active_strategies[strategy_key]
            print(f"✅ Removed strategy: {strategy_key}")
            return True
        else:
            print(f"❌ Strategy not found: {strategy_key}")
            return False

    def start_trading(self):
        """Start the live trading engine."""
        if self.is_running:
            print("⚠️  Engine is already running")
            return

        print("🚀 Starting Live Trading Engine...")

        # Test connections
        if not self._test_connections():
            print("❌ Connection tests failed - cannot start trading")
            return

        # Start main trading loop
        self.is_running = True
        self.engine_start_time = datetime.utcnow()
        self._trading_loop()

    def stop_trading(self):
        """Stop the live trading engine."""
        print("🛑 Stopping Live Trading Engine...")
        self.is_running = False

    def enable_trading(self):
        """Enable trade execution."""
        self.is_trading_enabled = True
        print("✅ Trading enabled")

    def disable_trading(self):
        """Disable trade execution (signal generation only)."""
        self.is_trading_enabled = False
        print("⚠️  Trading disabled - signals only")

    def get_engine_status(self) -> Dict[str, Any]:
        """Get current engine status and statistics."""
        account_info = self._get_account_info()
        open_positions = self.position_manager.get_open_positions()
        risk_metrics = self.risk_manager.assess_portfolio_risk(
            account_info, open_positions
        )

        return {
            "is_running": self.is_running,
            "is_trading_enabled": self.is_trading_enabled,
            "uptime": (
                str(datetime.utcnow() - self.engine_start_time)
                if self.engine_start_time
                else None
            ),
            "last_update": self.last_update,
            "active_strategies": len(self.active_strategies),
            "open_positions": len(open_positions),
            "account_balance": account_info.balance,
            "account_equity": account_info.equity,
            "total_exposure": risk_metrics.total_exposure,
            "risk_level": risk_metrics.risk_level.value,
            "risk_score": risk_metrics.risk_score,
            "signals_generated": self.signals_generated,
            "trades_executed": self.trades_executed,
            "strategies": list(self.active_strategies.keys()),
        }

    def _trading_loop(self):
        """Main trading loop that runs continuously."""
        print(f"🔄 Trading loop started (update interval: {self.update_interval}s)")

        while self.is_running:
            try:
                loop_start = time.time()

                # Update positions with current prices
                self.position_manager.update_positions()

                # Get current account info
                account_info = self._get_account_info()
                open_positions = self.position_manager.get_open_positions()

                # Update risk tracking
                self.risk_manager.update_daily_pnl(account_info.balance)

                # Check if we should stop trading due to risk
                should_stop, stop_reason = self.risk_manager.should_stop_trading(
                    account_info, open_positions
                )
                if should_stop:
                    print(f"🚨 Emergency stop triggered: {stop_reason}")
                    self.disable_trading()

                # Process each active strategy
                for strategy_key, strategy_data in self.active_strategies.items():
                    self._process_strategy(
                        strategy_key, strategy_data, account_info, open_positions
                    )

                self.last_update = datetime.utcnow()

                # Calculate sleep time
                loop_duration = time.time() - loop_start
                sleep_time = max(0, self.update_interval - loop_duration)

                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    print(
                        f"⚠️  Loop took {loop_duration:.1f}s (longer than {self.update_interval}s interval)"
                    )

            except KeyboardInterrupt:
                print("\n🛑 Keyboard interrupt received")
                break
            except Exception as e:
                print(f"❌ Error in trading loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying

        self.is_running = False
        print("🏁 Trading loop stopped")

    def _process_strategy(
        self,
        strategy_key: str,
        strategy_data: Dict,
        account_info: AccountInfo,
        open_positions: List,
    ) -> None:
        """
        Process a single strategy for signal generation and execution.

        Args:
            strategy_key: Unique strategy identifier
            strategy_data: Strategy data and configuration
            account_info: Current account information
            open_positions: List of open positions
        """
        try:
            strategy = strategy_data["strategy"]
            instrument = strategy_data["instrument"]
            timeframe = strategy_data["timeframe"]

            # Get latest market data
            market_data = self.data_feed.get_latest_candles(
                instrument=instrument,
                granularity=timeframe,
                count=100,  # Get enough data for indicators
            )

            if market_data.empty:
                print(f"⚠️  No market data for {strategy_key}")
                return

            # Detect market regime (simplified - using last regime)
            current_regime = MarketRegime.UNCERTAIN  # Default regime

            # Generate signals
            signals = strategy.generate_signals(market_data, current_regime)

            if not signals:
                return

            # Process each signal
            for signal in signals:
                self.signals_generated += 1
                strategy_data["total_signals"] += 1
                strategy_data["last_signal_time"] = datetime.utcnow()

                print(
                    f"📊 Signal generated: {strategy_key} - {signal.direction} {signal.pair} @ {signal.entry_price}"
                )

                # Validate signal with risk management
                is_valid, warnings = self.risk_manager.validate_signal_risk(
                    signal, account_info, open_positions
                )

                if warnings:
                    for warning in warnings:
                        print(f"⚠️  Risk warning: {warning}")

                if not is_valid:
                    print(f"❌ Signal rejected due to risk management")
                    continue

                # Execute trade if trading is enabled
                if self.is_trading_enabled:
                    position = self.position_manager.open_position(
                        signal,
                        strategy_name=strategy_key,
                        account_balance=account_info.balance,
                    )

                    if position:
                        self.trades_executed += 1
                        print(f"✅ Trade executed: {position.position_id}")
                    else:
                        print(f"❌ Failed to execute trade")
                else:
                    print(f"📝 Signal logged (trading disabled)")

        except Exception as e:
            print(f"❌ Error processing strategy {strategy_key}: {e}")

    def _test_connections(self) -> bool:
        """Test all required connections."""
        print("🧪 Testing connections...")

        # Test OANDA API connection
        if not self.data_feed.test_connection():
            print("❌ OANDA API connection failed")
            return False

        print("✅ OANDA API connection successful")

        # Test data feed
        test_data = self.data_feed.get_latest_candles("EUR_USD", "M5", count=5)
        if test_data.empty:
            print("❌ Data feed test failed")
            return False

        print("✅ Data feed test successful")

        return True

    def _get_account_info(self) -> AccountInfo:
        """Get current account information from OANDA."""
        try:
            account_summary = self.api.get_account_summary()

            if not account_summary:
                # Return default values if API call fails
                return AccountInfo(
                    balance=10000.0,
                    equity=10000.0,
                    margin_used=0.0,
                    free_margin=10000.0,
                    max_position_size=1000.0,
                )

            return AccountInfo(
                balance=float(account_summary.get("balance", 10000.0)),
                equity=float(account_summary.get("NAV", 10000.0)),
                margin_used=float(account_summary.get("marginUsed", 0.0)),
                free_margin=float(account_summary.get("marginAvailable", 10000.0)),
                max_position_size=1000.0,  # Default max position size
            )

        except Exception as e:
            print(f"Error getting account info: {e}")
            # Return default values
            return AccountInfo(
                balance=10000.0,
                equity=10000.0,
                margin_used=0.0,
                free_margin=10000.0,
                max_position_size=1000.0,
            )


if __name__ == "__main__":
    # Test the live trading engine
    print("🧪 Testing Live Trading Engine...")

    # Create engine
    engine = LiveTradingEngine(update_interval=60)  # 1 minute for testing

    # Add some strategies
    print("\n📈 Adding strategies...")

    # Add MA strategy
    ma_config = {"fast_ma": 10, "slow_ma": 20, "ma_type": "SMA"}
    engine.add_strategy("ma_crossover", "EUR_USD", "M5", ma_config)

    # Add RSI strategy
    rsi_config = {"rsi_period": 14, "overbought_level": 70, "oversold_level": 30}
    engine.add_strategy("rsi", "GBP_USD", "M15", rsi_config)

    # Check engine status
    status = engine.get_engine_status()
    print(f"\n📊 Engine Status:")
    for key, value in status.items():
        if value is not None:
            print(f"   {key}: {value}")

    print("\n🎯 Live Trading Engine test completed!")
    print("\n💡 To start live trading, call: engine.start_trading()")
    print(
        "💡 To run in demo mode: engine.disable_trading() then engine.start_trading()"
    )

"""
Live Trading Example

Example script showing how to set up and run the live trading system
with OANDA data and multiple strategies.
"""

import sys
import os
import time
from datetime import datetime

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.live_trading import LiveTradingEngine


def main():
    """Main example function."""
    print("🚀 4ex.ninja Live Trading System")
    print("=" * 50)

    # Create the live trading engine
    print("🔧 Initializing Live Trading Engine...")
    engine = LiveTradingEngine(
        update_interval=300,  # Check for signals every 5 minutes
        max_positions=5,  # Maximum 5 open positions
        risk_per_trade=0.02,  # Risk 2% per trade
    )

    # Add trading strategies
    print("\n📈 Adding Trading Strategies...")

    strategies = [
        {
            "name": "ma_crossover",
            "instrument": "EUR_USD",
            "timeframe": "M15",
            "config": {
                "fast_ma": 10,
                "slow_ma": 20,
                "ma_type": "SMA",
                "min_crossover_strength": 0.1,
            },
        },
        {
            "name": "rsi",
            "instrument": "GBP_USD",
            "timeframe": "M15",
            "config": {
                "rsi_period": 14,
                "overbought_level": 70,
                "oversold_level": 30,
                "min_rsi_strength": 0.2,
            },
        },
        {
            "name": "bollinger",
            "instrument": "USD_JPY",
            "timeframe": "H1",
            "config": {
                "bb_period": 20,
                "bb_std": 2.0,
                "signal_mode": "reversal",
                "min_band_width": 0.001,
            },
        },
        {
            "name": "ma_crossover",
            "instrument": "AUD_USD",
            "timeframe": "H1",
            "config": {
                "fast_ma": 5,
                "slow_ma": 15,
                "ma_type": "EMA",
                "min_crossover_strength": 0.15,
            },
        },
    ]

    successful_strategies = 0
    for strategy in strategies:
        success = engine.add_strategy(
            strategy["name"],
            strategy["instrument"],
            strategy["timeframe"],
            strategy["config"],
        )
        if success:
            successful_strategies += 1

    print(f"✅ Successfully added {successful_strategies}/{len(strategies)} strategies")

    # Display engine status
    print("\n📊 Engine Status:")
    status = engine.get_engine_status()
    for key, value in status.items():
        if value is not None and key not in ["strategies"]:
            print(f"   {key}: {value}")

    print(f"\n📋 Active Strategies:")
    for strategy_name in status["strategies"]:
        print(f"   • {strategy_name}")

    # Ask user for trading mode
    print("\n🤔 Choose trading mode:")
    print("1. Demo Mode (signals only, no real trades)")
    print("2. Live Trading (real trades with real money)")
    print("3. Exit")

    while True:
        try:
            choice = input("\nEnter your choice (1-3): ").strip()

            if choice == "1":
                print("\n🎭 Starting in DEMO MODE...")
                engine.disable_trading()
                run_trading_session(engine, demo_mode=True)
                break

            elif choice == "2":
                print(
                    "\n⚠️  WARNING: You are about to start LIVE TRADING with real money!"
                )
                confirm = input("Type 'CONFIRM' to proceed: ").strip()

                if confirm == "CONFIRM":
                    print("\n💰 Starting LIVE TRADING...")
                    engine.enable_trading()
                    run_trading_session(engine, demo_mode=False)
                else:
                    print("❌ Live trading cancelled")
                break

            elif choice == "3":
                print("👋 Goodbye!")
                break

            else:
                print("❌ Invalid choice. Please enter 1, 2, or 3.")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break


def run_trading_session(engine: LiveTradingEngine, demo_mode: bool = True):
    """
    Run a trading session with the engine.

    Args:
        engine: The live trading engine
        demo_mode: Whether running in demo mode
    """
    mode_text = "DEMO MODE" if demo_mode else "LIVE TRADING"
    print(f"\n🚀 Starting {mode_text}")
    print("=" * 50)

    if demo_mode:
        print("📝 Demo mode: Signals will be generated but no real trades executed")
    else:
        print("💰 Live mode: Real trades will be executed!")

    print("\nPress Ctrl+C to stop trading\n")

    try:
        # Start the trading engine (this will run continuously)
        engine.start_trading()

    except KeyboardInterrupt:
        print(f"\n🛑 Stopping {mode_text}...")
        engine.stop_trading()

        # Show final statistics
        print("\n📊 Final Statistics:")
        status = engine.get_engine_status()
        print(f"   Signals Generated: {status['signals_generated']}")
        print(f"   Trades Executed: {status['trades_executed']}")
        print(f"   Open Positions: {status['open_positions']}")
        print(f"   Account Balance: ${status['account_balance']:.2f}")
        print(f"   Risk Level: {status['risk_level']}")

        if status["uptime"]:
            print(f"   Session Duration: {status['uptime']}")


def quick_demo():
    """Quick demo function for testing."""
    print("🎭 Quick Demo Mode")
    print("=" * 30)

    # Create engine
    engine = LiveTradingEngine(update_interval=60)  # 1 minute for demo

    # Add one strategy
    engine.add_strategy(
        "ma_crossover", "EUR_USD", "M5", {"fast_ma": 5, "slow_ma": 10, "ma_type": "SMA"}
    )

    # Disable trading (demo mode)
    engine.disable_trading()

    print("\n📊 Running 3-minute demo...")
    print("Press Ctrl+C to stop early\n")

    try:
        # Start for 3 minutes
        start_time = time.time()
        engine.is_running = True

        # Run for 3 minutes or until interrupted
        while time.time() - start_time < 180:  # 3 minutes
            engine._trading_loop()
            time.sleep(5)  # Short demo intervals

        print("\n✅ Demo completed!")

    except KeyboardInterrupt:
        print("\n🛑 Demo stopped by user")

    finally:
        engine.stop_trading()

        # Show results
        status = engine.get_engine_status()
        print(f"\n📊 Demo Results:")
        print(f"   Signals Generated: {status['signals_generated']}")
        print(f"   Demo Duration: {status['uptime']}")


if __name__ == "__main__":
    print("🚀 4ex.ninja Live Trading System")
    print("Choose an option:")
    print("1. Full Interactive Mode")
    print("2. Quick Demo (3 minutes)")
    print("3. Exit")

    try:
        choice = input("\nEnter choice (1-3): ").strip()

        if choice == "1":
            main()
        elif choice == "2":
            quick_demo()
        elif choice == "3":
            print("👋 Goodbye!")
        else:
            print("❌ Invalid choice")

    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

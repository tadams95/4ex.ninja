#!/usr/bin/env python3
"""
Production Deployment Script for Multi-Timeframe Strategy
Run this script on DigitalOcean to backtest and deploy the optimized multi-timeframe strategy.
"""

import asyncio
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from services.production_backtest_service import (
    run_backtest_for_deployment,
    run_live_monitoring_service,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


async def main():
    """
    Main deployment function for 4ex.ninja Multi-Timeframe Strategy.
    """
    print("🚀 4ex.ninja - Multi-Timeframe Strategy Deployment")
    print("=" * 60)
    print(f"Deployment Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Strategy: Enhanced Multi-Timeframe (Weekly/Daily/4H)")
    print(f"Expected Performance: 28.7% Annual Returns")
    print("=" * 60)

    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()

        if mode == "backtest":
            print("\n📊 RUNNING COMPREHENSIVE BACKTEST...")
            results = await run_backtest_for_deployment()

            print("\n📋 BACKTEST SUMMARY:")
            print(
                f"- Strategy Performance Grade: {results['portfolio_performance']['performance_grade']}"
            )
            print(
                f"- Portfolio Return: {results['portfolio_performance']['average_annual_return']}%"
            )
            print(
                f"- Sharpe Ratio: {results['portfolio_performance']['portfolio_sharpe_ratio']}"
            )
            print(
                f"- Max Drawdown: {results['portfolio_performance']['maximum_drawdown']}%"
            )
            print(
                f"- Win Rate: {results['portfolio_performance']['average_win_rate']:.1%}"
            )

            deployment = results["deployment_readiness"]
            print(f"\n🚦 DEPLOYMENT STATUS:")
            print(
                f"- Ready for Live Trading: {'✅ YES' if deployment['ready_for_live_trading'] else '⚠️ NEEDS REVIEW'}"
            )
            print(f"- Risk Assessment: {deployment['risk_assessment']}")
            print(f"- Deployment Score: {deployment['live_deployment_score']}/1.0")

            if deployment["recommended_pairs"]:
                print(
                    f"- Recommended Pairs: {', '.join(deployment['recommended_pairs'])}"
                )

            print(f"\n📁 Results saved for frontend display")
            return results

        elif mode == "live":
            print("\n📡 STARTING LIVE MONITORING SERVICE...")
            print("This will run continuously and monitor all currency pairs.")
            print("Press Ctrl+C to stop.\n")

            await run_live_monitoring_service()

        elif mode == "both":
            print("\n🔄 RUNNING BACKTEST + LIVE MONITORING...")

            # First run backtest
            print("📊 Step 1: Running comprehensive backtest...")
            results = await run_backtest_for_deployment()

            deployment = results["deployment_readiness"]
            if deployment["ready_for_live_trading"]:
                print(f"✅ Backtest passed! Starting live monitoring...")
                await asyncio.sleep(5)
                await run_live_monitoring_service()
            else:
                print(f"⚠️ Backtest indicates review needed before live deployment.")
                print(
                    f"Performance Grade: {results['portfolio_performance']['performance_grade']}"
                )
                return results
        else:
            print(f"❌ Unknown mode: {mode}")
            print_usage()
    else:
        print_usage()


def print_usage():
    """Print usage instructions."""
    print("\n📖 USAGE:")
    print("python deploy_production_strategy.py <mode>")
    print("\nMODES:")
    print("  backtest  - Run comprehensive backtest only")
    print("  live      - Run live monitoring service only")
    print("  both      - Run backtest, then start live monitoring if passed")
    print("\nEXAMPLES:")
    print("  python deploy_production_strategy.py backtest")
    print("  python deploy_production_strategy.py live")
    print("  python deploy_production_strategy.py both")
    print("\n🎯 For production deployment, use 'both' mode.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Deployment stopped by user.")
    except Exception as e:
        print(f"\n❌ Deployment failed: {str(e)}")
        logging.exception("Deployment error")
        sys.exit(1)

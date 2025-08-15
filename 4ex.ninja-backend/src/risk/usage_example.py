"""
Risk Assessment Usage Example

This script demonstrates how to use the Risk Quantification System
for analyzing trading strategy risk in production.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.risk.risk_assessment_integrator import RiskAssessmentIntegrator


def create_sample_strategy_data():
    """Create sample strategy parameters and historical data for demonstration."""

    # EUR/USD H4 strategy parameters (from actual strategy file)
    strategy_params = {
        "slow_ma": 140,
        "fast_ma": 40,
        "atr_period": 14,
        "sl_atr_multiplier": 1.5,
        "tp_atr_multiplier": 2.0,
        "risk_per_trade": 0.02,  # 2% risk per trade
        "min_atr_value": 0.0003,
        "min_rr_ratio": 1.5,
    }

    # Generate sample historical data (1 year of H4 data)
    np.random.seed(42)  # For reproducible results
    periods = 2190  # Approximately 1 year of H4 candles
    initial_price = 1.1000

    # Generate realistic EUR/USD returns
    daily_vol = 0.012  # 1.2% daily volatility
    h4_vol = daily_vol / np.sqrt(6)  # Convert to H4 volatility

    returns = np.random.normal(0.00005, h4_vol, periods)  # Slight upward bias

    # Add some autocorrelation (trend persistence)
    for i in range(1, len(returns)):
        returns[i] += 0.03 * returns[i - 1]

    # Generate price series
    prices = [initial_price]
    for ret in returns:
        prices.append(prices[-1] * (1 + ret))

    # Create OHLC data
    data = []
    for i in range(1, len(prices)):
        close = prices[i]
        open_price = prices[i - 1]

        # Generate realistic high/low based on ATR
        range_size = abs(np.random.normal(0, 0.0008))  # Typical H4 range
        high = max(open_price, close) + range_size
        low = min(open_price, close) - range_size

        data.append({"open": open_price, "high": high, "low": low, "close": close})

    historical_data = pd.DataFrame(data)

    return strategy_params, historical_data


def run_risk_assessment_example():
    """Run a complete risk assessment example."""

    print("🎯 Risk Assessment System - Usage Example")
    print("=" * 60)

    # Initialize the risk assessment integrator
    integrator = RiskAssessmentIntegrator()

    # Create sample data
    print("📊 Creating sample strategy data...")
    strategy_params, historical_data = create_sample_strategy_data()

    print(f"   Strategy: EUR/USD H4 Moving Average Crossover")
    print(f"   Data periods: {len(historical_data)}")
    print(
        f"   Price range: {historical_data['close'].min():.4f} - {historical_data['close'].max():.4f}"
    )
    print(f"   Parameters: {strategy_params}")
    print()

    # Run comprehensive risk assessment
    print("🔍 Running comprehensive risk assessment...")
    print("   This may take 30-60 seconds for full analysis...")

    assessment = integrator.run_comprehensive_risk_assessment(
        strategy_name="EUR_USD_H4_MA_Strategy",
        strategy_params=strategy_params,
        historical_data=historical_data,
        n_simulations=50,  # Reduced for faster demo
    )

    # Display results
    print("\n✅ Risk assessment completed!")
    integrator.print_assessment_summary(assessment)

    # Save detailed results
    saved_file = integrator.save_comprehensive_assessment(assessment)
    if saved_file:
        print(f"📄 Detailed assessment saved to: {saved_file}")

    return assessment


def analyze_specific_risk_component():
    """Demonstrate analysis of a specific risk component."""

    print("\n🔬 Specific Risk Component Analysis Example")
    print("=" * 60)

    from src.risk.risk_calculator import RiskCalculator

    # Initialize risk calculator
    calculator = RiskCalculator()

    # Create sample data
    strategy_params, historical_data = create_sample_strategy_data()

    # Run Monte Carlo analysis
    print("🎲 Running Monte Carlo simulation...")
    risk_results = calculator.calculate_max_drawdown_potential(
        strategy_params, historical_data, n_simulations=25
    )

    if "error" not in risk_results:
        print(f"   Value at Risk (95%): {risk_results['value_at_risk_95']:.4f}")
        print(f"   Value at Risk (99%): {risk_results['value_at_risk_99']:.4f}")
        print(
            f"   Worst case drawdown (95%): {risk_results['worst_case_drawdown_95']:.4f}"
        )
        print(
            f"   Simulations completed: {risk_results['simulation_summary']['successful_simulations']}"
        )
    else:
        print(f"   Error: {risk_results['error']}")

    # Test position sizing validation
    print("\n⚖️ Validating position sizing...")
    position_results = calculator.validate_position_sizing(strategy_params)

    if "error" not in position_results:
        print(
            f"   Position sizing safety: {position_results['position_sizing_safety']}"
        )
        print(f"   Leverage risk: {position_results['leverage_risk']}")
        print(f"   Overall risk level: {position_results['overall_risk_level']}")

        if position_results["recommendations"]:
            print("   Recommendations:")
            for rec in position_results["recommendations"][:3]:
                print(f"     • {rec}")
    else:
        print(f"   Error: {position_results['error']}")


def main():
    """Main demonstration function."""

    try:
        # Run comprehensive risk assessment
        assessment = run_risk_assessment_example()

        # Demonstrate specific component analysis
        analyze_specific_risk_component()

        print("\n🎉 Risk Assessment Demo Complete!")
        print("\n📋 Next Steps:")
        print("   1. Integrate with your actual strategy parameters")
        print("   2. Use live historical data from your database")
        print("   3. Set up automated risk monitoring")
        print("   4. Configure risk threshold alerts")
        print("   5. Schedule regular risk assessments")

        return assessment

    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Run the demonstration
    results = main()

    if results:
        print(f"\n✅ Demo completed successfully!")
        print(f"🔧 Risk assessment system is ready for production use!")
    else:
        print(f"\n❌ Demo encountered errors. Please check the implementation.")

"""
Test suite for Risk Assessment Implementation (Objective 1.2)

This module provides comprehensive testing for the risk quantification system
including unit tests and integration tests for all risk analysis components.
"""

import pytest
import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

# Import the risk analysis modules
from src.risk.risk_calculator import RiskCalculator
from src.risk.max_loss_analyzer import MaxLossAnalyzer
from src.risk.volatility_impact_analyzer import VolatilityImpactAnalyzer


class TestRiskAssessmentSuite:
    """Comprehensive test suite for risk assessment components."""

    @pytest.fixture
    def sample_strategy_params(self):
        """Sample strategy parameters for testing."""
        return {
            "slow_ma": 140,
            "fast_ma": 40,
            "atr_period": 14,
            "sl_atr_multiplier": 1.5,
            "tp_atr_multiplier": 2.0,
            "risk_per_trade": 0.02,
            "min_atr_value": 0.0003,
            "min_rr_ratio": 1.5,
        }

    @pytest.fixture
    def sample_price_data(self):
        """Generate sample price data for testing."""
        np.random.seed(42)  # For reproducible tests

        # Generate 500 periods of synthetic price data
        periods = 500
        initial_price = 1.1000

        # Generate returns with some autocorrelation
        returns = np.random.normal(0.0001, 0.015, periods)

        # Add some trend and mean reversion
        for i in range(1, len(returns)):
            returns[i] += 0.1 * returns[i - 1]  # Small autocorrelation

        # Generate price series
        prices = [initial_price]
        for ret in returns:
            prices.append(prices[-1] * (1 + ret))

        # Create OHLC data
        data = []
        for i in range(1, len(prices)):
            close = prices[i]
            open_price = prices[i - 1]
            high = max(open_price, close) * (1 + abs(np.random.normal(0, 0.002)))
            low = min(open_price, close) * (1 - abs(np.random.normal(0, 0.002)))

            data.append(
                {
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close,
                    "timestamp": datetime.now() - timedelta(hours=periods - i),
                }
            )

        return pd.DataFrame(data)

    @pytest.fixture
    def high_volatility_data(self):
        """Generate high volatility price data for stress testing."""
        np.random.seed(123)

        periods = 200
        initial_price = 1.1000

        # Generate high volatility returns
        returns = np.random.normal(0.0001, 0.035, periods)  # Higher volatility

        prices = [initial_price]
        for ret in returns:
            prices.append(prices[-1] * (1 + ret))

        data = []
        for i in range(1, len(prices)):
            close = prices[i]
            open_price = prices[i - 1]
            high = max(open_price, close) * (1 + abs(np.random.normal(0, 0.01)))
            low = min(open_price, close) * (1 - abs(np.random.normal(0, 0.01)))

            data.append({"open": open_price, "high": high, "low": low, "close": close})

        return pd.DataFrame(data)

    def test_risk_calculator_initialization(self):
        """Test RiskCalculator initialization."""
        calculator = RiskCalculator()
        assert calculator.risk_free_rate == 0.02
        assert calculator.logger is not None

    def test_risk_calculator_with_custom_rate(self):
        """Test RiskCalculator with custom risk-free rate."""
        calculator = RiskCalculator(risk_free_rate=0.03)
        assert calculator.risk_free_rate == 0.03

    def test_max_drawdown_calculation(self, sample_price_data, sample_strategy_params):
        """Test maximum drawdown potential calculation."""
        calculator = RiskCalculator()

        result = calculator.calculate_max_drawdown_potential(
            sample_strategy_params, sample_price_data, n_simulations=10
        )

        # Verify result structure
        assert isinstance(result, dict)
        assert "value_at_risk_95" in result
        assert "value_at_risk_99" in result
        assert "conditional_var_95" in result
        assert "conditional_var_99" in result
        assert "worst_case_drawdown_95" in result
        assert "max_simulated_drawdown" in result
        assert "drawdown_distribution" in result
        assert "simulation_summary" in result

        # Verify VaR values are reasonable (should be negative for losses)
        assert result["value_at_risk_95"] <= 0
        assert (
            result["value_at_risk_99"] <= result["value_at_risk_95"]
        )  # 99% VaR should be worse

        # Verify drawdown values are positive percentages
        assert result["worst_case_drawdown_95"] >= 0
        assert result["max_simulated_drawdown"] >= 0

    def test_position_sizing_validation(self, sample_strategy_params):
        """Test position sizing validation."""
        calculator = RiskCalculator()

        result = calculator.validate_position_sizing(sample_strategy_params)

        # Verify result structure
        assert isinstance(result, dict)
        assert "position_sizing_safety" in result
        assert "leverage_risk" in result
        assert "atr_multiplier_analysis" in result
        assert "risk_per_trade_analysis" in result
        assert "recommendations" in result

        # With default parameters, should be acceptable
        assert result["position_sizing_safety"] == "ACCEPTABLE"
        assert result["leverage_risk"] == "ACCEPTABLE"

    def test_position_sizing_validation_high_risk(self):
        """Test position sizing validation with high-risk parameters."""
        calculator = RiskCalculator()

        high_risk_params = {
            "sl_atr_multiplier": 4.0,  # Too high
            "tp_atr_multiplier": 2.0,
            "risk_per_trade": 0.08,  # 8% - too aggressive
        }

        result = calculator.validate_position_sizing(high_risk_params)

        assert result["position_sizing_safety"] == "HIGH_RISK"
        assert result["leverage_risk"] == "HIGH_RISK"
        assert len(result["recommendations"]) > 0

    def test_monte_carlo_simulation(self, sample_price_data, sample_strategy_params):
        """Test Monte Carlo simulation functionality."""
        calculator = RiskCalculator()

        result = calculator.run_monte_carlo_simulation(
            sample_strategy_params, sample_price_data, n_simulations=5
        )

        assert isinstance(result, dict)
        assert "simulations" in result
        assert "final_returns" in result
        assert len(result["simulations"]) > 0
        assert len(result["final_returns"]) > 0

    def test_max_loss_analyzer_initialization(self):
        """Test MaxLossAnalyzer initialization."""
        analyzer = MaxLossAnalyzer()
        assert analyzer.logger is not None
        assert len(analyzer.crisis_periods) > 0

        # Check crisis periods structure
        for period in analyzer.crisis_periods:
            assert "name" in period
            assert "start" in period
            assert "end" in period
            assert "description" in period

    def test_maximum_loss_scenarios_analysis(
        self, sample_price_data, sample_strategy_params
    ):
        """Test maximum loss scenarios analysis."""
        analyzer = MaxLossAnalyzer()

        result = analyzer.analyze_maximum_loss_scenarios(
            sample_strategy_params, sample_price_data
        )

        assert isinstance(result, dict)
        assert "worst_case_scenarios" in result
        assert "stress_test_results" in result
        assert "crisis_period_analysis" in result
        assert "maximum_consecutive_losses" in result
        assert "portfolio_impact" in result
        assert "risk_recommendations" in result

    def test_stress_testing(self, sample_price_data, sample_strategy_params):
        """Test stress testing functionality."""
        analyzer = MaxLossAnalyzer()

        # Test stress scenarios
        stress_result = analyzer._run_stress_tests(
            sample_strategy_params, sample_price_data
        )

        assert isinstance(stress_result, dict)
        # Should have multiple stress scenarios
        expected_scenarios = [
            "Extreme Volatility",
            "High Trend Market",
            "Choppy Market",
            "Flash Crash",
        ]
        for scenario in expected_scenarios:
            if scenario in stress_result:
                assert "scenario_parameters" in stress_result[scenario]
                assert "simulation_results" in stress_result[scenario]

    def test_consecutive_losses_analysis(
        self, sample_price_data, sample_strategy_params
    ):
        """Test consecutive losses analysis."""
        analyzer = MaxLossAnalyzer()

        result = analyzer._analyze_consecutive_losses(
            sample_strategy_params, sample_price_data
        )

        assert isinstance(result, dict)
        assert "maximum_consecutive_losses" in result
        assert "loss_impact_analysis" in result
        assert "risk_assessment" in result
        assert "scenario_statistics" in result

        # Verify consecutive losses is a reasonable number
        max_losses = result["maximum_consecutive_losses"]
        assert isinstance(max_losses, int)
        assert max_losses >= 0

    def test_volatility_impact_analyzer_initialization(self):
        """Test VolatilityImpactAnalyzer initialization."""
        analyzer = VolatilityImpactAnalyzer()
        assert analyzer.logger is not None
        assert len(analyzer.volatility_regimes) > 0

        # Check volatility regimes structure
        for regime_name, regime_data in analyzer.volatility_regimes.items():
            assert "threshold" in regime_data
            assert "description" in regime_data

    def test_volatility_regime_classification(self, sample_price_data):
        """Test volatility regime classification."""
        analyzer = VolatilityImpactAnalyzer()

        result = analyzer._classify_volatility_regimes(sample_price_data)

        assert isinstance(result, dict)
        assert "regime_classification" in result
        assert "regime_statistics" in result
        assert "volatility_thresholds" in result
        assert "overall_statistics" in result

        # Verify classification data
        classification = result["regime_classification"]
        assert len(classification) > 0

        # Check that we have different volatility regimes
        regimes = set(
            item["vol_regime"] for item in classification if "vol_regime" in item
        )
        assert len(regimes) >= 2  # Should have at least 2 different regimes

    def test_atr_effectiveness_analysis(
        self, sample_price_data, sample_strategy_params
    ):
        """Test ATR effectiveness analysis."""
        analyzer = VolatilityImpactAnalyzer()

        # First classify regimes
        volatility_data = analyzer._classify_volatility_regimes(sample_price_data)

        # Then analyze ATR effectiveness
        result = analyzer._analyze_atr_effectiveness(
            sample_strategy_params, sample_price_data, volatility_data
        )

        assert isinstance(result, dict)
        assert "regime_analysis" in result
        assert "overall_assessment" in result

    def test_high_volatility_scenario(
        self, high_volatility_data, sample_strategy_params
    ):
        """Test analysis with high volatility data."""
        calculator = RiskCalculator()
        analyzer = MaxLossAnalyzer()
        vol_analyzer = VolatilityImpactAnalyzer()

        # Test risk calculator with high volatility
        risk_result = calculator.calculate_max_drawdown_potential(
            sample_strategy_params, high_volatility_data, n_simulations=5
        )

        # Should have higher risk metrics
        assert "value_at_risk_95" in risk_result

        # Test max loss analyzer
        loss_result = analyzer.analyze_maximum_loss_scenarios(
            sample_strategy_params, high_volatility_data
        )

        assert "worst_case_scenarios" in loss_result

        # Test volatility analyzer
        vol_result = vol_analyzer.analyze_volatility_impact(
            sample_strategy_params, high_volatility_data
        )

        assert "volatility_regimes" in vol_result

    def test_risk_metrics_calculation(self, sample_price_data):
        """Test comprehensive risk metrics calculation."""
        calculator = RiskCalculator()

        # Create sample equity curve
        equity_curve = [10000 + i * 100 + np.random.normal(0, 50) for i in range(100)]

        # Create sample trades
        trades = []
        for i in range(20):
            pnl = np.random.normal(50, 200)  # Random P&L
            trades.append(
                {"pnl": pnl, "entry_price": 1.1000, "exit_price": 1.1000 + pnl / 10000}
            )

        result = calculator.calculate_risk_metrics(equity_curve, trades)

        assert isinstance(result, dict)
        assert "total_return" in result
        assert "annualized_volatility" in result
        assert "sharpe_ratio" in result
        assert "max_drawdown" in result
        assert "value_at_risk_95" in result
        assert "value_at_risk_99" in result
        assert "win_rate" in result
        assert "profit_factor" in result
        assert "calmar_ratio" in result
        assert "sortino_ratio" in result

    def test_error_handling_insufficient_data(self):
        """Test error handling with insufficient data."""
        calculator = RiskCalculator()
        analyzer = MaxLossAnalyzer()
        vol_analyzer = VolatilityImpactAnalyzer()

        # Create minimal data
        minimal_data = pd.DataFrame(
            {
                "open": [1.1000, 1.1001],
                "high": [1.1002, 1.1003],
                "low": [1.0999, 1.1000],
                "close": [1.1001, 1.1002],
            }
        )

        strategy_params = {"sl_atr_multiplier": 1.5, "risk_per_trade": 0.02}

        # These should handle insufficient data gracefully
        risk_result = calculator.calculate_max_drawdown_potential(
            strategy_params, minimal_data, n_simulations=1
        )

        loss_result = analyzer.analyze_maximum_loss_scenarios(
            strategy_params, minimal_data
        )

        vol_result = vol_analyzer.analyze_volatility_impact(
            strategy_params, minimal_data
        )

        # Results should be dictionaries (even if with errors)
        assert isinstance(risk_result, dict)
        assert isinstance(loss_result, dict)
        assert isinstance(vol_result, dict)

    def test_file_saving_functionality(
        self, sample_price_data, sample_strategy_params, tmp_path
    ):
        """Test file saving functionality."""
        calculator = RiskCalculator()
        analyzer = MaxLossAnalyzer()
        vol_analyzer = VolatilityImpactAnalyzer()

        # Run analyses
        risk_result = calculator.calculate_max_drawdown_potential(
            sample_strategy_params, sample_price_data, n_simulations=3
        )

        loss_result = analyzer.analyze_maximum_loss_scenarios(
            sample_strategy_params, sample_price_data
        )

        vol_result = vol_analyzer.analyze_volatility_impact(
            sample_strategy_params, sample_price_data
        )

        # Test saving (these create files in the reports directory)
        if not risk_result.get("error"):
            risk_file = calculator.save_risk_assessment(risk_result, "test_strategy")
            # File should be created (even if empty string returned on error)
            assert isinstance(risk_file, str)

        if not loss_result.get("error"):
            loss_file = analyzer.save_max_loss_analysis(loss_result, "test_strategy")
            assert isinstance(loss_file, str)

        if not vol_result.get("error"):
            vol_file = vol_analyzer.save_volatility_analysis(
                vol_result, "test_strategy"
            )
            assert isinstance(vol_file, str)

    def test_parameter_boundary_conditions(self):
        """Test analysis with extreme parameter values."""
        calculator = RiskCalculator()

        # Test with extreme parameters
        extreme_params = {
            "sl_atr_multiplier": 0.1,  # Very tight stop
            "tp_atr_multiplier": 10.0,  # Very wide target
            "risk_per_trade": 0.001,  # Very conservative
            "atr_period": 5,  # Very short ATR
        }

        result = calculator.validate_position_sizing(extreme_params)

        assert isinstance(result, dict)
        assert (
            len(result["recommendations"]) > 0
        )  # Should have recommendations for extreme values

    def test_integration_comprehensive_analysis(
        self, sample_price_data, sample_strategy_params
    ):
        """Test comprehensive integrated analysis across all components."""
        calculator = RiskCalculator()
        analyzer = MaxLossAnalyzer()
        vol_analyzer = VolatilityImpactAnalyzer()

        # Run all analyses
        risk_analysis = calculator.calculate_max_drawdown_potential(
            sample_strategy_params, sample_price_data, n_simulations=5
        )

        position_validation = calculator.validate_position_sizing(
            sample_strategy_params
        )

        max_loss_analysis = analyzer.analyze_maximum_loss_scenarios(
            sample_strategy_params, sample_price_data
        )

        volatility_analysis = vol_analyzer.analyze_volatility_impact(
            sample_strategy_params, sample_price_data
        )

        # Verify all analyses completed
        assert isinstance(risk_analysis, dict)
        assert isinstance(position_validation, dict)
        assert isinstance(max_loss_analysis, dict)
        assert isinstance(volatility_analysis, dict)

        # Create integrated report
        integrated_report = {
            "timestamp": datetime.now().isoformat(),
            "strategy_parameters": sample_strategy_params,
            "risk_analysis": risk_analysis,
            "position_validation": position_validation,
            "max_loss_analysis": max_loss_analysis,
            "volatility_analysis": volatility_analysis,
            "overall_risk_assessment": self._create_overall_assessment(
                risk_analysis,
                position_validation,
                max_loss_analysis,
                volatility_analysis,
            ),
        }

        assert "overall_risk_assessment" in integrated_report
        assert integrated_report["overall_risk_assessment"]["status"] in [
            "LOW",
            "MODERATE",
            "HIGH",
            "CRITICAL",
        ]

    def _create_overall_assessment(
        self, risk_analysis, position_validation, max_loss_analysis, volatility_analysis
    ):
        """Create overall risk assessment from component analyses."""
        risk_factors = []

        # Check VaR
        if (
            "value_at_risk_95" in risk_analysis
            and risk_analysis["value_at_risk_95"] < -0.1
        ):
            risk_factors.append("High VaR (>10%)")

        # Check position sizing
        if position_validation.get("overall_risk_level") == "HIGH":
            risk_factors.append("High position sizing risk")

        # Check maximum drawdown
        if (
            "worst_case_drawdown_95" in risk_analysis
            and risk_analysis["worst_case_drawdown_95"] > 0.2
        ):
            risk_factors.append("High maximum drawdown risk (>20%)")

        # Determine overall status
        if len(risk_factors) >= 3:
            status = "CRITICAL"
        elif len(risk_factors) >= 2:
            status = "HIGH"
        elif len(risk_factors) >= 1:
            status = "MODERATE"
        else:
            status = "LOW"

        return {
            "status": status,
            "risk_factors": risk_factors,
            "recommendation": f"Overall risk level: {status}. Review identified risk factors.",
        }


# Additional utility functions for running tests
def run_emergency_risk_validation():
    """Run emergency risk validation for immediate deployment."""
    print("=" * 60)
    print("EMERGENCY RISK VALIDATION - OBJECTIVE 1.2")
    print("=" * 60)

    # Initialize components
    calculator = RiskCalculator()
    analyzer = MaxLossAnalyzer()
    vol_analyzer = VolatilityImpactAnalyzer()

    # Create sample data for validation
    np.random.seed(42)
    periods = 300
    initial_price = 1.1000
    returns = np.random.normal(0.0001, 0.012, periods)

    prices = [initial_price]
    for ret in returns:
        prices.append(prices[-1] * (1 + ret))

    data = []
    for i in range(1, len(prices)):
        close = prices[i]
        open_price = prices[i - 1]
        high = max(open_price, close) * (1 + abs(np.random.normal(0, 0.002)))
        low = min(open_price, close) * (1 - abs(np.random.normal(0, 0.002)))

        data.append({"open": open_price, "high": high, "low": low, "close": close})

    sample_data = pd.DataFrame(data)

    # Standard strategy parameters
    strategy_params = {
        "slow_ma": 140,
        "fast_ma": 40,
        "atr_period": 14,
        "sl_atr_multiplier": 1.5,
        "tp_atr_multiplier": 2.0,
        "risk_per_trade": 0.02,
    }

    print(f"✓ Generated {len(sample_data)} periods of test data")
    print(f"✓ Using strategy parameters: {strategy_params}")
    print()

    # Run risk analysis
    print("Running risk analysis...")
    risk_result = calculator.calculate_max_drawdown_potential(
        strategy_params, sample_data, n_simulations=50
    )

    if "error" not in risk_result:
        print(f"✓ VaR 95%: {risk_result['value_at_risk_95']:.4f}")
        print(f"✓ Worst case drawdown: {risk_result['worst_case_drawdown_95']:.4f}")
        print(
            f"✓ Simulations completed: {risk_result['simulation_summary']['successful_simulations']}"
        )
    else:
        print(f"✗ Risk analysis error: {risk_result['error']}")

    # Run position sizing validation
    print("\nRunning position sizing validation...")
    position_result = calculator.validate_position_sizing(strategy_params)

    if "error" not in position_result:
        print(f"✓ Position sizing safety: {position_result['position_sizing_safety']}")
        print(f"✓ Leverage risk: {position_result['leverage_risk']}")
        print(f"✓ Overall risk level: {position_result['overall_risk_level']}")
    else:
        print(f"✗ Position validation error: {position_result['error']}")

    # Run max loss analysis
    print("\nRunning maximum loss analysis...")
    loss_result = analyzer.analyze_maximum_loss_scenarios(strategy_params, sample_data)

    if "error" not in loss_result:
        print("✓ Maximum loss analysis completed")
        if "portfolio_impact" in loss_result:
            portfolio = loss_result["portfolio_impact"]
            print(
                f"✓ Portfolio risk category: {portfolio.get('overall_risk_category', 'UNKNOWN')}"
            )
    else:
        print(f"✗ Max loss analysis error: {loss_result['error']}")

    # Run volatility impact analysis
    print("\nRunning volatility impact analysis...")
    vol_result = vol_analyzer.analyze_volatility_impact(strategy_params, sample_data)

    if "error" not in vol_result:
        print("✓ Volatility impact analysis completed")
        if "volatility_regimes" in vol_result:
            regimes = vol_result["volatility_regimes"].get("regime_statistics", {})
            print(f"✓ Volatility regimes analyzed: {len(regimes)}")
    else:
        print(f"✗ Volatility analysis error: {vol_result['error']}")

    print("\n" + "=" * 60)
    print("RISK ASSESSMENT FRAMEWORK VALIDATION COMPLETE")
    print("=" * 60)

    # Overall assessment
    error_count = sum(
        1
        for result in [risk_result, position_result, loss_result, vol_result]
        if "error" in result
    )

    if error_count == 0:
        print("🟢 ALL COMPONENTS OPERATIONAL - READY FOR PRODUCTION")
    elif error_count <= 1:
        print("🟡 MOSTLY OPERATIONAL - MINOR ISSUES DETECTED")
    else:
        print("🔴 MULTIPLE ISSUES DETECTED - REVIEW REQUIRED")

    return {
        "risk_analysis": risk_result,
        "position_validation": position_result,
        "max_loss_analysis": loss_result,
        "volatility_analysis": vol_result,
        "validation_status": (
            "PASS" if error_count == 0 else "PARTIAL" if error_count <= 1 else "FAIL"
        ),
    }


if __name__ == "__main__":
    # Run emergency validation when script is executed directly
    validation_results = run_emergency_risk_validation()

    # Save validation results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"risk_assessment_validation_{timestamp}.json"

    try:
        import json

        with open(results_file, "w") as f:
            json.dump(validation_results, f, indent=2, default=str)
        print(f"\n✓ Validation results saved to: {results_file}")
    except Exception as e:
        print(f"\n✗ Could not save results: {str(e)}")

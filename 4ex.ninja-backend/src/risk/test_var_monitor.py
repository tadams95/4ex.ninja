"""
Unit tests for VaR Monitor - Phase 2 Week 1 validation
Tests core VaR calculation functionality and breach detection
"""

import pytest
import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.risk.var_monitor import (
    VaRMonitor,
    VaRResult,
    HistoricalVaR,
    ParametricVaR,
    MonteCarloVaR,
)
from src.backtesting.portfolio_manager import PortfolioState
from src.backtesting.position_manager import Position


class TestVaRCalculationMethods:
    """Test individual VaR calculation methods"""

    def setup_method(self):
        """Setup test data"""
        # Create realistic forex returns data
        np.random.seed(42)
        dates = pd.date_range(start="2024-01-01", periods=300, freq="D")
        returns = np.random.normal(0, 0.01, 300)  # 1% daily volatility
        self.returns_series = pd.Series(returns, index=dates)
        self.position_value = 10000.0
        self.confidence_level = 0.95

    @pytest.mark.asyncio
    async def test_historical_var_calculation(self):
        """Test historical VaR calculation"""
        historical_var = HistoricalVaR(lookback_days=252)

        var_result = await historical_var.calculate(
            self.returns_series, self.position_value, self.confidence_level
        )

        # Assertions
        assert isinstance(var_result, float)
        assert var_result >= 0  # VaR should be positive (loss amount)
        assert var_result <= self.position_value  # Cannot exceed position value

        # Check that result is reasonable (should be around 1-3% of position value)
        expected_range = (0.01 * self.position_value, 0.05 * self.position_value)
        assert expected_range[0] <= var_result <= expected_range[1]

    @pytest.mark.asyncio
    async def test_parametric_var_calculation(self):
        """Test parametric VaR calculation"""
        parametric_var = ParametricVaR(lookback_days=252)

        var_result = await parametric_var.calculate(
            self.returns_series, self.position_value, self.confidence_level
        )

        # Assertions
        assert isinstance(var_result, float)
        assert var_result >= 0
        assert var_result <= self.position_value

        # Should be reasonable for normal distribution assumption
        expected_range = (0.01 * self.position_value, 0.04 * self.position_value)
        assert expected_range[0] <= var_result <= expected_range[1]

    @pytest.mark.asyncio
    async def test_monte_carlo_var_calculation(self):
        """Test Monte Carlo VaR calculation"""
        monte_carlo_var = MonteCarloVaR(num_simulations=1000, lookback_days=252)

        var_result = await monte_carlo_var.calculate(
            self.returns_series, self.position_value, self.confidence_level
        )

        # Assertions
        assert isinstance(var_result, float)
        assert var_result >= 0
        assert var_result <= self.position_value

        # Should be reasonable for Monte Carlo simulation
        expected_range = (0.005 * self.position_value, 0.05 * self.position_value)
        assert expected_range[0] <= var_result <= expected_range[1]

    @pytest.mark.asyncio
    async def test_insufficient_data_handling(self):
        """Test handling of insufficient data"""
        # Create very short returns series
        short_returns = pd.Series(
            [0.01, -0.02], index=pd.date_range("2024-01-01", periods=2)
        )

        historical_var = HistoricalVaR()
        var_result = await historical_var.calculate(
            short_returns, self.position_value, self.confidence_level
        )

        # Should return 0.0 for insufficient data
        assert var_result == 0.0


class TestVaRMonitor:
    """Test VaR Monitor functionality"""

    def setup_method(self):
        """Setup test VaR monitor and portfolio"""
        self.var_monitor = VaRMonitor(confidence_level=0.95)

        # Create mock portfolio state
        self.mock_position = Position(
            position_id="test_001",
            pair="EUR_USD",
            direction="BUY",
            entry_price=1.1000,
            position_size=1000.0,
            stop_loss=1.0950,
            take_profit=1.1100,
            entry_time=datetime.now(),
            strategy_name="test_strategy",
            unrealized_pnl=50.0,
        )

        self.portfolio_state = PortfolioState(
            total_balance=100000.0,
            available_balance=90000.0,
            total_risk=0.02,
            active_positions={"EUR_USD": self.mock_position},
            strategy_allocations={},
        )

    @pytest.mark.asyncio
    async def test_portfolio_var_calculation(self):
        """Test portfolio-level VaR calculation"""
        var_results = await self.var_monitor.calculate_portfolio_var(
            self.portfolio_state
        )

        # Should have results for all three methods
        expected_methods = ["historical", "parametric", "monte_carlo"]
        assert all(method in var_results for method in expected_methods)

        # Each result should be a VaRResult object
        for method, result in var_results.items():
            assert isinstance(result, VaRResult)
            assert result.method == method
            assert result.confidence_level == 0.95
            assert result.currency_pair == "PORTFOLIO"
            assert result.value >= 0

    @pytest.mark.asyncio
    async def test_var_breach_detection(self):
        """Test VaR breach detection"""
        # First calculate VaR
        await self.var_monitor.calculate_portfolio_var(self.portfolio_state)

        # Check for breaches
        breaches = await self.var_monitor.check_var_breaches()

        # Should return breach status for each method
        assert isinstance(breaches, dict)
        expected_methods = ["historical", "parametric", "monte_carlo"]

        for method in expected_methods:
            if method in breaches:
                assert isinstance(breaches[method], bool)

    @pytest.mark.asyncio
    async def test_var_alert_generation(self):
        """Test VaR alert generation"""
        # First calculate VaR
        await self.var_monitor.calculate_portfolio_var(self.portfolio_state)

        # Create mock breach scenario
        mock_breaches = {"historical": True, "parametric": False, "monte_carlo": True}

        alerts = await self.var_monitor.generate_var_alerts(mock_breaches)

        # Should generate alerts for breached methods
        assert isinstance(alerts, list)

        for alert in alerts:
            assert "type" in alert
            assert "severity" in alert
            assert "method" in alert
            assert "message" in alert
            assert alert["type"] == "VAR_BREACH"

    @pytest.mark.asyncio
    async def test_empty_portfolio_handling(self):
        """Test handling of empty portfolio"""
        empty_portfolio = PortfolioState(
            total_balance=100000.0,
            available_balance=100000.0,
            total_risk=0.0,
            active_positions={},
            strategy_allocations={},
        )

        var_results = await self.var_monitor.calculate_portfolio_var(empty_portfolio)

        # Should return empty results for empty portfolio
        assert isinstance(var_results, dict)
        assert len(var_results) == 0

    def test_var_summary_generation(self):
        """Test VaR summary generation"""
        summary = self.var_monitor.get_var_summary()

        # Should contain expected fields
        expected_fields = [
            "timestamp",
            "target_var",
            "confidence_level",
            "breach_count",
            "methods_available",
            "last_calculation",
        ]

        for field in expected_fields:
            assert field in summary

        assert summary["target_var"] == 0.0031  # 0.31%
        assert summary["confidence_level"] == 0.95
        assert isinstance(summary["methods_available"], list)
        assert len(summary["methods_available"]) == 3


class TestVaRResultDataClass:
    """Test VaRResult data class functionality"""

    def test_var_result_creation(self):
        """Test VaRResult creation and conversion"""
        var_result = VaRResult(
            method="historical",
            value=150.25,
            confidence_level=0.95,
            timestamp=datetime.now(),
            currency_pair="EUR_USD",
            position_size=1000.0,
            volatility=0.012,
        )

        # Test to_dict conversion
        result_dict = var_result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["method"] == "historical"
        assert result_dict["value"] == 150.25
        assert result_dict["confidence_level"] == 0.95
        assert result_dict["currency_pair"] == "EUR_USD"
        assert result_dict["position_size"] == 1000.0
        assert result_dict["volatility"] == 0.012
        assert "timestamp" in result_dict


class TestVaRMonitorIntegration:
    """Integration tests for VaR monitoring system"""

    @pytest.mark.asyncio
    async def test_multi_position_portfolio(self):
        """Test VaR calculation with multiple positions"""
        var_monitor = VaRMonitor(confidence_level=0.95)

        # Create multiple positions
        positions = {
            "EUR_USD": Position(
                position_id="test_001",
                pair="EUR_USD",
                direction="BUY",
                entry_price=1.1000,
                position_size=1000.0,
                stop_loss=1.0950,
                take_profit=1.1100,
                entry_time=datetime.now(),
                strategy_name="test_strategy",
            ),
            "GBP_USD": Position(
                position_id="test_002",
                pair="GBP_USD",
                direction="SELL",
                entry_price=1.2500,
                position_size=-800.0,
                stop_loss=1.2600,
                take_profit=1.2400,
                entry_time=datetime.now(),
                strategy_name="test_strategy",
            ),
        }

        portfolio_state = PortfolioState(
            total_balance=100000.0,
            available_balance=90000.0,
            total_risk=0.03,
            active_positions=positions,
            strategy_allocations={},
        )

        # Calculate VaR
        var_results = await var_monitor.calculate_portfolio_var(portfolio_state)

        # Should have results for all methods
        assert len(var_results) == 3

        # Portfolio VaR should be higher than single position
        for method, result in var_results.items():
            assert result.value > 0
            assert result.currency_pair == "PORTFOLIO"
            # Total position size should reflect both positions
            assert result.position_size > 1000.0

    @pytest.mark.asyncio
    async def test_var_target_validation(self):
        """Test that VaR calculations align with target (0.31%)"""
        var_monitor = VaRMonitor(confidence_level=0.95)

        # This is more of a validation test - in production we'd compare against actual data
        assert var_monitor.target_daily_var == 0.0031
        assert var_monitor.confidence_level == 0.95
        assert var_monitor.lookback_period == 252


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

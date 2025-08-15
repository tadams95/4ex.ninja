"""
Tests for Emergency Validation Framework

This module provides comprehensive tests for the emergency backtesting
and performance validation systems.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.validation.emergency_backtest import EmergencyBacktester
from src.validation.performance_validator import PerformanceValidator


class TestEmergencyBacktester:
    """Test cases for EmergencyBacktester class."""

    @pytest.fixture
    def sample_ohlc_data(self):
        """Create sample OHLC data for testing."""
        dates = pd.date_range(start="2024-01-01", periods=100, freq="4H")

        # Generate realistic price data
        np.random.seed(42)
        price_base = 1.1000
        price_changes = np.random.normal(0, 0.0010, 100)
        prices = np.cumsum(price_changes) + price_base

        data = {
            "timestamp": dates,
            "open": prices + np.random.normal(0, 0.0005, 100),
            "high": prices + np.abs(np.random.normal(0, 0.0010, 100)),
            "low": prices - np.abs(np.random.normal(0, 0.0010, 100)),
            "close": prices,
        }

        df = pd.DataFrame(data)
        # Ensure high is actually higher than low
        df["high"] = np.maximum(df["high"], df[["open", "close"]].max(axis=1))
        df["low"] = np.minimum(df["low"], df[["open", "close"]].min(axis=1))

        return df

    @pytest.fixture
    def sample_strategy_params(self):
        """Create sample strategy parameters."""
        return {
            "slow_ma": 20,
            "fast_ma": 10,
            "atr_period": 14,
            "sl_atr_multiplier": 1.5,
            "tp_atr_multiplier": 2.0,
            "min_atr_value": 0.0003,
            "min_rr_ratio": 1.5,
        }

    @pytest.fixture
    def backtester(self):
        """Create EmergencyBacktester instance with mocked dependencies."""
        with patch("src.validation.emergency_backtest.OandaAPI"), patch(
            "src.validation.emergency_backtest.MongoClient"
        ):

            backtester = EmergencyBacktester()
            return backtester

    def test_parse_strategy_parameters(self, backtester):
        """Test strategy parameter parsing."""
        strategy_content = """
        def __init__(
            self,
            slow_ma: int = 140,
            fast_ma: int = 40,
            atr_period: int = 14,
            sl_atr_multiplier: float = 1.5,
            tp_atr_multiplier: float = 2.0,
            min_atr_value: float = 0.0003,
            min_rr_ratio: float = 1.5,
        ):
            self.slow_ma = slow_ma
            self.fast_ma = fast_ma
        """

        params = backtester._parse_strategy_parameters(strategy_content)

        assert params["slow_ma"] == 140
        assert params["fast_ma"] == 40
        assert params["atr_period"] == 14
        assert params["sl_atr_multiplier"] == 1.5
        assert params["tp_atr_multiplier"] == 2.0
        assert params["min_atr_value"] == 0.0003
        assert params["min_rr_ratio"] == 1.5

    def test_run_backtest(self, backtester, sample_ohlc_data, sample_strategy_params):
        """Test backtest execution."""
        trades = backtester.run_backtest(sample_ohlc_data, sample_strategy_params)

        assert isinstance(trades, list)

        # If trades were generated, check their structure
        if trades:
            trade = trades[0]
            required_fields = [
                "entry_time",
                "entry_price",
                "direction",
                "atr_at_entry",
                "sl_price",
                "tp_price",
                "exit_time",
                "exit_price",
                "exit_reason",
                "pips",
            ]

            for field in required_fields:
                assert field in trade, f"Trade missing required field: {field}"

            assert trade["direction"] in ["BUY", "SELL"]
            assert trade["exit_reason"] in ["signal_change", "stop_loss", "take_profit"]
            assert isinstance(trade["pips"], (int, float))

    def test_calculate_performance_metrics_empty_trades(self, backtester):
        """Test performance metrics calculation with no trades."""
        metrics = backtester.calculate_performance_metrics([])

        assert metrics["total_trades"] == 0
        assert metrics["total_pips"] == 0
        assert metrics["win_rate"] == 0
        assert "error" in metrics

    def test_calculate_performance_metrics_with_trades(self, backtester):
        """Test performance metrics calculation with sample trades."""
        sample_trades = [
            {"pips": 50.0, "entry_time": datetime.now(), "exit_time": datetime.now()},
            {"pips": -30.0, "entry_time": datetime.now(), "exit_time": datetime.now()},
            {"pips": 20.0, "entry_time": datetime.now(), "exit_time": datetime.now()},
            {"pips": -15.0, "entry_time": datetime.now(), "exit_time": datetime.now()},
        ]

        metrics = backtester.calculate_performance_metrics(sample_trades)

        assert metrics["total_trades"] == 4
        assert metrics["total_pips"] == 25.0  # 50 - 30 + 20 - 15
        assert metrics["winning_trades"] == 2
        assert metrics["losing_trades"] == 2
        assert metrics["win_rate"] == 0.5
        assert metrics["average_win_pips"] == 35.0  # (50 + 20) / 2
        assert metrics["average_loss_pips"] == -22.5  # (-30 - 15) / 2

    def test_calculate_max_drawdown(self, backtester):
        """Test maximum drawdown calculation."""
        sample_trades = [
            {"pips": 50.0},
            {"pips": -30.0},
            {"pips": -40.0},  # This should create max drawdown
            {"pips": 60.0},
        ]

        max_dd = backtester.calculate_max_drawdown(sample_trades)

        # Running balance: 50, 20, -20, 40
        # Peak: 50, Max drawdown when balance hits -20 = 70 pips
        assert max_dd == 70.0

    def test_calculate_sharpe_ratio(self, backtester):
        """Test Sharpe ratio calculation."""
        # Sample trades with consistent returns
        sample_trades = [
            {"pips": 10.0},
            {"pips": 15.0},
            {"pips": 5.0},
            {"pips": 20.0},
        ]

        sharpe = backtester.calculate_sharpe_ratio(sample_trades)

        assert isinstance(sharpe, float)
        assert not np.isnan(sharpe)

    @patch("src.validation.emergency_backtest.Path.exists")
    def test_load_production_parameters_file_not_found(self, mock_exists, backtester):
        """Test parameter loading when strategy file doesn't exist."""
        mock_exists.return_value = False

        params = backtester.load_production_parameters("EUR_USD", "H4")
        assert params is None

    def test_fetch_historical_data_empty_result(self, backtester):
        """Test historical data fetching with empty MongoDB result."""
        # Mock MongoDB collection to return empty result
        mock_collection = Mock()
        mock_collection.find.return_value.sort.return_value = []
        backtester.db = {"EUR_USD_H4": mock_collection}

        result = backtester.fetch_historical_data(
            "EUR_USD", "H4", datetime.now() - timedelta(days=30), datetime.now()
        )

        assert result is None


class TestPerformanceValidator:
    """Test cases for PerformanceValidator class."""

    @pytest.fixture
    def validator(self):
        """Create PerformanceValidator instance."""
        return PerformanceValidator()

    @pytest.fixture
    def sample_historical_results(self):
        """Create sample historical results."""
        return {
            "EUR_USD_H4": {
                "total_trades": 50,
                "total_pips": 250.0,
                "win_rate": 0.6,
                "profit_factor": 1.8,
                "max_drawdown": 80.0,
                "sharpe_ratio": 0.85,
            },
            "GBP_USD_H4": {
                "total_trades": 45,
                "total_pips": 180.0,
                "win_rate": 0.55,
                "profit_factor": 1.5,
                "max_drawdown": 120.0,
                "sharpe_ratio": 0.72,
            },
        }

    @pytest.fixture
    def sample_current_results(self):
        """Create sample current results."""
        return {
            "EUR_USD_H4": {
                "total_trades": 48,
                "total_pips": 300.0,
                "win_rate": 0.65,
                "profit_factor": 2.1,
                "max_drawdown": 75.0,
                "sharpe_ratio": 0.92,
            },
            "GBP_USD_H4": {
                "total_trades": 42,
                "total_pips": 120.0,
                "win_rate": 0.48,
                "profit_factor": 1.2,
                "max_drawdown": 150.0,
                "sharpe_ratio": 0.58,
            },
        }

    def test_calculate_performance_changes(
        self, validator, sample_historical_results, sample_current_results
    ):
        """Test performance change calculation."""
        changes = validator._calculate_performance_changes(
            sample_historical_results, sample_current_results
        )

        # Check EUR_USD_H4 changes
        eur_usd_changes = changes["EUR_USD_H4"]

        # Total pips should increase from 250 to 300 (20% increase)
        assert eur_usd_changes["total_pips"]["historical"] == 250.0
        assert eur_usd_changes["total_pips"]["current"] == 300.0
        assert eur_usd_changes["total_pips"]["absolute_change"] == 50.0
        assert abs(eur_usd_changes["total_pips"]["percentage_change"] - 20.0) < 0.1

        # Win rate should increase from 0.6 to 0.65
        assert eur_usd_changes["win_rate"]["historical"] == 0.6
        assert eur_usd_changes["win_rate"]["current"] == 0.65

    def test_calculate_risk_changes(
        self, validator, sample_historical_results, sample_current_results
    ):
        """Test risk change calculation."""
        risk_changes = validator._calculate_risk_changes(
            sample_historical_results, sample_current_results
        )

        # Check EUR_USD_H4 risk changes
        eur_usd_risk = risk_changes["EUR_USD_H4"]

        # Max drawdown should decrease (risk reduced)
        assert eur_usd_risk["max_drawdown"]["historical"] == 80.0
        assert eur_usd_risk["max_drawdown"]["current"] == 75.0
        assert eur_usd_risk["max_drawdown"]["risk_increased"] == False

        # Sharpe ratio should increase (risk-adjusted return improved)
        assert eur_usd_risk["sharpe_ratio"]["historical"] == 0.85
        assert eur_usd_risk["sharpe_ratio"]["current"] == 0.92
        assert eur_usd_risk["sharpe_ratio"]["risk_increased"] == False

    def test_assess_overall_performance_improved(
        self, validator, sample_historical_results, sample_current_results
    ):
        """Test overall performance assessment - improved case."""
        comparison = {
            "performance_change": validator._calculate_performance_changes(
                sample_historical_results, sample_current_results
            )
        }

        assessment = validator._assess_overall_performance(comparison)

        # EUR_USD improved, GBP_USD degraded, so should be MIXED
        assert assessment in ["IMPROVED", "MIXED"]

    def test_identify_critical_issues(self, validator):
        """Test critical issue identification."""
        # Create data with critical issues
        performance_changes = {
            "EUR_USD_H4": {
                "total_pips": {"percentage_change": -60.0},  # Critical drop
                "win_rate": {"percentage_change": -30.0},  # Significant drop
            }
        }

        risk_changes = {
            "EUR_USD_H4": {
                "max_drawdown": {
                    "historical": 100.0,
                    "current": 200.0,
                    "risk_increased": True,
                }
            }
        }

        comparison = {
            "performance_change": performance_changes,
            "risk_metrics_change": risk_changes,
        }

        issues = validator._identify_critical_issues(comparison)

        assert len(issues) >= 2  # Should identify both pips drop and drawdown increase
        assert any("CRITICAL" in issue for issue in issues)

    def test_generate_recommendations(self, validator):
        """Test recommendation generation."""
        comparison_data = {
            "performance_change": {
                "EUR_USD_H4": {
                    "win_rate": {"percentage_change": -15.0},
                    "profit_factor": {"percentage_change": -25.0},
                }
            },
            "risk_metrics_change": {
                "EUR_USD_H4": {"max_drawdown": {"risk_increased": True}}
            },
            "overall_assessment": "DEGRADED",
        }

        recommendations = validator.generate_recommendations(comparison_data)

        assert len(recommendations) > 0
        assert any("INVESTIGATE" in rec or "REVIEW" in rec for rec in recommendations)
        assert any(
            "URGENT" in rec for rec in recommendations
        )  # Due to DEGRADED assessment

    def test_validate_infrastructure_improvements(self, validator):
        """Test infrastructure improvement validation."""
        # Test excellent performance
        excellent_metrics = {
            "cache_hit_ratio": 0.98,
            "average_latency_ms": 45,
            "uptime_percentage": 99.9,
            "error_rate": 0.001,
        }

        result = validator.validate_infrastructure_improvements(excellent_metrics)

        assert result["cache_performance"] == "EXCELLENT"
        assert result["latency_improvements"] == "EXCELLENT"
        assert result["reliability_score"] > 0.95
        assert result["optimization_effectiveness"] == "SUCCESSFUL"

        # Test poor performance
        poor_metrics = {
            "cache_hit_ratio": 0.60,
            "average_latency_ms": 500,
            "uptime_percentage": 85.0,
            "error_rate": 0.1,
        }

        result = validator.validate_infrastructure_improvements(poor_metrics)

        assert result["cache_performance"] == "NEEDS_IMPROVEMENT"
        assert result["latency_improvements"] == "NEEDS_IMPROVEMENT"
        assert result["optimization_effectiveness"] == "INSUFFICIENT"
        assert len(result["recommendations"]) > 0


class TestIntegration:
    """Integration tests for the validation framework."""

    def test_end_to_end_validation_workflow(self):
        """Test complete validation workflow."""
        # This test would require more setup but demonstrates the workflow

        with patch("src.validation.emergency_backtest.OandaAPI"), patch(
            "src.validation.emergency_backtest.MongoClient"
        ) as mock_mongo:

            # Mock the MongoDB database
            mock_db = Mock()
            mock_mongo.return_value.__getitem__ = Mock(return_value=mock_db)

            # Create instances
            backtester = EmergencyBacktester()
            validator = PerformanceValidator()

            # Test that components can be instantiated without errors
            assert backtester is not None
            assert validator is not None

            # Test that reports directory is created
            assert backtester.results_dir.exists()
            assert validator.reports_dir.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

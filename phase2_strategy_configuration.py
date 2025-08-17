#!/usr/bin/env python3
"""
🚀 Phase 2 Strategy Configuration & Testing Setup
Comprehensive Backtesting Plan - Strategy Parameter Configuration

This script sets up and executes the strategy configuration phase including:
1. Parameter matrix creation for all strategy combinations
2. Regime detection calibration for forex markets
3. Strategy validation and testing preparation
4. Ready-to-execute backtesting configurations
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("strategy_configuration.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


class StrategyConfigurationManager:
    """
    Manages comprehensive strategy configuration for Phase 2 backtesting
    """

    def __init__(self):
        # Strategy configurations to test
        self.ma_combinations = {
            "conservative": {
                "fast": 50,
                "slow": 200,
                "description": "Lower frequency, higher accuracy",
            },
            "moderate": {"fast": 20, "slow": 50, "description": "Balanced approach"},
            "aggressive": {
                "fast": 10,
                "slow": 21,
                "description": "Higher frequency trading",
            },
        }

        self.risk_settings = {
            "conservative": {
                "risk_per_trade": 0.01,
                "min_rr": 2.0,
                "description": "1% risk, 2:1 R:R minimum",
            },
            "moderate": {
                "risk_per_trade": 0.02,
                "min_rr": 1.5,
                "description": "2% risk, 1.5:1 R:R minimum",
            },
            "aggressive": {
                "risk_per_trade": 0.03,
                "min_rr": 1.0,
                "description": "3% risk, 1:1 R:R minimum",
            },
        }

        self.timeframes = {
            "weekly": {"tf": "W", "description": "Long-term trend following"},
            "daily": {"tf": "D", "description": "Medium-term swing trading"},
            "fourhour": {"tf": "H4", "description": "Short-term opportunities"},
        }

        self.currency_pairs = {
            "major": ["EUR_USD", "GBP_USD", "USD_JPY", "USD_CHF", "AUD_USD", "USD_CAD"],
            "minor": ["EUR_GBP", "EUR_JPY", "GBP_JPY", "AUD_JPY"],
        }

        # Configuration directories
        self.config_dir = Path("strategy_configs")
        self.parameter_matrices_dir = self.config_dir / "parameter_matrices"
        self.regime_configs_dir = self.config_dir / "regime_configs"
        self.backtest_configs_dir = self.config_dir / "backtest_configs"

        self._setup_directories()

    def _setup_directories(self):
        """Create configuration directory structure"""
        for directory in [
            self.parameter_matrices_dir,
            self.regime_configs_dir,
            self.backtest_configs_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)
        logger.info("✅ Strategy configuration directories created")

    def create_parameter_matrix(self):
        """
        Create comprehensive parameter matrix for all strategy combinations
        """
        logger.info("🎯 Creating comprehensive parameter matrix...")

        parameter_matrix = {
            "creation_date": datetime.now().isoformat(),
            "total_combinations": 0,
            "configurations": [],
        }

        config_id = 1

        # Generate all combinations
        for ma_name, ma_config in self.ma_combinations.items():
            for risk_name, risk_config in self.risk_settings.items():
                for tf_name, tf_config in self.timeframes.items():

                    configuration = {
                        "config_id": f"CONFIG_{config_id:03d}",
                        "name": f"{ma_name}_{risk_name}_{tf_name}",
                        "description": f"{ma_config['description']} | {risk_config['description']} | {tf_config['description']}",
                        "parameters": {
                            "moving_averages": {
                                "fast_period": ma_config["fast"],
                                "slow_period": ma_config["slow"],
                                "type": ma_name,
                            },
                            "risk_management": {
                                "risk_per_trade": risk_config["risk_per_trade"],
                                "min_risk_reward": risk_config["min_rr"],
                                "max_drawdown": 0.20,  # 20% max drawdown
                                "type": risk_name,
                            },
                            "timeframe": {"primary": tf_config["tf"], "type": tf_name},
                            "entry_rules": {
                                "ma_cross_confirmation": True,
                                "volume_confirmation": False,
                                "regime_filter": True,
                            },
                            "exit_rules": {
                                "trailing_stop": True,
                                "profit_target": True,
                                "time_exit": False,
                            },
                        },
                        "expected_characteristics": {
                            "trade_frequency": self._estimate_trade_frequency(
                                ma_name, tf_name
                            ),
                            "expected_win_rate": self._estimate_win_rate(
                                ma_name, risk_name
                            ),
                            "expected_profit_factor": self._estimate_profit_factor(
                                ma_name, risk_name
                            ),
                        },
                    }

                    parameter_matrix["configurations"].append(configuration)
                    config_id += 1

        parameter_matrix["total_combinations"] = len(parameter_matrix["configurations"])

        # Save parameter matrix
        matrix_file = (
            self.parameter_matrices_dir / "comprehensive_parameter_matrix.json"
        )
        with open(matrix_file, "w") as f:
            json.dump(parameter_matrix, f, indent=2)

        logger.info(
            f"✅ Parameter matrix created: {parameter_matrix['total_combinations']} configurations"
        )
        return parameter_matrix

    def _estimate_trade_frequency(self, ma_type, tf_type):
        """Estimate trade frequency based on configuration"""
        frequency_map = {
            ("aggressive", "fourhour"): "Very High (50-100 trades/month)",
            ("aggressive", "daily"): "High (20-40 trades/month)",
            ("aggressive", "weekly"): "Medium (5-15 trades/month)",
            ("moderate", "fourhour"): "High (20-40 trades/month)",
            ("moderate", "daily"): "Medium (10-20 trades/month)",
            ("moderate", "weekly"): "Low (3-8 trades/month)",
            ("conservative", "fourhour"): "Medium (10-20 trades/month)",
            ("conservative", "daily"): "Low (5-10 trades/month)",
            ("conservative", "weekly"): "Very Low (1-5 trades/month)",
        }
        return frequency_map.get((ma_type, tf_type), "Medium")

    def _estimate_win_rate(self, ma_type, risk_type):
        """Estimate win rate based on configuration"""
        win_rate_map = {
            ("conservative", "conservative"): "60-70%",
            ("conservative", "moderate"): "55-65%",
            ("conservative", "aggressive"): "50-60%",
            ("moderate", "conservative"): "55-65%",
            ("moderate", "moderate"): "50-60%",
            ("moderate", "aggressive"): "45-55%",
            ("aggressive", "conservative"): "50-60%",
            ("aggressive", "moderate"): "45-55%",
            ("aggressive", "aggressive"): "40-50%",
        }
        return win_rate_map.get((ma_type, risk_type), "50-60%")

    def _estimate_profit_factor(self, ma_type, risk_type):
        """Estimate profit factor based on configuration"""
        pf_map = {
            ("conservative", "conservative"): "1.8-2.5",
            ("conservative", "moderate"): "1.6-2.2",
            ("conservative", "aggressive"): "1.4-1.9",
            ("moderate", "conservative"): "1.6-2.2",
            ("moderate", "moderate"): "1.4-1.9",
            ("moderate", "aggressive"): "1.2-1.6",
            ("aggressive", "conservative"): "1.4-1.9",
            ("aggressive", "moderate"): "1.2-1.6",
            ("aggressive", "aggressive"): "1.1-1.4",
        }
        return pf_map.get((ma_type, risk_type), "1.3-1.7")

    def calibrate_regime_detection(self):
        """
        Configure regime detection parameters optimized for forex markets
        """
        logger.info("🎛️ Calibrating regime detection for forex markets...")

        regime_config = {
            "creation_date": datetime.now().isoformat(),
            "forex_optimized": True,
            "regime_detection": {
                "trending_threshold": 0.65,  # Adjusted for forex volatility
                "ranging_threshold": 0.35,
                "volatility_lookback": 20,
                "trend_strength_period": 14,
                "regime_confirmation_period": 5,
            },
            "market_regimes": {
                "trending": {
                    "description": "Strong directional movement periods",
                    "characteristics": [
                        "sustained_direction",
                        "high_momentum",
                        "clear_structure",
                    ],
                    "strategy_adjustments": {
                        "increase_position_size": 1.2,
                        "wider_stops": 1.5,
                        "trend_following_bias": True,
                    },
                },
                "ranging": {
                    "description": "Sideways/consolidation periods",
                    "characteristics": [
                        "bounded_movement",
                        "support_resistance",
                        "low_momentum",
                    ],
                    "strategy_adjustments": {
                        "decrease_position_size": 0.8,
                        "tighter_stops": 0.8,
                        "mean_reversion_bias": True,
                    },
                },
                "high_volatility": {
                    "description": "Major news events, market stress",
                    "characteristics": [
                        "large_price_swings",
                        "news_driven",
                        "gap_movements",
                    ],
                    "strategy_adjustments": {
                        "reduce_position_size": 0.5,
                        "wider_stops": 2.0,
                        "avoid_trading": True,
                    },
                },
                "low_volatility": {
                    "description": "Quiet market periods",
                    "characteristics": ["small_ranges", "low_volume", "consolidation"],
                    "strategy_adjustments": {
                        "standard_position_size": 1.0,
                        "standard_stops": 1.0,
                        "patient_entries": True,
                    },
                },
            },
            "currency_pair_specific": {
                "EUR_USD": {"volatility_multiplier": 1.0, "trend_sensitivity": 1.0},
                "GBP_USD": {"volatility_multiplier": 1.3, "trend_sensitivity": 1.1},
                "USD_JPY": {"volatility_multiplier": 1.1, "trend_sensitivity": 0.9},
                "USD_CHF": {"volatility_multiplier": 0.9, "trend_sensitivity": 0.95},
                "AUD_USD": {"volatility_multiplier": 1.2, "trend_sensitivity": 1.05},
                "USD_CAD": {"volatility_multiplier": 1.0, "trend_sensitivity": 1.0},
                "EUR_GBP": {"volatility_multiplier": 0.8, "trend_sensitivity": 0.85},
                "EUR_JPY": {"volatility_multiplier": 1.4, "trend_sensitivity": 1.2},
                "GBP_JPY": {"volatility_multiplier": 1.6, "trend_sensitivity": 1.3},
                "AUD_JPY": {"volatility_multiplier": 1.5, "trend_sensitivity": 1.25},
            },
        }

        # Save regime configuration
        regime_file = self.regime_configs_dir / "forex_optimized_regime_config.json"
        with open(regime_file, "w") as f:
            json.dump(regime_config, f, indent=2)

        logger.info("✅ Regime detection calibrated for forex characteristics")
        return regime_config

    def create_backtest_configurations(self, parameter_matrix, regime_config):
        """
        Create ready-to-execute backtesting configurations
        """
        logger.info("🚀 Creating backtest execution configurations...")

        backtest_configs = []

        for config in parameter_matrix["configurations"]:
            for pair_type, pairs in self.currency_pairs.items():
                for pair in pairs:

                    backtest_config = {
                        "execution_id": f"BT_{config['config_id']}_{pair}",
                        "strategy_config": config,
                        "currency_pair": pair,
                        "pair_type": pair_type,
                        "data_source": {
                            "provider": "OANDA",
                            "timeframe": config["parameters"]["timeframe"]["primary"],
                            "history_period": "5Y",
                            "data_quality": "premium",
                        },
                        "regime_settings": {
                            "enabled": True,
                            "pair_specific_multipliers": regime_config[
                                "currency_pair_specific"
                            ][pair],
                        },
                        "execution_parameters": {
                            "start_capital": 10000,
                            "commission": 0.0002,  # 2 pips spread average
                            "slippage": 0.0001,  # 1 pip slippage
                            "leverage": 50,
                            "margin_requirement": 0.02,
                        },
                        "analysis_requirements": {
                            "walk_forward": True,
                            "monte_carlo": True,
                            "regime_performance": True,
                            "correlation_analysis": True,
                            "stress_testing": True,
                        },
                        "expected_execution_time": self._estimate_execution_time(
                            config
                        ),
                        "priority": self._calculate_priority(config, pair_type),
                    }

                    backtest_configs.append(backtest_config)

        # Sort by priority (high priority first)
        backtest_configs.sort(key=lambda x: x["priority"], reverse=True)

        # Save configurations in batches for organized execution
        self._save_backtest_batches(backtest_configs)

        logger.info(f"✅ Created {len(backtest_configs)} backtest configurations")
        return backtest_configs

    def _estimate_execution_time(self, config):
        """Estimate backtest execution time"""
        tf = config["parameters"]["timeframe"]["primary"]
        if tf == "H4":
            return "15-30 minutes"
        elif tf == "D":
            return "5-15 minutes"
        else:  # Weekly
            return "2-5 minutes"

    def _calculate_priority(self, config, pair_type):
        """Calculate execution priority"""
        priority = 5  # Base priority

        # Prioritize major pairs
        if pair_type == "major":
            priority += 2

        # Prioritize moderate configurations for initial validation
        if "moderate" in config["name"]:
            priority += 1

        # Prioritize daily timeframe for balance
        if config["parameters"]["timeframe"]["primary"] == "D":
            priority += 1

        return priority

    def _save_backtest_batches(self, configs):
        """Save configurations in organized batches"""

        # Batch 1: High priority major pairs with moderate settings
        batch1 = [c for c in configs if c["priority"] >= 8]
        batch1_file = self.backtest_configs_dir / "batch_1_high_priority.json"
        with open(batch1_file, "w") as f:
            json.dump(batch1, f, indent=2)

        # Batch 2: All major pairs
        batch2 = [c for c in configs if c["pair_type"] == "major"]
        batch2_file = self.backtest_configs_dir / "batch_2_major_pairs.json"
        with open(batch2_file, "w") as f:
            json.dump(batch2, f, indent=2)

        # Batch 3: All configurations
        batch3_file = self.backtest_configs_dir / "batch_3_complete.json"
        with open(batch3_file, "w") as f:
            json.dump(configs, f, indent=2)

        logger.info("✅ Backtest configurations saved in organized batches")

    def execute_strategy_configuration(self):
        """
        Execute complete strategy configuration process
        """
        logger.info("🎯 Starting comprehensive strategy configuration...")

        results = {
            "configuration_date": datetime.now().isoformat(),
            "phase": "Phase 2 - Strategy Configuration",
            "status": "In Progress",
            "components": {},
        }

        try:
            # Step 1: Create parameter matrix
            logger.info("Step 1: Creating parameter matrix...")
            parameter_matrix = self.create_parameter_matrix()
            results["components"]["parameter_matrix"] = {
                "status": "Complete",
                "total_configurations": parameter_matrix["total_combinations"],
            }

            # Step 2: Calibrate regime detection
            logger.info("Step 2: Calibrating regime detection...")
            regime_config = self.calibrate_regime_detection()
            results["components"]["regime_calibration"] = {
                "status": "Complete",
                "forex_optimized": True,
            }

            # Step 3: Create backtest configurations
            logger.info("Step 3: Creating backtest configurations...")
            backtest_configs = self.create_backtest_configurations(
                parameter_matrix, regime_config
            )
            results["components"]["backtest_configurations"] = {
                "status": "Complete",
                "total_configurations": len(backtest_configs),
            }

            results["status"] = "Complete"
            results["next_phase"] = "Phase 3 - Comprehensive Backtesting Execution"

            # Save results summary
            results_file = self.config_dir / "phase2_configuration_results.json"
            with open(results_file, "w") as f:
                json.dump(results, f, indent=2)

            logger.info("🎉 Strategy configuration complete!")
            self._print_configuration_summary(results)

            return results

        except Exception as e:
            logger.error(f"❌ Configuration failed: {e}")
            results["status"] = "Failed"
            results["error"] = str(e)
            return results

    def _print_configuration_summary(self, results):
        """Print configuration summary"""
        print("\n" + "=" * 70)
        print("🎯 PHASE 2 STRATEGY CONFIGURATION SUMMARY")
        print("=" * 70)
        print(f"📅 Configuration Date: {results['configuration_date']}")
        print(f"✅ Status: {results['status']}")
        print()
        print("📊 Configuration Components:")
        for component, details in results["components"].items():
            status_icon = "✅" if details["status"] == "Complete" else "❌"
            print(
                f"  {status_icon} {component.replace('_', ' ').title()}: {details['status']}"
            )
            if "total_configurations" in details:
                print(
                    f"     📈 Total Configurations: {details['total_configurations']}"
                )

        print("\n🚀 READY FOR PHASE 3: COMPREHENSIVE BACKTESTING EXECUTION")
        print("📋 Next Steps:")
        print("  1. Execute Batch 1: High Priority Major Pairs")
        print("  2. Analyze initial results and optimize")
        print("  3. Execute full backtesting suite")
        print("  4. Generate comprehensive performance reports")


def main():
    """
    Main execution function for Phase 2 Strategy Configuration
    """
    print("🎯 PHASE 2: STRATEGY CONFIGURATION & TESTING SETUP")
    print("=" * 60)
    print("Comprehensive Backtesting Plan - Strategy Parameter Configuration")
    print("Target: 27 strategy combinations across 10 currency pairs")
    print()

    # Initialize strategy configuration manager
    manager = StrategyConfigurationManager()

    # Execute comprehensive strategy configuration
    results = manager.execute_strategy_configuration()

    # Check completion status
    if results["status"] == "Complete":
        print("\n✅ PHASE 2 COMPLETE - READY FOR BACKTESTING EXECUTION!")
    else:
        print(f"\n❌ PHASE 2 INCOMPLETE - Status: {results['status']}")


if __name__ == "__main__":
    main()

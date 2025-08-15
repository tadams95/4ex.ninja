"""
Parameter Analyzer

This module provides analysis capabilities for current production parameters,
tracking changes, and assessing risk levels associated with parameter settings.
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import pandas as pd
import logging
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class ParameterAnalyzer:
    """
    Analyzer for strategy parameters and their risk assessment.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config_path = project_root / "config"
        self.strategy_path = project_root / "src" / "strategies"
        self.reports_dir = Path(__file__).parent / "reports"
        self.reports_dir.mkdir(exist_ok=True)

        # Parameter risk thresholds
        self.risk_thresholds = {
            "slow_ma": {"min": 50, "max": 200, "optimal_min": 80, "optimal_max": 160},
            "fast_ma": {"min": 10, "max": 50, "optimal_min": 20, "optimal_max": 40},
            "atr_period": {"min": 7, "max": 21, "optimal_min": 10, "optimal_max": 18},
            "sl_atr_multiplier": {
                "min": 0.5,
                "max": 3.0,
                "optimal_min": 1.0,
                "optimal_max": 2.5,
            },
            "tp_atr_multiplier": {
                "min": 1.0,
                "max": 5.0,
                "optimal_min": 1.5,
                "optimal_max": 3.0,
            },
            "min_atr_value": {
                "min": 0.0001,
                "max": 0.001,
                "optimal_min": 0.0002,
                "optimal_max": 0.0008,
            },
            "min_rr_ratio": {
                "min": 1.0,
                "max": 3.0,
                "optimal_min": 1.2,
                "optimal_max": 2.0,
            },
        }

    def extract_current_parameters(self) -> Dict:
        """
        Extract all current production parameters from strategy files.

        Returns:
            Dictionary mapping strategy names to their parameters
        """
        parameters = {}

        try:
            # Get all strategy files
            strategy_files = list(self.strategy_path.glob("MA_*_strat.py"))

            self.logger.info(f"Found {len(strategy_files)} strategy files")

            for file_path in strategy_files:
                pair_timeframe = self.parse_strategy_filename(file_path.name)

                if pair_timeframe:
                    params = self.extract_parameters_from_file(file_path)
                    if params:
                        parameters[pair_timeframe] = params
                        self.logger.debug(f"Extracted parameters for {pair_timeframe}")
                    else:
                        self.logger.warning(f"No parameters found in {file_path.name}")
                else:
                    self.logger.warning(
                        f"Could not parse strategy filename: {file_path.name}"
                    )

            self.logger.info(
                f"Successfully extracted parameters for {len(parameters)} strategies"
            )
            return parameters

        except Exception as e:
            self.logger.error(f"Failed to extract current parameters: {str(e)}")
            return {}

    def parse_strategy_filename(self, filename: str) -> Optional[str]:
        """
        Parse strategy filename to extract pair and timeframe.

        Args:
            filename: Strategy filename (e.g., "MA_EUR_USD_H4_strat.py")

        Returns:
            Formatted pair_timeframe string or None if parsing fails
        """
        try:
            # Remove .py extension and split by underscore
            name_parts = filename.replace(".py", "").split("_")

            # Expected format: MA_CURR1_CURR2_TIMEFRAME_strat
            if (
                len(name_parts) >= 5
                and name_parts[0] == "MA"
                and name_parts[-1] == "strat"
            ):
                curr1 = name_parts[1]
                curr2 = name_parts[2]
                timeframe = name_parts[3]

                return f"{curr1}_{curr2}_{timeframe}"

            return None

        except Exception as e:
            self.logger.error(f"Error parsing filename {filename}: {str(e)}")
            return None

    def extract_parameters_from_file(self, file_path: Path) -> Optional[Dict]:
        """
        Extract parameters from a strategy Python file.

        Args:
            file_path: Path to strategy file

        Returns:
            Dictionary of extracted parameters or None if failed
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            params = self._parse_strategy_parameters(content)

            if params:
                # Add metadata
                params["_metadata"] = {
                    "file_path": str(file_path),
                    "last_modified": datetime.fromtimestamp(
                        file_path.stat().st_mtime
                    ).isoformat(),
                    "extraction_timestamp": datetime.now().isoformat(),
                }

            return params

        except Exception as e:
            self.logger.error(
                f"Failed to extract parameters from {file_path}: {str(e)}"
            )
            return None

    def _parse_strategy_parameters(self, content: str) -> Dict:
        """
        Parse strategy parameters from Python file content.

        Args:
            content: Python file content as string

        Returns:
            Dictionary of extracted parameters
        """
        params = {}

        try:
            # Look for parameter lines directly in the file content
            lines = content.split("\n")
            in_init = False

            for line in lines:
                stripped_line = line.strip()

                # Check if we're entering the __init__ method
                if "def __init__(" in stripped_line:
                    in_init = True
                    continue

                # If we're in __init__ and hit another method, stop
                if (
                    in_init
                    and stripped_line.startswith("def ")
                    and "__init__" not in stripped_line
                ):
                    break

                # If we're in __init__, look for parameter definitions
                if in_init and "=" in stripped_line:
                    # Pattern for parameters like "slow_ma: int = 140,"
                    param_match = re.search(
                        r"(\w+):\s*(?:int|float)\s*=\s*([\d.]+)", stripped_line
                    )
                    if param_match:
                        param_name = param_match.group(1)
                        value_str = param_match.group(2)

                        # Convert to appropriate type
                        if "." in value_str:
                            params[param_name] = float(value_str)
                        else:
                            params[param_name] = int(value_str)

            return params

        except Exception as e:
            self.logger.error(f"Failed to parse strategy parameters: {str(e)}")
            return {}

    def document_parameter_changes(self, current_params: Dict) -> Dict:
        """
        Document what parameters have changed since last validation.

        Args:
            current_params: Current strategy parameters

        Returns:
            Dictionary documenting parameter changes
        """
        changes = {}

        try:
            # Load last known good parameters (if they exist)
            last_params = self.load_last_validated_parameters()

            for strategy, params in current_params.items():
                if "_metadata" in params:
                    # Remove metadata for comparison
                    clean_params = {k: v for k, v in params.items() if k != "_metadata"}
                else:
                    clean_params = params.copy()

                if strategy in last_params:
                    last_clean_params = {
                        k: v
                        for k, v in last_params[strategy].items()
                        if k != "_metadata"
                    }
                    changes[strategy] = self.compare_parameters(
                        last_clean_params, clean_params
                    )
                else:
                    changes[strategy] = {
                        "status": "NEW_STRATEGY",
                        "params": clean_params,
                        "risk_level": self.assess_parameter_risk_level(clean_params),
                    }

            # Save current parameters as the new baseline
            self.save_parameter_baseline(current_params)

            return changes

        except Exception as e:
            self.logger.error(f"Failed to document parameter changes: {str(e)}")
            return {}

    def compare_parameters(self, old_params: Dict, new_params: Dict) -> Dict:
        """
        Compare two parameter sets and identify changes.

        Args:
            old_params: Previous parameters
            new_params: Current parameters

        Returns:
            Dictionary describing changes
        """
        comparison = {
            "status": "UNCHANGED",
            "changes": {},
            "risk_level_change": "NONE",
            "old_risk_level": "UNKNOWN",
            "new_risk_level": "UNKNOWN",
        }

        try:
            # Calculate risk levels
            old_risk = self.assess_parameter_risk_level(old_params)
            new_risk = self.assess_parameter_risk_level(new_params)

            comparison["old_risk_level"] = old_risk
            comparison["new_risk_level"] = new_risk

            # Check for parameter changes
            all_params = set(old_params.keys()) | set(new_params.keys())

            for param in all_params:
                old_value = old_params.get(param)
                new_value = new_params.get(param)

                if old_value != new_value:
                    comparison["changes"][param] = {
                        "old": old_value,
                        "new": new_value,
                        "change_type": self._classify_parameter_change(
                            param, old_value, new_value
                        ),
                    }

            if comparison["changes"]:
                comparison["status"] = "CHANGED"

                # Determine risk level change
                if new_risk != old_risk:
                    if self._risk_level_value(new_risk) > self._risk_level_value(
                        old_risk
                    ):
                        comparison["risk_level_change"] = "INCREASED"
                    else:
                        comparison["risk_level_change"] = "DECREASED"

            return comparison

        except Exception as e:
            self.logger.error(f"Failed to compare parameters: {str(e)}")
            return comparison

    def _classify_parameter_change(
        self, param: str, old_value: Optional[float], new_value: Optional[float]
    ) -> str:
        """Classify the type of parameter change."""
        if old_value is None:
            return "ADDED"
        elif new_value is None:
            return "REMOVED"
        elif isinstance(old_value, (int, float)) and isinstance(
            new_value, (int, float)
        ):
            if new_value > old_value:
                return "INCREASED"
            else:
                return "DECREASED"
        else:
            return "MODIFIED"

    def _risk_level_value(self, risk_level: str) -> int:
        """Convert risk level to numeric value for comparison."""
        risk_values = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4, "UNKNOWN": 0}
        return risk_values.get(risk_level, 0)

    def load_last_validated_parameters(self) -> Dict:
        """
        Load last validated parameters from file.

        Returns:
            Dictionary of last validated parameters
        """
        try:
            baseline_file = self.reports_dir / "parameter_baseline.json"

            if baseline_file.exists():
                with open(baseline_file, "r") as f:
                    baseline = json.load(f)

                self.logger.info(
                    f"Loaded parameter baseline with {len(baseline)} strategies"
                )
                return baseline
            else:
                self.logger.info("No parameter baseline found")
                return {}

        except Exception as e:
            self.logger.error(f"Failed to load last validated parameters: {str(e)}")
            return {}

    def save_parameter_baseline(self, parameters: Dict) -> None:
        """
        Save current parameters as baseline for future comparison.

        Args:
            parameters: Current parameters to save as baseline
        """
        try:
            baseline_file = self.reports_dir / "parameter_baseline.json"

            with open(baseline_file, "w") as f:
                json.dump(parameters, f, indent=2, default=str)

            self.logger.info(
                f"Saved parameter baseline for {len(parameters)} strategies"
            )

        except Exception as e:
            self.logger.error(f"Failed to save parameter baseline: {str(e)}")

    def create_parameter_comparison_matrix(self, parameters: Dict) -> pd.DataFrame:
        """
        Create comparison matrix of parameters across all strategies.

        Args:
            parameters: Dictionary of strategy parameters

        Returns:
            DataFrame with parameter comparison matrix
        """
        try:
            # Prepare data for DataFrame
            rows = []

            for strategy, params in parameters.items():
                row = {"Strategy": strategy}

                # Add parameter values
                for param_name in self.risk_thresholds.keys():
                    row[param_name] = params.get(param_name, None)

                # Add risk assessment
                row["Risk_Level"] = self.assess_parameter_risk_level(params)

                # Add metadata if available
                if "_metadata" in params:
                    row["Last_Modified"] = params["_metadata"].get("last_modified", "")

                rows.append(row)

            df = pd.DataFrame(rows)

            # Save to CSV
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_file = self.reports_dir / f"parameter_matrix_{timestamp}.csv"
            df.to_csv(csv_file, index=False)

            self.logger.info(f"Parameter comparison matrix saved to {csv_file}")

            return df

        except Exception as e:
            self.logger.error(f"Failed to create parameter comparison matrix: {str(e)}")
            return pd.DataFrame()

    def generate_risk_assessment_report(self, parameters: Dict) -> Dict:
        """
        Generate comprehensive risk assessment based on current parameter settings.

        Args:
            parameters: Dictionary of strategy parameters

        Returns:
            Risk assessment report
        """
        risk_assessment = {
            "overall_risk_level": "UNKNOWN",
            "parameter_risks": {},
            "recommendations": [],
            "risk_statistics": {},
            "critical_strategies": [],
            "assessment_timestamp": datetime.now().isoformat(),
        }

        try:
            risk_levels = []

            # Analyze each strategy
            for strategy, params in parameters.items():
                strategy_risk = self.assess_strategy_risk(params)
                risk_assessment["parameter_risks"][strategy] = strategy_risk

                risk_level = strategy_risk.get("risk_level", "UNKNOWN")
                risk_levels.append(risk_level)

                if risk_level in ["HIGH", "CRITICAL"]:
                    risk_assessment["critical_strategies"].append(
                        {
                            "strategy": strategy,
                            "risk_level": risk_level,
                            "issues": strategy_risk.get("issues", []),
                        }
                    )

            # Calculate overall risk statistics
            total_strategies = len(parameters)
            if total_strategies > 0:
                risk_counts = {
                    level: risk_levels.count(level)
                    for level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
                }

                risk_assessment["risk_statistics"] = {
                    "total_strategies": total_strategies,
                    "risk_distribution": risk_counts,
                    "high_risk_percentage": (
                        risk_counts.get("HIGH", 0) + risk_counts.get("CRITICAL", 0)
                    )
                    / total_strategies
                    * 100,
                }

                # Determine overall risk level
                high_risk_ratio = (
                    risk_counts.get("HIGH", 0) + risk_counts.get("CRITICAL", 0)
                ) / total_strategies

                if high_risk_ratio > 0.5:
                    risk_assessment["overall_risk_level"] = "HIGH"
                elif high_risk_ratio > 0.25:
                    risk_assessment["overall_risk_level"] = "MEDIUM"
                else:
                    risk_assessment["overall_risk_level"] = "LOW"

            # Generate recommendations
            risk_assessment["recommendations"] = self._generate_risk_recommendations(
                risk_assessment
            )

            # Save risk assessment report
            self._save_risk_assessment_report(risk_assessment)

            return risk_assessment

        except Exception as e:
            self.logger.error(f"Failed to generate risk assessment report: {str(e)}")
            risk_assessment["error"] = str(e)
            return risk_assessment

    def assess_parameter_risk_level(self, params: Dict) -> str:
        """
        Assess the overall risk level of a parameter set.

        Args:
            params: Strategy parameters

        Returns:
            Risk level string: LOW, MEDIUM, HIGH, CRITICAL
        """
        if not params:
            return "UNKNOWN"

        risk_scores = []

        for param_name, value in params.items():
            if param_name in self.risk_thresholds and isinstance(value, (int, float)):
                thresholds = self.risk_thresholds[param_name]
                score = self._calculate_parameter_risk_score(
                    param_name, value, thresholds
                )
                risk_scores.append(score)

        if not risk_scores:
            return "UNKNOWN"

        avg_score = sum(risk_scores) / len(risk_scores)

        if avg_score >= 0.8:
            return "CRITICAL"
        elif avg_score >= 0.6:
            return "HIGH"
        elif avg_score >= 0.4:
            return "MEDIUM"
        else:
            return "LOW"

    def assess_strategy_risk(self, params: Dict) -> Dict:
        """
        Assess detailed risk for a single strategy.

        Args:
            params: Strategy parameters

        Returns:
            Detailed risk assessment
        """
        strategy_risk = {
            "risk_level": "UNKNOWN",
            "parameter_scores": {},
            "issues": [],
            "recommendations": [],
        }

        try:
            risk_scores = []

            for param_name, value in params.items():
                if param_name in self.risk_thresholds and isinstance(
                    value, (int, float)
                ):
                    thresholds = self.risk_thresholds[param_name]
                    score = self._calculate_parameter_risk_score(
                        param_name, value, thresholds
                    )
                    risk_scores.append(score)

                    strategy_risk["parameter_scores"][param_name] = {
                        "value": value,
                        "risk_score": score,
                        "status": self._get_parameter_status(
                            param_name, value, thresholds
                        ),
                    }

                    # Identify specific issues
                    if score > 0.7:
                        if value < thresholds["min"] or value > thresholds["max"]:
                            strategy_risk["issues"].append(
                                f"{param_name} value {value} is outside safe range"
                            )
                        elif (
                            value < thresholds["optimal_min"]
                            or value > thresholds["optimal_max"]
                        ):
                            strategy_risk["issues"].append(
                                f"{param_name} value {value} is outside optimal range"
                            )

            # Calculate overall risk level
            if risk_scores:
                avg_score = sum(risk_scores) / len(risk_scores)

                if avg_score >= 0.8:
                    strategy_risk["risk_level"] = "CRITICAL"
                elif avg_score >= 0.6:
                    strategy_risk["risk_level"] = "HIGH"
                elif avg_score >= 0.4:
                    strategy_risk["risk_level"] = "MEDIUM"
                else:
                    strategy_risk["risk_level"] = "LOW"

            # Generate specific recommendations
            strategy_risk["recommendations"] = self._generate_strategy_recommendations(
                strategy_risk
            )

        except Exception as e:
            self.logger.error(f"Failed to assess strategy risk: {str(e)}")
            strategy_risk["error"] = str(e)

        return strategy_risk

    def _calculate_parameter_risk_score(
        self, param_name: str, value: float, thresholds: Dict
    ) -> float:
        """Calculate risk score for a parameter value (0.0 = low risk, 1.0 = high risk)."""
        # Check if value is outside acceptable range
        if value < thresholds["min"] or value > thresholds["max"]:
            return 1.0  # Critical risk

        # Check if value is outside optimal range
        if value < thresholds["optimal_min"] or value > thresholds["optimal_max"]:
            return 0.7  # High risk

        # Value is in optimal range
        return 0.2  # Low risk

    def _get_parameter_status(
        self, param_name: str, value: float, thresholds: Dict
    ) -> str:
        """Get status description for a parameter value."""
        if value < thresholds["min"]:
            return "TOO_LOW"
        elif value > thresholds["max"]:
            return "TOO_HIGH"
        elif value < thresholds["optimal_min"]:
            return "BELOW_OPTIMAL"
        elif value > thresholds["optimal_max"]:
            return "ABOVE_OPTIMAL"
        else:
            return "OPTIMAL"

    def _generate_risk_recommendations(self, risk_assessment: Dict) -> List[str]:
        """Generate recommendations based on overall risk assessment."""
        recommendations = []

        overall_risk = risk_assessment.get("overall_risk_level", "UNKNOWN")
        critical_strategies = risk_assessment.get("critical_strategies", [])

        if overall_risk == "HIGH":
            recommendations.append(
                "URGENT: Overall parameter risk is HIGH - conduct immediate review"
            )
        elif overall_risk == "MEDIUM":
            recommendations.append(
                "Review parameter settings for strategies with elevated risk"
            )

        if len(critical_strategies) > 0:
            recommendations.append(
                f"CRITICAL: {len(critical_strategies)} strategies have critical risk levels"
            )

            for strategy_info in critical_strategies[:3]:  # Show first 3
                strategy = strategy_info["strategy"]
                recommendations.append(
                    f"  - {strategy}: Immediate parameter adjustment required"
                )

        high_risk_pct = risk_assessment.get("risk_statistics", {}).get(
            "high_risk_percentage", 0
        )
        if high_risk_pct > 30:
            recommendations.append(
                f"WARNING: {high_risk_pct:.1f}% of strategies have high risk parameters"
            )

        return recommendations

    def _generate_strategy_recommendations(self, strategy_risk: Dict) -> List[str]:
        """Generate recommendations for a specific strategy."""
        recommendations = []

        for param_name, score_info in strategy_risk.get("parameter_scores", {}).items():
            status = score_info.get("status", "UNKNOWN")
            value = score_info.get("value")

            if status == "TOO_LOW":
                recommendations.append(
                    f"Increase {param_name} from {value} to at least {self.risk_thresholds[param_name]['min']}"
                )
            elif status == "TOO_HIGH":
                recommendations.append(
                    f"Decrease {param_name} from {value} to at most {self.risk_thresholds[param_name]['max']}"
                )
            elif status in ["BELOW_OPTIMAL", "ABOVE_OPTIMAL"]:
                optimal_min = self.risk_thresholds[param_name]["optimal_min"]
                optimal_max = self.risk_thresholds[param_name]["optimal_max"]
                recommendations.append(
                    f"Consider adjusting {param_name} to optimal range {optimal_min}-{optimal_max}"
                )

        return recommendations

    def _save_risk_assessment_report(self, risk_assessment: Dict) -> None:
        """Save risk assessment report to file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"risk_assessment_{timestamp}.json"
            filepath = self.reports_dir / filename

            with open(filepath, "w") as f:
                json.dump(risk_assessment, f, indent=2, default=str)

            self.logger.info(f"Risk assessment report saved to {filepath}")

        except Exception as e:
            self.logger.error(f"Failed to save risk assessment report: {str(e)}")


def main():
    """Main function for parameter analysis."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Parameter Analysis and Risk Assessment"
    )
    parser.add_argument(
        "--extract", action="store_true", help="Extract current parameters"
    )
    parser.add_argument(
        "--changes", action="store_true", help="Document parameter changes"
    )
    parser.add_argument("--risk", action="store_true", help="Generate risk assessment")
    parser.add_argument(
        "--matrix", action="store_true", help="Create parameter comparison matrix"
    )
    parser.add_argument("--all", action="store_true", help="Run all analyses")

    args = parser.parse_args()

    analyzer = ParameterAnalyzer()

    if args.extract or args.all:
        print("Extracting current parameters...")
        parameters = analyzer.extract_current_parameters()
        print(f"Extracted parameters for {len(parameters)} strategies")

        if args.all:
            # Store parameters for other analyses
            current_params = parameters

    if args.changes or args.all:
        print("\nDocumenting parameter changes...")
        if not args.all:
            parameters = analyzer.extract_current_parameters()
        changes = analyzer.document_parameter_changes(parameters)

        print("\n=== PARAMETER CHANGES ===")
        for strategy, change_info in changes.items():
            status = change_info.get("status", "UNKNOWN")
            print(f"{strategy}: {status}")

            if "changes" in change_info and change_info["changes"]:
                for param, change in change_info["changes"].items():
                    print(
                        f"  - {param}: {change['old']} → {change['new']} ({change['change_type']})"
                    )

    if args.risk or args.all:
        print("\nGenerating risk assessment...")
        if not args.all:
            parameters = analyzer.extract_current_parameters()
        risk_assessment = analyzer.generate_risk_assessment_report(parameters)

        print("\n=== RISK ASSESSMENT ===")
        print(f"Overall Risk Level: {risk_assessment['overall_risk_level']}")

        if risk_assessment.get("critical_strategies"):
            print(f"Critical Strategies: {len(risk_assessment['critical_strategies'])}")
            for strategy_info in risk_assessment["critical_strategies"]:
                print(f"  - {strategy_info['strategy']}: {strategy_info['risk_level']}")

        if risk_assessment.get("recommendations"):
            print("\nRECOMMENDATIONS:")
            for rec in risk_assessment["recommendations"][:5]:
                print(f"  - {rec}")

    if args.matrix or args.all:
        print("\nCreating parameter comparison matrix...")
        if not args.all:
            parameters = analyzer.extract_current_parameters()
        matrix = analyzer.create_parameter_comparison_matrix(parameters)

        if not matrix.empty:
            print(f"Parameter matrix created with {len(matrix)} strategies")
            print("\nSample of parameter matrix:")
            print(matrix.head())


if __name__ == "__main__":
    main()

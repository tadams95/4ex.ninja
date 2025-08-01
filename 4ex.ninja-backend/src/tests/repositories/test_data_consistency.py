"""
Data Consistency and Constraint Enforcement Tests for Day 7 Task 1.5.27

This module provides comprehensive validation tests for data consistency,
constraint enforcement, and business rule validation across all entities.
"""

import pytest
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from decimal import Decimal, InvalidOperation
from dataclasses import asdict

from ...core.entities.signal import Signal, SignalType, SignalStatus, CrossoverType
from ...core.entities.market_data import MarketData, Candle, Granularity

logger = logging.getLogger(__name__)


class DataConsistencyValidator:
    """
    Validates data consistency and enforces business constraints.

    Provides comprehensive validation for entity integrity, business rules,
    and cross-entity consistency checks.
    """

    def __init__(self):
        """Initialize data consistency validator."""
        self.validation_results = []

    def validate_signal_constraints(self, signal: Signal) -> Dict[str, Any]:
        """
        Validate signal entity constraints and business rules.

        Args:
            signal: Signal entity to validate

        Returns:
            Validation result with passed/failed status and details
        """
        result = {
            "entity_type": "Signal",
            "entity_id": signal.signal_id,
            "validation_passed": True,
            "constraint_violations": [],
            "business_rule_violations": [],
            "warnings": [],
        }

        try:
            # Constraint validations
            self._validate_signal_required_fields(signal, result)
            self._validate_signal_data_types(signal, result)
            self._validate_signal_value_ranges(signal, result)
            self._validate_signal_price_relationships(signal, result)

            # Business rule validations
            self._validate_signal_business_rules(signal, result)
            self._validate_signal_temporal_consistency(signal, result)

        except Exception as e:
            result["validation_passed"] = False
            result["constraint_violations"].append(f"Validation error: {str(e)}")

        return result

    def _validate_signal_required_fields(self, signal: Signal, result: Dict[str, Any]):
        """Validate required fields are present and valid."""
        required_fields = [
            "signal_id",
            "pair",
            "timeframe",
            "signal_type",
            "crossover_type",
            "entry_price",
            "current_price",
            "fast_ma",
            "slow_ma",
            "timestamp",
        ]

        for field in required_fields:
            value = getattr(signal, field, None)
            if value is None:
                result["validation_passed"] = False
                result["constraint_violations"].append(
                    f"Required field '{field}' is None"
                )
            elif isinstance(value, str) and value.strip() == "":
                result["validation_passed"] = False
                result["constraint_violations"].append(
                    f"Required field '{field}' is empty"
                )

    def _validate_signal_data_types(self, signal: Signal, result: Dict[str, Any]):
        """Validate data types are correct."""
        # String fields
        string_fields = ["signal_id", "pair", "timeframe"]
        for field in string_fields:
            value = getattr(signal, field, None)
            if value is not None and not isinstance(value, str):
                result["validation_passed"] = False
                result["constraint_violations"].append(
                    f"Field '{field}' must be string, got {type(value)}"
                )

        # Decimal fields
        decimal_fields = ["entry_price", "current_price"]
        for field in decimal_fields:
            value = getattr(signal, field, None)
            if value is not None and not isinstance(value, Decimal):
                result["validation_passed"] = False
                result["constraint_violations"].append(
                    f"Field '{field}' must be Decimal, got {type(value)}"
                )

        # Integer fields
        integer_fields = ["fast_ma", "slow_ma"]
        for field in integer_fields:
            value = getattr(signal, field, None)
            if value is not None and not isinstance(value, int):
                result["validation_passed"] = False
                result["constraint_violations"].append(
                    f"Field '{field}' must be integer, got {type(value)}"
                )

        # Enum fields
        if not isinstance(signal.signal_type, SignalType):
            result["validation_passed"] = False
            result["constraint_violations"].append(
                f"signal_type must be SignalType enum"
            )

        if not isinstance(signal.crossover_type, CrossoverType):
            result["validation_passed"] = False
            result["constraint_violations"].append(
                f"crossover_type must be CrossoverType enum"
            )

        if not isinstance(signal.status, SignalStatus):
            result["validation_passed"] = False
            result["constraint_violations"].append(f"status must be SignalStatus enum")

    def _validate_signal_value_ranges(self, signal: Signal, result: Dict[str, Any]):
        """Validate value ranges are within acceptable limits."""
        # Price values must be positive
        price_fields = [
            "entry_price",
            "current_price",
            "stop_loss",
            "take_profit",
            "atr_value",
        ]
        for field in price_fields:
            value = getattr(signal, field, None)
            if value is not None and value <= 0:
                result["validation_passed"] = False
                result["constraint_violations"].append(
                    f"Field '{field}' must be positive, got {value}"
                )

        # Moving average periods must be positive and reasonable
        if signal.fast_ma <= 0 or signal.fast_ma > 200:
            result["validation_passed"] = False
            result["constraint_violations"].append(
                f"fast_ma must be between 1-200, got {signal.fast_ma}"
            )

        if signal.slow_ma <= 0 or signal.slow_ma > 500:
            result["validation_passed"] = False
            result["constraint_violations"].append(
                f"slow_ma must be between 1-500, got {signal.slow_ma}"
            )

        # Fast MA should be less than slow MA
        if signal.fast_ma >= signal.slow_ma:
            result["validation_passed"] = False
            result["constraint_violations"].append(
                f"fast_ma ({signal.fast_ma}) must be less than slow_ma ({signal.slow_ma})"
            )

        # Confidence score validation
        if signal.confidence_score is not None:
            if not (0.0 <= signal.confidence_score <= 1.0):
                result["validation_passed"] = False
                result["constraint_violations"].append(
                    f"confidence_score must be between 0-1, got {signal.confidence_score}"
                )

    def _validate_signal_price_relationships(
        self, signal: Signal, result: Dict[str, Any]
    ):
        """Validate price relationships make sense."""
        if signal.stop_loss is not None and signal.take_profit is not None:
            if signal.signal_type == SignalType.BUY:
                # For BUY signals: stop_loss < entry_price < take_profit
                if signal.stop_loss >= signal.entry_price:
                    result["validation_passed"] = False
                    result["constraint_violations"].append(
                        "BUY signal: stop_loss must be less than entry_price"
                    )

                if signal.take_profit <= signal.entry_price:
                    result["validation_passed"] = False
                    result["constraint_violations"].append(
                        "BUY signal: take_profit must be greater than entry_price"
                    )

            elif signal.signal_type == SignalType.SELL:
                # For SELL signals: take_profit < entry_price < stop_loss
                if signal.stop_loss <= signal.entry_price:
                    result["validation_passed"] = False
                    result["constraint_violations"].append(
                        "SELL signal: stop_loss must be greater than entry_price"
                    )

                if signal.take_profit >= signal.entry_price:
                    result["validation_passed"] = False
                    result["constraint_violations"].append(
                        "SELL signal: take_profit must be less than entry_price"
                    )

    def _validate_signal_business_rules(self, signal: Signal, result: Dict[str, Any]):
        """Validate business rules for signals."""
        # Signal type and crossover type consistency
        if (
            signal.signal_type == SignalType.BUY
            and signal.crossover_type != CrossoverType.BULLISH
        ):
            result["business_rule_violations"].append(
                "BUY signals should have BULLISH crossover type"
            )

        if (
            signal.signal_type == SignalType.SELL
            and signal.crossover_type != CrossoverType.BEARISH
        ):
            result["business_rule_violations"].append(
                "SELL signals should have BEARISH crossover type"
            )

        # Risk-reward ratio validation
        if signal.risk_reward_ratio is not None and signal.risk_reward_ratio < 1.0:
            result["warnings"].append(
                f"Low risk-reward ratio: {signal.risk_reward_ratio:.2f}"
            )

        # ATR-based validation
        if signal.atr_value is not None:
            if signal.stop_loss is not None:
                price_diff = abs(signal.entry_price - signal.stop_loss)
                if price_diff < signal.atr_value * Decimal("0.5"):
                    result["warnings"].append("Stop loss too tight relative to ATR")
                elif price_diff > signal.atr_value * Decimal("3.0"):
                    result["warnings"].append("Stop loss too wide relative to ATR")

    def _validate_signal_temporal_consistency(
        self, signal: Signal, result: Dict[str, Any]
    ):
        """Validate temporal consistency."""
        now = datetime.utcnow()

        # Timestamp should not be too far in the future
        if signal.timestamp > now + timedelta(minutes=5):
            result["validation_passed"] = False
            result["constraint_violations"].append(
                "Signal timestamp is too far in the future"
            )

        # Created_at should be around timestamp
        if hasattr(signal, "created_at") and signal.created_at:
            time_diff = abs((signal.created_at - signal.timestamp).total_seconds())
            if time_diff > 300:  # 5 minutes
                result["warnings"].append(
                    "Large time difference between timestamp and created_at"
                )

        # Updated_at should not be before created_at
        if hasattr(signal, "updated_at") and hasattr(signal, "created_at"):
            if (
                signal.updated_at
                and signal.created_at
                and signal.updated_at < signal.created_at
            ):
                result["validation_passed"] = False
                result["constraint_violations"].append(
                    "updated_at cannot be before created_at"
                )

    def validate_market_data_constraints(
        self, market_data: MarketData
    ) -> Dict[str, Any]:
        """
        Validate market data constraints and consistency.

        Args:
            market_data: MarketData entity to validate

        Returns:
            Validation result with passed/failed status and details
        """
        result = {
            "entity_type": "MarketData",
            "entity_id": f"{market_data.instrument}_{market_data.granularity.value}",
            "validation_passed": True,
            "constraint_violations": [],
            "business_rule_violations": [],
            "warnings": [],
        }

        try:
            # Validate required fields
            if not market_data.instrument or not isinstance(
                market_data.instrument, str
            ):
                result["validation_passed"] = False
                result["constraint_violations"].append(
                    "instrument must be a non-empty string"
                )

            if not isinstance(market_data.granularity, Granularity):
                result["validation_passed"] = False
                result["constraint_violations"].append(
                    "granularity must be a Granularity enum"
                )

            # Validate candles
            if not market_data.candles or len(market_data.candles) == 0:
                result["validation_passed"] = False
                result["constraint_violations"].append(
                    "MarketData must contain at least one candle"
                )

            # Validate individual candles
            for i, candle in enumerate(market_data.candles):
                candle_result = self.validate_candle_constraints(candle)
                if not candle_result["validation_passed"]:
                    result["validation_passed"] = False
                    result["constraint_violations"].extend(
                        [
                            f"Candle {i}: {violation}"
                            for violation in candle_result["constraint_violations"]
                        ]
                    )

            # Validate candle sequence
            self._validate_candle_sequence(market_data.candles, result)

        except Exception as e:
            result["validation_passed"] = False
            result["constraint_violations"].append(f"Validation error: {str(e)}")

        return result

    def validate_candle_constraints(self, candle: Candle) -> Dict[str, Any]:
        """
        Validate individual candle constraints.

        Args:
            candle: Candle entity to validate

        Returns:
            Validation result
        """
        result = {
            "entity_type": "Candle",
            "validation_passed": True,
            "constraint_violations": [],
        }

        try:
            # Validate required fields
            if not isinstance(candle.time, datetime):
                result["validation_passed"] = False
                result["constraint_violations"].append("time must be datetime")

            # Validate OHLC values
            ohlc_fields = ["open", "high", "low", "close"]
            for field in ohlc_fields:
                value = getattr(candle, field)
                if not isinstance(value, Decimal) or value <= 0:
                    result["validation_passed"] = False
                    result["constraint_violations"].append(
                        f"{field} must be positive Decimal"
                    )

            # Validate volume
            if not isinstance(candle.volume, int) or candle.volume < 0:
                result["validation_passed"] = False
                result["constraint_violations"].append(
                    "volume must be non-negative integer"
                )

            # Validate OHLC relationships (this will raise ValueError if invalid)
            try:
                candle.validate()
            except ValueError as e:
                result["validation_passed"] = False
                result["constraint_violations"].append(str(e))

        except Exception as e:
            result["validation_passed"] = False
            result["constraint_violations"].append(f"Validation error: {str(e)}")

        return result

    def _validate_candle_sequence(self, candles: List[Candle], result: Dict[str, Any]):
        """Validate candle sequence consistency."""
        if len(candles) <= 1:
            return

        # Check timestamp ordering
        for i in range(1, len(candles)):
            if candles[i].time <= candles[i - 1].time:
                result["validation_passed"] = False
                result["constraint_violations"].append(
                    f"Candles must be in chronological order at index {i}"
                )

        # Check for reasonable price continuity
        for i in range(1, len(candles)):
            prev_candle = candles[i - 1]
            curr_candle = candles[i]

            # Check for extreme price gaps (more than 10% change)
            max_price = max(prev_candle.high, curr_candle.high)
            min_price = min(prev_candle.low, curr_candle.low)

            if max_price > min_price * Decimal("1.1"):  # More than 10% gap
                result["warnings"].append(
                    f"Large price gap between candles at index {i-1} and {i}"
                )

    def validate_cross_entity_consistency(
        self, entities: Dict[str, List]
    ) -> Dict[str, Any]:
        """
        Validate consistency across multiple entities.

        Args:
            entities: Dictionary with entity type as key and list of entities as value

        Returns:
            Cross-entity validation result
        """
        result = {
            "validation_type": "Cross-Entity Consistency",
            "validation_passed": True,
            "consistency_violations": [],
            "warnings": [],
        }

        try:
            signals = entities.get("signals", [])
            market_data = entities.get("market_data", [])

            # Validate signal-market data consistency
            if signals and market_data:
                self._validate_signal_market_data_consistency(
                    signals, market_data, result
                )

            # Validate signal collection consistency
            if signals:
                self._validate_signal_collection_consistency(signals, result)

        except Exception as e:
            result["validation_passed"] = False
            result["consistency_violations"].append(
                f"Cross-entity validation error: {str(e)}"
            )

        return result

    def _validate_signal_market_data_consistency(
        self,
        signals: List[Signal],
        market_data: List[MarketData],
        result: Dict[str, Any],
    ):
        """Validate consistency between signals and market data."""
        # Check if signals reference valid instruments
        signal_pairs = {signal.pair for signal in signals}
        market_data_instruments = {md.instrument for md in market_data}

        for pair in signal_pairs:
            if pair not in market_data_instruments:
                result["warnings"].append(
                    f"Signal references pair '{pair}' without corresponding market data"
                )

        # Check timestamp consistency
        for signal in signals:
            matching_market_data = [
                md for md in market_data if md.instrument == signal.pair
            ]

            if matching_market_data:
                md = matching_market_data[0]
                if md.candles:
                    latest_candle_time = max(candle.time for candle in md.candles)

                    # Signal should not be much newer than latest market data
                    if signal.timestamp > latest_candle_time + timedelta(hours=24):
                        result["warnings"].append(
                            f"Signal {signal.signal_id} timestamp much newer than market data"
                        )

    def _validate_signal_collection_consistency(
        self, signals: List[Signal], result: Dict[str, Any]
    ):
        """Validate consistency within signal collection."""
        # Check for duplicate signal IDs
        signal_ids = [signal.signal_id for signal in signals]
        duplicate_ids = [sid for sid in set(signal_ids) if signal_ids.count(sid) > 1]

        if duplicate_ids:
            result["validation_passed"] = False
            result["consistency_violations"].extend(
                [f"Duplicate signal ID found: {sid}" for sid in duplicate_ids]
            )


class ConstraintEnforcementTests:
    """Test suite for constraint enforcement and data validation."""

    def __init__(self):
        """Initialize constraint enforcement tests."""
        self.validator = DataConsistencyValidator()

    def test_valid_signal_creation(self) -> Dict[str, Any]:
        """Test creation of valid signals."""
        result = {"test_name": "valid_signal_creation", "passed": True, "details": []}

        try:
            # Create valid signal
            valid_signal = Signal(
                signal_id="valid_test_signal",
                pair="EUR/USD",
                timeframe="H1",
                signal_type=SignalType.BUY,
                crossover_type=CrossoverType.BULLISH,
                entry_price=Decimal("1.1000"),
                current_price=Decimal("1.1005"),
                fast_ma=10,
                slow_ma=20,
                timestamp=datetime.utcnow(),
                stop_loss=Decimal("1.0950"),
                take_profit=Decimal("1.1100"),
                atr_value=Decimal("0.0025"),
            )

            # Validate signal
            validation_result = self.validator.validate_signal_constraints(valid_signal)

            if not validation_result["validation_passed"]:
                result["passed"] = False
                result["details"].append(
                    f"Valid signal failed validation: {validation_result}"
                )
            else:
                result["details"].append("Valid signal passed all validations")

        except Exception as e:
            result["passed"] = False
            result["details"].append(f"Error testing valid signal: {str(e)}")

        return result

    def test_invalid_signal_constraints(self) -> Dict[str, Any]:
        """Test detection of invalid signal constraints."""
        result = {
            "test_name": "invalid_signal_constraints",
            "passed": True,
            "details": [],
        }

        test_cases = [
            # Missing required field
            {
                "description": "Missing signal_id",
                "signal_data": {
                    "signal_id": None,
                    "pair": "EUR/USD",
                    "timeframe": "H1",
                    "signal_type": SignalType.BUY,
                    "crossover_type": CrossoverType.BULLISH,
                    "entry_price": Decimal("1.1000"),
                    "current_price": Decimal("1.1000"),
                    "fast_ma": 10,
                    "slow_ma": 20,
                    "timestamp": datetime.utcnow(),
                },
            },
            # Invalid price relationship
            {
                "description": "Invalid stop loss for BUY signal",
                "signal_data": {
                    "signal_id": "invalid_sl_test",
                    "pair": "EUR/USD",
                    "timeframe": "H1",
                    "signal_type": SignalType.BUY,
                    "crossover_type": CrossoverType.BULLISH,
                    "entry_price": Decimal("1.1000"),
                    "current_price": Decimal("1.1000"),
                    "fast_ma": 10,
                    "slow_ma": 20,
                    "timestamp": datetime.utcnow(),
                    "stop_loss": Decimal("1.1050"),  # Above entry for BUY
                    "take_profit": Decimal("1.1100"),
                },
            },
            # Invalid MA relationship
            {
                "description": "Fast MA greater than slow MA",
                "signal_data": {
                    "signal_id": "invalid_ma_test",
                    "pair": "EUR/USD",
                    "timeframe": "H1",
                    "signal_type": SignalType.BUY,
                    "crossover_type": CrossoverType.BULLISH,
                    "entry_price": Decimal("1.1000"),
                    "current_price": Decimal("1.1000"),
                    "fast_ma": 50,  # Greater than slow MA
                    "slow_ma": 20,
                    "timestamp": datetime.utcnow(),
                },
            },
        ]

        for test_case in test_cases:
            try:
                # Create signal with invalid data
                signal = Signal(**test_case["signal_data"])

                # Validate - should fail
                validation_result = self.validator.validate_signal_constraints(signal)

                if validation_result["validation_passed"]:
                    result["passed"] = False
                    result["details"].append(
                        f"FAILED: {test_case['description']} - should have failed validation"
                    )
                else:
                    result["details"].append(
                        f"PASSED: {test_case['description']} - correctly failed validation"
                    )

            except Exception as e:
                # Exception during creation is also acceptable for invalid data
                result["details"].append(
                    f"PASSED: {test_case['description']} - creation raised exception: {str(e)}"
                )

        return result

    def test_candle_constraint_validation(self) -> Dict[str, Any]:
        """Test candle constraint validation."""
        result = {
            "test_name": "candle_constraint_validation",
            "passed": True,
            "details": [],
        }

        try:
            # Valid candle
            valid_candle = Candle(
                time=datetime.utcnow(),
                open=Decimal("1.1000"),
                high=Decimal("1.1010"),
                low=Decimal("1.0990"),
                close=Decimal("1.1005"),
                volume=50000,
            )

            validation_result = self.validator.validate_candle_constraints(valid_candle)
            if not validation_result["validation_passed"]:
                result["passed"] = False
                result["details"].append(
                    f"Valid candle failed validation: {validation_result}"
                )
            else:
                result["details"].append("Valid candle passed validation")

            # Test invalid candle (high < close)
            try:
                invalid_candle = Candle(
                    time=datetime.utcnow(),
                    open=Decimal("1.1000"),
                    high=Decimal("1.0995"),  # High less than open
                    low=Decimal("1.0990"),
                    close=Decimal("1.1005"),
                    volume=50000,
                )

                validation_result = self.validator.validate_candle_constraints(
                    invalid_candle
                )
                if validation_result["validation_passed"]:
                    result["passed"] = False
                    result["details"].append(
                        "Invalid candle should have failed validation"
                    )
                else:
                    result["details"].append(
                        "Invalid candle correctly failed validation"
                    )

            except ValueError:
                # Exception during creation is expected for invalid OHLC
                result["details"].append(
                    "Invalid candle correctly raised ValueError during creation"
                )

        except Exception as e:
            result["passed"] = False
            result["details"].append(f"Error testing candle validation: {str(e)}")

        return result

    def test_cross_entity_consistency(self) -> Dict[str, Any]:
        """Test cross-entity consistency validation."""
        result = {
            "test_name": "cross_entity_consistency",
            "passed": True,
            "details": [],
        }

        try:
            # Create test entities
            signals = [
                Signal(
                    signal_id="cross_test_1",
                    pair="EUR/USD",
                    timeframe="H1",
                    signal_type=SignalType.BUY,
                    crossover_type=CrossoverType.BULLISH,
                    entry_price=Decimal("1.1000"),
                    current_price=Decimal("1.1000"),
                    fast_ma=10,
                    slow_ma=20,
                    timestamp=datetime.utcnow(),
                ),
                Signal(
                    signal_id="cross_test_2",
                    pair="GBP/USD",  # Different pair
                    timeframe="H1",
                    signal_type=SignalType.SELL,
                    crossover_type=CrossoverType.BEARISH,
                    entry_price=Decimal("1.2500"),
                    current_price=Decimal("1.2500"),
                    fast_ma=10,
                    slow_ma=20,
                    timestamp=datetime.utcnow(),
                ),
            ]

            # Market data only for EUR/USD
            candles = [
                Candle(
                    time=datetime.utcnow() - timedelta(hours=i),
                    open=Decimal("1.1000"),
                    high=Decimal("1.1010"),
                    low=Decimal("1.0990"),
                    close=Decimal("1.1005"),
                    volume=50000,
                )
                for i in range(5)
            ]

            market_data = [
                MarketData(
                    instrument="EUR/USD", granularity=Granularity.H1, candles=candles
                )
            ]

            # Validate cross-entity consistency
            entities = {"signals": signals, "market_data": market_data}
            validation_result = self.validator.validate_cross_entity_consistency(
                entities
            )

            # Should pass but have warnings about missing market data for GBP/USD
            if not validation_result["validation_passed"]:
                result["passed"] = False
                result["details"].append(
                    f"Cross-entity validation failed: {validation_result}"
                )
            else:
                if validation_result["warnings"]:
                    result["details"].append(
                        f"Cross-entity validation passed with warnings: {validation_result['warnings']}"
                    )
                else:
                    result["details"].append(
                        "Cross-entity validation passed without warnings"
                    )

        except Exception as e:
            result["passed"] = False
            result["details"].append(
                f"Error testing cross-entity consistency: {str(e)}"
            )

        return result


class DataConsistencyTestSuite:
    """Comprehensive data consistency and constraint enforcement test suite."""

    def __init__(self):
        """Initialize data consistency test suite."""
        self.constraint_tests = ConstraintEnforcementTests()

    async def run_all_consistency_tests(self) -> Dict[str, Any]:
        """
        Run all data consistency and constraint enforcement tests.

        Returns:
            Comprehensive test results
        """
        results = {
            "test_suite": "Data Consistency and Constraint Enforcement",
            "test_run_timestamp": datetime.utcnow().isoformat(),
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": [],
        }

        # Define all tests to run
        test_methods = [
            self.constraint_tests.test_valid_signal_creation,
            self.constraint_tests.test_invalid_signal_constraints,
            self.constraint_tests.test_candle_constraint_validation,
            self.constraint_tests.test_cross_entity_consistency,
        ]

        # Run all tests
        for test_method in test_methods:
            try:
                test_result = test_method()
                results["test_details"].append(test_result)
                results["total_tests"] += 1

                if test_result["passed"]:
                    results["passed_tests"] += 1
                else:
                    results["failed_tests"] += 1

            except Exception as e:
                results["test_details"].append(
                    {
                        "test_name": test_method.__name__,
                        "passed": False,
                        "details": [f"Test execution failed: {str(e)}"],
                    }
                )
                results["total_tests"] += 1
                results["failed_tests"] += 1

        return results


# Pytest integration
@pytest.mark.consistency
class TestDataConsistencyPytest:
    """Pytest-compatible data consistency tests."""

    def test_signal_constraint_validation(self):
        """Test signal constraint validation."""
        tests = ConstraintEnforcementTests()

        # Test valid signal
        result = tests.test_valid_signal_creation()
        assert result["passed"], f"Valid signal test failed: {result['details']}"

        # Test invalid signals
        result = tests.test_invalid_signal_constraints()
        assert result["passed"], f"Invalid signal test failed: {result['details']}"

    def test_candle_validation(self):
        """Test candle validation."""
        tests = ConstraintEnforcementTests()
        result = tests.test_candle_constraint_validation()
        assert result["passed"], f"Candle validation test failed: {result['details']}"

    def test_cross_entity_validation(self):
        """Test cross-entity validation."""
        tests = ConstraintEnforcementTests()
        result = tests.test_cross_entity_consistency()
        assert result[
            "passed"
        ], f"Cross-entity validation test failed: {result['details']}"


if __name__ == "__main__":
    # Can be run directly for quick testing
    async def main():
        suite = DataConsistencyTestSuite()
        results = await suite.run_all_consistency_tests()

        print("\n=== Data Consistency Test Results ===")
        print(f"Total Tests: {results['total_tests']}")
        print(f"Passed: {results['passed_tests']}")
        print(f"Failed: {results['failed_tests']}")

        for test in results["test_details"]:
            status = "✅" if test["passed"] else "❌"
            print(f"\n{status} {test['test_name']}")
            for detail in test.get("details", []):
                print(f"    {detail}")

    import asyncio

    asyncio.run(main())

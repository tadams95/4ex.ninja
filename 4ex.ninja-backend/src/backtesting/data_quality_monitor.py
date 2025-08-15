"""
Data quality monitoring for swing trading backtesting.

This module provides comprehensive data quality monitoring and validation
specifically designed for swing trading requirements.
"""

import asyncio
from typing import List, Dict, Optional, Tuple, Set
from datetime import datetime, timedelta
from decimal import Decimal
import logging
from dataclasses import dataclass, field
from enum import Enum
import statistics

from .data_providers.base_provider import (
    BaseDataProvider,
    SwingCandleData,
    DataQualityMetrics,
)

logger = logging.getLogger(__name__)


class QualityAlert(Enum):
    """Data quality alert levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class QualityIssue:
    """Data quality issue representation."""

    alert_level: QualityAlert
    issue_type: str
    description: str
    affected_pair: str
    affected_timeframe: str
    timestamp: datetime
    impact_score: float  # 0-1, where 1 is most severe


@dataclass
class DataValidationReport:
    """Comprehensive data validation report."""

    pair: str
    timeframe: str
    period_start: datetime
    period_end: datetime
    total_candles: int
    expected_candles: int
    missing_candles: int
    gap_percentage: float
    outlier_count: int
    price_anomalies: List[Dict]
    volume_anomalies: List[Dict]
    spread_consistency: float
    provider_comparison: Dict[str, DataQualityMetrics]
    issues: List[QualityIssue]
    overall_quality_score: float  # 0-1, where 1 is perfect quality
    generated_at: datetime = field(default_factory=datetime.utcnow)


class DataQualityMonitor:
    """
    Advanced data quality monitoring for swing trading.

    This monitor performs comprehensive validation of market data with focus
    on swing trading requirements and multi-provider consistency.
    """

    def __init__(self, providers: List[BaseDataProvider]):
        """
        Initialize data quality monitor.

        Args:
            providers: List of data providers to monitor
        """
        self.providers = providers
        self.quality_thresholds = {
            "max_gap_percentage": 10.0,  # Max 10% missing data
            "max_outlier_percentage": 5.0,  # Max 5% outliers
            "min_spread_consistency": 0.7,  # Min 70% spread consistency
            "max_price_gap_percentage": 3.0,  # Max 3% price gaps
            "min_volume_consistency": 0.6,  # Min 60% volume consistency (if available)
        }
        self.alert_history: List[QualityIssue] = []

    async def validate_data_comprehensive(
        self, pair: str, timeframe: str, start_time: datetime, end_time: datetime
    ) -> DataValidationReport:
        """
        Perform comprehensive data validation across all providers.

        Args:
            pair: Currency pair
            timeframe: Timeframe
            start_time: Start datetime
            end_time: End datetime

        Returns:
            Comprehensive validation report
        """
        logger.info(f"Starting comprehensive validation for {pair} {timeframe}")

        # Collect data from all providers
        provider_data = {}
        provider_quality = {}

        for provider in self.providers:
            if not provider.is_available:
                continue

            try:
                # Get candles
                candles = await provider.get_candles(
                    pair, timeframe, start_time, end_time
                )
                provider_data[provider.name] = candles

                # Get quality metrics
                quality = await provider.validate_data_quality(
                    pair, timeframe, start_time, end_time
                )
                provider_quality[provider.name] = quality

            except Exception as e:
                logger.error(f"Failed to get data from {provider.name}: {str(e)}")
                continue

        # Use primary provider data for main analysis
        primary_candles = []
        primary_provider = None

        for provider in sorted(self.providers, key=lambda p: p.priority):
            if provider.name in provider_data and provider_data[provider.name]:
                primary_candles = provider_data[provider.name]
                primary_provider = provider.name
                break

        if not primary_candles:
            logger.error("No data available for validation")
            return self._create_empty_report(pair, timeframe, start_time, end_time)

        # Calculate expected candles
        expected_candles = self._calculate_expected_candles(
            timeframe, start_time, end_time
        )

        # Perform detailed analysis
        issues = []

        # 1. Gap analysis
        gap_issues = await self._analyze_data_gaps(
            primary_candles, expected_candles, pair, timeframe
        )
        issues.extend(gap_issues)

        # 2. Price anomaly detection
        price_anomalies, price_issues = await self._detect_price_anomalies(
            primary_candles, pair, timeframe
        )
        issues.extend(price_issues)

        # 3. Volume analysis (if available)
        volume_anomalies, volume_issues = await self._analyze_volume_consistency(
            primary_candles, pair, timeframe
        )
        issues.extend(volume_issues)

        # 4. Cross-provider validation
        cross_provider_issues = await self._validate_cross_provider_consistency(
            provider_data, pair, timeframe
        )
        issues.extend(cross_provider_issues)

        # 5. Spread consistency
        spread_consistency = await self._calculate_spread_consistency(primary_candles)
        if spread_consistency < self.quality_thresholds["min_spread_consistency"]:
            issues.append(
                QualityIssue(
                    alert_level=QualityAlert.WARNING,
                    issue_type="spread_inconsistency",
                    description=f"Spread consistency below threshold: {spread_consistency:.2%}",
                    affected_pair=pair,
                    affected_timeframe=timeframe,
                    timestamp=datetime.utcnow(),
                    impact_score=0.3,
                )
            )

        # Calculate overall quality score
        quality_score = self._calculate_overall_quality_score(
            len(primary_candles),
            expected_candles,
            len(price_anomalies),
            spread_consistency,
            issues,
        )

        # Store alerts in history
        self.alert_history.extend(issues)

        # Create comprehensive report
        report = DataValidationReport(
            pair=pair,
            timeframe=timeframe,
            period_start=start_time,
            period_end=end_time,
            total_candles=len(primary_candles),
            expected_candles=expected_candles,
            missing_candles=max(0, expected_candles - len(primary_candles)),
            gap_percentage=(
                (
                    max(0, expected_candles - len(primary_candles))
                    / expected_candles
                    * 100
                )
                if expected_candles > 0
                else 0
            ),
            outlier_count=len(price_anomalies),
            price_anomalies=price_anomalies,
            volume_anomalies=volume_anomalies,
            spread_consistency=spread_consistency,
            provider_comparison=provider_quality,
            issues=issues,
            overall_quality_score=quality_score,
        )

        logger.info(f"Validation completed. Quality score: {quality_score:.2%}")
        return report

    async def _analyze_data_gaps(
        self,
        candles: List[SwingCandleData],
        expected_count: int,
        pair: str,
        timeframe: str,
    ) -> List[QualityIssue]:
        """Analyze data gaps and missing periods."""
        issues = []

        if not candles:
            issues.append(
                QualityIssue(
                    alert_level=QualityAlert.CRITICAL,
                    issue_type="no_data",
                    description="No candle data available",
                    affected_pair=pair,
                    affected_timeframe=timeframe,
                    timestamp=datetime.utcnow(),
                    impact_score=1.0,
                )
            )
            return issues

        # Check overall gap percentage
        missing_count = max(0, expected_count - len(candles))
        gap_percentage = (
            (missing_count / expected_count * 100) if expected_count > 0 else 0
        )

        if gap_percentage > self.quality_thresholds["max_gap_percentage"]:
            alert_level = (
                QualityAlert.CRITICAL if gap_percentage > 25 else QualityAlert.WARNING
            )
            issues.append(
                QualityIssue(
                    alert_level=alert_level,
                    issue_type="data_gaps",
                    description=f"High percentage of missing data: {gap_percentage:.1f}%",
                    affected_pair=pair,
                    affected_timeframe=timeframe,
                    timestamp=datetime.utcnow(),
                    impact_score=min(gap_percentage / 100, 1.0),
                )
            )

        # Check for consecutive gaps
        sorted_candles = sorted(candles, key=lambda c: c.timestamp)
        gap_threshold = self._get_timeframe_delta(timeframe) * 2  # 2x normal interval

        large_gaps = []
        for i in range(1, len(sorted_candles)):
            time_diff = sorted_candles[i].timestamp - sorted_candles[i - 1].timestamp
            if time_diff > gap_threshold:
                large_gaps.append(
                    {
                        "start": sorted_candles[i - 1].timestamp,
                        "end": sorted_candles[i].timestamp,
                        "duration_hours": time_diff.total_seconds() / 3600,
                    }
                )

        if large_gaps:
            issues.append(
                QualityIssue(
                    alert_level=QualityAlert.WARNING,
                    issue_type="large_gaps",
                    description=f"Found {len(large_gaps)} large time gaps in data",
                    affected_pair=pair,
                    affected_timeframe=timeframe,
                    timestamp=datetime.utcnow(),
                    impact_score=min(len(large_gaps) / 10, 0.7),
                )
            )

        return issues

    async def _detect_price_anomalies(
        self, candles: List[SwingCandleData], pair: str, timeframe: str
    ) -> Tuple[List[Dict], List[QualityIssue]]:
        """Detect price anomalies and outliers."""
        anomalies = []
        issues = []

        if len(candles) < 2:
            return anomalies, issues

        # Sort candles by timestamp
        sorted_candles = sorted(candles, key=lambda c: c.timestamp)

        # Calculate price changes
        price_changes = []
        for i in range(1, len(sorted_candles)):
            prev_close = sorted_candles[i - 1].close
            curr_open = sorted_candles[i].open

            if prev_close > 0:
                change_pct = abs(curr_open - prev_close) / prev_close * 100
                price_changes.append(change_pct)

                # Check for large gaps
                if change_pct > self.quality_thresholds["max_price_gap_percentage"]:
                    anomalies.append(
                        {
                            "type": "price_gap",
                            "timestamp": sorted_candles[i].timestamp,
                            "prev_close": float(prev_close),
                            "curr_open": float(curr_open),
                            "gap_percentage": change_pct,
                            "severity": "high" if change_pct > 5.0 else "medium",
                        }
                    )

        # Statistical outlier detection
        if price_changes:
            mean_change = statistics.mean(price_changes)
            std_change = (
                statistics.stdev(price_changes) if len(price_changes) > 1 else 0
            )

            outlier_threshold = mean_change + (3 * std_change)  # 3-sigma rule
            outlier_count = sum(
                1 for change in price_changes if change > outlier_threshold
            )

            outlier_percentage = (outlier_count / len(price_changes)) * 100

            if outlier_percentage > self.quality_thresholds["max_outlier_percentage"]:
                issues.append(
                    QualityIssue(
                        alert_level=QualityAlert.WARNING,
                        issue_type="price_outliers",
                        description=f"High percentage of price outliers: {outlier_percentage:.1f}%",
                        affected_pair=pair,
                        affected_timeframe=timeframe,
                        timestamp=datetime.utcnow(),
                        impact_score=min(outlier_percentage / 20, 0.8),
                    )
                )

        return anomalies, issues

    async def _analyze_volume_consistency(
        self, candles: List[SwingCandleData], pair: str, timeframe: str
    ) -> Tuple[List[Dict], List[QualityIssue]]:
        """Analyze volume data consistency (if available)."""
        anomalies = []
        issues = []

        # Check if volume data is available
        volumes = [c.volume for c in candles if c.volume is not None]

        if not volumes:
            # Volume not available - not an issue for FX data
            return anomalies, issues

        if len(volumes) < len(candles) * 0.5:  # Less than 50% have volume
            issues.append(
                QualityIssue(
                    alert_level=QualityAlert.INFO,
                    issue_type="incomplete_volume",
                    description="Volume data missing for significant portion of candles",
                    affected_pair=pair,
                    affected_timeframe=timeframe,
                    timestamp=datetime.utcnow(),
                    impact_score=0.1,
                )
            )

        return anomalies, issues

    async def _validate_cross_provider_consistency(
        self, provider_data: Dict[str, List[SwingCandleData]], pair: str, timeframe: str
    ) -> List[QualityIssue]:
        """Validate consistency across multiple providers."""
        issues = []

        if len(provider_data) < 2:
            return issues  # Need at least 2 providers for comparison

        providers = list(provider_data.keys())
        primary_data = provider_data[providers[0]]

        for secondary_provider in providers[1:]:
            secondary_data = provider_data[secondary_provider]

            # Compare data availability
            count_diff = abs(len(primary_data) - len(secondary_data))
            if count_diff > len(primary_data) * 0.1:  # More than 10% difference
                issues.append(
                    QualityIssue(
                        alert_level=QualityAlert.WARNING,
                        issue_type="provider_inconsistency",
                        description=f"Significant data count difference between {providers[0]} and {secondary_provider}",
                        affected_pair=pair,
                        affected_timeframe=timeframe,
                        timestamp=datetime.utcnow(),
                        impact_score=0.4,
                    )
                )

            # Compare price accuracy (if we have overlapping periods)
            price_differences = await self._compare_provider_prices(
                primary_data, secondary_data
            )

            if price_differences["avg_difference"] > 0.001:  # 10 pips difference
                issues.append(
                    QualityIssue(
                        alert_level=QualityAlert.WARNING,
                        issue_type="price_divergence",
                        description=f"Price divergence between providers: {price_differences['avg_difference']:.4f}",
                        affected_pair=pair,
                        affected_timeframe=timeframe,
                        timestamp=datetime.utcnow(),
                        impact_score=0.5,
                    )
                )

        return issues

    async def _compare_provider_prices(
        self, data1: List[SwingCandleData], data2: List[SwingCandleData]
    ) -> Dict:
        """Compare prices between two providers."""
        if not data1 or not data2:
            return {"avg_difference": 0, "max_difference": 0, "comparison_count": 0}

        # Create timestamp-based lookup for data2
        data2_lookup = {c.timestamp: c for c in data2}

        differences = []
        comparison_count = 0

        for candle1 in data1:
            if candle1.timestamp in data2_lookup:
                candle2 = data2_lookup[candle1.timestamp]

                # Compare close prices
                diff = abs(candle1.close - candle2.close)
                differences.append(float(diff))
                comparison_count += 1

        if not differences:
            return {"avg_difference": 0, "max_difference": 0, "comparison_count": 0}

        return {
            "avg_difference": statistics.mean(differences),
            "max_difference": max(differences),
            "comparison_count": comparison_count,
        }

    async def _calculate_spread_consistency(
        self, candles: List[SwingCandleData]
    ) -> float:
        """Calculate spread consistency score."""
        spreads = [float(c.spread) for c in candles if c.spread is not None]

        if not spreads or len(spreads) < 2:
            return 0.8  # Default assumption for swing trading

        # Calculate coefficient of variation (lower is better)
        mean_spread = statistics.mean(spreads)
        std_spread = statistics.stdev(spreads)

        if mean_spread == 0:
            return 0.0

        cv = std_spread / mean_spread

        # Convert to consistency score (1 - normalized CV)
        consistency = max(0.0, 1.0 - min(cv, 1.0))

        return consistency

    def _calculate_overall_quality_score(
        self,
        actual_candles: int,
        expected_candles: int,
        anomaly_count: int,
        spread_consistency: float,
        issues: List[QualityIssue],
    ) -> float:
        """Calculate overall data quality score (0-1)."""
        # Completeness score
        completeness = (
            min(actual_candles / expected_candles, 1.0) if expected_candles > 0 else 0.0
        )

        # Anomaly score
        anomaly_rate = anomaly_count / actual_candles if actual_candles > 0 else 1.0
        anomaly_score = max(0, 1 - anomaly_rate)

        # Issue penalty
        critical_issues = sum(
            1 for issue in issues if issue.alert_level == QualityAlert.CRITICAL
        )
        warning_issues = sum(
            1 for issue in issues if issue.alert_level == QualityAlert.WARNING
        )

        issue_penalty = (critical_issues * 0.2) + (warning_issues * 0.1)
        issue_score = max(0, 1 - issue_penalty)

        # Weighted average
        weights = {"completeness": 0.4, "anomaly": 0.3, "spread": 0.1, "issues": 0.2}

        overall_score = (
            weights["completeness"] * completeness
            + weights["anomaly"] * anomaly_score
            + weights["spread"] * spread_consistency
            + weights["issues"] * issue_score
        )

        return min(max(overall_score, 0.0), 1.0)

    def _calculate_expected_candles(
        self, timeframe: str, start_time: datetime, end_time: datetime
    ) -> int:
        """Calculate expected number of candles."""
        time_diff = end_time - start_time

        if timeframe == "4H":
            # 6 candles per day (4-hour intervals), minus weekends
            days = time_diff.days
            weekdays = days - (days // 7 * 2)
            return weekdays * 6
        elif timeframe == "D":
            # 1 candle per day, minus weekends
            days = time_diff.days
            return days - (days // 7 * 2)
        elif timeframe == "W":
            # 1 candle per week
            return time_diff.days // 7

        return 0

    def _get_timeframe_delta(self, timeframe: str) -> timedelta:
        """Get timedelta for a given timeframe."""
        if timeframe == "4H":
            return timedelta(hours=4)
        elif timeframe == "D":
            return timedelta(days=1)
        elif timeframe == "W":
            return timedelta(weeks=1)

        return timedelta(hours=1)  # Default

    def _create_empty_report(
        self, pair: str, timeframe: str, start_time: datetime, end_time: datetime
    ) -> DataValidationReport:
        """Create empty validation report for error cases."""
        return DataValidationReport(
            pair=pair,
            timeframe=timeframe,
            period_start=start_time,
            period_end=end_time,
            total_candles=0,
            expected_candles=0,
            missing_candles=0,
            gap_percentage=100.0,
            outlier_count=0,
            price_anomalies=[],
            volume_anomalies=[],
            spread_consistency=0.0,
            provider_comparison={},
            issues=[
                QualityIssue(
                    alert_level=QualityAlert.CRITICAL,
                    issue_type="no_data",
                    description="No data available from any provider",
                    affected_pair=pair,
                    affected_timeframe=timeframe,
                    timestamp=datetime.utcnow(),
                    impact_score=1.0,
                )
            ],
            overall_quality_score=0.0,
        )

    def get_recent_alerts(self, hours: int = 24) -> List[QualityIssue]:
        """Get recent quality alerts within specified hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [alert for alert in self.alert_history if alert.timestamp >= cutoff_time]

    def get_quality_summary(self) -> Dict:
        """Get summary of data quality status."""
        recent_alerts = self.get_recent_alerts()

        return {
            "total_alerts_24h": len(recent_alerts),
            "critical_alerts_24h": len(
                [a for a in recent_alerts if a.alert_level == QualityAlert.CRITICAL]
            ),
            "warning_alerts_24h": len(
                [a for a in recent_alerts if a.alert_level == QualityAlert.WARNING]
            ),
            "providers_monitored": len(self.providers),
            "active_providers": len([p for p in self.providers if p.is_available]),
            "quality_thresholds": self.quality_thresholds,
        }

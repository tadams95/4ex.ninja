"""
Repository query optimization based on usage patterns.

This module analyzes query patterns, identifies optimization opportunities,
and provides automated query optimization features for repository operations.
"""

import logging
import time
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from abc import ABC, abstractmethod
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class QueryPattern:
    """Represents a query pattern for analysis."""

    collection: str
    operation: str
    fields_used: Set[str]
    filter_patterns: Dict[str, str]
    frequency: int = 0
    avg_execution_time_ms: float = 0.0
    total_execution_time_ms: float = 0.0
    last_seen: datetime = field(default_factory=datetime.utcnow)
    result_count_avg: float = 0.0


@dataclass
class IndexRecommendation:
    """Represents an index recommendation."""

    collection: str
    fields: List[str]
    index_type: str  # 'single', 'compound', 'text', 'geo'
    reason: str
    potential_improvement: str
    priority: int  # 1 (high) to 5 (low)
    frequency: int = 0
    avg_execution_time_ms: float = 0.0


@dataclass
class OptimizationResult:
    """Result of a query optimization operation."""

    optimization_type: str
    collection: str
    description: str
    before_metrics: Dict[str, Any]
    after_metrics: Optional[Dict[str, Any]] = None
    success: bool = False
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


class QueryPatternAnalyzer:
    """
    Analyzes query patterns to identify optimization opportunities.

    This analyzer examines query execution patterns, frequency,
    and performance metrics to suggest database optimizations.
    """

    def __init__(self, analysis_window_hours: int = 24):
        """
        Initialize the query pattern analyzer.

        Args:
            analysis_window_hours: Time window for pattern analysis
        """
        self.analysis_window = timedelta(hours=analysis_window_hours)

        # Pattern storage
        self.query_patterns: Dict[str, QueryPattern] = {}
        self.query_executions: List[Dict[str, Any]] = []

        # Optimization tracking
        self.applied_optimizations: List[OptimizationResult] = []

        # Thresholds for recommendations
        self.thresholds = {
            "min_frequency_for_index": 10,
            "min_avg_time_for_optimization_ms": 100,
            "high_frequency_threshold": 100,
            "slow_query_threshold_ms": 1000,
        }

    def record_query_execution(
        self,
        collection: str,
        operation: str,
        query_filter: Dict[str, Any],
        execution_time_ms: float,
        result_count: int = 0,
    ) -> None:
        """
        Record a query execution for pattern analysis.

        Args:
            collection: Collection name
            operation: Operation type (find, insert, update, delete)
            query_filter: Query filter used
            execution_time_ms: Execution time in milliseconds
            result_count: Number of results returned
        """
        try:
            # Extract fields used in query
            fields_used = self._extract_fields_from_filter(query_filter)

            # Create pattern key
            pattern_key = self._generate_pattern_key(collection, operation, fields_used)

            # Record execution
            execution_record = {
                "timestamp": datetime.utcnow(),
                "collection": collection,
                "operation": operation,
                "query_filter": query_filter,
                "fields_used": fields_used,
                "execution_time_ms": execution_time_ms,
                "result_count": result_count,
                "pattern_key": pattern_key,
            }

            self.query_executions.append(execution_record)

            # Update pattern
            if pattern_key not in self.query_patterns:
                self.query_patterns[pattern_key] = QueryPattern(
                    collection=collection,
                    operation=operation,
                    fields_used=fields_used,
                    filter_patterns=self._extract_filter_patterns(query_filter),
                )

            pattern = self.query_patterns[pattern_key]
            pattern.frequency += 1
            pattern.total_execution_time_ms += execution_time_ms
            pattern.avg_execution_time_ms = (
                pattern.total_execution_time_ms / pattern.frequency
            )
            pattern.last_seen = datetime.utcnow()

            # Update average result count
            pattern.result_count_avg = (
                pattern.result_count_avg * (pattern.frequency - 1) + result_count
            ) / pattern.frequency

            # Clean old executions
            self._cleanup_old_executions()

        except Exception as e:
            logger.error(f"Error recording query execution: {e}")

    def _extract_fields_from_filter(self, query_filter: Dict[str, Any]) -> Set[str]:
        """Extract field names from query filter."""
        fields = set()

        def extract_recursive(obj: Any, prefix: str = ""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key.startswith("$"):
                        # MongoDB operator
                        if isinstance(value, dict):
                            extract_recursive(value, prefix)
                        elif isinstance(value, list):
                            for item in value:
                                extract_recursive(item, prefix)
                    else:
                        # Field name
                        field_name = f"{prefix}.{key}" if prefix else key
                        fields.add(field_name)
                        if isinstance(value, dict):
                            extract_recursive(value, field_name)
            elif isinstance(obj, list):
                for item in obj:
                    extract_recursive(item, prefix)

        extract_recursive(query_filter)
        return fields

    def _extract_filter_patterns(self, query_filter: Dict[str, Any]) -> Dict[str, str]:
        """Extract patterns from query filter for analysis."""
        patterns = {}

        def analyze_recursive(obj: Any, path: str = ""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key

                    if key.startswith("$"):
                        # MongoDB operator
                        patterns[current_path] = key
                        if isinstance(value, (dict, list)):
                            analyze_recursive(value, current_path)
                    else:
                        # Field with value
                        if isinstance(value, dict):
                            # Complex query on field
                            analyze_recursive(value, current_path)
                        else:
                            # Simple equality
                            patterns[current_path] = "equality"
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    analyze_recursive(item, f"{path}[{i}]")

        analyze_recursive(query_filter)
        return patterns

    def _generate_pattern_key(
        self, collection: str, operation: str, fields: Set[str]
    ) -> str:
        """Generate a unique key for a query pattern."""
        sorted_fields = sorted(fields)
        fields_str = "+".join(sorted_fields)
        return f"{collection}:{operation}:{fields_str}"

    def _cleanup_old_executions(self):
        """Remove old query executions outside the analysis window."""
        cutoff_time = datetime.utcnow() - self.analysis_window
        self.query_executions = [
            exec for exec in self.query_executions if exec["timestamp"] >= cutoff_time
        ]

    def analyze_patterns(self) -> Dict[str, Any]:
        """
        Analyze query patterns and return insights.

        Returns:
            Analysis results with pattern insights
        """
        try:
            # Clean old data first
            self._cleanup_old_executions()

            # Analyze patterns
            high_frequency_patterns = []
            slow_patterns = []
            optimization_opportunities = []

            for pattern_key, pattern in self.query_patterns.items():
                # High frequency patterns
                if pattern.frequency >= self.thresholds["high_frequency_threshold"]:
                    high_frequency_patterns.append(
                        {
                            "pattern_key": pattern_key,
                            "collection": pattern.collection,
                            "operation": pattern.operation,
                            "fields": list(pattern.fields_used),
                            "frequency": pattern.frequency,
                            "avg_time_ms": round(pattern.avg_execution_time_ms, 2),
                        }
                    )

                # Slow patterns
                if (
                    pattern.avg_execution_time_ms
                    >= self.thresholds["slow_query_threshold_ms"]
                ):
                    slow_patterns.append(
                        {
                            "pattern_key": pattern_key,
                            "collection": pattern.collection,
                            "operation": pattern.operation,
                            "fields": list(pattern.fields_used),
                            "avg_time_ms": round(pattern.avg_execution_time_ms, 2),
                            "frequency": pattern.frequency,
                        }
                    )

                # Optimization opportunities
                if (
                    pattern.frequency >= self.thresholds["min_frequency_for_index"]
                    and pattern.avg_execution_time_ms
                    >= self.thresholds["min_avg_time_for_optimization_ms"]
                ):
                    optimization_opportunities.append(
                        {
                            "pattern_key": pattern_key,
                            "collection": pattern.collection,
                            "operation": pattern.operation,
                            "fields": list(pattern.fields_used),
                            "frequency": pattern.frequency,
                            "avg_time_ms": round(pattern.avg_execution_time_ms, 2),
                            "potential_optimization": self._suggest_optimization(
                                pattern
                            ),
                        }
                    )

            # Sort by importance
            high_frequency_patterns.sort(key=lambda x: x["frequency"], reverse=True)
            slow_patterns.sort(key=lambda x: x["avg_time_ms"], reverse=True)
            optimization_opportunities.sort(
                key=lambda x: x["frequency"] * x["avg_time_ms"], reverse=True
            )

            return {
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "analysis_window_hours": self.analysis_window.total_seconds() / 3600,
                "total_patterns": len(self.query_patterns),
                "total_executions": len(self.query_executions),
                "high_frequency_patterns": high_frequency_patterns[:10],
                "slow_patterns": slow_patterns[:10],
                "optimization_opportunities": optimization_opportunities[:10],
                "collection_summary": self._get_collection_summary(),
            }

        except Exception as e:
            logger.error(f"Error analyzing query patterns: {e}")
            return {"error": "Failed to analyze query patterns"}

    def _suggest_optimization(self, pattern: QueryPattern) -> str:
        """Suggest optimization for a query pattern."""
        fields = list(pattern.fields_used)

        if len(fields) == 1:
            return f"Single field index on '{fields[0]}'"
        elif len(fields) <= 5:
            return f"Compound index on {fields}"
        else:
            # Too many fields, suggest partial index
            main_fields = fields[:3]
            return f"Compound index on primary fields: {main_fields}"

    def _get_collection_summary(self) -> Dict[str, Any]:
        """Get summary statistics by collection."""
        collection_stats = defaultdict(
            lambda: {
                "total_queries": 0,
                "unique_patterns": 0,
                "avg_execution_time_ms": 0.0,
                "total_execution_time_ms": 0.0,
            }
        )

        for pattern in self.query_patterns.values():
            stats = collection_stats[pattern.collection]
            stats["total_queries"] += pattern.frequency
            stats["unique_patterns"] += 1
            stats["total_execution_time_ms"] += pattern.total_execution_time_ms

        # Calculate averages
        for collection, stats in collection_stats.items():
            if stats["total_queries"] > 0:
                stats["avg_execution_time_ms"] = round(
                    stats["total_execution_time_ms"] / stats["total_queries"], 2
                )

        return dict(collection_stats)

    def generate_index_recommendations(self) -> List[IndexRecommendation]:
        """Generate index recommendations based on query patterns."""
        recommendations = []

        try:
            for pattern in self.query_patterns.values():
                # Skip patterns with low frequency or fast execution
                if (
                    pattern.frequency < self.thresholds["min_frequency_for_index"]
                    or pattern.avg_execution_time_ms
                    < self.thresholds["min_avg_time_for_optimization_ms"]
                ):
                    continue

                fields = list(pattern.fields_used)

                # Determine index type and priority
                if len(fields) == 1:
                    # Single field index
                    priority = 1 if pattern.frequency > 50 else 2
                    recommendations.append(
                        IndexRecommendation(
                            collection=pattern.collection,
                            fields=fields,
                            index_type="single",
                            reason=f"Frequently queried field (frequency: {pattern.frequency})",
                            potential_improvement=f"Expected {self._estimate_improvement(pattern)}% improvement",
                            priority=priority,
                            frequency=pattern.frequency,
                            avg_execution_time_ms=pattern.avg_execution_time_ms,
                        )
                    )

                elif len(fields) <= 5:
                    # Compound index
                    priority = 1 if pattern.avg_execution_time_ms > 500 else 2
                    recommendations.append(
                        IndexRecommendation(
                            collection=pattern.collection,
                            fields=fields,
                            index_type="compound",
                            reason=f"Multi-field query pattern (avg time: {pattern.avg_execution_time_ms:.1f}ms)",
                            potential_improvement=f"Expected {self._estimate_improvement(pattern)}% improvement",
                            priority=priority,
                            frequency=pattern.frequency,
                            avg_execution_time_ms=pattern.avg_execution_time_ms,
                        )
                    )

                # Check for text search patterns
                if any(
                    "text" in str(pattern.filter_patterns.get(field, ""))
                    for field in fields
                ):
                    recommendations.append(
                        IndexRecommendation(
                            collection=pattern.collection,
                            fields=[
                                field
                                for field in fields
                                if "text" in str(pattern.filter_patterns.get(field, ""))
                            ],
                            index_type="text",
                            reason="Text search operations detected",
                            potential_improvement="Significant improvement for text queries",
                            priority=2,
                            frequency=pattern.frequency,
                            avg_execution_time_ms=pattern.avg_execution_time_ms,
                        )
                    )

            # Sort by priority and impact
            recommendations.sort(
                key=lambda x: (x.priority, -x.frequency * x.avg_execution_time_ms)
            )

            return recommendations[:20]  # Limit to top 20 recommendations

        except Exception as e:
            logger.error(f"Error generating index recommendations: {e}")
            return []

    def _estimate_improvement(self, pattern: QueryPattern) -> int:
        """Estimate potential performance improvement percentage."""
        # Simple heuristic based on query characteristics
        base_improvement = 30  # Base improvement from indexing

        # Higher improvement for slower queries
        if pattern.avg_execution_time_ms > 1000:
            base_improvement += 40
        elif pattern.avg_execution_time_ms > 500:
            base_improvement += 20

        # Higher improvement for frequent queries
        if pattern.frequency > 100:
            base_improvement += 20
        elif pattern.frequency > 50:
            base_improvement += 10

        return min(base_improvement, 90)  # Cap at 90%


class RepositoryOptimizer:
    """
    Automated repository optimization based on usage patterns.

    This optimizer analyzes repository usage, applies optimizations,
    and monitors the impact of changes.
    """

    def __init__(self, database_manager, query_analyzer: QueryPatternAnalyzer):
        """
        Initialize the repository optimizer.

        Args:
            database_manager: Database manager instance
            query_analyzer: Query pattern analyzer
        """
        self.database_manager = database_manager
        self.query_analyzer = query_analyzer

        # Optimization state
        self.optimization_in_progress = False
        self.last_optimization_run = None

        # Applied optimizations tracking
        self.applied_optimizations: List[OptimizationResult] = []

    async def run_optimization_analysis(self) -> Dict[str, Any]:
        """
        Run a comprehensive optimization analysis.

        Returns:
            Analysis results and recommendations
        """
        try:
            logger.info("Starting repository optimization analysis")

            # Analyze query patterns
            pattern_analysis = self.query_analyzer.analyze_patterns()

            # Generate index recommendations
            index_recommendations = self.query_analyzer.generate_index_recommendations()

            # Check existing indexes
            existing_indexes = await self._get_existing_indexes()

            # Filter out redundant recommendations
            filtered_recommendations = self._filter_redundant_recommendations(
                index_recommendations, existing_indexes
            )

            # Generate optimization plan
            optimization_plan = self._create_optimization_plan(filtered_recommendations)

            return {
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "pattern_analysis": pattern_analysis,
                "index_recommendations": [
                    {
                        "collection": rec.collection,
                        "fields": rec.fields,
                        "index_type": rec.index_type,
                        "reason": rec.reason,
                        "potential_improvement": rec.potential_improvement,
                        "priority": rec.priority,
                    }
                    for rec in filtered_recommendations
                ],
                "optimization_plan": optimization_plan,
                "existing_indexes": existing_indexes,
            }

        except Exception as e:
            logger.error(f"Error running optimization analysis: {e}")
            return {"error": "Failed to run optimization analysis"}

    async def _get_existing_indexes(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get existing indexes for all collections."""
        try:
            db = await self.database_manager.get_database()
            existing_indexes = {}

            # Get list of collections
            collections = await db.list_collection_names()

            for collection_name in collections:
                collection = db[collection_name]
                indexes = await collection.list_indexes().to_list(None)

                # Format index information
                formatted_indexes = []
                for index in indexes:
                    if index["name"] != "_id_":  # Skip default _id index
                        formatted_indexes.append(
                            {
                                "name": index["name"],
                                "keys": dict(index["key"]),
                                "unique": index.get("unique", False),
                                "sparse": index.get("sparse", False),
                            }
                        )

                existing_indexes[collection_name] = formatted_indexes

            return existing_indexes

        except Exception as e:
            logger.error(f"Error getting existing indexes: {e}")
            return {}

    def _filter_redundant_recommendations(
        self,
        recommendations: List[IndexRecommendation],
        existing_indexes: Dict[str, List[Dict[str, Any]]],
    ) -> List[IndexRecommendation]:
        """Filter out recommendations for indexes that already exist."""
        filtered = []

        for rec in recommendations:
            # Check if similar index already exists
            collection_indexes = existing_indexes.get(rec.collection, [])

            is_redundant = False
            for existing_index in collection_indexes:
                existing_fields = list(existing_index["keys"].keys())

                # Check for exact match or subset
                if set(rec.fields) == set(existing_fields) or set(rec.fields).issubset(
                    set(existing_fields)
                ):
                    is_redundant = True
                    break

            if not is_redundant:
                filtered.append(rec)

        return filtered

    def _create_optimization_plan(
        self, recommendations: List[IndexRecommendation]
    ) -> Dict[str, Any]:
        """Create an optimization execution plan."""
        if not recommendations:
            return {"message": "No optimizations needed"}

        # Group by priority
        high_priority = [r for r in recommendations if r.priority == 1]
        medium_priority = [r for r in recommendations if r.priority == 2]
        low_priority = [r for r in recommendations if r.priority >= 3]

        return {
            "total_recommendations": len(recommendations),
            "high_priority_count": len(high_priority),
            "medium_priority_count": len(medium_priority),
            "low_priority_count": len(low_priority),
            "execution_phases": {
                "phase_1_critical": [
                    {
                        "collection": r.collection,
                        "action": f"Create {r.index_type} index on {r.fields}",
                        "estimated_improvement": r.potential_improvement,
                    }
                    for r in high_priority[:5]  # Limit to top 5
                ],
                "phase_2_important": [
                    {
                        "collection": r.collection,
                        "action": f"Create {r.index_type} index on {r.fields}",
                        "estimated_improvement": r.potential_improvement,
                    }
                    for r in medium_priority[:10]  # Limit to top 10
                ],
                "phase_3_optional": [
                    {
                        "collection": r.collection,
                        "action": f"Create {r.index_type} index on {r.fields}",
                        "estimated_improvement": r.potential_improvement,
                    }
                    for r in low_priority[:5]  # Limit to top 5
                ],
            },
        }

    async def apply_optimization(
        self, recommendation: IndexRecommendation
    ) -> OptimizationResult:
        """
        Apply a specific optimization recommendation.

        Args:
            recommendation: Index recommendation to apply

        Returns:
            Optimization result
        """
        try:
            logger.info(
                f"Applying optimization: {recommendation.index_type} index on {recommendation.collection}"
            )

            # Measure before metrics
            before_metrics = await self._measure_query_performance(
                recommendation.collection, recommendation.fields
            )

            # Create the index
            success = await self._create_index(recommendation)

            if success:
                # Measure after metrics (wait a bit for the index to be utilized)
                await asyncio.sleep(1)
                after_metrics = await self._measure_query_performance(
                    recommendation.collection, recommendation.fields
                )

                result = OptimizationResult(
                    optimization_type="index_creation",
                    collection=recommendation.collection,
                    description=f"Created {recommendation.index_type} index on {recommendation.fields}",
                    before_metrics=before_metrics,
                    after_metrics=after_metrics,
                    success=True,
                )

                self.applied_optimizations.append(result)
                logger.info(
                    f"Successfully applied optimization on {recommendation.collection}"
                )

                return result

            else:
                return OptimizationResult(
                    optimization_type="index_creation",
                    collection=recommendation.collection,
                    description=f"Failed to create {recommendation.index_type} index on {recommendation.fields}",
                    before_metrics=before_metrics,
                    success=False,
                    error="Index creation failed",
                )

        except Exception as e:
            logger.error(f"Error applying optimization: {e}")
            return OptimizationResult(
                optimization_type="index_creation",
                collection=recommendation.collection,
                description=f"Error creating index: {str(e)}",
                before_metrics={},
                success=False,
                error=str(e),
            )

    async def _create_index(self, recommendation: IndexRecommendation) -> bool:
        """Create an index based on recommendation."""
        try:
            db = await self.database_manager.get_database()
            collection = db[recommendation.collection]

            # Build index specification
            if recommendation.index_type == "single":
                index_spec = {recommendation.fields[0]: 1}
            elif recommendation.index_type == "compound":
                index_spec = {field: 1 for field in recommendation.fields}
            elif recommendation.index_type == "text":
                index_spec = {field: "text" for field in recommendation.fields}
            else:
                logger.error(f"Unsupported index type: {recommendation.index_type}")
                return False

            # Create index
            await collection.create_index(list(index_spec.items()))

            logger.info(f"Created index {index_spec} on {recommendation.collection}")
            return True

        except Exception as e:
            logger.error(f"Error creating index: {e}")
            return False

    async def _measure_query_performance(
        self, collection: str, fields: List[str]
    ) -> Dict[str, Any]:
        """Measure query performance for specific fields."""
        try:
            # This is a simplified implementation
            # In practice, you would run representative queries and measure performance
            return {
                "collection": collection,
                "fields": fields,
                "timestamp": datetime.utcnow().isoformat(),
                "avg_query_time_ms": 0.0,  # Placeholder
                "queries_measured": 0,
            }

        except Exception as e:
            logger.error(f"Error measuring query performance: {e}")
            return {}

    def get_optimization_history(self) -> List[Dict[str, Any]]:
        """Get history of applied optimizations."""
        return [
            {
                "optimization_type": opt.optimization_type,
                "collection": opt.collection,
                "description": opt.description,
                "success": opt.success,
                "timestamp": opt.timestamp.isoformat(),
                "before_metrics": opt.before_metrics,
                "after_metrics": opt.after_metrics,
                "error": opt.error,
            }
            for opt in self.applied_optimizations
        ]


# Global instances
query_pattern_analyzer: Optional[QueryPatternAnalyzer] = None
repository_optimizer: Optional[RepositoryOptimizer] = None


def initialize_query_optimizer(
    database_manager,
) -> Tuple[QueryPatternAnalyzer, RepositoryOptimizer]:
    """Initialize the global query optimization components."""
    global query_pattern_analyzer, repository_optimizer

    query_pattern_analyzer = QueryPatternAnalyzer()
    repository_optimizer = RepositoryOptimizer(database_manager, query_pattern_analyzer)

    logger.info("Query optimization components initialized")
    return query_pattern_analyzer, repository_optimizer


def get_query_optimizer() -> (
    Tuple[Optional[QueryPatternAnalyzer], Optional[RepositoryOptimizer]]
):
    """Get the global query optimization components."""
    return query_pattern_analyzer, repository_optimizer

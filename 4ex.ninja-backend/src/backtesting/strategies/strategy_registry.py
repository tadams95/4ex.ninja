"""
Strategy Registry for dynamic strategy management.

This module provides a registry for managing strategies dynamically,
including runtime registration and strategy metadata management.
"""

from typing import Dict, List, Any, Type, Optional
from dataclasses import dataclass
from datetime import datetime

from .base_strategy import ConcreteBaseStrategy
from .strategy_factory import StrategyFactory


@dataclass
class StrategyMetadata:
    """Metadata for a registered strategy."""

    name: str
    strategy_class: Type[ConcreteBaseStrategy]
    description: str
    category: str
    version: str
    registered_at: datetime
    default_config: Dict[str, Any]
    author: Optional[str] = None
    tags: Optional[List[str]] = None


class StrategyRegistry:
    """
    Dynamic registry for strategy management.

    This registry extends the factory pattern to provide dynamic
    strategy registration, versioning, and metadata management.
    """

    def __init__(self):
        """Initialize the registry."""
        self._strategies: Dict[str, StrategyMetadata] = {}
        self._load_default_strategies()

    def _load_default_strategies(self):
        """Load default strategies from the factory."""
        for strategy_name in StrategyFactory.get_available_strategies():
            try:
                self._register_from_factory(strategy_name)
            except Exception as e:
                print(f"Failed to register strategy '{strategy_name}': {e}")

    def _register_from_factory(self, strategy_name: str):
        """Register a strategy from the factory."""
        strategy_info = StrategyFactory.get_strategy_info(strategy_name)
        strategy_class = StrategyFactory.STRATEGIES[strategy_name.lower()]

        metadata = StrategyMetadata(
            name=strategy_name,
            strategy_class=strategy_class,
            description=strategy_info["description"],
            category=strategy_info["category"],
            version="1.0.0",
            registered_at=datetime.now(),
            default_config=strategy_info["default_config"],
            author="4ex.ninja",
            tags=self._generate_tags(strategy_name, strategy_info["category"]),
        )

        self._strategies[strategy_name] = metadata

    def _generate_tags(self, strategy_name: str, category: str) -> List[str]:
        """Generate tags for a strategy based on name and category."""
        tags = [category]

        # Add tags based on strategy name
        name_lower = strategy_name.lower()
        if "ma" in name_lower or "moving" in name_lower:
            tags.extend(["moving_average", "trend_following"])
        if "rsi" in name_lower:
            tags.extend(["momentum", "oscillator"])
        if "bollinger" in name_lower:
            tags.extend(["volatility", "bands", "mean_reversion"])
        if "crossover" in name_lower:
            tags.append("crossover")

        return list(set(tags))  # Remove duplicates

    def register_strategy(
        self,
        name: str,
        strategy_class: Type[ConcreteBaseStrategy],
        description: str = "",
        author: str = "",
        version: str = "1.0.0",
        tags: Optional[List[str]] = None,
    ) -> None:
        """
        Register a new strategy.

        Args:
            name: Strategy name
            strategy_class: Strategy class
            description: Strategy description
            author: Strategy author
            version: Strategy version
            tags: Strategy tags
        """
        # Create temporary instance to get metadata
        temp_config = {}
        temp_instance = strategy_class(temp_config)

        metadata = StrategyMetadata(
            name=name,
            strategy_class=strategy_class,
            description=description or temp_instance._get_strategy_description(),
            category=temp_instance._get_strategy_category(),
            version=version,
            registered_at=datetime.now(),
            default_config=self._extract_default_config(strategy_class),
            author=author,
            tags=tags or [],
        )

        self._strategies[name] = metadata

        # Also register with factory for backwards compatibility
        StrategyFactory.register_strategy(name, strategy_class)

    def _extract_default_config(
        self, strategy_class: Type[ConcreteBaseStrategy]
    ) -> Dict[str, Any]:
        """Extract default configuration from strategy class."""
        # Try to get from factory first
        try:
            return StrategyFactory._get_default_config(strategy_class)
        except:
            # Fallback to basic config
            return {
                "atr_period": 14,
                "sl_atr_multiplier": 2.0,
                "tp_atr_multiplier": 3.0,
                "min_atr_value": 0.0001,
                "min_rr_ratio": 1.5,
                "risk_per_trade": 0.02,
            }

    def get_strategy(self, name: str, config: Dict[str, Any]) -> ConcreteBaseStrategy:
        """
        Get a strategy instance.

        Args:
            name: Strategy name
            config: Strategy configuration

        Returns:
            Strategy instance
        """
        if name not in self._strategies:
            raise ValueError(f"Strategy '{name}' not found in registry")

        metadata = self._strategies[name]

        # Merge with default config
        full_config = metadata.default_config.copy()
        full_config.update(config)

        return metadata.strategy_class(full_config)

    def list_strategies(
        self, category: Optional[str] = None, tags: Optional[List[str]] = None
    ) -> List[str]:
        """
        List available strategies.

        Args:
            category: Filter by category
            tags: Filter by tags

        Returns:
            List of strategy names
        """
        strategies = []

        for name, metadata in self._strategies.items():
            # Filter by category
            if category and metadata.category != category:
                continue

            # Filter by tags
            if tags and not any(tag in (metadata.tags or []) for tag in tags):
                continue

            strategies.append(name)

        return strategies

    def get_strategy_info(self, name: str) -> Dict[str, Any]:
        """
        Get detailed strategy information.

        Args:
            name: Strategy name

        Returns:
            Strategy information dictionary
        """
        if name not in self._strategies:
            raise ValueError(f"Strategy '{name}' not found in registry")

        metadata = self._strategies[name]

        return {
            "name": metadata.name,
            "description": metadata.description,
            "category": metadata.category,
            "version": metadata.version,
            "author": metadata.author,
            "tags": metadata.tags,
            "registered_at": metadata.registered_at.isoformat(),
            "default_config": metadata.default_config,
            "class_name": metadata.strategy_class.__name__,
        }

    def get_categories(self) -> List[str]:
        """Get all available categories."""
        categories = set()
        for metadata in self._strategies.values():
            categories.add(metadata.category)
        return list(categories)

    def get_all_tags(self) -> List[str]:
        """Get all available tags."""
        tags = set()
        for metadata in self._strategies.values():
            if metadata.tags:
                tags.update(metadata.tags)
        return list(tags)

    def search_strategies(self, query: str) -> List[str]:
        """
        Search strategies by name, description, or tags.

        Args:
            query: Search query

        Returns:
            List of matching strategy names
        """
        query_lower = query.lower()
        matches = []

        for name, metadata in self._strategies.items():
            # Search in name
            if query_lower in name.lower():
                matches.append(name)
                continue

            # Search in description
            if query_lower in metadata.description.lower():
                matches.append(name)
                continue

            # Search in tags
            if metadata.tags and any(
                query_lower in tag.lower() for tag in metadata.tags
            ):
                matches.append(name)
                continue

        return matches

    def validate_strategy_config(
        self, name: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate strategy configuration.

        Args:
            name: Strategy name
            config: Configuration to validate

        Returns:
            Validated configuration
        """
        if name not in self._strategies:
            raise ValueError(f"Strategy '{name}' not found in registry")

        metadata = self._strategies[name]

        # Merge with defaults
        validated_config = metadata.default_config.copy()
        validated_config.update(config)

        return validated_config

    def get_strategy_statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        total_strategies = len(self._strategies)
        categories = {}
        tags = {}

        for metadata in self._strategies.values():
            # Count by category
            if metadata.category in categories:
                categories[metadata.category] += 1
            else:
                categories[metadata.category] = 1

            # Count by tags
            if metadata.tags:
                for tag in metadata.tags:
                    if tag in tags:
                        tags[tag] += 1
                    else:
                        tags[tag] = 1

        return {
            "total_strategies": total_strategies,
            "categories": categories,
            "tags": tags,
            "most_common_category": (
                max(categories.items(), key=lambda x: x[1])[0] if categories else None
            ),
            "most_common_tag": (
                max(tags.items(), key=lambda x: x[1])[0] if tags else None
            ),
        }


# Global registry instance
strategy_registry = StrategyRegistry()

"""
Backtesting module for 4ex.ninja swing trading strategies.

This module provides a comprehensive backtesting framework optimized for
swing trading with focus on market regime analysis and longer timeframes.
"""

from .data_infrastructure import DataInfrastructure, SwingTradingCosts
from .data_quality_monitor import DataQualityMonitor, DataValidationReport, QualityIssue
from .data_providers.base_provider import (
    BaseDataProvider,
    SwingCandleData,
    DataQualityMetrics,
)
from .data_providers.oanda_provider import OandaProvider
from .data_providers.alpha_vantage_provider import AlphaVantageProvider

__version__ = "1.0.0"
__author__ = "4ex.ninja Team"

__all__ = [
    # Core infrastructure
    "DataInfrastructure",
    "SwingTradingCosts",
    # Data quality monitoring
    "DataQualityMonitor",
    "DataValidationReport",
    "QualityIssue",
    # Data providers
    "BaseDataProvider",
    "OandaProvider",
    "AlphaVantageProvider",
    # Data models
    "SwingCandleData",
    "DataQualityMetrics",
]

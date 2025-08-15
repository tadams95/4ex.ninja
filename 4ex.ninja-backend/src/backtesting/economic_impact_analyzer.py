"""
Economic Impact Analyzer for Fundamental Analysis Integration.

This module analyzes the impact of economic events and news releases
on strategy performance, enabling fundamental analysis integration.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd

logger = logging.getLogger(__name__)


class EconomicEventAnalyzer:
    """
    Analyzes the impact of economic events on strategy performance.

    Provides insights into how economic news releases affect trading
    performance and helps optimize strategy timing around events.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the economic impact analyzer."""
        self.config = config or self._get_default_config()
        logger.info("EconomicEventAnalyzer initialized successfully")

    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "economic_analysis": {
                "event_impact_window_hours": 24,  # Hours before/after event to analyze
                "high_impact_events": [
                    "NFP",
                    "CPI",
                    "GDP",
                    "FOMC",
                    "ECB",
                    "BOJ",
                    "BOE",
                    "Unemployment",
                    "Retail_Sales",
                    "PMI",
                ],
                "medium_impact_events": [
                    "PPI",
                    "Industrial_Production",
                    "Consumer_Confidence",
                    "Housing_Data",
                    "Trade_Balance",
                ],
                "currencies": {
                    "USD": ["NFP", "CPI", "GDP", "FOMC", "Unemployment"],
                    "EUR": ["ECB", "CPI_EU", "GDP_EU", "PMI_EU"],
                    "GBP": ["BOE", "CPI_UK", "GDP_UK", "PMI_UK"],
                    "JPY": ["BOJ", "CPI_JP", "GDP_JP", "Tankan"],
                    "CHF": ["SNB", "CPI_CH", "GDP_CH"],
                    "AUD": ["RBA", "CPI_AU", "GDP_AU"],
                    "CAD": ["BOC", "CPI_CA", "GDP_CA"],
                    "NZD": ["RBNZ", "CPI_NZ", "GDP_NZ"],
                },
            }
        }

    async def analyze_economic_impact(
        self, strategy_results: pd.DataFrame, market_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, float]:
        """
        Analyze the impact of economic events on strategy performance.

        Args:
            strategy_results: DataFrame with strategy trades and returns
            market_data: Dictionary of market data by currency pair

        Returns:
            Dictionary of economic event impacts
        """
        try:
            logger.info("Starting economic impact analysis")

            if strategy_results.empty:
                return {}

            # Get economic events in the time range
            economic_events = await self._get_economic_events(strategy_results)

            # Analyze performance around economic events
            event_impacts = await self._analyze_event_impacts(
                strategy_results, economic_events, market_data
            )

            # Calculate aggregate impact metrics
            aggregate_impacts = self._calculate_aggregate_impacts(event_impacts)

            logger.info(
                f"Economic impact analysis completed for {len(aggregate_impacts)} event types"
            )
            return aggregate_impacts

        except Exception as e:
            logger.error(f"Error in economic impact analysis: {e}")
            return {}

    async def _get_economic_events(
        self, strategy_results: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """
        Get economic events for the strategy time period.

        In production, this would integrate with an economic calendar API.
        For now, we'll simulate key events based on typical schedules.
        """
        try:
            if strategy_results.empty:
                return []

            start_date = strategy_results["timestamp"].min()
            end_date = strategy_results["timestamp"].max()

            # Simulate economic events based on typical schedules
            events = []

            # Generate monthly NFP (first Friday of each month)
            current_date = start_date.replace(day=1)
            while current_date <= end_date:
                # Find first Friday of the month
                first_friday = current_date
                while first_friday.weekday() != 4:  # Friday is 4
                    first_friday += timedelta(days=1)
                    if first_friday.day > 7:  # If we've gone past the first week
                        break

                if first_friday <= end_date:
                    events.append(
                        {
                            "timestamp": first_friday.replace(
                                hour=8, minute=30
                            ),  # 8:30 AM EST
                            "event_type": "NFP",
                            "currency": "USD",
                            "impact": "high",
                            "description": "Non-Farm Payrolls",
                        }
                    )

                # Move to next month
                if current_date.month == 12:
                    current_date = current_date.replace(
                        year=current_date.year + 1, month=1
                    )
                else:
                    current_date = current_date.replace(month=current_date.month + 1)

            # Generate monthly CPI (around 10th of each month)
            current_date = start_date.replace(day=1)
            while current_date <= end_date:
                cpi_date = current_date.replace(
                    day=min(10, 28)
                )  # 10th or last valid day
                if cpi_date <= end_date:
                    events.append(
                        {
                            "timestamp": cpi_date.replace(hour=8, minute=30),
                            "event_type": "CPI",
                            "currency": "USD",
                            "impact": "high",
                            "description": "Consumer Price Index",
                        }
                    )

                # Move to next month
                if current_date.month == 12:
                    current_date = current_date.replace(
                        year=current_date.year + 1, month=1
                    )
                else:
                    current_date = current_date.replace(month=current_date.month + 1)

            # Generate FOMC meetings (8 times per year, roughly every 6 weeks)
            fomc_dates = []
            current_date = start_date
            while current_date <= end_date:
                fomc_dates.append(current_date)
                current_date += timedelta(weeks=6)

            for fomc_date in fomc_dates:
                if fomc_date <= end_date:
                    events.append(
                        {
                            "timestamp": fomc_date.replace(
                                hour=14, minute=0
                            ),  # 2:00 PM EST
                            "event_type": "FOMC",
                            "currency": "USD",
                            "impact": "high",
                            "description": "Federal Open Market Committee Meeting",
                        }
                    )

            # Generate ECB meetings (monthly)
            current_date = start_date.replace(day=1)
            while current_date <= end_date:
                # ECB typically meets first Thursday of the month
                ecb_date = current_date
                while ecb_date.weekday() != 3:  # Thursday is 3
                    ecb_date += timedelta(days=1)
                    if ecb_date.day > 7:
                        break

                if ecb_date <= end_date:
                    events.append(
                        {
                            "timestamp": ecb_date.replace(
                                hour=13, minute=45
                            ),  # 1:45 PM CET
                            "event_type": "ECB",
                            "currency": "EUR",
                            "impact": "high",
                            "description": "European Central Bank Meeting",
                        }
                    )

                # Move to next month
                if current_date.month == 12:
                    current_date = current_date.replace(
                        year=current_date.year + 1, month=1
                    )
                else:
                    current_date = current_date.replace(month=current_date.month + 1)

            return sorted(events, key=lambda x: x["timestamp"])

        except Exception as e:
            logger.error(f"Error getting economic events: {e}")
            return []

    async def _analyze_event_impacts(
        self,
        strategy_results: pd.DataFrame,
        economic_events: List[Dict[str, Any]],
        market_data: Dict[str, pd.DataFrame],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Analyze performance impact around each economic event."""
        try:
            event_impacts = {}

            impact_window_hours = self.config["economic_analysis"][
                "event_impact_window_hours"
            ]

            for event in economic_events:
                event_type = event["event_type"]
                event_time = event["timestamp"]

                # Define time windows
                pre_event_start = event_time - timedelta(hours=impact_window_hours)
                post_event_end = event_time + timedelta(hours=impact_window_hours)

                # Get trades in the impact window
                impact_trades = strategy_results[
                    (strategy_results["timestamp"] >= pre_event_start)
                    & (strategy_results["timestamp"] <= post_event_end)
                ].copy()

                if not impact_trades.empty:
                    # Analyze performance before and after event
                    pre_event_trades = impact_trades[
                        impact_trades["timestamp"] <= event_time
                    ]
                    post_event_trades = impact_trades[
                        impact_trades["timestamp"] > event_time
                    ]

                    # Calculate performance metrics
                    impact_analysis = {
                        "event": event,
                        "pre_event_performance": self._calculate_performance_metrics(
                            pre_event_trades
                        ),
                        "post_event_performance": self._calculate_performance_metrics(
                            post_event_trades
                        ),
                        "total_trades": len(impact_trades),
                        "market_volatility": await self._calculate_event_volatility(
                            event_time, market_data, event["currency"]
                        ),
                    }

                    if event_type not in event_impacts:
                        event_impacts[event_type] = []
                    event_impacts[event_type].append(impact_analysis)

            return event_impacts

        except Exception as e:
            logger.error(f"Error analyzing event impacts: {e}")
            return {}

    def _calculate_performance_metrics(self, trades: pd.DataFrame) -> Dict[str, float]:
        """Calculate basic performance metrics for a set of trades."""
        try:
            if trades.empty:
                return {
                    "total_pnl": 0.0,
                    "win_rate": 0.0,
                    "avg_pnl_per_trade": 0.0,
                    "trade_count": 0,
                }

            total_pnl = float(trades["pnl"].sum()) if "pnl" in trades.columns else 0.0
            winning_trades = (
                trades[trades["pnl"] > 0] if "pnl" in trades.columns else pd.DataFrame()
            )
            win_rate = (
                float(len(winning_trades) / len(trades)) if len(trades) > 0 else 0.0
            )
            avg_pnl_per_trade = total_pnl / len(trades) if len(trades) > 0 else 0.0

            return {
                "total_pnl": total_pnl,
                "win_rate": win_rate,
                "avg_pnl_per_trade": avg_pnl_per_trade,
                "trade_count": len(trades),
            }

        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            return {
                "total_pnl": 0.0,
                "win_rate": 0.0,
                "avg_pnl_per_trade": 0.0,
                "trade_count": 0,
            }

    async def _calculate_event_volatility(
        self, event_time: datetime, market_data: Dict[str, pd.DataFrame], currency: str
    ) -> float:
        """Calculate market volatility around an economic event."""
        try:
            # Get relevant currency pairs for the currency
            relevant_pairs = [pair for pair in market_data.keys() if currency in pair]

            if not relevant_pairs:
                return 0.0

            volatilities = []
            window_hours = 4  # 4 hours around event

            for pair in relevant_pairs:
                pair_data = market_data[pair]
                if pair_data.empty or "timestamp" not in pair_data.columns:
                    continue

                # Get data around event time
                event_start = event_time - timedelta(hours=window_hours)
                event_end = event_time + timedelta(hours=window_hours)

                event_data = pair_data[
                    (pair_data["timestamp"] >= event_start)
                    & (pair_data["timestamp"] <= event_end)
                ]

                if not event_data.empty and "close" in event_data.columns:
                    returns = event_data["close"].pct_change().dropna()
                    if not returns.empty:
                        volatility = returns.std()
                        volatilities.append(volatility)

            return float(sum(volatilities) / len(volatilities)) if volatilities else 0.0

        except Exception as e:
            logger.error(f"Error calculating event volatility: {e}")
            return 0.0

    def _calculate_aggregate_impacts(
        self, event_impacts: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, float]:
        """Calculate aggregate impact metrics across all events."""
        try:
            aggregate_impacts = {}

            for event_type, events in event_impacts.items():
                if not events:
                    continue

                # Aggregate metrics across all instances of this event type
                total_pre_pnl = sum(
                    event["pre_event_performance"]["total_pnl"] for event in events
                )
                total_post_pnl = sum(
                    event["post_event_performance"]["total_pnl"] for event in events
                )

                avg_pre_win_rate = sum(
                    event["pre_event_performance"]["win_rate"] for event in events
                ) / len(events)

                avg_post_win_rate = sum(
                    event["post_event_performance"]["win_rate"] for event in events
                ) / len(events)

                avg_volatility = sum(
                    event["market_volatility"] for event in events
                ) / len(events)

                total_trades = sum(event["total_trades"] for event in events)

                # Calculate impact score
                pnl_impact = total_post_pnl - total_pre_pnl
                win_rate_impact = avg_post_win_rate - avg_pre_win_rate

                # Normalize impact score
                if total_trades > 0:
                    normalized_pnl_impact = pnl_impact / total_trades
                    impact_score = (normalized_pnl_impact * 0.7) + (
                        win_rate_impact * 0.3
                    )
                else:
                    impact_score = 0.0

                aggregate_impacts[event_type] = float(impact_score)

            return aggregate_impacts

        except Exception as e:
            logger.error(f"Error calculating aggregate impacts: {e}")
            return {}

    async def analyze_currency_specific_events(
        self,
        strategy_results: pd.DataFrame,
        market_data: Dict[str, pd.DataFrame],
        target_currency: str,
    ) -> Dict[str, Any]:
        """Analyze impact of events specific to a target currency."""
        try:
            logger.info(f"Analyzing {target_currency} specific economic events")

            # Get events for the target currency
            currency_events = self.config["economic_analysis"]["currencies"].get(
                target_currency, []
            )

            # Filter strategy results for pairs containing the target currency
            currency_trades = (
                strategy_results[
                    strategy_results["currency_pair"].str.contains(target_currency)
                ]
                if "currency_pair" in strategy_results.columns
                else pd.DataFrame()
            )

            if currency_trades.empty:
                return {}

            # Get economic events
            all_events = await self._get_economic_events(currency_trades)
            currency_specific_events = [
                event for event in all_events if event["currency"] == target_currency
            ]

            # Analyze impacts
            event_impacts = await self._analyze_event_impacts(
                currency_trades, currency_specific_events, market_data
            )

            aggregate_impacts = self._calculate_aggregate_impacts(event_impacts)

            # Calculate currency-specific metrics
            total_currency_trades = len(currency_trades)
            avg_pnl_per_trade = (
                currency_trades["pnl"].mean()
                if "pnl" in currency_trades.columns
                else 0.0
            )

            return {
                "currency": target_currency,
                "total_trades": total_currency_trades,
                "avg_pnl_per_trade": float(avg_pnl_per_trade),
                "event_impacts": aggregate_impacts,
                "events_analyzed": len(currency_specific_events),
            }

        except Exception as e:
            logger.error(f"Error analyzing currency specific events: {e}")
            return {}

    async def get_event_trading_recommendations(
        self, event_impacts: Dict[str, float]
    ) -> List[str]:
        """Generate trading recommendations based on economic event analysis."""
        try:
            recommendations = []

            # Analyze high-impact events
            high_impact_threshold = 0.1
            negative_impact_threshold = -0.05

            for event_type, impact in event_impacts.items():
                if impact > high_impact_threshold:
                    recommendations.append(
                        f"Consider increasing exposure around {event_type} events (positive impact: {impact:.3f})"
                    )
                elif impact < negative_impact_threshold:
                    recommendations.append(
                        f"Consider reducing exposure around {event_type} events (negative impact: {impact:.3f})"
                    )

            # General recommendations
            if not recommendations:
                recommendations.append(
                    "Economic event impact appears neutral - maintain current strategy"
                )

            # Add timing recommendations
            recommendations.append(
                "Consider implementing pre-event position sizing adjustments"
            )
            recommendations.append(
                "Monitor volatility spikes during high-impact events"
            )

            return recommendations

        except Exception as e:
            logger.error(f"Error generating event trading recommendations: {e}")
            return ["Unable to generate recommendations due to analysis error"]

"""
Enhanced Daily Production Service

Integrates Phase 1 Enhanced Daily Strategy into the production environment.
Provides real-time analysis with Session-Based Trading, Support/Resistance Confluence,
and Dynamic Position Sizing.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import logging
import pandas as pd

from deployed_strategies.enhanced_daily_strategy import EnhancedDailyStrategy
from services.data_service import DataService
from services.enhanced_discord_service import get_enhanced_discord_service, SignalPriority
from services.notification_service import NotificationService
from models.signal_models import PriceData, TradingSignal, SignalType, SignalStatus


class EnhancedDailyProductionService:
    """Production service for Enhanced Daily Strategy with Phase 1 enhancements."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.data_service = DataService()
        self.strategy = EnhancedDailyStrategy()
        
        # Initialize Discord integration
        self.discord_service = get_enhanced_discord_service()
        self.notification_service = NotificationService()

        # Track performance and signals
        self.active_signals = {}
        self.performance_metrics = {
            "total_signals_generated": 0,
            "signals_sent_to_discord": 0,
            "discord_delivery_success_rate": 0.0,
            "session_filtered_signals": 0,
            "confluence_enhanced_signals": 0,
            "dynamic_sized_signals": 0,
            "phase1_coverage": {},
        }

        # Currency pairs to monitor (focus on JPY pairs)
        self.monitored_pairs = [
            "USD_JPY",
            "EUR_JPY",
            "GBP_JPY",
            "AUD_JPY",  # JPY specialty
            "EUR_USD",
            "GBP_USD",
            "AUD_USD",
            "USD_CAD",
            "USD_CHF",
            "EUR_GBP",
        ]

    async def generate_enhanced_signals(self) -> List[Dict]:
        """Generate trading signals using Enhanced Daily Strategy."""
        try:
            self.logger.info("Generating Enhanced Daily Strategy signals...")

            # Fetch current market data
            market_data = await self._fetch_market_data()

            if not market_data:
                self.logger.warning("No market data available for signal generation")
                return []

            # Run strategy analysis
            scan_results = self.strategy.scan_all_pairs(market_data)

            # Update performance metrics
            self._update_performance_metrics(scan_results)

            # Convert opportunities to production signals
            signals = await self._convert_to_production_signals(scan_results)

            # Send signals to Discord if any were generated
            if signals:
                await self._send_signals_to_discord(signals)

            self.logger.info(
                f"Generated {len(signals)} enhanced signals with Phase 1 improvements"
            )

            return signals

        except Exception as e:
            self.logger.error(f"Error generating enhanced signals: {str(e)}")
            return []

    async def _fetch_market_data(self) -> Dict[str, pd.DataFrame]:
        """Fetch OHLC data for all monitored pairs."""
        market_data = {}

        for pair in self.monitored_pairs:
            try:
                # Fetch daily data for the last 100 days
                data = await self.data_service.get_historical_data(
                    pair=pair, timeframe="D", count=100  # Daily timeframe
                )

                if data and len(data) >= 50:  # Minimum data requirement
                    # Convert to DataFrame
                    df_data = []
                    for candle in data:
                        df_data.append(
                            {
                                "open": float(candle.open),
                                "high": float(candle.high),
                                "low": float(candle.low),
                                "close": float(candle.close),
                                "volume": float(candle.volume or 0),
                            }
                        )

                    # Create datetime index
                    end_date = datetime.now(timezone.utc)
                    dates = pd.date_range(end=end_date, periods=len(df_data), freq="D")

                    df = pd.DataFrame(df_data, index=dates)
                    market_data[pair] = df

                else:
                    self.logger.warning(f"Insufficient data for {pair}")

            except Exception as e:
                self.logger.error(f"Error fetching data for {pair}: {str(e)}")

        return market_data

    async def _convert_to_production_signals(self, scan_results: Dict) -> List[Dict]:
        """Convert strategy opportunities to production trading signals."""
        signals = []

        opportunities = scan_results.get("top_opportunities", [])

        for opp in opportunities:
            try:
                pair = opp["pair"]

                # Get detailed analysis for this pair
                detailed_analysis = scan_results["detailed_results"].get(pair, {})

                if "error" in detailed_analysis:
                    continue

                # Extract signal data
                tech_signal = detailed_analysis.get("technical_signal", {})
                trade_rec = detailed_analysis.get("trade_recommendation", {})
                position_sizing = detailed_analysis.get("position_sizing", {})

                # Create production signal
                signal_data = {
                    "pair": pair,
                    "signal_type": "enhanced_daily",
                    "direction": tech_signal.get("direction", "").lower(),
                    "entry_price": tech_signal.get("entry_price"),
                    "stop_loss": tech_signal.get("stop_loss"),
                    "take_profit": tech_signal.get("take_profit"),
                    "confidence": trade_rec.get("confidence", 0.0),
                    "recommendation": trade_rec.get("recommendation", "WAIT"),
                    # Phase 1 enhancements
                    "session_analysis": detailed_analysis.get("session_analysis", {}),
                    "confluence_score": detailed_analysis.get("confluence_score", 0.0),
                    "signal_strength": detailed_analysis.get("signal_strength", "weak"),
                    "position_sizing": position_sizing,
                    # Additional metadata
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "timeframe": "1d",
                    "strategy_version": "enhanced_daily_v1.0",
                    "phase1_features": {
                        "session_filtered": detailed_analysis["session_analysis"][
                            "is_optimal_session"
                        ],
                        "confluence_enhanced": detailed_analysis["confluence_score"]
                        >= 0.8,
                        "dynamic_sized": position_sizing is not None
                        and "error" not in position_sizing,
                    },
                    # Priority and scoring
                    "priority_score": opp.get("priority_score", 0.0),
                    "filters_passed": trade_rec.get("filters_passed", []),
                    "filters_failed": trade_rec.get("filters_failed", []),
                }

                signals.append(signal_data)

            except Exception as e:
                self.logger.error(f"Error converting opportunity to signal: {str(e)}")

        return signals

    def _update_performance_metrics(self, scan_results: Dict):
        """Update performance tracking metrics."""
        try:
            self.performance_metrics["total_signals_generated"] += scan_results.get(
                "opportunities_found", 0
            )

            # Count Phase 1 enhancements
            detailed_results = scan_results.get("detailed_results", {})

            session_filtered = 0
            confluence_enhanced = 0
            dynamic_sized = 0

            for pair, analysis in detailed_results.items():
                if isinstance(analysis, dict) and "error" not in analysis:
                    if analysis.get("session_analysis", {}).get(
                        "is_optimal_session", False
                    ):
                        session_filtered += 1

                    if analysis.get("confluence_score", 0.0) >= 0.8:
                        confluence_enhanced += 1

                    if analysis.get("position_sizing") is not None:
                        dynamic_sized += 1

            self.performance_metrics["session_filtered_signals"] += session_filtered
            self.performance_metrics[
                "confluence_enhanced_signals"
            ] += confluence_enhanced
            self.performance_metrics["dynamic_sized_signals"] += dynamic_sized

            # Update Phase 1 coverage
            phase1_summary = scan_results.get("phase1_summary", {})
            self.performance_metrics["phase1_coverage"] = phase1_summary.get(
                "enhancement_coverage", {}
            )

        except Exception as e:
            self.logger.error(f"Error updating performance metrics: {str(e)}")

    async def _send_signals_to_discord(self, signals: List[Dict]) -> None:
        """Send generated signals to Discord with multi-tier routing."""
        try:
            if not signals:
                return
                
            discord_signals_sent = 0
            discord_delivery_failures = 0
            
            for signal in signals:
                try:
                    # Determine signal priority based on confluence and strength
                    priority = self._determine_signal_priority(signal)
                    
                    # Convert to enhanced signal format for Discord
                    enhanced_signal = self._convert_to_enhanced_signal(signal)
                    
                    # Send to Discord with appropriate tier routing
                    success = await self.discord_service.send_enhanced_signal(
                        enhanced_signal, priority
                    )
                    
                    if success:
                        discord_signals_sent += 1
                        self.logger.info(f"Signal sent to Discord: {signal['pair']} - {signal['trade_recommendation']['recommendation']}")
                    else:
                        discord_delivery_failures += 1
                        self.logger.warning(f"Failed to send Discord signal for {signal['pair']}")
                        
                except Exception as e:
                    discord_delivery_failures += 1
                    self.logger.error(f"Error sending signal to Discord for {signal['pair']}: {str(e)}")
            
            # Update Discord delivery metrics
            self.performance_metrics["signals_sent_to_discord"] += discord_signals_sent
            total_attempts = discord_signals_sent + discord_delivery_failures
            if total_attempts > 0:
                success_rate = discord_signals_sent / total_attempts
                self.performance_metrics["discord_delivery_success_rate"] = round(success_rate, 3)
            
            self.logger.info(f"Discord delivery: {discord_signals_sent} sent, {discord_delivery_failures} failed")
            
        except Exception as e:
            self.logger.error(f"Error in Discord signal delivery: {str(e)}")

    def _determine_signal_priority(self, signal: Dict) -> SignalPriority:
        """Determine signal priority based on Enhanced Daily Strategy analysis."""
        try:
            confluence_score = signal.get("confluence_score", 0.0)
            signal_strength = signal.get("signal_strength", "weak")
            confidence = signal.get("trade_recommendation", {}).get("confidence", 0.0)
            
            # High priority: Strong confluence + high confidence
            if confluence_score >= 1.5 and confidence >= 0.8 and signal_strength in ["confluence", "very_strong"]:
                return SignalPriority.HIGH
            
            # Medium priority: Good confluence or strong signal
            elif confluence_score >= 0.8 or confidence >= 0.6 or signal_strength in ["strong", "very_strong"]:
                return SignalPriority.MEDIUM
            
            # Low priority: Basic signals
            else:
                return SignalPriority.LOW
                
        except Exception as e:
            self.logger.warning(f"Error determining signal priority: {str(e)}")
            return SignalPriority.LOW

    def _convert_to_enhanced_signal(self, signal: Dict) -> Dict:
        """Convert Enhanced Daily Strategy signal to enhanced Discord format."""
        try:
            # Extract key data
            pair = signal.get("pair", "UNKNOWN")
            trade_rec = signal.get("trade_recommendation", {})
            technical_signal = signal.get("technical_signal", {})
            session_analysis = signal.get("session_analysis", {})
            
            # Build enhanced signal for Discord
            enhanced_signal = {
                "pair": pair,
                "signal_type": technical_signal.get("signal", "NONE"),
                "direction": technical_signal.get("direction", "NONE"),
                "price": signal.get("current_price", 0.0),
                "entry_price": technical_signal.get("entry_price", 0.0),
                "stop_loss": technical_signal.get("stop_loss", 0.0),
                "take_profit": technical_signal.get("take_profit", 0.0),
                "confidence": trade_rec.get("confidence", 0.0),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                
                # Phase 1 Enhancement Details
                "confluence_score": signal.get("confluence_score", 0.0),
                "signal_strength": signal.get("signal_strength", "unknown"),
                "session_quality": session_analysis.get("session_quality_multiplier", 1.0),
                "is_optimal_session": session_analysis.get("is_optimal_session", False),
                "phase1_score": trade_rec.get("phase1_score", {}),
                
                # Technical Indicators
                "indicators": technical_signal.get("indicators", {}),
                
                # Recommendations
                "recommendation": trade_rec.get("recommendation", "WAIT"),
                "filters_passed": trade_rec.get("filters_passed", []),
                "filters_failed": trade_rec.get("filters_failed", []),
                
                # Strategy identification
                "strategy_type": "Enhanced Daily Strategy (Phase 1)",
                "timeframe": "D"
            }
            
            return enhanced_signal
            
        except Exception as e:
            self.logger.error(f"Error converting signal to enhanced format: {str(e)}")
            return {
                "pair": signal.get("pair", "UNKNOWN"),
                "signal_type": "ERROR",
                "error": str(e)
            }

    async def get_enhanced_market_analysis(self) -> Dict:
        """Get comprehensive market analysis with Phase 1 enhancements."""
        try:
            # Generate signals
            signals = await self.generate_enhanced_signals()

            # Get current session information
            session_analysis = self.strategy.session_manager.get_session_analysis()

            # Get portfolio analysis (if we had current positions)
            portfolio_analysis = (
                self.strategy.position_sizer.get_portfolio_risk_analysis({}, 10000)
            )

            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "market_status": {
                    "active_sessions": session_analysis["current_sessions"],
                    "major_overlap_active": session_analysis["major_overlap_active"],
                    "pairs_analyzed": len(self.monitored_pairs),
                },
                "signals": signals,
                "signal_count": len(signals),
                "performance_metrics": self.performance_metrics,
                "session_analysis": session_analysis,
                "portfolio_analysis": portfolio_analysis,
                "phase1_status": {
                    "session_filtering": "ACTIVE",
                    "confluence_detection": "ACTIVE",
                    "dynamic_sizing": "ACTIVE",
                    "integration_status": "COMPLETE",
                },
                "recommendations": self._generate_market_recommendations(
                    signals, session_analysis
                ),
            }

        except Exception as e:
            self.logger.error(f"Error generating market analysis: {str(e)}")
            return {"error": str(e)}

    def _generate_market_recommendations(
        self, signals: List[Dict], session_analysis: Dict
    ) -> List[str]:
        """Generate market recommendations based on current conditions."""
        recommendations = []

        # Session-based recommendations
        current_sessions = session_analysis.get("current_sessions", [])
        if "Tokyo" in current_sessions:
            recommendations.append("🇯🇵 Tokyo session active - Focus on JPY pairs")
        elif "London_NY_Overlap" in current_sessions:
            recommendations.append("🌐 London-NY overlap - High liquidity period")
        elif "New_York" in current_sessions:
            recommendations.append("🇺🇸 NY session active - Good for USD pairs")

        # Signal-based recommendations
        if len(signals) == 0:
            recommendations.append(
                "⏳ No high-quality signals currently - Wait for better setups"
            )
        elif len(signals) >= 3:
            recommendations.append(
                "🎯 Multiple opportunities available - Prioritize by confluence score"
            )

        # JPY specialization recommendations
        jpy_signals = [s for s in signals if "JPY" in s["pair"]]
        if len(jpy_signals) >= 2:
            recommendations.append(
                "🔥 Multiple JPY opportunities - Our specialty pairs performing well"
            )

        return recommendations

    async def monitor_enhanced_signals(self, duration_minutes: int = 60):
        """Monitor and log enhanced signal generation for specified duration."""
        self.logger.info(
            f"Starting enhanced signal monitoring for {duration_minutes} minutes..."
        )

        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(minutes=duration_minutes)

        monitoring_results = []

        while datetime.now(timezone.utc) < end_time:
            try:
                # Generate analysis
                analysis = await self.get_enhanced_market_analysis()

                # Log results
                monitoring_results.append(
                    {
                        "timestamp": analysis["timestamp"],
                        "signals_found": analysis["signal_count"],
                        "active_sessions": analysis["market_status"]["active_sessions"],
                        "phase1_coverage": analysis.get("performance_metrics", {}).get(
                            "phase1_coverage", {}
                        ),
                    }
                )

                self.logger.info(
                    f"Enhanced analysis complete - {analysis['signal_count']} signals found"
                )

                # Wait 5 minutes before next analysis
                await asyncio.sleep(300)

            except Exception as e:
                self.logger.error(f"Error during monitoring: {str(e)}")
                await asyncio.sleep(60)

        self.logger.info(
            f"Enhanced signal monitoring completed after {duration_minutes} minutes"
        )
        return monitoring_results


# Test function for production service
async def test_enhanced_production_service():
    """Test the Enhanced Daily Production Service."""
    print("🧪 Testing Enhanced Daily Production Service...")

    service = EnhancedDailyProductionService()

    # Test market analysis
    analysis = await service.get_enhanced_market_analysis()

    if "error" not in analysis:
        print(f"✅ Market Analysis Complete")
        print(f"   Signals Found: {analysis['signal_count']}")
        print(f"   Active Sessions: {analysis['market_status']['active_sessions']}")
        print(f"   Phase 1 Status: {analysis['phase1_status']['integration_status']}")

        if analysis["signal_count"] > 0:
            print(
                f"   Top Signal: {analysis['signals'][0]['pair']} - {analysis['signals'][0]['recommendation']}"
            )

        print(f"   Recommendations: {len(analysis['recommendations'])}")
        for rec in analysis["recommendations"]:
            print(f"   - {rec}")
    else:
        print(f"❌ Error: {analysis['error']}")


if __name__ == "__main__":
    asyncio.run(test_enhanced_production_service())

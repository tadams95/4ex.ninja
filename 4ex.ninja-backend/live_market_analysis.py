"""
Live Market Regime Detection Test with Real OANDA Data.

This script demonstrates the Market Regime Detection Engine analyzing
real market conditions using live OANDA data from your trading account.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.backtesting.regime_detector import RegimeDetector
from src.backtesting.data_infrastructure import DataInfrastructure


async def analyze_live_market_regimes():
    """Analyze current market regimes using live OANDA data."""
    print("🎯 === LIVE MARKET REGIME ANALYSIS ===")
    print(f"⏰ Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    
    try:
        # 1. Initialize and connect to data sources
        print("📡 Connecting to OANDA live data feed...")
        data_infra = DataInfrastructure()
        connected = await data_infra.connect_all()
        
        if not connected:
            print("❌ Failed to connect to data providers")
            return
        
        # Check connection health
        health_status = await data_infra.health_check_all()
        print("📊 Data Provider Status:")
        for provider, health in health_status.items():
            status_icon = "✅" if health.status.value == "healthy" else "⚠️"
            print(f"  {status_icon} {provider}: {health.status.value}")
            if health.response_time_ms:
                print(f"     Response time: {health.response_time_ms:.0f}ms")
        print()
        
        # 2. Fetch recent market data
        print("📈 Fetching live market data...")
        major_pairs = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CHF', 'AUD_USD', 'USD_CAD', 'NZD_USD']
        
        # Get last 50 4-hour candles (about 8-9 days of data)
        end_time = datetime.now()
        start_time = end_time - timedelta(days=10)
        
        market_data = {}
        for pair in major_pairs:
            print(f"  📊 {pair}...", end="")
            try:
                candles = await data_infra.get_candles(
                    pair, '4H', start_time, end_time
                )
                
                if candles and len(candles) > 20:  # Need sufficient data
                    market_data[pair] = candles
                    latest = candles[-1]
                    change = ((float(latest.close) - float(candles[-2].close)) / float(candles[-2].close)) * 100
                    change_icon = "📈" if change > 0 else "📉"
                    print(f" ✅ {len(candles)} candles | Latest: {latest.close} {change_icon} {change:+.2f}%")
                else:
                    print(f" ⚠️ Insufficient data ({len(candles) if candles else 0} candles)")
                    
            except Exception as e:
                print(f" ❌ Error: {str(e)[:30]}...")
        
        if not market_data:
            print("\n❌ No market data available for analysis")
            return
        
        print(f"\n✅ Successfully loaded data for {len(market_data)} currency pairs")
        print()
        
        # 3. Run comprehensive regime analysis
        print("🧠 Analyzing Market Regimes...")
        detector = RegimeDetector()
        
        # Analyze current regime
        result = await detector.detect_current_regime(list(market_data.keys()), timeframe='4H')
        
        # 4. Display comprehensive results
        print("=" * 60)
        print("🎯 LIVE MARKET REGIME ANALYSIS RESULTS")
        print("=" * 60)
        
        # Overall regime
        regime_icons = {
            'trending_high_vol': '📈🔥',
            'trending_low_vol': '📈😌',
            'ranging_high_vol': '📊🔥',
            'ranging_low_vol': '📊😌',
            'transition': '🔄',
            'uncertain': '❓'
        }
        
        sentiment_icons = {
            'risk_on': '💪',
            'risk_off': '🛡️',
            'neutral': '⚖️'
        }
        
        print(f"🎯 PRIMARY REGIME: {regime_icons.get(result.regime.value, '📊')} {result.regime.value.upper()}")
        print(f"😎 RISK SENTIMENT: {sentiment_icons.get(result.sentiment.value, '⚖️')} {result.sentiment.value.upper()}")
        print(f"🎯 CONFIDENCE LEVEL: {result.confidence:.1%}")
        print(f"📊 VOLATILITY REGIME: {result.volatility_level.upper()}")
        print(f"⏱️  REGIME DURATION: {result.regime_duration_hours:.1f} hours")
        print()
        
        # Contributing factors
        print("🔍 KEY FACTORS DRIVING CURRENT REGIME:")
        for factor in result.contributing_factors:
            print(f"  • {factor}")
        print()
        
        # 5. Detailed component analysis
        print("📋 DETAILED COMPONENT ANALYSIS:")
        print("-" * 40)
        
        # Test individual components with live data
        components_data = {
            'timestamp': datetime.now(),
            'timeframe': '4H'
        }
        components_data.update(market_data)
        
        # Market Classification
        market_analysis = await detector.market_classifier.classify_market_condition(components_data)
        trending_pct = market_analysis.get('trending_percentage', 0) * 100
        print(f"📈 MARKET CONDITION:")
        print(f"   • Trending: {'YES' if market_analysis.get('is_trending') else 'NO'} ({trending_pct:.0f}% of pairs)")
        print(f"   • Dominant Direction: {market_analysis.get('dominant_direction', 'N/A').upper()}")
        print(f"   • Trend Strength: {market_analysis.get('trend_strength', 0):.2f}/1.0")
        print()
        
        # Volatility Analysis
        vol_analysis = await detector.volatility_analyzer.analyze_volatility_regime(components_data)
        print(f"📊 VOLATILITY ANALYSIS:")
        print(f"   • Current Regime: {vol_analysis.get('regime', 'N/A').upper()}")
        print(f"   • Average Volatility: {vol_analysis.get('average_volatility', 0):.3f}")
        print(f"   • Normalized Level: {vol_analysis.get('normalized_volatility', 1):.2f}x normal")
        vol_dist = vol_analysis.get('regime_distribution', {})
        print(f"   • Distribution: {vol_dist.get('high', 0)} high, {vol_dist.get('normal', 0)} normal, {vol_dist.get('low', 0)} low")
        print()
        
        # Trend Analysis
        trend_analysis = await detector.trend_analyzer.analyze_trend_strength(components_data)
        print(f"📈 TREND ANALYSIS:")
        print(f"   • Overall Strength: {trend_analysis.get('strength', 0):.2f}/1.0")
        print(f"   • Market Bias: {trend_analysis.get('market_bias', 'mixed').upper()}")
        print(f"   • Trend Consistency: {trend_analysis.get('consistency', 0):.2f}/1.0")
        print(f"   • Current Momentum: {trend_analysis.get('momentum', 0):+.2f}")
        trend_dist = trend_analysis.get('trend_distribution', {})
        print(f"   • Pairs: {trend_dist.get('up_trends', 0)} up, {trend_dist.get('down_trends', 0)} down, {trend_dist.get('no_trend', 0)} ranging")
        print()
        
        # Sentiment Analysis
        sentiment_analysis = await detector.sentiment_analyzer.analyze_risk_sentiment(components_data)
        print(f"😎 RISK SENTIMENT:")
        print(f"   • Sentiment Score: {sentiment_analysis.get('risk_sentiment_score', 0):+.2f} (-1=risk-off, +1=risk-on)")
        print(f"   • Safe Haven Strength: {sentiment_analysis.get('safe_haven_strength', 0):+.2f}")
        print(f"   • Risk Asset Performance: {sentiment_analysis.get('risk_asset_performance', 0):+.2f}")
        print(f"   • Correlation Breakdown: {'YES' if sentiment_analysis.get('correlation_breakdown') else 'NO'}")
        print()
        
        # Economic Events
        econ_analysis = await detector.economic_analyzer.analyze_event_impact(components_data)
        print(f"📰 ECONOMIC EVENT IMPACT:")
        print(f"   • High Impact Events: {econ_analysis.get('high_impact_events', 0)}")
        print(f"   • Volatility Spike Detected: {'YES' if econ_analysis.get('volatility_spike_detected') else 'NO'}")
        print(f"   • Market Reaction Strength: {econ_analysis.get('market_reaction_strength', 0):.2f}/1.0")
        affected = econ_analysis.get('affected_currencies', [])
        print(f"   • Affected Currencies: {', '.join(affected) if affected else 'None'}")
        print()
        
        # 6. Individual pair analysis
        print("💱 INDIVIDUAL PAIR BREAKDOWN:")
        print("-" * 40)
        
        for pair, candles in market_data.items():
            if len(candles) >= 2:
                latest = candles[-1]
                prev = candles[-2]
                change = ((float(latest.close) - float(prev.close)) / float(prev.close)) * 100
                change_icon = "📈" if change > 0 else "📉"
                
                # Get individual analysis if available
                individual_market = market_analysis.get('individual_pairs', {}).get(pair, {})
                individual_vol = vol_analysis.get('individual_pairs', {}).get(pair, {})
                individual_trend = trend_analysis.get('individual_pairs', {}).get(pair, {})
                
                trending = "📈 Trending" if individual_market.get('is_trending') else "📊 Ranging"
                vol_regime = individual_vol.get('regime', 'normal')
                trend_dir = individual_trend.get('direction', 'none') or 'none'
                
                print(f"  {pair}: {latest.close} {change_icon} {change:+.2f}% | {trending} {trend_dir} | Vol: {vol_regime}")
        
        print()
        print("🎯 Next regime evaluation scheduled for:", result.next_evaluation.strftime('%Y-%m-%d %H:%M:%S UTC'))
        print()
        print("✅ LIVE MARKET REGIME ANALYSIS COMPLETE!")
        print("🚀 The system is successfully analyzing real market conditions!")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()


async def quick_regime_check():
    """Quick regime check with current market data."""
    print("⚡ === QUICK REGIME CHECK ===\n")
    
    detector = RegimeDetector()
    major_pairs = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'AUD_USD']
    
    result = await detector.detect_current_regime(major_pairs, timeframe='4H')
    
    print(f"Current Regime: {result.regime.value}")
    print(f"Risk Sentiment: {result.sentiment.value}")
    print(f"Confidence: {result.confidence:.1%}")
    print(f"Volatility: {result.volatility_level}")
    print(f"Key Factors: {', '.join(result.contributing_factors)}")


if __name__ == "__main__":
    print("Select analysis type:")
    print("1. Full Live Market Analysis (recommended)")
    print("2. Quick Regime Check")
    
    choice = input("\nEnter choice (1 or 2, default=1): ").strip() or "1"
    
    if choice == "2":
        asyncio.run(quick_regime_check())
    else:
        asyncio.run(analyze_live_market_regimes())

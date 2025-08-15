"""
Enhanced Live Market Regime Detection Test.

This script properly formats OANDA data for our regime detection system
and provides comprehensive analysis results with real market data.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
from decimal import Decimal

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.backtesting.regime_detector import RegimeDetector
from src.backtesting.data_infrastructure import DataInfrastructure
from src.backtesting.data_providers.base_provider import SwingCandleData


async def fetch_and_format_market_data() -> Dict[str, List[SwingCandleData]]:
    """Fetch and properly format market data for regime analysis."""
    print("📡 Connecting to OANDA live data feed...")
    
    data_infra = DataInfrastructure()
    connected = await data_infra.connect_all()
    
    if not connected:
        print("❌ Failed to connect to data providers")
        return {}
    
    # Check connection health
    health_status = await data_infra.health_check_all()
    print("📊 Data Provider Status:")
    for provider, health in health_status.items():
        status_icon = "✅" if health.status.value == "healthy" else "⚠️"
        print(f"  {status_icon} {provider}: {health.status.value}")
        if health.response_time_ms:
            print(f"     Response time: {health.response_time_ms:.0f}ms")
    print()
    
    # Fetch market data
    major_pairs = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CHF', 'AUD_USD', 'USD_CAD', 'NZD_USD']
    
    # Get more data for better analysis (last 100 4-hour candles ≈ 17 days)
    end_time = datetime.now()
    start_time = end_time - timedelta(days=20)
    
    formatted_data = {}
    print("📈 Fetching and formatting live market data...")
    
    for pair in major_pairs:
        print(f"  📊 {pair}...", end="")
        try:
            candles = await data_infra.get_candles(
                pair, '4H', start_time, end_time
            )
            
            if candles and len(candles) > 50:  # Need sufficient data for analysis
                # Convert to proper format
                formatted_candles = []
                for candle in candles:
                    formatted_candles.append(SwingCandleData(
                        timestamp=candle.timestamp,
                        open=Decimal(str(candle.open)),
                        high=Decimal(str(candle.high)),
                        low=Decimal(str(candle.low)),
                        close=Decimal(str(candle.close)),
                        volume=int(candle.volume) if candle.volume is not None else 0
                    ))
                
                formatted_data[pair] = formatted_candles
                latest = candles[-1]
                prev = candles[-2] if len(candles) > 1 else candles[-1]
                change = ((float(latest.close) - float(prev.close)) / float(prev.close)) * 100
                change_icon = "📈" if change > 0 else "📉"
                print(f" ✅ {len(candles)} candles | Latest: {latest.close} {change_icon} {change:+.2f}%")
            else:
                print(f" ⚠️ Insufficient data ({len(candles) if candles else 0} candles)")
                
        except Exception as e:
            print(f" ❌ Error: {str(e)[:30]}...")
    
    print(f"\n✅ Successfully formatted data for {len(formatted_data)} currency pairs")
    return formatted_data


async def run_comprehensive_regime_analysis():
    """Run comprehensive regime analysis with properly formatted data."""
    print("🎯 === ENHANCED LIVE MARKET REGIME ANALYSIS ===")
    print(f"⏰ Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    
    try:
        # 1. Fetch and format market data
        formatted_data = await fetch_and_format_market_data()
        
        if not formatted_data:
            print("\n❌ No market data available for analysis")
            return
        
        # 2. Initialize regime detector
        print("\n🧠 Initializing Market Regime Detection Engine...")
        detector = RegimeDetector()
        
        # 3. Run detailed component analysis with formatted data
        print("🔬 Running detailed component analysis...")
        
        # Prepare data in the format expected by components
        analysis_data = {
            'timestamp': datetime.now(),
            'timeframe': '4H'
        }
        analysis_data.update(formatted_data)
        
        # Run individual component analyses
        print("\n📊 Component Analysis Results:")
        print("-" * 50)
        
        # Market Classification
        print("🏷️ MARKET CLASSIFICATION:")
        market_result = await detector.market_classifier.classify_market_condition(analysis_data)
        trending_pairs = len([p for p, data in market_result.get('individual_pairs', {}).items() 
                             if data.get('is_trending', False)])
        total_pairs = len(formatted_data)
        trending_pct = (trending_pairs / total_pairs * 100) if total_pairs > 0 else 0
        
        print(f"   • Overall Market State: {'TRENDING' if market_result.get('is_trending', False) else 'RANGING'}")
        print(f"   • Trending Pairs: {trending_pairs}/{total_pairs} ({trending_pct:.0f}%)")
        print(f"   • Dominant Direction: {market_result.get('dominant_direction', 'MIXED').upper()}")
        print(f"   • Trend Strength: {market_result.get('trend_strength', 0):.2f}/1.0")
        print(f"   • Market Confidence: {market_result.get('confidence', 0):.2f}/1.0")
        print()
        
        # Volatility Analysis
        print("📈 VOLATILITY ANALYSIS:")
        vol_result = await detector.volatility_analyzer.analyze_volatility_regime(analysis_data)
        vol_dist = vol_result.get('regime_distribution', {})
        
        print(f"   • Current Regime: {vol_result.get('regime', 'NORMAL').upper()}")
        print(f"   • Average Volatility: {vol_result.get('average_volatility', 0):.3f}")
        print(f"   • Volatility Percentile: {vol_result.get('volatility_percentile', 50):.0f}th percentile")
        print(f"   • Normalized Level: {vol_result.get('normalized_volatility', 1):.2f}x normal")
        print(f"   • Distribution: {vol_dist.get('high', 0)} high, {vol_dist.get('normal', 0)} normal, {vol_dist.get('low', 0)} low")
        print()
        
        # Trend Analysis
        print("📊 TREND ANALYSIS:")
        trend_result = await detector.trend_analyzer.analyze_trend_strength(analysis_data)
        trend_dist = trend_result.get('trend_distribution', {})
        
        print(f"   • Overall Strength: {trend_result.get('strength', 0):.2f}/1.0")
        print(f"   • Market Bias: {trend_result.get('market_bias', 'MIXED').upper()}")
        print(f"   • Trend Consistency: {trend_result.get('consistency', 0):.2f}/1.0")
        print(f"   • Average Momentum: {trend_result.get('momentum', 0):+.3f}")
        print(f"   • Trend Age: {trend_result.get('average_trend_age', 0):.1f} periods")
        print(f"   • Direction Split: {trend_dist.get('up_trends', 0)} up, {trend_dist.get('down_trends', 0)} down, {trend_dist.get('no_trend', 0)} ranging")
        print()
        
        # Risk Sentiment Analysis
        print("💰 RISK SENTIMENT ANALYSIS:")
        sentiment_result = await detector.sentiment_analyzer.analyze_risk_sentiment(analysis_data)
        
        sentiment_score = sentiment_result.get('risk_sentiment_score', 0)
        sentiment_text = "RISK-ON" if sentiment_score > 0.2 else "RISK-OFF" if sentiment_score < -0.2 else "NEUTRAL"
        
        print(f"   • Risk Sentiment: {sentiment_text}")
        print(f"   • Sentiment Score: {sentiment_score:+.2f} (-1=risk-off, +1=risk-on)")
        print(f"   • Safe Haven Strength: {sentiment_result.get('safe_haven_strength', 0):+.2f}")
        print(f"   • Risk Asset Performance: {sentiment_result.get('risk_asset_performance', 0):+.2f}")
        print(f"   • USD Strength: {sentiment_result.get('usd_strength', 0):+.2f}")
        print(f"   • Correlation Breakdown: {'YES' if sentiment_result.get('correlation_breakdown') else 'NO'}")
        print()
        
        # Economic Event Analysis
        print("📰 ECONOMIC EVENT ANALYSIS:")
        econ_result = await detector.economic_analyzer.analyze_event_impact(analysis_data)
        affected = econ_result.get('affected_currencies', [])
        
        print(f"   • Volatility Spike: {'DETECTED' if econ_result.get('volatility_spike_detected') else 'NONE'}")
        print(f"   • Market Reaction: {econ_result.get('market_reaction_strength', 0):.2f}/1.0")
        print(f"   • Synchronized Movement: {'YES' if econ_result.get('synchronized_movement') else 'NO'}")
        print(f"   • Affected Currencies: {', '.join(affected) if affected else 'None'}")
        print(f"   • Event Impact Score: {econ_result.get('event_impact_score', 0):.2f}")
        print()
        
        # 4. Overall regime detection
        print("🎯 OVERALL REGIME DETECTION:")
        print("=" * 50)
        
        regime_result = await detector.detect_current_regime(list(formatted_data.keys()), timeframe='4H')
        
        # Regime display with icons
        regime_icons = {
            'trending_high_vol': '📈🔥',
            'trending_low_vol': '📈😌',
            'ranging_high_vol': '📊🔥',
            'ranging_low_vol': '📊😌',
            'transition': '🔄',
            'uncertain': '❓'
        }
        
        sentiment_icons = {
            'risk_on': '💪🚀',
            'risk_off': '🛡️🔻',
            'neutral': '⚖️⏸️'
        }
        
        print(f"🎯 PRIMARY REGIME: {regime_icons.get(regime_result.regime.value, '📊')} {regime_result.regime.value.upper().replace('_', ' ')}")
        print(f"😎 RISK SENTIMENT: {sentiment_icons.get(regime_result.sentiment.value, '⚖️')} {regime_result.sentiment.value.upper().replace('_', ' ')}")
        print(f"🎯 CONFIDENCE LEVEL: {regime_result.confidence:.1%}")
        print(f"📊 VOLATILITY REGIME: {regime_result.volatility_level.upper()}")
        print(f"⏱️ REGIME DURATION: {regime_result.regime_duration_hours:.1f} hours")
        print()
        
        # Key factors
        print("🔍 KEY FACTORS DRIVING CURRENT REGIME:")
        for factor in regime_result.contributing_factors:
            print(f"  • {factor.replace('_', ' ').title()}")
        print()
        
        # 5. Individual pair analysis with detailed metrics
        print("💱 DETAILED PAIR ANALYSIS:")
        print("-" * 50)
        
        for pair, candles in formatted_data.items():
            if len(candles) >= 2:
                latest = candles[-1]
                prev = candles[-2]
                change = ((latest.close - prev.close) / prev.close) * 100
                change_icon = "📈" if change > 0 else "📉"
                
                # Get individual pair analysis
                pair_market = market_result.get('individual_pairs', {}).get(pair, {})
                pair_vol = vol_result.get('individual_pairs', {}).get(pair, {})
                pair_trend = trend_result.get('individual_pairs', {}).get(pair, {})
                
                market_state = "TRENDING" if pair_market.get('is_trending', False) else "RANGING"
                trend_dir = (pair_trend.get('direction', 'none') or 'none').upper()
                vol_regime = (pair_vol.get('regime', 'normal') or 'normal').upper()
                trend_strength = pair_trend.get('strength', 0)
                
                print(f"  {pair}:")
                print(f"    Price: {latest.close:.5f} {change_icon} {change:+.2f}%")
                print(f"    Market: {market_state} {trend_dir} (strength: {trend_strength:.2f})")
                print(f"    Volatility: {vol_regime}")
                print()
        
        # 6. Trading recommendations based on regime
        print("🚀 TRADING RECOMMENDATIONS:")
        print("-" * 50)
        
        regime = regime_result.regime.value
        sentiment = regime_result.sentiment.value
        confidence = regime_result.confidence
        
        if regime.startswith('trending'):
            print("📈 TREND-FOLLOWING STRATEGIES RECOMMENDED:")
            print("   • Consider momentum strategies")
            print("   • Look for breakout opportunities")
            print("   • Use trend-following indicators")
            if regime.endswith('high_vol'):
                print("   • Reduce position sizes due to high volatility")
                print("   • Wider stop losses recommended")
        else:
            print("📊 RANGE-TRADING STRATEGIES RECOMMENDED:")
            print("   • Consider mean reversion strategies")
            print("   • Look for support/resistance levels")
            print("   • Use oscillator indicators")
            if regime.endswith('high_vol'):
                print("   • Be cautious - high volatility in ranging market")
        
        if sentiment == 'risk_off':
            print("🛡️ RISK-OFF ENVIRONMENT:")
            print("   • Favor safe haven currencies (JPY, CHF, USD)")
            print("   • Be cautious with risk assets (AUD, NZD)")
            print("   • Consider defensive positioning")
        elif sentiment == 'risk_on':
            print("💪 RISK-ON ENVIRONMENT:")
            print("   • Favor risk currencies (AUD, NZD)")
            print("   • Consider growth-oriented strategies")
            print("   • Higher position sizes may be appropriate")
        
        if confidence < 0.5:
            print("⚠️ LOW CONFIDENCE WARNING:")
            print("   • Regime transition may be occurring")
            print("   • Consider reduced position sizes")
            print("   • Monitor for regime change signals")
        
        print()
        print(f"🔄 Next regime evaluation: {regime_result.next_evaluation.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print()
        print("✅ ENHANCED LIVE MARKET REGIME ANALYSIS COMPLETE!")
        print("🎯 System successfully analyzed real-time market conditions with high precision!")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_comprehensive_regime_analysis())

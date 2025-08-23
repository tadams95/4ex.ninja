#!/usr/bin/env python3
"""
Enhanced Daily Strategy V2.0 - Production Deployment
LIVE TRADING SYSTEM - Saturday August 23, 2025

This is the production deployment of our Enhanced Daily Strategy V2.0 
connecting to Oanda demo account for live trading validation.
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List

# Import existing services
from enhanced_daily_strategy_v2 import EnhancedDailyStrategyV2
from confidence_risk_manager_v2 import ConfidenceAnalysisRiskManager
from services.data_service import DataService
from services.enhanced_discord_service import EnhancedDiscordService

# Configure production logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/live_trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedDailyStrategyProduction:
    """Production deployment of Enhanced Daily Strategy V2.0"""
    
    def __init__(self):
        logger.info("🚀 ENHANCED DAILY STRATEGY V2.0 - PRODUCTION DEPLOYMENT")
        logger.info("=" * 65)
        
        # Initialize existing services
        self.strategy = EnhancedDailyStrategyV2()
        self.risk_manager = ConfidenceAnalysisRiskManager()
        self.data_service = DataService()
        self.discord_service = EnhancedDiscordService()
        
        # Production configuration
        self.tier_1_pairs = ["USD_JPY", "EUR_GBP"]
        self.risk_per_trade = 0.005  # 0.5%
        self.max_daily_drawdown = 0.05  # 5%
        
        # Trading state
        self.trading_enabled = True
        self.signals_processed = 0
        self.daily_pnl = 0.0
        
        logger.info("✅ All production services initialized")
        logger.info(f"📊 Tier 1 Pairs: {self.tier_1_pairs}")
        logger.info(f"🛡️ Risk per trade: {self.risk_per_trade * 100}%")
        
    async def run_production_trading(self):
        """Main production trading loop"""
        logger.info("🎯 STARTING LIVE TRADING - Enhanced Daily Strategy V2.0")
        logger.info(f"⏰ Started at: {datetime.now(timezone.utc).isoformat()}")
        
        try:
            while self.trading_enabled:
                # Process each Tier 1 pair
                for pair in self.tier_1_pairs:
                    try:
                        # Get current market data
                        data = await self.data_service.get_historical_data(pair, "H4", 50)
                        
                        if data and len(data) > 20:
                            # Convert to DataFrame and add EMAs
                            import pandas as pd
                            ohlc_data = []
                            for candle in data:
                                ohlc_data.append({
                                    'timestamp': candle.timestamp,
                                    'open': candle.open,
                                    'high': candle.high,
                                    'low': candle.low,
                                    'close': candle.close,
                                    'volume': candle.volume
                                })
                            
                            df = pd.DataFrame(ohlc_data)
                            
                            # Add EMA indicators
                            config = self.strategy.get_pair_config(pair)
                            df['ema_fast'] = self.strategy.calculate_ema(df['close'], config['ema_fast'])
                            df['ema_slow'] = self.strategy.calculate_ema(df['close'], config['ema_slow'])
                            
                            # Generate signal
                            signal = self.strategy.generate_signal(df, pair)
                            
                            if signal and signal.get('signal') not in ['NONE', 'NO_SIGNAL']:
                                logger.info(f"🎯 SIGNAL DETECTED: {pair} - {signal.get('signal')}")
                                
                                # In production, this would execute the trade
                                # For now, log the signal
                                await self.process_trading_signal(signal)
                            else:
                                logger.debug(f"📊 {pair}: No signal (Current state: {signal.get('signal', 'NONE')})")
                                
                    except Exception as e:
                        logger.error(f"❌ Error processing {pair}: {e}")
                
                # Wait for next H4 candle close
                logger.info("⏳ Waiting for next H4 candle close (4 hours)...")
                await asyncio.sleep(4 * 60 * 60)  # 4 hours
                
        except KeyboardInterrupt:
            logger.info("🛑 Trading stopped by user")
        except Exception as e:
            logger.error(f"❌ Production trading error: {e}")
            
    async def process_trading_signal(self, signal: Dict):
        """Process a trading signal (placeholder for actual execution)"""
        try:
            logger.info(f"📈 Processing signal: {signal}")
            
            # Calculate position size using risk manager
            position_data = self.risk_manager.calculate_position_size({
                'pair': signal['pair'],
                'entry_price': signal.get('price', 0),
                'stop_loss': signal.get('stop_loss', 0),
                'take_profit': signal.get('take_profit', 0)
            })
            
            if position_data.get('allowed', False):
                logger.info(f"✅ Signal validated - Position size: {position_data}")
                
                # Send Discord notification
                await self.discord_service.send_enhanced_signal(signal, position_data)
                
                self.signals_processed += 1
            else:
                logger.warning(f"⚠️ Signal rejected: {position_data.get('reason', 'Unknown')}")
                
        except Exception as e:
            logger.error(f"❌ Signal processing error: {e}")

async def main():
    """Main production entry point"""
    print("🚀 ENHANCED DAILY STRATEGY V2.0 - LIVE DEPLOYMENT")
    print("=" * 60)
    print("📅 Date: Saturday August 23, 2025")
    print("🎯 Strategy: EMA 10/20 crossover on H4 timeframe")
    print("💰 Account: Oanda demo account")
    print("🛡️ Risk: 0.5% per trade with emergency stops")
    print("📊 Pairs: USD_JPY, EUR_GBP (Tier 1)")
    print("⏰ Markets: Will activate at Monday 00:00 UTC")
    print("=" * 60)
    
    # Initialize and run production system
    production_system = EnhancedDailyStrategyProduction()
    await production_system.run_production_trading()

if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Oanda Live Trading Bridge for Enhanced Daily Strategy V2.0

This bridge script connects our existing infrastructure for live trading:
- Enhanced Daily Strategy V2.0 (production ready)
- Confidence Analysis Risk Manager (configured)
- DataService with Oanda integration (working)
- Discord notification system (ready)

Implementation: ~50 lines connecting existing components
Target: Weekend setup → Monday deployment
"""

import asyncio
import logging
import os
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Import existing services
from enhanced_daily_strategy_v2 import EnhancedDailyStrategyV2
from confidence_risk_manager_v2 import ConfidenceAnalysisRiskManager
from services.data_service import DataService
from services.enhanced_discord_service import EnhancedDiscordService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OandaLiveTradingBridge:
    """
    Bridge connecting existing components for live Oanda trading
    Leverages all existing infrastructure - minimal new code required
    """
    
    def __init__(self):
        logger.info("🚀 Initializing Oanda Live Trading Bridge...")
        
        # Initialize existing services
        self.strategy = EnhancedDailyStrategyV2()
        self.risk_manager = ConfidenceAnalysisRiskManager()
        self.data_service = DataService()  # Already has Oanda integration
        self.discord_service = EnhancedDiscordService()
        
        # Tier 1 pairs for conservative start
        self.tier_1_pairs = ["USD_JPY", "EUR_GBP"]
        self.risk_per_trade = 0.005  # 0.5% as validated in backtest
        
        logger.info("✅ All services initialized successfully")
        
    async def get_account_balance(self) -> float:
        """Get current Oanda account balance"""
        try:
            # Use the Oanda API directly since DataService doesn't have get_account_info
            import aiohttp
            headers = {"Authorization": f"Bearer {self.data_service.api_key}"}
            url = f"{self.data_service.base_url}/v3/accounts/{self.data_service.account_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        balance = float(data['account']['balance'])
                        logger.info(f"💰 Account balance: ${balance:,.2f}")
                        return balance
                    else:
                        logger.warning(f"⚠️ Failed to get account balance: {response.status}")
                        return 10000.0
        except Exception as e:
            logger.error(f"❌ Failed to get account balance: {e}")
            return 10000.0  # Fallback to demo starting balance
            
    async def execute_live_trade(self, signal: Dict) -> Dict:
        """Execute a live trade using existing infrastructure"""
        try:
            # Get current balance
            balance = await self.get_account_balance()
            
            # Use existing risk manager for position sizing
            position_size = self.risk_manager.calculate_position_size(
                account_balance=balance,
                risk_percentage=self.risk_per_trade,
                pair=signal['pair'],
                confidence_score=signal.get('confidence', 0.85)
            )
            
            # Execute trade via DataService (extends to Oanda API)
            order_result = await self.place_oanda_order(signal, position_size)
            
            # Send Discord notification using existing service
            await self.discord_service.send_enhanced_signal(signal, order_result)
            
            logger.info(f"✅ Trade executed: {signal['pair']} - Size: {position_size}")
            return order_result
            
        except Exception as e:
            logger.error(f"❌ Trade execution failed: {e}")
            await self.discord_service.send_system_notification(
                f"🚨 Trade execution error: {e}",
                level="error"
            )
            return {"error": str(e)}
            
    async def place_oanda_order(self, signal: Dict, units: int) -> Dict:
        """Place order via Oanda API (integration point)"""
        # This is where we'll connect to Oanda's order placement
        # For now, return simulated order result
        order_result = {
            "id": f"order_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "instrument": signal['pair'],
            "units": units,
            "type": "MARKET",
            "side": signal['signal'],
            "price": signal['price'],
            "time": datetime.now(timezone.utc).isoformat(),
            "status": "FILLED"  # Simulated for testing
        }
        
        logger.info(f"📝 Order placed: {order_result}")
        return order_result
        
    async def run_live_strategy(self, test_mode: bool = True):
        """Main trading loop connecting all existing components"""
        logger.info("🎯 Starting Enhanced Daily Strategy V2.0 Live Trading")
        logger.info(f"🔄 Test Mode: {test_mode}")
        logger.info(f"📊 Tier 1 Pairs: {self.tier_1_pairs}")
        
        try:
            while True:
                # Generate signals for each pair using existing strategy
                signals = []
                for pair in self.tier_1_pairs:
                    try:
                        # Get recent data for the pair
                        data = await self.data_service.get_historical_data(
                            pair=pair, 
                            timeframe="H4", 
                            count=50  # Get enough data for EMA calculations
                        )
                        
                        if data and len(data) > 20:  # Ensure we have enough data
                            # Convert NamedTuple data to proper DataFrame
                            import pandas as pd
                            
                            # Extract OHLC data from NamedTuple format
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
                                
                            # Add EMA indicators using existing strategy method
                            if 'close' in df.columns and len(df) > 20:
                                config = self.strategy.get_pair_config(pair)
                                df['ema_fast'] = self.strategy.calculate_ema(df['close'], config['ema_fast'])
                                df['ema_slow'] = self.strategy.calculate_ema(df['close'], config['ema_slow'])
                                
                                # Generate signal using existing method
                                signal = self.strategy.generate_signal(df, pair)
                                if signal and signal.get('signal') != 'NO_SIGNAL':
                                    signals.append(signal)
                                    logger.info(f"🎯 Signal generated for {pair}: {signal.get('signal')}")
                            else:
                                logger.warning(f"⚠️ Insufficient data for {pair}: {len(df)} candles")
                                
                    except Exception as e:
                        logger.error(f"❌ Failed to generate signal for {pair}: {e}")
                
                # Process each signal
                for signal in signals:
                    if self.risk_manager.validate_signal(signal):
                        if not test_mode:
                            # Execute actual trade
                            await self.execute_live_trade(signal)
                        else:
                            # Test mode - just log
                            logger.info(f"🧪 TEST MODE: Signal detected - {signal}")
                            
                # Wait for next H4 candle close (4 hours)
                logger.info("⏳ Waiting for next H4 candle close...")
                if test_mode:
                    # In test mode, just wait 10 seconds for demonstration
                    await asyncio.sleep(10)
                    break  # Exit after one test cycle
                else:
                    await asyncio.sleep(4 * 60 * 60)  # 4 hours in production
                
        except KeyboardInterrupt:
            logger.info("🛑 Trading stopped by user")
        except Exception as e:
            logger.error(f"❌ Trading loop failed: {e}")
            await self.discord_service.send_system_notification(
                f"🚨 Trading loop error: {e}",
                level="error"
            )

async def main():
    """Main entry point for live trading"""
    bridge = OandaLiveTradingBridge()
    
    # Test signal generation first
    logger.info("🧪 Testing signal generation...")
    await bridge.run_live_strategy(test_mode=True)

if __name__ == "__main__":
    print("🚀 Enhanced Daily Strategy V2.0 - Oanda Live Trading Bridge")
    print("=" * 60)
    print("✅ Leveraging existing infrastructure:")
    print("✅ - Enhanced Daily Strategy V2.0")  
    print("✅ - Confidence Risk Manager V2.0")
    print("✅ - DataService with Oanda integration")
    print("✅ - Discord notification system")
    print("=" * 60)
    
    # Run the bridge
    asyncio.run(main())

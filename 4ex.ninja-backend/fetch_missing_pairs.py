#!/usr/bin/env python3
"""
Fetch Missing JPY and CHF Pairs
Specialized script to fetch USD_CHF, EUR_JPY, and AUD_JPY data from OANDA
"""

import asyncio
import json
import logging
import os
import ssl
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any
import aiohttp
import certifi
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingPairsFetcher:
    """Specialized fetcher for missing currency pairs"""
    
    def __init__(self):
        # OANDA Configuration
        self.api_key = os.getenv("OANDA_API_KEY")
        self.account_id = os.getenv("OANDA_ACCOUNT_ID")
        
        # Use practice environment for data fetching
        self.base_url = "https://api-fxpractice.oanda.com"
        
        # Output directory
        self.output_dir = "backtest_data/historical_data"
        
        # Missing pairs with their OANDA instrument names
        self.missing_pairs = {
            "USD_CHF": "USD_CHF",  # US Dollar / Swiss Franc
            "EUR_JPY": "EUR_JPY",  # Euro / Japanese Yen  
            "AUD_JPY": "AUD_JPY",  # Australian Dollar / Japanese Yen
        }
        
        # Data parameters
        self.backtest_years = 5
        self.max_candles_per_request = 4999  # OANDA API limit
        
        # SSL context for requests
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        logger.info(f"🚀 MissingPairsFetcher initialized")
        logger.info(f"📊 Target pairs: {list(self.missing_pairs.keys())}")
        logger.info(f"🕐 Data period: {self.backtest_years} years")
    
    async def fetch_pair_data_chunked(self, pair: str, oanda_instrument: str) -> Dict[str, Any]:
        """Fetch historical data for a single currency pair using chunked requests"""
        try:
            logger.info(f"📊 Fetching {self.backtest_years} years of H4 data for {pair}...")
            
            # Calculate date range
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=self.backtest_years * 365)
            
            # Calculate expected periods (H4 = 6 candles per day)
            expected_periods = self.backtest_years * 365 * 6
            
            logger.info(f"   Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            logger.info(f"   Expected candles: ~{expected_periods}")
            
            # Fetch data in chunks
            all_candles = []
            current_to_date = end_date
            chunk_count = 0
            
            while len(all_candles) < expected_periods and chunk_count < 100:  # Safety limit
                chunk_count += 1
                logger.info(f"   📦 Fetching chunk {chunk_count}...")
                
                # Fetch chunk
                chunk_data = await self._fetch_chunk(
                    oanda_instrument, 
                    to_time=current_to_date,
                    count=self.max_candles_per_request
                )
                
                if not chunk_data:
                    logger.warning(f"   ⚠️ No data in chunk {chunk_count}, stopping")
                    break
                
                # Add to collection (reverse to get chronological order)
                all_candles = chunk_data + all_candles
                
                logger.info(f"   ✅ Chunk {chunk_count}: {len(chunk_data)} candles")
                logger.info(f"   📊 Total collected: {len(all_candles)} candles")
                
                # Update current_to_date to the earliest timestamp from this chunk
                if chunk_data:
                    earliest_candle = chunk_data[0]
                    current_to_date = datetime.fromisoformat(earliest_candle["timestamp"].replace('Z', '+00:00'))
                    
                    # Stop if we've reached our target start date
                    if current_to_date <= start_date:
                        logger.info(f"   🎯 Reached target start date, stopping")
                        break
                
                # Small delay between requests
                await asyncio.sleep(0.5)
            
            # Filter to actual date range and sort chronologically
            filtered_candles = []
            for candle in all_candles:
                candle_time = datetime.fromisoformat(candle["timestamp"].replace('Z', '+00:00'))
                if start_date <= candle_time <= end_date:
                    filtered_candles.append(candle)
            
            # Sort chronologically (oldest first)
            filtered_candles.sort(key=lambda c: c["timestamp"])
            
            logger.info(f"✅ {pair}: Fetched {len(filtered_candles)} H4 candles ({chunk_count} chunks)")
            
            return {
                "pair": pair,
                "timeframe": "H4",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "candle_count": len(filtered_candles),
                "data": filtered_candles,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"❌ Error fetching {pair}: {str(e)}")
            return {
                "pair": pair,
                "error": str(e),
                "success": False
            }
    
    async def _fetch_chunk(self, instrument: str, to_time: datetime, count: int) -> List[Dict]:
        """Fetch a single chunk of candles from OANDA API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            params = {
                "granularity": "H4",
                "count": count,
                "to": to_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
            
            url = f"{self.base_url}/v3/instruments/{instrument}/candles"
            
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status != 200:
                        logger.error(f"❌ OANDA API error: {response.status}")
                        return []
                    
                    data = await response.json()
                    
                    if "candles" not in data:
                        logger.error(f"❌ No candles in response")
                        return []
                    
                    # Convert OANDA format to our format
                    candles = []
                    for candle in data["candles"]:
                        if candle.get("complete", False):  # Only complete candles
                            mid_data = candle.get("mid", {})
                            candles.append({
                                "timestamp": candle["time"],
                                "open": float(mid_data.get("o", 0)),
                                "high": float(mid_data.get("h", 0)),
                                "low": float(mid_data.get("l", 0)),
                                "close": float(mid_data.get("c", 0)),
                                "volume": int(candle.get("volume", 0))
                            })
                    
                    return candles
                    
        except Exception as e:
            logger.error(f"❌ Error in chunk fetch: {str(e)}")
            return []
    
    async def save_pair_data(self, pair_data: Dict[str, Any]):
        """Save pair data to JSON file"""
        try:
            if not pair_data.get("success", False):
                logger.error(f"❌ Cannot save failed data for {pair_data.get('pair', 'unknown')}")
                return
            
            pair = pair_data["pair"]
            filename = f"{pair}_H4_5Y.json"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(pair_data, f, indent=2)
            
            logger.info(f"💾 Saved {pair} data to {filename}")
            
        except Exception as e:
            logger.error(f"❌ Error saving data: {str(e)}")
    
    async def fetch_all_missing_pairs(self) -> Dict[str, Any]:
        """Fetch all missing pairs and generate summary"""
        logger.info(f"🚀 Starting fetch for {len(self.missing_pairs)} missing pairs...")
        
        results = {}
        successful_pairs = []
        failed_pairs = []
        
        for pair, oanda_instrument in self.missing_pairs.items():
            logger.info(f"\n📊 [{len(results)+1}/{len(self.missing_pairs)}] Processing {pair}...")
            
            # Fetch data
            pair_data = await self.fetch_pair_data_chunked(pair, oanda_instrument)
            results[pair] = pair_data
            
            # Save successful data
            if pair_data.get("success", False):
                await self.save_pair_data(pair_data)
                successful_pairs.append(pair)
            else:
                failed_pairs.append(pair)
            
            # Delay between pairs
            await asyncio.sleep(1)
        
        # Generate summary
        summary = {
            "fetch_date": datetime.now(timezone.utc).isoformat(),
            "total_pairs": len(self.missing_pairs),
            "successful_pairs": len(successful_pairs),
            "failed_pairs": len(failed_pairs),
            "success_rate": len(successful_pairs) / len(self.missing_pairs) * 100,
            "results": results
        }
        
        # Save summary
        summary_file = os.path.join(self.output_dir, "missing_pairs_fetch_summary.json")
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Print results
        print("\n" + "="*60)
        print("📊 MISSING PAIRS FETCH SUMMARY")
        print("="*60)
        print(f"Target Pairs: {len(self.missing_pairs)}")
        print(f"Successful: {len(successful_pairs)}")
        print(f"Failed: {len(failed_pairs)}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        
        if successful_pairs:
            print(f"\n✅ Successfully fetched:")
            for pair in successful_pairs:
                candle_count = results[pair].get("candle_count", 0)
                print(f"   {pair}: {candle_count:,} candles")
        
        if failed_pairs:
            print(f"\n❌ Failed to fetch:")
            for pair in failed_pairs:
                error = results[pair].get("error", "Unknown error")
                print(f"   {pair}: {error}")
        
        print("="*60)
        
        return summary


async def main():
    """Main execution function"""
    fetcher = MissingPairsFetcher()
    
    try:
        # Verify API credentials
        if not fetcher.api_key or not fetcher.account_id:
            logger.error("❌ Missing OANDA API credentials in .env file")
            return
        
        # Fetch all missing pairs
        summary = await fetcher.fetch_all_missing_pairs()
        
        # Success message
        if summary["successful_pairs"] > 0:
            logger.info(f"\n🎉 Successfully fetched {summary['successful_pairs']} missing pairs!")
            logger.info(f"📁 Data saved to: {fetcher.output_dir}/")
            logger.info(f"📊 Ready for backtesting with JPY pairs and USD_CHF!")
        else:
            logger.error(f"\n😞 Failed to fetch any missing pairs")
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())

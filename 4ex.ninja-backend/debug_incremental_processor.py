#!/usr/bin/env python3
"""
Debug script to test incremental processor behavior and identify why it's failing.
"""

import asyncio
import logging
import os
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Add src to path for imports
import sys

sys.path.append("/Users/tyrelle/Desktop/4ex.ninja/4ex.ninja-backend/src")

# Import services
from infrastructure.cache.redis_cache_service import get_cache_service
from infrastructure.services.incremental_signal_processor import (
    create_incremental_processor,
)

# MongoDB connection
MONGO_CONNECTION_STRING = "mongodb+srv://tyrelle:dcvsniTYFG9ojCgn@cluster0.6h6fdf2.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"


async def debug_incremental_processor():
    """Debug the incremental processor behavior."""

    print("🔍 Debugging Incremental Signal Processor")
    print("=" * 50)

    # Connect to database
    client = MongoClient(
        MONGO_CONNECTION_STRING, tls=True, tlsAllowInvalidCertificates=True
    )
    price_db = client["streamed_prices"]
    collection = price_db["EUR_USD_H4"]

    print(f"📊 Collection: {collection.name}")
    print(f"📈 Total documents: {collection.count_documents({})}")

    # Get latest candle
    latest_docs = list(collection.find().sort("time", -1).limit(1))
    if latest_docs:
        latest_time = latest_docs[0]["time"]
        print(f"🕒 Latest candle: {latest_time}")

    # Test cache service
    print("\n🔧 Testing Redis Cache Service...")
    try:
        cache_service = await get_cache_service()
        print("✅ Cache service connected")

        # Check for existing cache
        last_processed = await cache_service.get_last_processed_time("EUR_USD", "H4")
        print(f"📝 Last processed time: {last_processed}")

        # Check MA cache
        ma_state = await cache_service.get_ma_cache("EUR_USD", "H4", 21)
        print(f"📈 MA cache for period 21: {ma_state is not None}")

        if ma_state:
            print(
                f"   Cache entries: {len(ma_state) if isinstance(ma_state, list) else 'dict'}"
            )

    except Exception as e:
        print(f"❌ Cache service error: {e}")
        return

    # Test incremental processor
    print("\n🚀 Testing Incremental Processor...")
    try:
        processor = await create_incremental_processor(
            pair="EUR_USD",
            timeframe="H4",
            slow_ma=21,
            fast_ma=9,
            atr_period=14,
            collection=collection,
        )
        print("✅ Incremental processor created")

        # Test data fetch
        print("\n📊 Testing incremental data fetch...")
        df, is_incremental = await processor.get_incremental_data(limit_new_candles=10)

        print(f"📈 Data returned: {len(df)} rows")
        print(f"🔄 Is incremental: {is_incremental}")

        if not df.empty:
            print(f"⏰ Data time range: {df['time'].min()} to {df['time'].max()}")
            print(f"📊 Sample data: {df.head(2).to_dict('records')}")
        else:
            print("❌ No data returned")

        # Test full processing
        print("\n🎯 Testing process_signals_optimized...")
        result_df = await processor.process_signals_optimized(min_candles_required=20)

        print(f"📈 Result rows: {len(result_df)}")
        if not result_df.empty:
            print(f"📊 Columns: {list(result_df.columns)}")
            print(
                f"⏰ Result time range: {result_df['time'].min()} to {result_df['time'].max()}"
            )
            if "slow_ma" in result_df.columns:
                ma_count = result_df["slow_ma"].notna().sum()
                print(f"📈 Rows with slow_ma: {ma_count}/{len(result_df)}")
        else:
            print("❌ process_signals_optimized returned empty DataFrame")

        # Get performance stats
        stats = await processor.get_performance_stats()
        print(f"\n📈 Performance Stats:")
        for key, value in stats.items():
            print(f"   {key}: {value}")

    except Exception as e:
        print(f"❌ Incremental processor error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_incremental_processor())

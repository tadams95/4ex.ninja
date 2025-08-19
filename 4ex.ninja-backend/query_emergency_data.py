#!/usr/bin/env python3
"""
Emergency Risk Management Dashboard Query

This script demonstrates how to query the emergency risk management data
that is now persisted to MongoDB for historical analysis.
"""

import sys
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient

# Add the src directory to path
sys.path.append("/Users/tyrelle/Desktop/4ex.ninja/4ex.ninja-backend/src")

from config.settings import MONGO_CONNECTION_STRING

# Database connection
client = MongoClient(
    MONGO_CONNECTION_STRING, tls=True, tlsAllowInvalidCertificates=True
)
risk_db = client["risk_management"]


def query_emergency_events(hours_back=24):
    """Query emergency level escalation events"""
    print(f"\n🚨 Emergency Events (Last {hours_back} hours):")
    print("=" * 60)

    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)

    events = (
        risk_db["emergency_events"]
        .find({"saved_at": {"$gte": cutoff_time}})
        .sort("saved_at", -1)
    )

    count = 0
    for event in events:
        count += 1
        timestamp = event.get("timestamp", "Unknown")[:19]  # YYYY-MM-DDTHH:MM:SS
        prev_level = event.get("previous_level", "Unknown")
        new_level = event.get("new_level", "Unknown")
        drawdown = event.get("drawdown", 0) * 100
        portfolio_value = event.get("portfolio_value", 0)

        print(f"⚡ {timestamp} | {prev_level} → {new_level}")
        print(f"   Portfolio: ${portfolio_value:,.2f} | Drawdown: {drawdown:.2f}%")
        print(f"   Action: {event.get('protocol', {}).get('description', 'Unknown')}")
        print()

    if count == 0:
        print("   No emergency events found in the specified timeframe.")
    else:
        print(f"Total events: {count}")


def query_stress_events(hours_back=24):
    """Query stress event detections"""
    print(f"\n📈 Stress Events (Last {hours_back} hours):")
    print("=" * 60)

    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)

    events = (
        risk_db["stress_events"]
        .find({"saved_at": {"$gte": cutoff_time}})
        .sort("saved_at", -1)
    )

    count = 0
    for event in events:
        count += 1
        timestamp = event.get("detected_at", "Unknown")[:19]
        event_type = event.get("event_type", "Unknown")
        severity = event.get("severity", 0)
        pairs = ", ".join(event.get("affected_pairs", []))
        current_vol = event.get("current_volatility", 0)
        threshold_vol = event.get("threshold_volatility", 0)

        print(f"⚠️  {timestamp} | {event_type.upper()}")
        print(f"   Severity: {severity:.2f}x | Pairs: {pairs}")
        print(f"   Volatility: {current_vol:.4f} (threshold: {threshold_vol:.4f})")
        print(f"   Action: {event.get('recommended_action', 'Unknown')}")
        print()

    if count == 0:
        print("   No stress events found in the specified timeframe.")
    else:
        print(f"Total events: {count}")


def query_portfolio_metrics(hours_back=24):
    """Query portfolio risk metrics"""
    print(f"\n💰 Portfolio Risk Metrics (Last {hours_back} hours):")
    print("=" * 60)

    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)

    metrics = (
        risk_db["portfolio_metrics"]
        .find({"timestamp": {"$gte": cutoff_time}})
        .sort("timestamp", -1)
        .limit(10)
    )  # Last 10 records

    count = 0
    for metric in metrics:
        count += 1
        timestamp = (
            metric.get("timestamp", "Unknown").strftime("%Y-%m-%d %H:%M:%S")
            if hasattr(metric.get("timestamp"), "strftime")
            else str(metric.get("timestamp", "Unknown"))[:19]
        )
        portfolio_value = metric.get("portfolio_value", 0)
        drawdown = metric.get("drawdown_percentage", 0) * 100
        emergency_level = metric.get("emergency_level", "Unknown")
        multiplier = metric.get("position_size_multiplier", 1.0) * 100
        stress_count = metric.get("active_stress_events_count", 0)

        print(f"📊 {timestamp} | {emergency_level}")
        print(f"   Portfolio: ${portfolio_value:,.2f} | Drawdown: {drawdown:.2f}%")
        print(
            f"   Position Multiplier: {multiplier:.0f}% | Stress Events: {stress_count}"
        )
        print()

    if count == 0:
        print("   No portfolio metrics found in the specified timeframe.")
    else:
        print(f"Total records: {count}")


def query_summary_stats():
    """Query summary statistics"""
    print(f"\n📈 Summary Statistics:")
    print("=" * 60)

    # Count by collection
    emergency_count = risk_db["emergency_events"].count_documents({})
    stress_count = risk_db["stress_events"].count_documents({})
    metrics_count = risk_db["portfolio_metrics"].count_documents({})

    print(f"Total Emergency Events: {emergency_count}")
    print(f"Total Stress Events: {stress_count}")
    print(f"Total Portfolio Metrics: {metrics_count}")

    # Latest emergency level
    latest_metric = risk_db["portfolio_metrics"].find().sort("timestamp", -1).limit(1)
    for metric in latest_metric:
        print(f"Current Emergency Level: {metric.get('emergency_level', 'Unknown')}")
        print(f"Latest Portfolio Value: ${metric.get('portfolio_value', 0):,.2f}")
        print(f"Latest Drawdown: {metric.get('drawdown_percentage', 0) * 100:.2f}%")
        break


if __name__ == "__main__":
    print("🎯 Emergency Risk Management Dashboard Query")
    print("=" * 60)

    try:
        query_summary_stats()
        query_emergency_events(hours_back=24)
        query_stress_events(hours_back=24)
        query_portfolio_metrics(hours_back=24)

        print("\n✅ Query completed successfully!")
        print("\n💡 Usage Examples:")
        print("   - Monitor emergency escalations in real-time")
        print("   - Analyze stress event patterns and triggers")
        print("   - Track portfolio risk metrics over time")
        print("   - Generate historical risk reports")

    except Exception as e:
        print(f"❌ Query failed: {e}")
        sys.exit(1)

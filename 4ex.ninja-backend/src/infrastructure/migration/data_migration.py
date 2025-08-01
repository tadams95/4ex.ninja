"""
Data migration script for Day 5: Integration & Migration

This script migrates existing data to work with the new repository pattern
and ensures data consistency across the system.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import pymongo
from pymongo import MongoClient
from decimal import Decimal

from ...core.entities.signal import Signal, SignalType, SignalStatus, CrossoverType
from ...core.entities.market_data import MarketData, Candle, Granularity
from ...infrastructure.configuration.repository_config import (
    RepositoryConfiguration,
    RepositoryServiceProvider,
)
from ...infrastructure.database.connection import DatabaseManager

# Default connection string (should be replaced with actual config)
MONGO_CONNECTION_STRING = "mongodb://localhost:27017/"

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataMigrationService:
    """
    Service for migrating existing data to the new repository pattern.
    """

    def __init__(self):
        """Initialize the migration service."""
        self.repository_provider: Optional[RepositoryServiceProvider] = None
        self.legacy_client: Optional[MongoClient] = None

    async def initialize(self) -> None:
        """Initialize repositories and legacy database connections."""
        try:
            # Create configured DI container
            container = await RepositoryConfiguration.create_configured_container()
            self.repository_provider = RepositoryServiceProvider(container)

            # Initialize legacy MongoDB client
            self.legacy_client = MongoClient(
                MONGO_CONNECTION_STRING, tls=True, tlsAllowInvalidCertificates=True
            )

            logger.info("Migration service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize migration service: {e}")
            raise

    async def migrate_all_data(self) -> Dict[str, int]:
        """
        Migrate all existing data to the new repository pattern.

        Returns:
            Dictionary with migration counts
        """
        results = {"signals_migrated": 0, "market_data_migrated": 0, "errors": 0}

        try:
            logger.info("Starting data migration...")

            # Migrate signals
            signals_count = await self.migrate_signals()
            results["signals_migrated"] = signals_count

            # Migrate market data
            market_data_count = await self.migrate_market_data()
            results["market_data_migrated"] = market_data_count

            logger.info(f"Migration completed: {results}")

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            results["errors"] += 1

        return results

    async def migrate_signals(self) -> int:
        """
        Migrate existing signals from legacy format to new Signal entities.

        Returns:
            Number of signals migrated
        """
        try:
            logger.info("Starting signal migration...")

            if not self.legacy_client or not self.repository_provider:
                logger.error("Migration service not properly initialized")
                return 0

            # Get legacy signals collection
            legacy_signals_db = self.legacy_client["signals"]
            legacy_trades_collection = legacy_signals_db["trades"]

            # Get signal repository
            signal_repository = await self.repository_provider.get_signal_repository()

            # Fetch all legacy signals
            legacy_signals = list(legacy_trades_collection.find({}))
            logger.info(f"Found {len(legacy_signals)} legacy signals to migrate")

            migrated_count = 0

            for legacy_signal in legacy_signals:
                try:
                    # Convert legacy signal to Signal entity
                    signal = await self._convert_legacy_signal_to_entity(legacy_signal)

                    if signal:
                        # Check if signal already exists (avoid duplicates)
                        existing_signal = await signal_repository.get_by_id(
                            signal.signal_id
                        )

                        if not existing_signal:
                            # Store the migrated signal
                            stored_signal = await signal_repository.create(signal)
                            if stored_signal:
                                migrated_count += 1
                                if migrated_count % 100 == 0:
                                    logger.info(f"Migrated {migrated_count} signals...")
                            else:
                                logger.warning(
                                    f"Failed to store migrated signal: {signal.signal_id}"
                                )
                        else:
                            logger.debug(
                                f"Signal already exists, skipping: {signal.signal_id}"
                            )

                except Exception as e:
                    logger.error(
                        f"Error migrating signal {legacy_signal.get('_id', 'unknown')}: {e}"
                    )
                    continue

            logger.info(f"Successfully migrated {migrated_count} signals")
            return migrated_count

        except Exception as e:
            logger.error(f"Signal migration failed: {e}")
            return 0

    async def migrate_market_data(self) -> int:
        """
        Migrate existing market data from legacy format to new MarketData entities.

        Returns:
            Number of market data records migrated
        """
        try:
            logger.info("Starting market data migration...")

            if not self.legacy_client or not self.repository_provider:
                logger.error("Migration service not properly initialized")
                return 0

            # Get legacy price database
            legacy_price_db = self.legacy_client["streamed_prices"]

            # Get market data repository
            market_data_repository = (
                await self.repository_provider.get_market_data_repository()
            )

            migrated_count = 0

            # Get all collections (each represents a pair/timeframe combination)
            collection_names = legacy_price_db.list_collection_names()
            logger.info(f"Found {len(collection_names)} collections to migrate")

            for collection_name in collection_names:
                try:
                    # Parse collection name to extract pair and timeframe
                    # Assume format like "EUR_USD_H4" or "EUR_USD_D"
                    parts = collection_name.split("_")
                    if len(parts) >= 3:
                        pair = f"{parts[0]}_{parts[1]}"
                        timeframe = "_".join(parts[2:])

                        # Migrate this collection
                        count = await self._migrate_collection_data(
                            legacy_price_db[collection_name],
                            pair,
                            timeframe,
                            market_data_repository,
                        )
                        migrated_count += count

                except Exception as e:
                    logger.error(f"Error migrating collection {collection_name}: {e}")
                    continue

            logger.info(f"Successfully migrated {migrated_count} market data records")
            return migrated_count

        except Exception as e:
            logger.error(f"Market data migration failed: {e}")
            return 0

    async def _convert_legacy_signal_to_entity(
        self, legacy_signal: Dict[str, Any]
    ) -> Optional[Signal]:
        """
        Convert legacy signal format to Signal entity.

        Args:
            legacy_signal: Legacy signal dictionary

        Returns:
            Signal entity or None if conversion fails
        """
        try:
            # Generate signal ID if not present
            signal_id = str(
                legacy_signal.get("_id", f"migrated_{int(datetime.now().timestamp())}")
            )

            # Extract required fields with defaults
            pair = legacy_signal.get("instrument", "UNKNOWN")
            timeframe = legacy_signal.get("timeframe", "UNKNOWN")

            # Determine signal type
            signal_value = legacy_signal.get("signal", 0)
            signal_type = SignalType.BUY if signal_value == 1 else SignalType.SELL

            # Determine crossover type (assume based on signal type if not present)
            crossover_type = (
                CrossoverType.BULLISH if signal_value == 1 else CrossoverType.BEARISH
            )

            # Extract prices with safety checks
            entry_price = Decimal(str(legacy_signal.get("close", 0)))
            current_price = (
                entry_price  # Use entry price as current for historical data
            )

            # Extract optional fields
            stop_loss = None
            if legacy_signal.get("stop_loss"):
                stop_loss = Decimal(str(legacy_signal["stop_loss"]))

            take_profit = None
            if legacy_signal.get("take_profit"):
                take_profit = Decimal(str(legacy_signal["take_profit"]))

            atr_value = None
            if legacy_signal.get("atr"):
                atr_value = Decimal(str(legacy_signal["atr"]))

            # Extract timestamp
            timestamp = legacy_signal.get("time")
            if not isinstance(timestamp, datetime):
                timestamp = datetime.now(timezone.utc)

            # Create Signal entity
            signal = Signal(
                signal_id=signal_id,
                pair=pair,
                timeframe=timeframe,
                signal_type=signal_type,
                crossover_type=crossover_type,
                entry_price=entry_price,
                current_price=current_price,
                fast_ma=int(legacy_signal.get("fast_ma", 10)),
                slow_ma=int(legacy_signal.get("slow_ma", 20)),
                timestamp=timestamp,
                stop_loss=stop_loss,
                take_profit=take_profit,
                atr_value=atr_value,
                risk_reward_ratio=legacy_signal.get("risk_reward_ratio"),
                strategy_name=legacy_signal.get("strategy_name", "MA_Crossover"),
                status=SignalStatus.FILLED,  # Historical signals are considered filled
            )

            return signal

        except Exception as e:
            logger.error(f"Error converting legacy signal: {e}")
            return None

    async def _migrate_collection_data(
        self, collection, pair: str, timeframe: str, market_data_repository
    ) -> int:
        """
        Migrate data from a single collection to MarketData entities.

        Args:
            collection: Legacy MongoDB collection
            pair: Currency pair
            timeframe: Timeframe
            market_data_repository: Market data repository

        Returns:
            Number of records migrated
        """
        try:
            # Fetch all documents from the collection
            documents = list(
                collection.find({}).sort("time", 1).limit(1000)
            )  # Limit for performance

            if not documents:
                return 0

            # Convert to Candle entities
            candles = []
            for doc in documents:
                try:
                    candle = Candle(
                        time=doc.get("time", datetime.now(timezone.utc)),
                        open=Decimal(str(doc.get("open", 0))),
                        high=Decimal(str(doc.get("high", 0))),
                        low=Decimal(str(doc.get("low", 0))),
                        close=Decimal(str(doc.get("close", 0))),
                        volume=int(doc.get("volume", 0)),
                        complete=doc.get("complete", True),
                    )
                    candles.append(candle)
                except Exception as e:
                    logger.warning(
                        f"Error converting candle for {pair} {timeframe}: {e}"
                    )
                    continue

            if not candles:
                return 0

            # Map timeframe to Granularity enum
            try:
                granularity = Granularity(timeframe)
            except ValueError:
                # Default to H4 if timeframe not recognized
                granularity = Granularity.H4
                logger.warning(f"Unknown timeframe {timeframe}, defaulting to H4")

            # Create MarketData entity
            market_data = MarketData(
                instrument=pair,
                granularity=granularity,
                candles=candles,
                last_updated=datetime.now(timezone.utc),
                source="LEGACY_MIGRATION",
            )

            # Store the market data
            stored_data = await market_data_repository.create(market_data)

            if stored_data:
                logger.info(f"Migrated {len(candles)} candles for {pair} {timeframe}")
                return 1  # Return 1 MarketData record created
            else:
                logger.warning(f"Failed to store market data for {pair} {timeframe}")
                return 0

        except Exception as e:
            logger.error(f"Error migrating collection data for {pair} {timeframe}: {e}")
            return 0

    async def cleanup(self) -> None:
        """Clean up resources."""
        try:
            if self.legacy_client:
                self.legacy_client.close()
            logger.info("Migration service cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


async def run_migration():
    """
    Main function to run the data migration.
    """
    migration_service = DataMigrationService()

    try:
        # Initialize the migration service
        await migration_service.initialize()

        # Run the migration
        results = await migration_service.migrate_all_data()

        print("\n" + "=" * 50)
        print("DATA MIGRATION RESULTS")
        print("=" * 50)
        print(f"Signals migrated: {results['signals_migrated']}")
        print(f"Market data migrated: {results['market_data_migrated']}")
        print(f"Errors encountered: {results['errors']}")
        print("=" * 50)

        if results["errors"] == 0:
            print("✅ Migration completed successfully!")
        else:
            print("⚠️  Migration completed with errors. Check logs for details.")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        logger.error(f"Migration failed: {e}")

    finally:
        # Clean up
        await migration_service.cleanup()


if __name__ == "__main__":
    """Run migration when script is executed directly."""
    asyncio.run(run_migration())

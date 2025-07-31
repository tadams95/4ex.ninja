import pandas as pd
from config.settings import MONGO_CONNECTION_STRING
from pymongo import MongoClient
import numpy as np
import matplotlib.pyplot as plt
import datetime
from typing import Dict, Optional, Tuple
from datetime import datetime, timezone
from decimal import Decimal
import asyncio
import logging
from datetime import datetime, timezone, timedelta

client = MongoClient(
    MONGO_CONNECTION_STRING,
    tls=True,
    tlsAllowInvalidCertificates=True,  # For development only
    # tlsCAFile='/Users/tyrelle/Desktop/4ex.ninja/4ex.ninja/config/global-bundle.pem'
)


db = client["streamed_prices"]
collection = db["EUR_USD_H4"]

collection_name = "EUR_USD_H4"

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class MovingAverageCrossStrategy_EUR_USD_H4:
    def __init__(
        self,
        slow_ma: int = 140,  # Changed from 160
        fast_ma: int = 40,   # Changed from 50
        atr_period: int = 14,
        sl_atr_multiplier: float = 1.5,
        tp_atr_multiplier: float = 2.0,
        min_atr_value: float = 0.0003,  # Minimum ATR value to consider a signal valid
        min_rr_ratio: float = 1.5,  # Minimum risk:reward ratio to consider a signal valid
    ):
        self.slow_ma = slow_ma
        self.fast_ma = fast_ma
        self.atr_period = atr_period
        self.sl_atr_multiplier = sl_atr_multiplier
        self.tp_atr_multiplier = tp_atr_multiplier
        self.min_atr_value = min_atr_value
        self.min_rr_ratio = min_rr_ratio

    def validate_signal(
        self, signal: int, atr: float, risk_reward_ratio: float
    ) -> bool:
        """Validate if a signal meets our minimum criteria"""
        try:
            if signal == 0:
                return False

            # Check if ATR is above minimum threshold
            if atr < self.min_atr_value:
                return False

            # Check if risk:reward ratio meets minimum requirement
            if risk_reward_ratio < self.min_rr_ratio:
                return False

            return True
        except Exception as e:
            print(f"Error validating signal: {str(e)}")
            return False

    def calculate_atr(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Average True Range"""
        try:
            high = df["high"]
            low = df["low"]
            close = df["close"].shift(1)

            tr1 = high - low
            tr2 = abs(high - close)
            tr3 = abs(low - close)

            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(window=self.atr_period).mean()

            return atr
        except Exception as e:
            print(f"Error calculating ATR: {str(e)}")
            return pd.Series(index=df.index)

    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate MA crossover signals with stop loss and take profit levels"""
        try:
            df = df.copy()

            # Calculate moving averages
            df["slow_ma"] = df["close"].rolling(window=self.slow_ma).mean()
            df["fast_ma"] = df["close"].rolling(window=self.fast_ma).mean()

            # Calculate ATR for dynamic stops
            df["atr"] = self.calculate_atr(df)

            # Initialize signal column
            df["signal"] = 0

            # Generate signals for MA crossover
            df.loc[
                (df["fast_ma"] > df["slow_ma"])
                & (df["fast_ma"].shift(1) <= df["slow_ma"].shift(1)),
                "signal",
            ] = 1  # Buy signal

            df.loc[
                (df["fast_ma"] < df["slow_ma"])
                & (df["fast_ma"].shift(1) >= df["slow_ma"].shift(1)),
                "signal",
            ] = -1  # Sell signal

            # Calculate stop loss and take profit for each signal
            df["stop_loss"] = pd.NA
            df["take_profit"] = pd.NA

            # For buy signals
            buy_signals = df["signal"] == 1
            df.loc[buy_signals, "stop_loss"] = df["close"] - (
                df["atr"] * self.sl_atr_multiplier
            )
            df.loc[buy_signals, "take_profit"] = df["close"] + (
                df["atr"] * self.tp_atr_multiplier
            )

            # For sell signals
            sell_signals = df["signal"] == -1
            df.loc[sell_signals, "stop_loss"] = df["close"] + (
                df["atr"] * self.sl_atr_multiplier
            )
            df.loc[sell_signals, "take_profit"] = df["close"] - (
                df["atr"] * self.tp_atr_multiplier
            )

            # Calculate risk:reward ratio for each trade
            df["risk_reward_ratio"] = pd.NA
            df.loc[buy_signals, "risk_reward_ratio"] = (
                df["take_profit"] - df["close"]
            ) / (df["close"] - df["stop_loss"])
            df.loc[sell_signals, "risk_reward_ratio"] = (
                df["close"] - df["take_profit"]
            ) / (df["stop_loss"] - df["close"])

            # Add signal validation
            for index, row in df.iterrows():
                if row["signal"] != 0:
                    is_valid = self.validate_signal(
                        row["signal"], row["atr"], row["risk_reward_ratio"]
                    )
                    if not is_valid:
                        df.loc[index, "signal"] = 0

            return df
        except Exception as e:
            print(f"Error calculating signals: {str(e)}")
            return df

    def generate_trade_dict(self, row: pd.Series) -> Optional[Dict]:
        """Generate trade dictionary for database storage"""
        try:
            # Use Decimal for precise financial calculations
            close_price = Decimal(str(row["close"]))
            stop_loss = Decimal(str(row["stop_loss"]))
            take_profit = Decimal(str(row["take_profit"]))

            # Calculate actual pip values for SL and TP
            sl_pips = abs(close_price - stop_loss) * Decimal("10000")
            tp_pips = abs(take_profit - close_price) * Decimal("10000")

            return {
                "time": row.name,
                "signal": int(row["signal"]),
                "entry_price": float(close_price),
                "stop_loss": float(stop_loss),
                "take_profit": float(take_profit),
                "sl_pips": float(sl_pips),
                "tp_pips": float(tp_pips),
                "atr": float(row["atr"]),
                "risk_reward_ratio": float(row["risk_reward_ratio"]),
                "slow_ma": float(row["slow_ma"]),
                "fast_ma": float(row["fast_ma"]),
                "created_at": datetime.now(timezone.utc),  # Use UTC time
            }
        except Exception as e:
            print(f"Error generating trade dictionary: {str(e)}")
            return None

    def get_latest_signal(self, df: pd.DataFrame) -> Optional[Dict]:
        """Get the latest signal if one exists"""
        try:
            signals_df = self.calculate_signals(df)
            signal_rows = signals_df[signals_df["signal"] != 0]

            if signal_rows.empty:
                return None

            latest_signal = signal_rows.iloc[-1]
            return self.generate_trade_dict(latest_signal)

        except Exception as e:
            print(f"Error getting latest signal: {str(e)}")
            return None

    async def monitor_prices(self):
        """Continuously monitor for new price data and generate signals"""
        while True:
            try:
                # Get the latest processed signal timestamp
                last_signal = db["EUR_USD_H4_signals"].find_one(sort=[("time", -1)])
                last_processed_time = last_signal["time"] if last_signal else None

                # Fetch new price data
                query = {}
                if last_processed_time:
                    query["time"] = {"$gt": last_processed_time}

                new_prices = list(collection.find(query).sort("time", 1))

                if new_prices:
                    # Process new data and generate signals
                    # ...existing processing code...
                    logging.info(
                        f"Processed daily candles at {datetime.now(timezone.utc)}"
                    )

                # Sleep until next daily candle (24 hours)
                await asyncio.sleep(86400)  # 24 hours in seconds

            except Exception as e:
                logging.error(f"Error in price monitoring: {str(e)}")
                # If error occurs, wait 15 minutes before retrying
                await asyncio.sleep(900)


if __name__ == "__main__":
    strategy = MovingAverageCrossStrategy_EUR_USD_H4()
    logging.info("Starting EUR/USD Daily strategy monitoring...")
    asyncio.run(strategy.monitor_prices())


# Fetch all documents and convert to DataFrame
df_EURUSD_H4 = pd.DataFrame(list(collection.find()))

# Set the time column as the index
df_EURUSD_H4.set_index("time", inplace=True)

# Extract OHLC values from the mid dictionary
df_EURUSD_H4["open"] = df_EURUSD_H4["mid"].apply(lambda x: x["o"])
df_EURUSD_H4["high"] = df_EURUSD_H4["mid"].apply(lambda x: x["h"])
df_EURUSD_H4["low"] = df_EURUSD_H4["mid"].apply(lambda x: x["l"])
df_EURUSD_H4["close"] = df_EURUSD_H4["mid"].apply(lambda x: x["c"])

# Drop unnecessary columns and reorder
df_EURUSD_H4 = df_EURUSD_H4[["open", "high", "low", "close"]]


def identify_multiple_ma_crossovers(df, ma_pairs):
    """
    Identify MA crossover signals for multiple MA combinations

    Parameters:
    df : pandas DataFrame with price data
    ma_pairs : list of tuples, each containing (fast_period, slow_period)

    Returns:
    DataFrame with signals for each MA combination
    """
    # Create a copy of the DataFrame to avoid modifying the original
    df = df.copy()

    # Calculate all required MAs
    for fast, slow in ma_pairs:
        df[f"SMA_{fast}"] = df["close"].rolling(window=fast).mean()
        df[f"SMA_{slow}"] = df["close"].rolling(window=slow).mean()

        # Generate signals for this MA pair
        signal_col = f"signal_{fast}_{slow}"
        df[signal_col] = np.where(
            (df[f"SMA_{fast}"] > df[f"SMA_{slow}"])
            & (df[f"SMA_{fast}"].shift(1) <= df[f"SMA_{slow}"].shift(1)),
            1,  # Buy signal
            np.where(
                (df[f"SMA_{fast}"] < df[f"SMA_{slow}"])
                & (df[f"SMA_{fast}"].shift(1) >= df[f"SMA_{slow}"].shift(1)),
                -1,  # Sell signal
                0,  # No signal
            ),
        )

    return df


# MA optimized to EUR_USD_H4
ma_pair = [(140, 40)]

# Apply to DataFrame
df_with_signals = identify_multiple_ma_crossovers(df_EURUSD_H4, ma_pair)

# Initialize strategy
strategy = MovingAverageCrossStrategy_EUR_USD_H4()

# Calculate signals with SL/TP
df_with_signals = strategy.calculate_signals(df_EURUSD_H4)

# Create a new collection for signals if it doesn't exist
signals_collection = db["EUR_USD_H4_signals"]

# Convert DataFrame to dictionary and save to MongoDB
for index, row in df_with_signals.iterrows():
    if row["signal"] != 0:  # Only save rows with actual signals
        signal_data = {
            "time": index,
            "instrument": "EUR_USD",
            "timeframe": "H4",
            "close": float(row["close"]),
            "SMA_60": float(row["slow_ma"]),
            "SMA_40": float(row["fast_ma"]),
            "signal": int(row["signal"]),
            "stop_loss": float(row["stop_loss"]),
            "take_profit": float(row["take_profit"]),
            "atr": float(row["atr"]),
            "risk_reward_ratio": float(row["risk_reward_ratio"]),
            "created_at": datetime.datetime.now(datetime.timezone.utc),
        }

        # Update or insert (upsert) based on timestamp
        signals_collection.update_one(
            {"time": index}, {"$set": signal_data}, upsert=True
        )

print(
    f"Saved signals with SL/TP levels to MongoDB collection: {signals_collection.name}"
)

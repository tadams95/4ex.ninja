import pandas as pd
from config.settings import MONGO_CONNECTION_STRING
from pymongo import MongoClient
import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Optional
from config.strat_settings import STRATEGIES

# Set up database connections
client = MongoClient(
    MONGO_CONNECTION_STRING, tls=True, tlsAllowInvalidCertificates=True
)
price_db = client["streamed_prices"]
signals_db = client["signals"]

# Logging setup
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class MovingAverageCrossStrategy:
    def __init__(
        self,
        pair: str,
        timeframe: str,
        slow_ma: int,
        fast_ma: int,
        atr_period: int,
        sl_atr_multiplier: float,
        tp_atr_multiplier: float,
        min_atr_value: float,
        min_rr_ratio: float,
        sleep_seconds: int,
        min_candles: int,
    ):
        self.pair = pair
        self.timeframe = timeframe
        self.collection = price_db[f"{pair}_{timeframe}"]
        self.signals_collection = signals_db["trades"]
        self.slow_ma = slow_ma
        self.fast_ma = fast_ma
        self.atr_period = atr_period
        self.sl_atr_multiplier = sl_atr_multiplier
        self.tp_atr_multiplier = tp_atr_multiplier
        self.min_atr_value = min_atr_value
        self.min_rr_ratio = min_rr_ratio
        self.sleep_seconds = sleep_seconds
        self.min_candles = min_candles  # Kept but unused with 200-candle fetch
        self.is_jpy_pair = pair.endswith("JPY")

    def validate_signal(self, signal: int, atr: float, risk_reward_ratio: float) -> bool:
        """Validate if a signal meets the minimum criteria."""
        try:
            is_valid = (
                signal != 0
                and atr >= self.min_atr_value
                and risk_reward_ratio >= self.min_rr_ratio
            )
            logging.debug(f"Validating signal for {self.pair}: signal={signal}, atr={atr}, rr={risk_reward_ratio}, valid={is_valid}")
            return is_valid
        except Exception as e:
            logging.error(f"Error validating signal for {self.pair}: {e}")
            return False

    def calculate_atr(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Average True Range."""
        try:
            high = df["high"]
            low = df["low"]
            close = df["close"].shift(1)
            tr = pd.concat(
                [high - low, abs(high - close), abs(low - close)], axis=1
            ).max(axis=1)
            return tr.rolling(window=self.atr_period).mean()
        except Exception as e:
            logging.error(f"Error calculating ATR for {self.pair}: {e}")
            return pd.Series(index=df.index)

    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate trading signals based on moving average crossovers."""
        try:
            # Create an explicit deep copy to avoid SettingWithCopyWarning
            df = df.copy(deep=True)

            # Calculate moving averages and ATR
            df["slow_ma"] = df["close"].rolling(window=self.slow_ma).mean()
            df["fast_ma"] = df["close"].rolling(window=self.fast_ma).mean()
            df["atr"] = self.calculate_atr(df)
            df["signal"] = 0

            # Determine crossovers
            buy_crossover = (df["fast_ma"] > df["slow_ma"]) & (
                df["fast_ma"].shift(1) <= df["slow_ma"].shift(1)
            )
            sell_crossover = (df["fast_ma"] < df["slow_ma"]) & (
                df["fast_ma"].shift(1) >= df["slow_ma"].shift(1)
            )
            df.loc[buy_crossover, "signal"] = 1
            df.loc[sell_crossover, "signal"] = -1
            logging.info(f"Detected {len(df[df['signal'] != 0])} crossovers for {self.pair} {self.timeframe}")

            # Calculate stop loss and take profit
            df["stop_loss"] = pd.NA
            df["take_profit"] = pd.NA
            df["risk_reward_ratio"] = pd.NA

            # For buy signals
            buy_signals = df["signal"] == 1
            df.loc[buy_signals, "stop_loss"] = df.loc[buy_signals, "close"] - (
                df.loc[buy_signals, "atr"] * self.sl_atr_multiplier
            )
            df.loc[buy_signals, "take_profit"] = df.loc[buy_signals, "close"] + (
                df.loc[buy_signals, "atr"] * self.tp_atr_multiplier
            )
            df.loc[buy_signals, "risk_reward_ratio"] = (
                df.loc[buy_signals, "take_profit"] - df.loc[buy_signals, "close"]
            ) / (df.loc[buy_signals, "close"] - df.loc[buy_signals, "stop_loss"])

            # For sell signals
            sell_signals = df["signal"] == -1
            df.loc[sell_signals, "stop_loss"] = df.loc[sell_signals, "close"] + (
                df.loc[sell_signals, "atr"] * self.sl_atr_multiplier
            )
            df.loc[sell_signals, "take_profit"] = df.loc[sell_signals, "close"] - (
                df.loc[sell_signals, "atr"] * self.tp_atr_multiplier
            )
            df.loc[sell_signals, "risk_reward_ratio"] = (
                df.loc[sell_signals, "close"] - df.loc[sell_signals, "take_profit"]
            ) / (df.loc[sell_signals, "stop_loss"] - df.loc[sell_signals, "close"])

            # Ensure numeric types after calculations
            df["stop_loss"] = pd.to_numeric(df["stop_loss"], errors="coerce")
            df["take_profit"] = pd.to_numeric(df["take_profit"], errors="coerce")
            df["risk_reward_ratio"] = pd.to_numeric(df["risk_reward_ratio"], errors="coerce")

            # Filter signals based on validation criteria
            invalid_indices = []
            for index, row in df[df["signal"] != 0].iterrows():
                if not self.validate_signal(
                    row["signal"], row["atr"], row["risk_reward_ratio"]
                ):
                    invalid_indices.append(index)

            if invalid_indices:
                df.loc[invalid_indices, "signal"] = 0
                logging.info(f"Filtered {len(invalid_indices)} signals for {self.pair} {self.timeframe}")

            return df
        except Exception as e:
            logging.error(f"Error calculating signals for {self.pair}: {e}", exc_info=True)
            return df

    def generate_trade_dict(self, row: pd.Series) -> Optional[Dict]:
        """Generate a dictionary of trade data from a signal row."""
        try:
            close_price = Decimal(str(row["close"]))
            stop_loss = Decimal(str(row["stop_loss"]))
            take_profit = Decimal(str(row["take_profit"]))
            pip_multiplier = Decimal("100") if self.is_jpy_pair else Decimal("10000")
            sl_pips = abs(close_price - stop_loss) * pip_multiplier
            tp_pips = abs(take_profit - close_price) * pip_multiplier
            signal_data = {
                "time": row.name,
                "instrument": self.pair,
                "timeframe": self.timeframe,
                "close": float(row["close"]),
                "slow_ma": float(row["slow_ma"]),
                "fast_ma": float(row["fast_ma"]),
                "signal": int(row["signal"]),
                "stop_loss": float(stop_loss),
                "take_profit": float(take_profit),
                "sl_pips": float(sl_pips),
                "tp_pips": float(tp_pips),
                "atr": float(row["atr"]),
                "risk_reward_ratio": float(row["risk_reward_ratio"]),
                "created_at": datetime.now(timezone.utc),
            }
            logging.info(f"Generated signal for {self.pair} {self.timeframe}: {signal_data}")
            return signal_data
        except Exception as e:
            logging.error(f"Error generating trade dict for {self.pair}: {e}", exc_info=True)
            return None

    async def process_dataframe(self, df: pd.DataFrame) -> None:
        """Process a dataframe of price data to generate and store signals."""
        if df.empty:
            logging.info(f"No data found for {self.pair} {self.timeframe}")
            return

        # Set time as index
        df.set_index("time", inplace=True)

        # Prepare OHLC data - create a new DataFrame
        df = df[["open", "high", "low", "close"]].copy(deep=True)

        # Ensure numeric types
        for col in ["open", "high", "low", "close"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Clean the data
        df = df.dropna(subset=["open", "high", "low", "close"])
        logging.info(f"After NaN removal: {len(df)} valid candles for {self.pair} {self.timeframe}")

        # Remove duplicates
        df = df[~df.index.duplicated(keep="last")].copy(deep=True)

        # Calculate signals
        df = self.calculate_signals(df)

        # Log signal count
        signal_count = len(df[df["signal"] != 0])
        logging.info(f"Found {signal_count} signals for {self.pair} {self.timeframe}")

        # Store valid signals
        for index, row in df[df["signal"] != 0].iterrows():
            signal_data = self.generate_trade_dict(row)
            if signal_data:
                self.signals_collection.update_one(
                    {"time": index}, {"$set": signal_data}, upsert=True
                )
                logging.info(f"Saved signal to signals.trades for {self.pair} {self.timeframe}")

    async def monitor_prices(self):
        """Main monitoring loop that fetches data and processes it periodically."""
        logging.info(f"Starting monitoring for {self.pair} {self.timeframe}")
        while True:
            try:
                # Fetch last 200 candles
                df = pd.DataFrame(list(self.collection.find().sort("time", -1).limit(200)))
                logging.info(f"Retrieved {len(df)} candles for {self.pair} {self.timeframe}")

                # Process the dataframe
                await self.process_dataframe(df)

                # Clean up and wait for next cycle
                del df
                await asyncio.sleep(self.sleep_seconds)
            except Exception as e:
                logging.error(f"Error monitoring {self.pair}: {e}", exc_info=True)
                await asyncio.sleep(900)  # Sleep for 15 minutes on error


async def run_strategies():
    """Start all strategies concurrently."""
    strategies = [MovingAverageCrossStrategy(**cfg) for cfg in STRATEGIES.values()]
    tasks = [asyncio.create_task(strategy.monitor_prices()) for strategy in strategies]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    logging.info("Starting multi-strategy monitoring...")
    asyncio.run(run_strategies())
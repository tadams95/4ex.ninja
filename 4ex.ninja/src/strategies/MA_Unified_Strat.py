import pandas as pd
from config.settings import MONGO_CONNECTION_STRING
from pymongo import MongoClient
import numpy as np
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, Optional
from config.strat_settings import STRATEGIES

client = MongoClient(
    MONGO_CONNECTION_STRING, tls=True, tlsAllowInvalidCertificates=True
)
# db = client["streamed_prices"]
price_db = client["streamed_prices"]
signals_db = client["signals"]

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
        self.is_jpy_pair = pair.endswith("JPY")

    def validate_signal(
        self, signal: int, atr: float, risk_reward_ratio: float
    ) -> bool:
        try:
            return (
                signal != 0
                and atr >= self.min_atr_value
                and risk_reward_ratio >= self.min_rr_ratio
            )
        except Exception as e:
            logging.error(f"Error validating signal for {self.pair}: {e}")
            return False

    def calculate_atr(self, df: pd.DataFrame) -> pd.Series:
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
        try:
            df = df.copy()
            df["slow_ma"] = df["close"].rolling(window=self.slow_ma).mean()
            df["fast_ma"] = df["close"].rolling(window=self.fast_ma).mean()
            df["atr"] = self.calculate_atr(df)
            df["signal"] = 0
            df.loc[
                (df["fast_ma"] > df["slow_ma"])
                & (df["fast_ma"].shift(1) <= df["slow_ma"].shift(1)),
                "signal",
            ] = 1
            df.loc[
                (df["fast_ma"] < df["slow_ma"])
                & (df["fast_ma"].shift(1) >= df["slow_ma"].shift(1)),
                "signal",
            ] = -1
            df["stop_loss"] = pd.NA
            df["take_profit"] = pd.NA
            buy_signals = df["signal"] == 1
            sell_signals = df["signal"] == -1
            df.loc[buy_signals, "stop_loss"] = df["close"] - (
                df["atr"] * self.sl_atr_multiplier
            )
            df.loc[buy_signals, "take_profit"] = df["close"] + (
                df["atr"] * self.tp_atr_multiplier
            )
            df.loc[sell_signals, "stop_loss"] = df["close"] + (
                df["atr"] * self.sl_atr_multiplier
            )
            df.loc[sell_signals, "take_profit"] = df["close"] - (
                df["atr"] * self.tp_atr_multiplier
            )
            df["risk_reward_ratio"] = pd.NA
            df.loc[buy_signals, "risk_reward_ratio"] = (
                df["take_profit"] - df["close"]
            ) / (df["close"] - df["stop_loss"])
            df.loc[sell_signals, "risk_reward_ratio"] = (
                df["close"] - df["take_profit"]
            ) / (df["stop_loss"] - df["close"])
            for index, row in df.iterrows():
                if row["signal"] != 0 and not self.validate_signal(
                    row["signal"], row["atr"], row["risk_reward_ratio"]
                ):
                    df.loc[index, "signal"] = 0
            return df
        except Exception as e:
            logging.error(f"Error calculating signals for {self.pair}: {e}")
            return df

    def generate_trade_dict(self, row: pd.Series) -> Optional[Dict]:
        try:
            close_price = Decimal(str(row["close"]))
            stop_loss = Decimal(str(row["stop_loss"]))
            take_profit = Decimal(str(row["take_profit"]))
            pip_multiplier = Decimal("100") if self.is_jpy_pair else Decimal("10000")
            sl_pips = abs(close_price - stop_loss) * pip_multiplier
            tp_pips = abs(take_profit - close_price) * pip_multiplier
            return {
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
        except Exception as e:
            logging.error(f"Error generating trade dict for {self.pair}: {e}")
            return None

    async def monitor_prices(self):
        while True:
            try:
                last_signal = self.signals_collection.find_one(sort=[("time", -1)])
                start_time = (
                    last_signal["time"] - timedelta(days=30) if last_signal else None
                )
                query = {"time": {"$gt": start_time}} if start_time else {}
                df = pd.DataFrame(list(self.collection.find(query).sort("time", 1)))
                if not df.empty:
                    df.set_index("time", inplace=True)
                    # Handle mixed mid formats
                    if (
                        "open" in df.columns and df["open"].notna().any()
                    ):  # Use OHLC if present
                        df = df[["open", "high", "low", "close"]]
                    elif "mid" in df.columns:  # Fallback to mid
                        if isinstance(df["mid"].iloc[0], dict):  # Mid is dict
                            df["open"] = df["mid"].apply(lambda x: float(x["o"]))
                            df["high"] = df["mid"].apply(lambda x: float(x["h"]))
                            df["low"] = df["mid"].apply(lambda x: float(x["l"]))
                            df["close"] = df["mid"].apply(lambda x: float(x["c"]))
                            df = df[["open", "high", "low", "close"]]
                        else:  # Mid is float (old data)
                            logging.warning(
                                f"{self.pair} {self.timeframe} has float mid, skipping"
                            )
                            continue
                    else:
                        logging.warning(
                            f"{self.pair} {self.timeframe} missing OHLC/mid, skipping"
                        )
                        continue
                    df = df[~df.index.duplicated(keep="last")]
                    df = self.calculate_signals(df)
                    for index, row in df[df["signal"] != 0].iterrows():
                        signal_data = self.generate_trade_dict(row)
                        if signal_data:
                            self.signals_collection.update_one(
                                {"time": index}, {"$set": signal_data}, upsert=True
                            )
                    logging.info(
                        f"Processed {self.pair} {self.timeframe} at {datetime.now(timezone.utc)}"
                    )
                del df
                await asyncio.sleep(self.sleep_seconds)
            except Exception as e:
                logging.error(f"Error monitoring {self.pair}: {e}")
                await asyncio.sleep(900)


async def run_strategies():
    strategies = [MovingAverageCrossStrategy(**cfg) for cfg in STRATEGIES.values()]
    tasks = [asyncio.create_task(strategy.monitor_prices()) for strategy in strategies]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    logging.info("Starting multi-strategy monitoring...")
    asyncio.run(run_strategies())

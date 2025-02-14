from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from src.models.market_data import MarketData
from src.indicators.sma import calculate_sma
from src.indicators.ema import calculate_ema
from src.indicators.rsi import calculate_rsi
from src.indicators.macd import calculate_macd
from src.indicators.stochastic import calculate_stochastic
from src.indicators.bollinger_bands import calculate_bollinger_bands


class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    NEUTRAL = "NEUTRAL"


@dataclass
class Signal:
    type: SignalType
    timestamp: datetime
    instrument: str
    price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class BaseStrategy:
    def __init__(self, instrument: str, timeframes: List[str]):
        self.instrument = instrument
        self.timeframes = timeframes
        self.positions = []
        self.market_data = MarketData()
        self.data: Dict[str, pd.DataFrame] = {}

    def prepare_data(self, start_date: datetime, end_date: datetime) -> None:
        """
        Fetch data from MongoDB and prepare it for strategy analysis.
        Convert to pandas DataFrame and calculate basic indicators
        """

        try:
            for timeframe in self.timeframes:
                # fetch data from MongoDB
                candles = self.market_data.get_candles(
                    instrument=self.instrument,
                    granularity=timeframe,
                    start_date=start_date,
                    end_date=end_date,
                )
                if not candles:
                    raise ValueError(
                        f"No data found for {self.instrument} in {timeframe}"
                    )

                # convert to pandas DataFrame
                df = pd.DataFrame(candles)
                df.set_index("time", inplace=True)
                df.sort_index(inplace=True)

                # extract OHLCV data
                df["open"] = df["mid"].apply(lambda x: float(x["o"]))
                df["high"] = df["mid"].apply(lambda x: float(x["h"]))
                df["low"] = df["mid"].apply(lambda x: float(x["l"]))
                df["close"] = df["mid"].apply(lambda x: float(x["c"]))
                df["volume"] = df["volume"].astype(float)

                # Calculate indicators
                sma_periods = [10, 20, 30, 50, 100, 200]
                ema_periods = [10, 20, 30, 50, 100, 200]

                # Add indicators
                df = pd.concat(
                    [
                        df,
                        calculate_sma(df["close"], sma_periods),
                        calculate_ema(df["close"], ema_periods),
                        calculate_bollinger_bands(df["close"]),
                    ],
                    axis=1,
                )

                df["rsi"] = calculate_rsi(df["close"])
                df = pd.concat([df, calculate_macd(df["close"])], axis=1)
                df = pd.concat([df, calculate_stochastic(df)], axis=1)

                self.data[timeframe] = df
                print(f"Data prepared for {self.instrument} in {timeframe}")

        except Exception as e:
            print(f"Error preparing data: {e}")
            raise

    def generate_signal(self, current_time: datetime) -> Signal:
        """
        Generate trading signals based on strategy rules.
        Should be implemented by child classes.
        """
        raise NotImplementedError

    def calculate_position_size(self, signal: Signal) -> float:
        """
        Calculate position size based on risk management rules.
        Should be implemented by child classes.
        """
        raise NotImplementedError

    def execute_trade(self, signal: Signal) -> bool:
        """
        Execute a trade based on the signal.
        Returns True if trade was executed successfully.
        """
        try:
            # Implementation will depend on whether live trading or backtesting
            position_size = self.calculate_position_size(signal)
            self.positions.append(
                {
                    "type": signal.type,
                    "entry_time": signal.timestamp,
                    "entry_price": signal.price,
                    "size": position_size,
                    "stop_loss": signal.stop_loss,
                    "take_profit": signal.take_profit,
                }
            )
            return True
        except Exception as e:
            print(f"Error executing trade: {e}")
            return False

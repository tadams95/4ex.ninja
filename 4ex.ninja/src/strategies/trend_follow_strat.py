from datetime import datetime, timezone
import pandas as pd
from .base_strategy import BaseStrategy, Signal, SignalType


class TrendFollowingStrategy(BaseStrategy):
    def __init__(self, instrument: str):
        # Initialize with multiple timeframes for multi-timeframe analysis
        super().__init__(instrument, timeframes=["D", "H4", "H1"])

    def generate_signal(self, current_time: datetime) -> Signal:
        """
        Generate trading signals based on trend-following rules:
        - Daily trend determined by 200 SMA
        - H4 for trend confirmation using 50 SMA
        - H1 for entry using 20 EMA and RSI
        """
        try:
            # Convert current_time properly depending on whether it's naive or tz-aware
            if current_time.tzinfo is None:
                current_time = pd.Timestamp(current_time).tz_localize("UTC")
            else:
                current_time = pd.Timestamp(current_time).tz_convert("UTC")

            # Get current data for each timeframe
            daily_data = self.data["D"]
            h4_data = self.data["H4"]
            h1_data = self.data["H1"]

            # Ensure indices are timezone-aware
            daily_data.index = daily_data.index.tz_localize(
                "UTC" if daily_data.index.tz is None else None
            )
            h4_data.index = h4_data.index.tz_localize(
                "UTC" if h4_data.index.tz is None else None
            )
            h1_data.index = h1_data.index.tz_localize(
                "UTC" if h1_data.index.tz is None else None
            )

            # Get latest available data
            current_daily = daily_data[daily_data.index <= current_time].iloc[-1]
            current_h4 = h4_data[h4_data.index <= current_time].iloc[-1]
            current_h1 = h1_data[h1_data.index <= current_time].iloc[-1]

            # Get latest values
            current_price = current_h1["close"]
            daily_sma200 = current_daily["sma_200"]
            h4_sma50 = current_h4["sma_50"]
            h1_ema20 = current_h1["ema_20"]
            h1_rsi = current_h1["rsi"]

            # Define trend conditions
            daily_trend = current_price > daily_sma200
            h4_trend = current_price > h4_sma50
            h1_trend = current_price > h1_ema20

            # Generate signal
            if daily_trend and h4_trend and h1_trend and h1_rsi < 70:
                # Calculate stop loss and take profit
                stop_loss = h1_data[h1_data.index <= current_time]["low"].iloc[-1]
                take_profit = (
                    current_price + (current_price - stop_loss) * 2
                )  # 1:2 risk/reward

                return Signal(
                    type=SignalType.BUY,
                    timestamp=current_time,
                    instrument=self.instrument,
                    price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                )

            elif not daily_trend and not h4_trend and not h1_trend and h1_rsi > 30:
                # Calculate stop loss and take profit
                stop_loss = h1_data[h1_data.index <= current_time]["high"].iloc[-1]
                take_profit = (
                    current_price - (stop_loss - current_price) * 2
                )  # 1:2 risk/reward

                return Signal(
                    type=SignalType.SELL,
                    timestamp=current_time,
                    instrument=self.instrument,
                    price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                )

            return Signal(
                type=SignalType.NEUTRAL,
                timestamp=current_time,
                instrument=self.instrument,
                price=current_price,
            )

        except Exception as e:
            print(f"Error generating signal: {e}")
            last_price = h1_data[h1_data.index <= current_time]["close"].iloc[-1]
            return Signal(
                type=SignalType.NEUTRAL,
                timestamp=current_time,
                instrument=self.instrument,
                price=last_price,
            )

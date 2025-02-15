from datetime import datetime, timezone
import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy, Signal, SignalType

# Not a fan of this strategy

class TrendFollowingStrategy(BaseStrategy):
    def __init__(self, instrument: str):
        # Initialize with multiple timeframes for multi-timeframe analysis
        super().__init__(instrument, timeframes=["D", "H4", "H1"])

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """
        Calculate the Average True Range (ATR) using high, low, and close.
        """
        high_low = df["high"] - df["low"]
        high_close = np.abs(df["high"] - df["close"].shift())
        low_close = np.abs(df["low"] - df["close"].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr.iloc[-1]

    def generate_signal(self, current_time: datetime) -> Signal:
        """
        Generate trading signals based on trend-following rules:
          - Daily trend determined by 200 SMA
          - H4 trend confirmation using 50 SMA
          - H1 entry using 20 EMA and RSI
          - ATR used for adaptive stop loss and take profit levels
        """
        try:
            # Ensure current_time is a timezone-aware Timestamp in UTC
            current_time = pd.to_datetime(current_time, utc=True)

            # Get current data for each timeframe
            daily_data = self.data["D"]
            h4_data = self.data["H4"]
            h1_data = self.data["H1"]

            # Force all indices to be timezone-aware in UTC
            daily_data.index = pd.to_datetime(daily_data.index, utc=True)
            h4_data.index = pd.to_datetime(h4_data.index, utc=True)
            h1_data.index = pd.to_datetime(h1_data.index, utc=True)

            # Get the latest available data up to current_time
            current_daily = daily_data[daily_data.index <= current_time].iloc[-1]
            current_h4 = h4_data[h4_data.index <= current_time].iloc[-1]
            current_h1 = h1_data[h1_data.index <= current_time].iloc[-1]

            # Get latest values from H1 (entry timeframe)
            current_price = current_h1["close"]
            daily_sma200 = current_daily["sma_200"]
            h4_sma50 = current_h4["sma_50"]
            h1_ema20 = current_h1["ema_20"]
            h1_rsi = current_h1["rsi"]

            # Define trend conditions (using multi-timeframe trend confirmation)
            daily_trend = current_price > daily_sma200
            h4_trend = current_price > h4_sma50
            h1_trend = current_price > h1_ema20

            # Calculate ATR from H1 data to account for short-term volatility
            atr = self._calculate_atr(h1_data, period=14)
            # Only trade if ATR is high enough (filter out low volatility periods)
            min_atr = 0.0005  # for example; adjust based on instrument volatility
            if atr < min_atr:
                print("\n⚪ Volatility too low. No signal generated.")
                return Signal(
                    type=SignalType.NEUTRAL,
                    timestamp=current_time,
                    instrument=self.instrument,
                    price=current_price,
                )

            # Use wider ATR multiples for stop loss and target
            risk_multiplier = 2.0  # 2 ATRs for stop loss
            reward_multiplier = 6.0  # 6 ATRs for take profit

            if daily_trend and h4_trend and h1_trend and h1_rsi < 70:
                # BUY: Set stop loss below current price by ATR multiple.
                stop_loss = current_price - atr * risk_multiplier
                take_profit = current_price + atr * reward_multiplier

                print("\n🟢 BUY SIGNAL GENERATED")
                print(f"Entry Price: {current_price:.5f}")
                print(f"ATR: {atr:.5f}")
                print(f"Stop Loss: {stop_loss:.5f}")
                print(f"Take Profit: {take_profit:.5f}")
                print(f"Risk/Reward Ratio: {reward_multiplier}:1")
                return Signal(
                    type=SignalType.BUY,
                    timestamp=current_time,
                    instrument=self.instrument,
                    price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                )

            elif not daily_trend and not h4_trend and not h1_trend and h1_rsi > 30:
                # SELL: Set stop loss above current price by ATR multiple.
                stop_loss = current_price + atr * risk_multiplier
                take_profit = current_price - atr * reward_multiplier

                print("\n🔴 SELL SIGNAL GENERATED")
                print(f"Entry Price: {current_price:.5f}")
                print(f"ATR: {atr:.5f}")
                print(f"Stop Loss: {stop_loss:.5f}")
                print(f"Take Profit: {take_profit:.5f}")
                print(f"Risk/Reward Ratio: {reward_multiplier}:1")
                return Signal(
                    type=SignalType.SELL,
                    timestamp=current_time,
                    instrument=self.instrument,
                    price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                )

            # Simply return NEUTRAL signal without printing
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

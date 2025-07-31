import pandas as pd


def calculate_stochastic(
    df: pd.DataFrame, period: int = 14, k_period: int = 3
) -> pd.DataFrame:
    """Calculate Stochastic Oscillator"""
    result = pd.DataFrame()
    result["stoch_k"] = (
        (df["close"] - df["low"].rolling(window=period).min())
        / (
            df["high"].rolling(window=period).max()
            - df["low"].rolling(window=period).min()
        )
    ) * 100
    result["stoch_d"] = result["stoch_k"].rolling(window=k_period).mean()
    return result

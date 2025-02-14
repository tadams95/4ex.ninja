import pandas as pd
from typing import List


def calculate_sma(data: pd.Series, periods: List[int]) -> pd.DataFrame:
    """Calculate Simple Moving Averages for multiple periods"""
    df = pd.DataFrame()
    for period in periods:
        df[f"sma_{period}"] = data.rolling(window=period).mean()
    return df

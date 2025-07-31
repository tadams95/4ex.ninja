import pandas as pd
from typing import List


def calculate_ema(data: pd.Series, periods: List[int]) -> pd.DataFrame:
    """Calculate Exponential Moving Averages for multiple periods"""
    df = pd.DataFrame()
    for period in periods:
        df[f"ema_{period}"] = data.ewm(span=period, adjust=False).mean()
    return df

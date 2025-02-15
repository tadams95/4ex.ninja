import pandas as pd
from typing import List, Union


def calculate_sma(data: pd.Series, periods: Union[List[int], int]) -> pd.DataFrame:
    """Calculate Simple Moving Averages for multiple periods"""
    df = pd.DataFrame()

    # Convert single period to list if necessary
    if isinstance(periods, int):
        periods = [periods]

    for period in periods:
        df[f"sma_{period}"] = data.rolling(window=period).mean()
    return df

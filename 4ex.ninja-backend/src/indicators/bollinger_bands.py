import pandas as pd


def calculate_bollinger_bands(
    data: pd.Series, period: int = 20, std: int = 2
) -> pd.DataFrame:
    """Calculate Bollinger Bands"""
    df = pd.DataFrame()
    df["bb_middle"] = data.rolling(window=period).mean()
    std_dev = data.rolling(window=period).std()
    df["bb_upper"] = df["bb_middle"] + (std_dev * std)
    df["bb_lower"] = df["bb_middle"] - (std_dev * std)
    return df

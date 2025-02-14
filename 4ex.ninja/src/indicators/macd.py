import pandas as pd


def calculate_macd(
    data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
) -> pd.DataFrame:
    """Calculate MACD, Signal line, and Histogram"""
    df = pd.DataFrame()
    df["macd"] = (
        data.ewm(span=fast, adjust=False).mean()
        - data.ewm(span=slow, adjust=False).mean()
    )
    df["signal"] = df["macd"].ewm(span=signal, adjust=False).mean()
    df["hist"] = df["macd"] - df["signal"]
    return df

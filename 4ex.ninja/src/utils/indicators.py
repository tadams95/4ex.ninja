def moving_average(prices, window):
    """Calculate the moving average of a list of prices."""
    if len(prices) < window:
        return None
    return sum(prices[-window:]) / window

def rsi(prices, period=14):
    """Calculate the Relative Strength Index (RSI) of a list of prices."""
    if len(prices) < period:
        return None

    gains = []
    losses = []

    for i in range(1, period + 1):
        change = prices[i] - prices[i - 1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            losses.append(-change)
            gains.append(0)

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))
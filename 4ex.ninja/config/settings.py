from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("OANDA_API_KEY")
ACCOUNT_ID = os.getenv("OANDA_ACCOUNT_ID")

PRACTICE_URL = "https://api-fxpractice.oanda.com/v3"
LIVE_URL = "https://api-fxtrade.oanda.com/v3"

PRACTICE_STREAM_URL = "https://stream-fxpractice.oanda.com/v3"
LIVE_STREAM_URL = "https://stream-fxtrade.oanda.com/v3"

ENVIRONMENT = "practice"

SECURE_HEADER = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

SELL = -1
BUY = 1
NONE = 0

# Granularity settings
GRANULARITIES = {
    "M1": 60,  # 1 minute
    "M5": 300,  # 5 minutes
    "M15": 900,  # 15 minutes
    "M30": 1800,  # 30 minutes
    "H1": 3600,  # 1 hour
    "H4": 14400,  # 4 hours
    "D": 86400,  # 1 day
}

MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING")

ma_pairs = [
    (10, 20),
    (10, 30),
    (10, 40),
    (10, 50),
    (10, 60),
    (10, 70),
    (10, 80),
    (10, 90),
    (10, 100),
    (10, 110),
    (10, 120),
    (10, 130),
    (10, 140),
    (10, 150),
    (10, 160),
    (10, 170),
    (10, 180),
    (10, 190),
    (10, 200),
    (20, 30),
    (20, 40),
    (20, 50),
    (20, 60),
    (20, 70),
    (20, 80),
    (20, 90),
    (20, 100),
    (20, 110),
    (20, 120),
    (20, 130),
    (20, 140),
    (20, 150),
    (20, 160),
    (20, 170),
    (20, 180),
    (20, 190),
    (20, 200),
    (30, 40),
    (30, 50),
    (30, 60),
    (30, 70),
    (30, 80),
    (30, 90),
    (30, 100),
    (30, 110),
    (30, 120),
    (30, 130),
    (30, 140),
    (30, 150),
    (30, 160),
    (30, 170),
    (30, 180),
    (30, 190),
    (30, 200),
    (40, 50),
    (40, 60),
    (40, 70),
    (40, 80),
    (40, 90),
    (40, 100),
    (40, 110),
    (40, 120),
    (40, 130),
    (40, 140),
    (40, 150),
    (40, 160),
    (40, 170),
    (40, 180),
    (40, 190),
    (40, 200),
    (50, 60),
    (50, 70),
    (50, 80),
    (50, 90),
    (50, 100),
    (50, 110),
    (50, 120),
    (50, 130),
    (50, 140),
    (50, 150),
    (50, 160),
    (50, 170),
    (50, 180),
    (50, 190),
    (50, 200),
]
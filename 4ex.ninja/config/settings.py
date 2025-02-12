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

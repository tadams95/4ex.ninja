from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime, timezone
from config.settings import MONGO_CONNECTION_STRING, GRANULARITIES
from api.oanda_api import OandaAPI


class MarketData:
    def __init__(self):
        self.oanda = OandaAPI()
        # Add SSL configuration to handle certificate verification
        self.client = MongoClient(
            MONGO_CONNECTION_STRING,
            tls=True,
            tlsAllowInvalidCertificates=True,  # For development only
            # tlsCAFile='/Users/tyrelle/Desktop/4ex.ninja/4ex.ninja/config/global-bundle.pem'
        )
        self.db = self.client["forex_data"]
        self.date_format = "%Y-%m-%dT%H:%M:%S.%fZ"

    def fetch_and_store_candles(
        self, instrument, granularity, start_date=None, end_date=None, count=None
    ):
        try:
            # Format timestamps for OANDA API
            start_str = (
                start_date.strftime(self.date_format)[:-4] + "000Z"
                if start_date
                else None
            )
            end_str = (
                end_date.strftime(self.date_format)[:-4] + "000Z" if end_date else None
            )
            # Fetch candles from OANDA
            candles = self.oanda.get_candles(
                instrument=instrument,
                granularity=granularity,
                count=count,
                start=start_str,
                end=end_str,
            )

            if candles:
                self.store_candles(instrument, granularity, candles)
                return len(candles)
            return 0

        except Exception as error:
            print(f"Error fetching and storing candles: {error}")
            return 0

    def _clean_timestamp(self, timestamp_str):
        """clean timestamp to handle nanosecond precision"""
        if "." in timestamp_str:
            time_part, fraction = timestamp_str.split(".")
            # Remove the trailing 'Z'
            fraction = fraction.rstrip("Z")
            # Trim fraction to 6 digits; pad if necessary
            micro = fraction[:6].ljust(6, "0")
            return f"{time_part}.{micro}Z"
        return timestamp_str

    def store_candles(self, instrument, granularity, candles):
        # store OHLC data in MongoDB
        collection = self.db[f"{instrument}_{granularity}"]
        collection.create_index([("time", ASCENDING)], unique=True)

        for candle in candles:
            try:
                # convert time only if it is a string
                if isinstance(candle["time"], str):
                    cleaned_time = self._clean_timestamp(candle["time"])
                    candle["time"] = datetime.strptime(cleaned_time, self.date_format)
                collection.update_one(
                    {"time": candle["time"]}, {"$set": candle}, upsert=True
                )
            except Exception as error:
                print(f"Error storing candle data: {error}")
                print(f"Problematic candle: {candle["time"]}")
                continue

    def get_candles(
        self, instrument, granularity, start_date=None, end_date=None, count=None
    ):
        """Get historical candle data

        Args:
            instrument (str): The trading pair (e.g. 'EUR_USD')
            granularity (str): Time frame (M1, M5, M15, M30, H1, H4, D)
            start_date (datetime): Start date for historical data
            end_date (datetime): End date for historical data
            count (int): Number of candles to return (ignored if start_date and end_date are provided)
        """
        collection = self.db[f"{instrument}_{granularity}"]

        query = {}
        if start_date and end_date:
            query["time"] = {"$gte": start_date, "$lte": end_date}

        cursor = collection.find(query).sort("time", DESCENDING)
        if count and not (start_date and end_date):
            cursor = cursor.limit(count)

        return list(cursor)

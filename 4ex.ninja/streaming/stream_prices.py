import asyncio
import datetime
from pymongo import MongoClient
import oandapyV20
from oandapyV20.endpoints import instruments
from src.models.market_data import MarketData
from config.settings import MONGO_CONNECTION_STRING, API_KEY, ACCOUNT_ID, INSTRUMENTS
from src.models.market_data import MarketData


class PriceStreamer:
    def __init__(self):
        self.client = MongoClient(
            MONGO_CONNECTION_STRING,
            tls=True,
            tlsAllowInvalidCertificates=True,  # For development only
            # tlsCAFile='/Users/tyrelle/Desktop/4ex.ninja/4ex.ninja/config/global-bundle.pem'
        )
        self.db = self.client["streamed_prices"]
        self.oanda_client = oandapyV20.API(access_token=API_KEY)

        # Initialize collections dictionary
        self.collections = {}
        for instrument in INSTRUMENTS:
            self.collections[instrument] = {
                "H4": self.db[f"{instrument}_H4"],
                "D": self.db[f"{instrument}_D"],
                "M1": self.db[f"{instrument}_M1"],
            }

    async def fetch_candles(self, instrument, granularity="M1", count=10):
        try:
            params = {"count": count, "granularity": granularity, "price": "M"}
            request = instruments.InstrumentsCandles(
                instrument=instrument, params=params
            )
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.oanda_client.request, request
            )
            # print(f"Raw response for {instrument} {granularity}: {response}")
            return response.get("candles", [])
        except Exception as e:
            print(f"Error fetching candles for {instrument} {granularity}: {str(e)}")
            return []

    async def stream_1_min_candles(self, instrument_list, timeframes=["M1"]):
        """Stream 1 minute candles"""
        while True:
            try:
                for instrument in instrument_list:
                    for timeframe in timeframes:
                        candles = await self.fetch_candles(
                            instrument, granularity=timeframe
                        )

                        # Process and save all completed candles
                        if candles:
                            for candle in candles:
                                candle_data = {
                                    "instrument": instrument,
                                    "time": candle["time"],
                                    "open": float(candle["mid"]["o"]),
                                    "high": float(candle["mid"]["h"]),
                                    "low": float(candle["mid"]["l"]),
                                    "close": float(candle["mid"]["c"]),
                                    "volume": int(candle["volume"]),
                                    "complete": candle["complete"],
                                }

                                # Only save completed candles
                                if candle_data["complete"]:
                                    # Add timestamp for debugging
                                    print(
                                        f"Processing {instrument} {timeframe} at {datetime.datetime.now(datetime.timezone.utc)}"
                                    )

                                    # Insert as new document
                                    result = self.collections[instrument][
                                        timeframe
                                    ].insert_one(candle_data)

                                    print(
                                        f"Saved {instrument} {timeframe} candle with id: {result.inserted_id}"
                                    )

                # Sleep after processing all instruments
                await asyncio.sleep(60)

            except Exception as e:
                print(f"Error in streaming loop: {str(e)}")
                # Continue running even if there's an error
                await asyncio.sleep(5)


if __name__ == "__main__":
    streamer = PriceStreamer()
    instrument_list = INSTRUMENTS  # This is your list of instrument strings
    asyncio.run(streamer.stream_1_min_candles(instrument_list))

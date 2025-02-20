import asyncio
import datetime
from pymongo import MongoClient
import oandapyV20
from oandapyV20.endpoints import instruments

from config.settings import MONGO_CONNECTION_STRING, API_KEY, ACCOUNT_ID, INSTRUMENTS


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
            }

    async def fetch_candles(self, instrument, granularity="M1", count=20):
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

    async def stream_H4_candles(self, instrument_list):
        """Stream H4 candles"""
        while True:
            try:
                for instrument in instrument_list:
                    candles = await self.fetch_candles(instrument, granularity="H4")

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

                            if candle_data["complete"]:
                                print(
                                    f"Processing {instrument} H4 at {datetime.datetime.now(datetime.timezone.utc)}"
                                )
                                result = self.collections[instrument]["H4"].insert_one(
                                    candle_data
                                )
                                print(
                                    f"Saved {instrument} H4 candle with id: {result.inserted_id}"
                                )

                # Sleep for 4 hours (14400 seconds)
                await asyncio.sleep(14400)

            except Exception as e:
                print(f"Error in H4 streaming loop: {str(e)}")
                await asyncio.sleep(5)

    async def stream_D_candles(self, instrument_list):
        """Stream Daily candles"""
        while True:
            try:
                for instrument in instrument_list:
                    candles = await self.fetch_candles(instrument, granularity="D")

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

                            if candle_data["complete"]:
                                print(
                                    f"Processing {instrument} D at {datetime.datetime.now(datetime.timezone.utc)}"
                                )
                                result = self.collections[instrument]["D"].insert_one(
                                    candle_data
                                )
                                print(
                                    f"Saved {instrument} D candle with id: {result.inserted_id}"
                                )

                # Sleep for 24 hours (86400 seconds)
                await asyncio.sleep(86400)

            except Exception as e:
                print(f"Error in Daily streaming loop: {str(e)}")
                await asyncio.sleep(5)

    async def run_all_streams(self, instrument_list):
        """Run both H4 and D streams concurrently"""
        await asyncio.gather(
            self.stream_H4_candles(instrument_list),
            self.stream_D_candles(instrument_list),
        )


if __name__ == "__main__":
    streamer = PriceStreamer()
    instrument_list = INSTRUMENTS
    asyncio.run(streamer.run_all_streams(instrument_list))

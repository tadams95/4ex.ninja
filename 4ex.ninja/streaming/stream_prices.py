import asyncio
import datetime
from pymongo import MongoClient
import oandapyV20
from oandapyV20.endpoints import instruments
from config.settings import MONGO_CONNECTION_STRING, API_KEY, ACCOUNT_ID, INSTRUMENTS


class PriceStreamer:
    def __init__(self):
        self.client = MongoClient(
            MONGO_CONNECTION_STRING, tls=True, tlsAllowInvalidCertificates=True
        )
        self.db = self.client["streamed_prices"]
        self.oanda_client = oandapyV20.API(access_token=API_KEY)
        self.collections = {
            inst: {"H4": self.db[f"{inst}_H4"], "D": self.db[f"{inst}_D"]}
            for inst in INSTRUMENTS
        }
        self.initial_fetch_done = {"H4": False, "D": False}  # Track initial fetch

    async def fetch_candles(
        self, instrument: str, granularity: str, count: int = 2
    ) -> list:
        try:
            params = {"count": count, "granularity": granularity, "price": "M"}
            request = instruments.InstrumentsCandles(
                instrument=instrument, params=params
            )
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.oanda_client.request, request
            )
            return response.get("candles", [])
        except Exception as e:
            print(f"Error fetching {instrument} {granularity}: {e}")
            return []

    async def stream_H4_candles(self, instrument_list):
        while True:
            try:
                count = 200 if not self.initial_fetch_done["H4"] else 2
                for instrument in instrument_list:
                    candles = await self.fetch_candles(instrument, "H4", count=count)
                    if candles:
                        for candle in candles:
                            if candle["complete"]:
                                candle_data = {
                                    "instrument": instrument,
                                    "time": candle["time"],
                                    "open": float(candle["mid"]["o"]),
                                    "high": float(candle["mid"]["h"]),
                                    "low": float(candle["mid"]["l"]),
                                    "close": float(candle["mid"]["c"]),
                                    "volume": int(candle["volume"]),
                                    "complete": candle["complete"],
                                    "mid": {
                                        "o": candle["mid"]["o"],
                                        "h": candle["mid"]["h"],
                                        "l": candle["mid"]["l"],
                                        "c": candle["mid"]["c"],
                                    },
                                }
                                self.collections[instrument]["H4"].update_one(
                                    {"time": candle_data["time"]},
                                    {"$set": candle_data},
                                    upsert=True,
                                )
                                print(
                                    f"Saved {instrument} H4 at {datetime.datetime.now(datetime.timezone.utc)}"
                                )
                self.initial_fetch_done["H4"] = True  # Mark initial fetch done
                await asyncio.sleep(14400)  # 4 hours
            except Exception as e:
                print(f"H4 stream error: {e}")
                await asyncio.sleep(300)

    async def stream_D_candles(self, instrument_list):
        while True:
            try:
                count = 200 if not self.initial_fetch_done["D"] else 1
                for instrument in instrument_list:
                    candles = await self.fetch_candles(instrument, "D", count=count)
                    if candles:
                        for candle in candles:
                            if candle["complete"]:
                                candle_data = {
                                    "instrument": instrument,
                                    "time": candle["time"],
                                    "open": float(candle["mid"]["o"]),
                                    "high": float(candle["mid"]["h"]),
                                    "low": float(candle["mid"]["l"]),
                                    "close": float(candle["mid"]["c"]),
                                    "volume": int(candle["volume"]),
                                    "complete": candle["complete"],
                                    "mid": {
                                        "o": candle["mid"]["o"],
                                        "h": candle["mid"]["h"],
                                        "l": candle["mid"]["l"],
                                        "c": candle["mid"]["c"],
                                    },
                                }
                                self.collections[instrument]["D"].update_one(
                                    {"time": candle_data["time"]},
                                    {"$set": candle_data},
                                    upsert=True,
                                )
                                print(
                                    f"Saved {instrument} D at {datetime.datetime.now(datetime.timezone.utc)}"
                                )
                self.initial_fetch_done["D"] = True  # Mark initial fetch done
                await asyncio.sleep(86400)  # 24 hours
            except Exception as e:
                print(f"D stream error: {e}")
                await asyncio.sleep(300)

    async def run_all_streams(self, instrument_list):
        await asyncio.gather(
            self.stream_H4_candles(instrument_list),
            self.stream_D_candles(instrument_list),
        )


if __name__ == "__main__":
    streamer = PriceStreamer()
    asyncio.run(streamer.run_all_streams(INSTRUMENTS))

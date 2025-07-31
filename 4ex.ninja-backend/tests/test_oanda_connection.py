from api.oanda_api import OandaAPI
from pprint import pprint


def test_oanda_connection():
    api = OandaAPI()

    # print("\n=== Testing OANDA API Connection ===\n")

    # print("1. Testing get_accounts()")
    # accounts = api.get_accounts()
    # pprint(accounts)

    # print("\n2. Testing get_account_details()")
    # details = api.get_account_details()
    # pprint(details)

    # print("\n3. Testing get_account_summary()")
    # summary = api.get_account_summary()
    # pprint(summary)

    # print("\n4. Testing get_instruments()")
    # instruments = api.get_instruments()
    # if instruments:
    #     print(f"Number of available instruments: {len(instruments)}")
    #     print("First 5 instruments:")
    #     pprint(instruments[:5])

    # print("\n5. Testing get_instrument_candles()")
    # params = {
    #     "count": 5,
    #     "granularity": "H1"
    # }
    # candles = api.get_instrument_candles("EUR_USD", params)
    # print("Latest EUR/USD H1 candles:")
    # pprint(candles)

    print("\n=== Testing Trading Functions ===\n")

    # # Get current EUR/USD price
    # instrument = "EUR_USD"
    # current_price = api.get_current_price(instrument)
    # print(f"Current {instrument} price: {current_price}")

    # if current_price:
    #     # Calculate TP and SL based on current price (50 pips each)
    #     pip_value = 0.0001  # For EUR/USD, 1 pip = 0.0001
    #     take_profit = round(current_price + (50 * pip_value), 5)
    #     stop_loss = round(current_price - (50 * pip_value), 5)

    #     print(f"Setting TP at: {take_profit} (+50 pips)")
    #     print(f"Setting SL at: {stop_loss} (-50 pips)")

    #     # Place a buy trade for EUR/USD
    #     print("\n1. Placing buy trade for EUR/USD")
    #     trade_response = api.place_trade(
    #         instrument=instrument,
    #         units=1000,  # Mini lot
    #         take_profit=take_profit,
    #         stop_loss=stop_loss,
    #     )
    #     pprint(trade_response)

    #     # Get open trades
    #     print("\n2. Getting open trades")
    #     open_trades = api.get_open_trades()
    #     pprint(open_trades)

    # close specific trade
    print("\n3. Closing specific trade")
    trade_id = "123"
    close_trade_response = api.close_trade(trade_id)
    pprint(close_trade_response)


if __name__ == "__main__":
    test_oanda_connection()

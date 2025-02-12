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

    print("\n5. Testing get_instrument_candles()")
    params = {
        "count": 5,
        "granularity": "H1"
    }
    candles = api.get_instrument_candles("EUR_USD", params)
    print("Latest EUR/USD H1 candles:")
    pprint(candles)


if __name__ == "__main__":
    test_oanda_connection()

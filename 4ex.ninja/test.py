from api.oanda_api import OandaAPI
from pprint import pprint


def test_oanda_connection():
    api = OandaAPI()

    print("\n=== Testing OANDA API Connection ===\n")

    print("1. Testing get_accounts()")
    accounts = api.get_accounts()
    pprint(accounts)

    print("\n2. Testing get_account_details()")
    details = api.get_account_details()
    pprint(details)

    print("\n3. Testing get_account_summary()")
    summary = api.get_account_summary()
    pprint(summary)


if __name__ == "__main__":
    test_oanda_connection()

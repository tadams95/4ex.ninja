from oandapyV20 import API
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.pricing as pricing
import oandapyV20.endpoints.accounts as accounts
import oandapyV20.endpoints.instruments as instruments
from config.settings import API_KEY, ACCOUNT_ID, PRACTICE_URL, SECURE_HEADER
import requests


class OandaAPI:
    def __init__(self):
        self.client = API(access_token=API_KEY)
        self.account_id = ACCOUNT_ID
        self.session = requests.Session()
        self.session.headers.update(SECURE_HEADER)

    def get_accounts(self):
        """Get a list of all accounts authorized for the provided token"""
        try:
            r = accounts.AccountList()
            response = self.client.request(r)
            return response["accounts"]
        except Exception as error:
            print(f"Error getting accounts: {error}")
            return None

    def get_account_details(self, account_id=None):
        """Get detailed information about a specific account"""
        try:
            acc_id = account_id if account_id else self.account_id
            r = accounts.AccountDetails(accountID=acc_id)
            response = self.client.request(r)
            return response["account"]
        except Exception as error:
            print(f"Error getting account details: {error}")
            return None

    def get_account_summary(self, account_id=None):
        """Get a summary of a specific account"""
        try:
            acc_id = account_id if account_id else self.account_id
            r = accounts.AccountSummary(accountID=acc_id)
            response = self.client.request(r)
            return response["account"]
        except Exception as error:
            print(f"Error getting account summary: {error}")
            return None

    def get_instruments(self):
        """Get list of available trading instruments"""
        try:
            r = accounts.AccountInstruments(accountID=self.account_id)
            response = self.client.request(r)
            return response["instruments"]
        except Exception as error:
            print(f"Error getting instruments: {error}")
            return None

    def get_instrument_candles(self, instrument, params: None):
        """Get historical candlestick data for an instrument"""
        try:
            r = instruments.InstrumentsCandles(instrument=instrument, params=params)
            response = self.client.request(r)
            return response["candles"]
        except Exception as error:
            print(f"Error getting instrument candles: {error}")
            return None

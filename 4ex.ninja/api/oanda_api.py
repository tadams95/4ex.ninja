from oandapyV20 import API
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.pricing as pricing
import oandapyV20.endpoints.accounts as accounts
import oandapyV20.endpoints.instruments as instruments
import oandapyV20.endpoints.trades as trades
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

    def get_current_price(self, instrument):
        """Get the current price for an instrument"""
        try:
            params = {"instruments": instrument}
            r = pricing.PricingInfo(accountID=self.account_id, params=params)
            response = self.client.request(r)
            return float(response["prices"][0]["closeoutAsk"])
        except Exception as error:
            print(f"Error getting current price: {error}")
            return None

    def place_trade(self, instrument, units, take_profit=None, stop_loss=None):
        """Execute a trade

        Args:
            instrument (str): The instrument to trade (e.g. 'EUR_USD')
            units (int): Positive for buy, negative for sell
            take_profit (float): Optional take profit price
            stop_loss (float): Optional stop loss price
        """
        try:
            data = {
                "order": {
                    "type": "MARKET",
                    "instrument": instrument,
                    "units": str(units),
                }
            }

            if take_profit:
                data["order"]["takeProfitOnFill"] = {"price": str(take_profit)}
            if stop_loss:
                data["order"]["stopLossOnFill"] = {"price": str(stop_loss)}

            r = orders.OrderCreate(self.account_id, data=data)
            response = self.client.request(r)
            return response
        except Exception as error:
            print(f"Error placing trade: {error}")
            return None

    def get_open_trades(self):
        """Get all open trades for the account"""
        try:
            r = trades.OpenTrades(accountID=self.account_id)
            response = self.client.request(r)
            return response["trades"]
        except Exception as error:
            print(f"Error getting open trades: {error}")
            return None

    def close_trade(self, trade_id):
        """Close a specific trade by its ID"""
        try:
            r = trades.TradeClose(accountID=self.account_id, tradeID=trade_id)
            response = self.client.request(r)
            return response
        except Exception as error:
            print(f"Error closing trade: {error}")
            return None

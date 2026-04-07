from lumibot.brokers import Alpaca
from lumibot.backtesting import YahooDataBacktesting
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader
from datetime import datetime
from lumibot.entities.order import Order

import os
from dotenv import load_dotenv

load_dotenv()

ALPACA_CREDS ={
    "API_KEY": os.getenv("API_KEY"),
    "API_SECRET": os.getenv("API_SECRET"),
    "PAPER": True
}

class MLTrader(Strategy):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.symbol: str = ""
        self.last_trade: str | None = None
        self.cash_at_risk: float = 0.5

    def initialize(self, symbol:str="SPY", cash_at_risk:float=0.5):
        self.symbol = symbol
        self.sleeptime = "24H"
        self.last_trade = None
        self.cash_at_risk = cash_at_risk

    def position_sizing(self):
        cash = self.get_cash()
        last_price = self.get_last_price(self.symbol)
        quantity = int((cash * self.cash_at_risk) / last_price)
        return cash, last_price, quantity

    def on_trading_iteration(self):
        cash, last_price, quantity = self.position_sizing()
        if cash > last_price:
            if self.last_trade is None:
                order = self.create_order(self.symbol,
                                          side="buy",
                                          order_type=Order.OrderType.MARKET,
                                          order_class=Order.OrderClass.BRACKET,
                                          quantity=quantity,
                                          take_profit_price=last_price*1.20,
                                          stop_loss_price=last_price*0.95
                                          )
                self.submit_order(order)
                self.last_trade = "buy"

start_date = datetime(2022, 1, 1)
end_date = datetime(2022, 1, 31)

broker = Alpaca(ALPACA_CREDS)

strategy = MLTrader(name="MLTrader", broker=broker, parameters={"symbol": "SPY", "cash_at_risk": 0.5})
strategy.backtest(YahooDataBacktesting, start_date, end_date, parameters={"symbol": "SPY", "cash_at_risk": 0.5})


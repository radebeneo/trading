from lumibot.brokers import Alpaca
from lumibot.backtesting import YahooDataBacktesting
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader
from datetime import datetime
from lumibot.entities.order import Order
from alpaca.trading.client import TradingClient
from alpaca.data.historical import NewsClient
from alpaca.data import NewsRequest
from alpaca.data.models.news import News
from timedelta import Timedelta
from finbert_utils import estimate_sentiment

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

    def initialize(self, symbol:str="SPY", cash_at_risk:float=0.5):
        self.symbol = symbol
        self.sleeptime = "24H"
        self.last_trade = None
        self.cash_at_risk = cash_at_risk
        self.trading_client = TradingClient(os.getenv("API_KEY"), os.getenv("API_SECRET"), paper=True)
        self.news_client = NewsClient(os.getenv("API_KEY"), os.getenv("API_SECRET"))


    def position_sizing(self):
        cash = self.get_cash()
        last_price = self.get_last_price(self.symbol)
        quantity = int((cash * self.cash_at_risk) / last_price)
        return cash, last_price, quantity

    def get_dates(self):
        today = self.get_datetime()
        three_days_prior = today - Timedelta(days=3)
        return today, three_days_prior

    def get_sentiment(self):
        news = self.get_news()
        probability, sentiment = estimate_sentiment(news)
        return probability, sentiment


    def get_news(self) -> list[str]:
        today, three_days_prior = self.get_dates()
        print(f"Fetching news for {self.symbol} from {three_days_prior} to {today}")
        # Use keywords instead of symbol if news is not being returned for the ticker
        request = NewsRequest(symbols=self.symbol, start=three_days_prior, end=today)
        try:
            response = self.news_client.get_news(request)
            print(f"Response type: {type(response)}")
            if isinstance(response, dict):
                return [article["headline"] for article in response.get("news", [])]
            # In alpaca-py NewsClient.get_news(request) returns NewsResponse object
            # which has 'news' attribute that's a list of News objects
            news_list = response.data.get("news", [])
            print(f"News list length: {len(news_list)}")
            return [article.headline for article in news_list]
        except Exception as e:
            print(f"Error fetching news: {e}")
            return []

    def on_trading_iteration(self):
        cash, last_price, quantity = self.position_sizing()
        print(f"on_trading_iteration: cash={cash}, last_price={last_price}, quantity={quantity}")
        if cash > last_price:
            if self.last_trade is None:
                probability, sentiment = self.get_sentiment()
                print(probability, sentiment)
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

strategy = MLTrader(broker, parameters={"symbol": "SPY", "cash_at_risk": 0.5})
strategy.backtest(YahooDataBacktesting, start_date, end_date, parameters={"symbol": "SPY", "cash_at_risk": 0.5})

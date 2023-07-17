import pandas as pd
import vectorbt as vbt
# import yfinance as yf
# import pyfolio as pf
# import seaborn as sns
# import matplotlib.pyplot as plt
# from api_keys import demo_oanda_key
import warnings

from oandapyV20 import API
from oandapyV20.contrib.factories import InstrumentsCandlesFactory
import os

warnings.filterwarnings('ignore')

# Set your OANDA Account Credentials
# live_oanda_key = os.environ['demo_oanda_key']

demo_oanda_key = "25d3e35052f562976eb1722541bedfe1-5cd767d9272170436242b276ee6da169"

def get_candle_data():
    # demo_oanda_key = "f73f8046bfa47e5374f237ef8e3f5478-0494f5a4f8b1ef6d2545ae4077d1862a"
    instrument = 'EUR_USD'
    granularity = 'M1'
    start = pd.Timestamp.now() - pd.DateOffset(years=1)

    api = API(access_token=demo_oanda_key, environment="live")
    params = {
        "from": start,
        "granularity": granularity
    }
    candles_path = "candles/{}.{}".format(instrument, granularity)

    if not os.path.exists(candles_path):
        # Read the existing CSV file
        os.makedirs("candles", exist_ok=True)
        candles = pd.DataFrame()
        with open(candles_path, "w") as OUT:
            for r in InstrumentsCandlesFactory(instrument=instrument, 
                                            params={'from': 
                                                start.strftime('%Y-%m-%dT%H:%M:%SZ'), 
                                                'granularity': granularity}):
                api.request(r)
                for candle in r.response.get('candles'):
                    line = "{},{},{},{},{}\n".format(
                        candle['time'],
                        candle['mid']['o'],
                        candle['mid']['h'],
                        candle['mid']['l'],
                        candle['mid']['c']
                    )
                    OUT.write(line)
                    candles = pd.concat([candles, pd.DataFrame([candle])])
                    candles.set_index('time', inplace=True)
                    candles.index = pd.to_datetime(candles.index)
                    candles = candles.apply(pd.to_numeric, errors='coerce')
    else:
        candles = pd.read_csv(candles_path, )
        candles['time'] = pd.to_datetime(candles['time'])
        candles.set_index('time', inplace=True)
        candles = candles.apply(pd.to_numeric, errors='coerce')
    return candles
# Calculate indicators
candles = get_candle_data()
df = candles.ta.bbands()
fast_ma = vbt.MA.run(candles['close'], 14)
slow_ma = vbt.MA.run(candles['close'], 50)

# Generate signals with vectorbt
entries = vbt.signals.ma_crossed_above(fast_ma, slow_ma)
exits = vbt.signals.ma_crossed_below(fast_ma, slow_ma)

# Create portfolio and print some stats
portfolio = vbt.Portfolio.from_signals(candles['close'], entries, exits)
print(portfolio.stats())

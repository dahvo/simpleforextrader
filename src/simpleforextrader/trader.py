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
import json
import os

warnings.filterwarnings('ignore')

# Set your OANDA Account Credentials
# live_oanda_key = os.environ['demo_oanda_key']

demo_oanda_key = "f73f8046bfa47e5374f237ef8e3f5478-0494f5a4f8b1ef6d2545ae4077d1862a"
instrument = 'EUR_USD'
granularity = 'S5'
start = pd.Timestamp.now() - pd.DateOffset(years=1)

api = API(access_token=demo_oanda_key)
params = {
    "from": start,
    "granularity": "M5"  # 5 minute candlesticks
}
candles_file = "candles/{}.{}".format(instrument, granularity)

if not os.path.exists(candles_file):
    # Read the existing CSV file
    os.makedirs("candles", exist_ok=True)
    data = pd.DataFrame()

    with open(candles_file, "w") as OUT:
        # The factory returns a generator generating consecutive candlesticks
        # requests to retrieve full history from date 'from' till 'to'
        for r in InstrumentsCandlesFactory(instrument=instrument, params={'from': start.strftime('%Y-%m-%dT%H:%M:%SZ'), 'granularity': "M5"}):
            api.request(r)
            OUT.write(json.dumps(r.response.get('candles'), indent=2))
            data = pd.concat([data, pd.DataFrame(r.response.get('candles'))])

    data.set_index('time', inplace=True)
    data.index = pd.to_datetime(data.index)
    data = data.apply(pd.to_numeric, errors='coerce')
else:
    data = pd.read_json(candles_file, lines=True)
    data = pd.json_normalize(data)
    data['time'] = pd.to_datetime(data['time'])
    data.set_index('time', inplace=True)
    data = data.apply(pd.to_numeric, errors='coerce')

# Calculate indicators
df = data.ta.bbands()
fast_ma = vbt.MA.run(data['close'], 14)
slow_ma = vbt.MA.run(data['close'], 50)

# Generate signals with vectorbt
entries = vbt.signals.ma_crossed_above(fast_ma, slow_ma)
exits = vbt.signals.ma_crossed_below(fast_ma, slow_ma)

# Create portfolio and print some stats
portfolio = vbt.Portfolio.from_signals(data['close'], entries, exits)
print(portfolio.stats())

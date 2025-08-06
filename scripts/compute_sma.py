import requests
import pandas as pd
from datetime import datetime, timedelta

BASE_URL = "https://benchmarks.pyth.network/v1/"
SYMBOL = "Crypto.BTC/USD"

def fetch_historical_data(start_date, end_date):
    params = {
        "symbol": SYMBOL,
        "from": int(start_date.timestamp()),
        "to": int(end_date.timestamp()),
        "resolution": "1D"
    }
    response = requests.get(f"{BASE_URL}ohlcv", params=params)
    if response.status_code != 200:
        raise Exception(f"Error: {response.text}")
    data = response.json()
    if 'data' not in data:
        raise Exception("No data returned")
    df = pd.DataFrame(data['data'], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    return df

end_date = datetime.now()
start_date = end_date - timedelta(days=1000)
df = fetch_historical_data(start_date, end_date)
sma_1000 = df['close'].mean()
sma_1000_scaled = int(sma_1000 * 100)  # Scale to cents

print(f"1000-day SMA (USD): {sma_1000:.2f}")
print(f"Scaled SMA: {sma_1000_scaled}")
# TODO: Integrate solana-py to update on-chain

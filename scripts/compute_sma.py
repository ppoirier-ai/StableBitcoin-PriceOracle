import requests
import pandas as pd
from datetime import datetime, timedelta

# Use CoinGecko API instead as it's more reliable and doesn't require authentication
BASE_URL = "https://api.coingecko.com/api/v3"

def fetch_historical_data(days=365):
    # CoinGecko API uses days parameter for historical data
    params = {
        "vs_currency": "usd",
        "days": days
    }
    
    print(f"Requesting {days} days of Bitcoin price data")
    print(f"API URL: {BASE_URL}/coins/bitcoin/market_chart")
    print(f"Parameters: {params}")
    
    response = requests.get(f"{BASE_URL}/coins/bitcoin/market_chart", params=params)
    print(f"Response status: {response.status_code}")
    
    if response.status_code != 200:
        raise Exception(f"API error: {response.text}")
    
    data = response.json()
    if 'prices' not in data or not data['prices']:
        raise Exception("No price data returned from CoinGecko API")
    
    # Convert to DataFrame
    prices = data['prices']
    df = pd.DataFrame(prices, columns=['timestamp', 'price'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    # Resample to daily data and calculate OHLCV
    df.set_index('timestamp', inplace=True)
    df = df.resample('D').agg({
        'price': ['first', 'max', 'min', 'last']
    }).dropna()
    
    # Flatten column names
    df.columns = ['open', 'high', 'low', 'close']
    df.reset_index(inplace=True)
    
    return df

try:
    # CoinGecko free API allows up to 365 days
    days = 365
    df = fetch_historical_data(days)
    
    # Calculate 365-day SMA
    sma_365 = df['close'].mean()
    sma_365_scaled = int(sma_365 * 100)  # Scale to cents for on-chain u64

    print(f"\nResults:")
    print(f"365-day SMA (USD): {sma_365:.2f}")
    print(f"Scaled SMA (cents): {sma_365_scaled}")
    print(f"Data points: {len(df)}")
    
    # Calculate other periods for comparison
    if len(df) >= 30:
        sma_30 = df.tail(30)['close'].mean()
        print(f"30-day SMA (USD): {sma_30:.2f}")
    
    if len(df) >= 90:
        sma_90 = df.tail(90)['close'].mean()
        print(f"90-day SMA (USD): {sma_90:.2f}")
    
except Exception as e:
    print(f"Error computing SMA: {e}")
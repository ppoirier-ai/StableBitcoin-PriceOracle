import numpy as np
import pandas as pd
import requests
from datetime import datetime, timedelta
import json

def get_coingecko_historical_data(days=365):
    """Fetch historical BTC/USD data from CoinGecko API as fallback."""
    url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days={days}&interval=daily"
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(f"Failed to fetch data: {response.status_code}")
    data = response.json()
    prices = data['prices']
    df = pd.DataFrame(prices, columns=['timestamp', 'price'])
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms').dt.date
    df = df.set_index('date')
    df = df.sort_index(ascending=False)  # Recent first
    return df

def compute_trend_indicator(df, short_window=20, long_window=100):
    """Compute a simplified trend indicator based on moving averages."""
    close = df['price'].values
    
    # Calculate short and long moving averages
    short_ma = pd.Series(close).rolling(short_window, min_periods=1).mean()
    long_ma = pd.Series(close).rolling(long_window, min_periods=1).mean()
    
    # Calculate trend strength
    trend_ratio = short_ma / long_ma
    
    # Calculate volatility-adjusted trend
    returns = pd.Series(close).pct_change().dropna()
    volatility = returns.rolling(20, min_periods=1).std()
    
    # Weight the trend by volatility
    trend_value = trend_ratio.iloc[0] * (1 + volatility.iloc[0] if not pd.isna(volatility.iloc[0]) else 1)
    
    # Scale to current price
    current_price = close[0]
    trend_price = current_price * trend_value
    
    return trend_price

if __name__ == "__main__":
    try:
        # Fetch data from CoinGecko (Pyth Network is primarily for on-chain access)
        print("Fetching Bitcoin historical data from CoinGecko...")
        print("Note: Pyth Network is used on-chain for real-time price validation")
        df = get_coingecko_historical_data(days=365)
        print(f"Data points: {len(df)}")
        
        if len(df) == 0:
            print("No data available, exiting...")
            exit(1)
        
        print("Computing trend indicator...")
        trend_value = compute_trend_indicator(df)
        
        if np.isnan(trend_value):
            print("Error: Trend computation resulted in NaN")
        else:
            trend_scaled = int(trend_value * 100)  # Scale to cents for on-chain u64
            current_price = df['price'].iloc[0]
            print(f"\nResults:")
            print(f"Current Bitcoin price: ${current_price:.2f}")
            print(f"Trend indicator value: ${trend_value:.2f}")
            print(f"Scaled trend (cents): {trend_scaled}")
            print(f"Data source: CoinGecko (Pyth Network used on-chain for validation)")
            
    except Exception as e:
        print(f"Error computing trend indicator: {e}")
        import traceback
        traceback.print_exc()
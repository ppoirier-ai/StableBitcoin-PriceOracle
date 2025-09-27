#!/usr/bin/env python3
"""
Test script to verify Pyth Network Bitcoin price feed integration
"""

import requests
import json
from datetime import datetime, timedelta

# Pyth Network Bitcoin price feed addresses
PYTH_BTC_USD_DEVNET = "H6ARHf6YXhGYeQfUzQNGk6rDNnLBQKrenN712K4AQJEG"
PYTH_BTC_USD_MAINNET = "H6ARHf6YXhGYeQfUzQNGk6rDNnLBQKrenN712K4AQJEG"

def test_pyth_current_price(cluster="devnet"):
    """Test fetching current Bitcoin price from Pyth Network"""
    if cluster == "devnet":
        base_url = "https://hermes.pyth.network/v2/updates/price/latest"
    else:
        base_url = "https://hermes.pyth.network/v2/updates/price/latest"
    
    price_feed_id = PYTH_BTC_USD_DEVNET if cluster == "devnet" else PYTH_BTC_USD_MAINNET
    
    params = {
        "ids": [price_feed_id]
    }
    
    print(f"Testing Pyth Network {cluster}...")
    print(f"Price feed ID: {price_feed_id}")
    print(f"URL: {base_url}")
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        
        data = response.json()
        print(f"Response status: {response.status_code}")
        print(f"Response data: {json.dumps(data, indent=2)}")
        
        if 'parsed' in data and data['parsed']:
            price_info = data['parsed'][0]['price']
            price = price_info['price']
            expo = price_info.get('expo', -8)
            conf = price_info.get('conf', 0)
            
            # Convert to actual price
            actual_price = price / (10 ** (-expo))
            actual_conf = conf / (10 ** (-expo))
            
            print(f"\n✅ Successfully fetched Bitcoin price from Pyth Network:")
            print(f"   Price: ${actual_price:.2f}")
            print(f"   Confidence: ±${actual_conf:.2f}")
            print(f"   Exponent: {expo}")
            
            return True
        else:
            print("❌ No price data found in response")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching from Pyth Network: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_pyth_historical_data(cluster="devnet", days=7):
    """Test fetching historical Bitcoin price data from Pyth Network"""
    if cluster == "devnet":
        base_url = "https://hermes.pyth.network/v2/updates/price"
    else:
        base_url = "https://hermes.pyth.network/v2/updates/price"
    
    price_feed_id = PYTH_BTC_USD_DEVNET if cluster == "devnet" else PYTH_BTC_USD_MAINNET
    
    # Get the current timestamp and calculate start time
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    
    # Convert to Unix timestamps
    start_timestamp = int(start_time.timestamp())
    end_timestamp = int(end_time.timestamp())
    
    params = {
        "ids": [price_feed_id],
        "start_time": start_timestamp,
        "end_time": end_timestamp,
        "interval": "1d"
    }
    
    print(f"\nTesting Pyth Network historical data ({days} days)...")
    print(f"Start time: {start_time}")
    print(f"End time: {end_time}")
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        
        data = response.json()
        print(f"Response status: {response.status_code}")
        
        if 'parsed' in data and data['parsed']:
            print(f"✅ Successfully fetched {len(data['parsed'])} historical data points")
            
            # Show first few data points
            for i, update in enumerate(data['parsed'][:3]):
                if 'price' in update and 'price' in update['price']:
                    price_info = update['price']
                    price = price_info['price']
                    expo = price_info.get('expo', -8)
                    actual_price = price / (10 ** (-expo))
                    timestamp = update.get('publish_time', 0)
                    date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                    print(f"   {i+1}. {date}: ${actual_price:.2f}")
            
            return True
        else:
            print("❌ No historical data found in response")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching historical data from Pyth Network: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing Pyth Network Bitcoin Price Feed Integration")
    print("=" * 60)
    
    # Test current price
    current_success = test_pyth_current_price("devnet")
    
    # Test historical data
    historical_success = test_pyth_historical_data("devnet", days=7)
    
    print("\n" + "=" * 60)
    if current_success and historical_success:
        print("✅ All tests passed! Pyth Network integration is working.")
    else:
        print("❌ Some tests failed. Check the error messages above.")
        print("💡 You may need to use CoinGecko as a fallback for historical data.")

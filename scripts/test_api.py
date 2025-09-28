#!/usr/bin/env python3
"""
Test script for SBTC Target Price Oracle API
"""

import requests
import json
import time

def test_api_endpoint(url, description):
    """Test an API endpoint and display results"""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"URL: {url}")
    print('='*60)
    
    try:
        response = requests.get(url, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS!")
            print(json.dumps(data, indent=2))
        else:
            print("❌ ERROR!")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ CONNECTION ERROR: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON DECODE ERROR: {e}")
        print(f"Raw response: {response.text}")

def main():
    """Run all API tests"""
    base_url = "http://localhost:5000"
    
    print("🚀 SBTC Target Price Oracle API Test Suite")
    print("Make sure the API server is running: python sbtc_api.py")
    
    # Test endpoints
    endpoints = [
        (f"{base_url}/health", "Health Check"),
        (f"{base_url}/", "API Information"),
        (f"{base_url}/sbtc/current", "SBTC Target Price Computation")
    ]
    
    for url, description in endpoints:
        test_api_endpoint(url, description)
        time.sleep(1)  # Small delay between requests
    
    print(f"\n{'='*60}")
    print("🎯 Test Summary")
    print('='*60)
    print("✅ Health check should return status: healthy")
    print("✅ API info should return endpoint descriptions")
    print("✅ SBTC current should return:")
    print("   - current_btc_price: ~$46,000-47,000")
    print("   - sbtc_target_price: similar to current price")
    print("   - sbtc_scaled_cents: price * 100")
    print("   - data_points_used: 1000")
    print("   - data_source: Pyth Network BTC/USD Price Feed")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Test script for SBTC datapoint endpoints
Tests storing and retrieving SBTC datapoints
"""

import requests
import json
import time
from datetime import datetime, timedelta

API_BASE_URL = "http://localhost:5000"

def test_datapoint_endpoints():
    """Test all datapoint-related endpoints"""
    print("Testing SBTC Datapoint Endpoints")
    print("=" * 40)
    
    # Test 1: Store a datapoint (auto-compute SBTC value)
    print("\n1. Testing POST /datapoints/store (auto-compute)")
    try:
        response = requests.post(f"{API_BASE_URL}/datapoints/store", json={})
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data['success']}")
            print(f"Datapoint: {json.dumps(data['data']['datapoint'], indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Wait a moment
    time.sleep(1)
    
    # Test 2: Store a datapoint with custom values
    print("\n2. Testing POST /datapoints/store (custom values)")
    try:
        custom_data = {
            "sbtc_value": 47000.0,
            "btc_price": 46500.0,
            "data_points_used": 1000
        }
        response = requests.post(f"{API_BASE_URL}/datapoints/store", json=custom_data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data['success']}")
            print(f"Datapoint: {json.dumps(data['data']['datapoint'], indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Wait a moment
    time.sleep(1)
    
    # Test 3: Store another datapoint
    print("\n3. Testing POST /datapoints/store (another datapoint)")
    try:
        response = requests.post(f"{API_BASE_URL}/datapoints/store", json={})
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data['success']}")
            print(f"Total datapoints: {data['data']['total_datapoints']}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test 4: Get last datapoint
    print("\n4. Testing GET /datapoints/last")
    try:
        response = requests.get(f"{API_BASE_URL}/datapoints/last")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data['success']}")
            print(f"Last datapoint: {json.dumps(data['data']['datapoint'], indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test 5: Get datapoint batch (last hour)
    print("\n5. Testing GET /datapoints/batch (last hour)")
    try:
        end_time = int(time.time())
        start_time = end_time - 3600  # 1 hour ago
        
        response = requests.get(f"{API_BASE_URL}/datapoints/batch", params={
            'start_timestamp': start_time,
            'end_timestamp': end_time
        })
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data['success']}")
            print(f"Count: {data['data']['count']}")
            print(f"Datapoints: {json.dumps(data['data']['datapoints'], indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test 6: Get datapoint batch (last 24 hours)
    print("\n6. Testing GET /datapoints/batch (last 24 hours)")
    try:
        end_time = int(time.time())
        start_time = end_time - (24 * 3600)  # 24 hours ago
        
        response = requests.get(f"{API_BASE_URL}/datapoints/batch", params={
            'start_timestamp': start_time,
            'end_timestamp': end_time
        })
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data['success']}")
            print(f"Count: {data['data']['count']}")
            print(f"Total datapoints: {data['data']['total_datapoints']}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test 7: Test error handling - invalid timestamp range
    print("\n7. Testing error handling (invalid timestamp range)")
    try:
        response = requests.get(f"{API_BASE_URL}/datapoints/batch", params={
            'start_timestamp': int(time.time()),
            'end_timestamp': int(time.time()) - 3600  # End before start
        })
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test 8: Test error handling - missing parameters
    print("\n8. Testing error handling (missing parameters)")
    try:
        response = requests.get(f"{API_BASE_URL}/datapoints/batch")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

def test_api_info():
    """Test the API info endpoint to see all available endpoints"""
    print("\n" + "=" * 40)
    print("Testing API Info Endpoint")
    print("=" * 40)
    
    try:
        response = requests.get(f"{API_BASE_URL}/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"API Name: {data['name']}")
            print(f"Version: {data['version']}")
            print(f"Description: {data['description']}")
            print("\nAvailable Endpoints:")
            for endpoint, description in data['endpoints'].items():
                print(f"  {endpoint}: {description}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    print("SBTC Datapoint API Test Suite")
    print("Make sure the API server is running on http://localhost:5000")
    print()
    
    # Test API info first
    test_api_info()
    
    # Test datapoint endpoints
    test_datapoint_endpoints()
    
    print("\n" + "=" * 40)
    print("Test completed!")
    print("=" * 40)

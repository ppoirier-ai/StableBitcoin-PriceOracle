#!/usr/bin/env python3
"""
Solana Datapoint Client for SBTC Oracle
Handles storing and retrieving SBTC datapoints from the Solana program
"""

import json
import requests
import subprocess
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import base58

# Configuration
PROGRAM_ID = "FtDpp1TsamUskkz2AS7NTuRGqyB3j4dpP7mj9ATHbDoa"
PYTH_BTC_PRICE_ACCOUNT = "8SXvChNYFh3qEi4J6tK1wQREu5x6YdE3C6HmZzThoG6E"
RPC_URL = "https://api.devnet.solana.com"
API_BASE_URL = "http://localhost:5000"

class SolanaDatapointClient:
    def __init__(self, keypair_path: str = "~/.config/solana/id.json"):
        self.keypair_path = keypair_path
        self.program_id = PROGRAM_ID
        self.pyth_btc_account = PYTH_BTC_PRICE_ACCOUNT
        self.rpc_url = RPC_URL
        self.api_base_url = API_BASE_URL

    def get_sbtc_value_from_api(self) -> Tuple[float, float, int]:
        """Get current SBTC value from the API"""
        try:
            response = requests.get(f"{self.api_base_url}/sbtc/current")
            response.raise_for_status()
            data = response.json()
            
            if data['success']:
                return (
                    data['data']['sbtc_target_price'],
                    data['data']['current_btc_price'],
                    data['data']['data_points_used']
                )
            else:
                raise Exception(f"API error: {data.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"Error fetching SBTC value from API: {e}")
            raise

    def store_datapoint(self, sbtc_value: float, btc_price: float, data_points_used: int) -> str:
        """Store a datapoint to the Solana program"""
        try:
            # Convert to cents
            sbtc_cents = int(sbtc_value * 100)
            btc_cents = int(btc_price * 100)
            
            # Build the Solana program invoke command
            cmd = [
                "solana", "program", "invoke",
                "--program-id", self.program_id,
                "--accounts", f"datapoint=<DATAPOINT_ACCOUNT>",
                "--accounts", f"authority={self.keypair_path}",
                "--accounts", f"system_program=11111111111111111111111111111111",
                "--data", f"store_datapoint {sbtc_cents} {btc_cents} {data_points_used}",
                "--url", self.rpc_url
            ]
            
            print(f"Storing datapoint: SBTC=${sbtc_value:.2f}, BTC=${btc_price:.2f}, data_points={data_points_used}")
            print(f"Command: {' '.join(cmd)}")
            
            # Note: This is a simplified example. In practice, you'd need to:
            # 1. Generate the datapoint account address
            # 2. Handle account creation properly
            # 3. Use proper Anchor client libraries
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"Transaction successful: {result.stdout}")
            return result.stdout.strip()
            
        except subprocess.CalledProcessError as e:
            print(f"Transaction failed: {e.stderr}")
            raise
        except Exception as e:
            print(f"Error storing datapoint: {e}")
            raise

    def get_last_datapoint(self) -> Dict:
        """Get the last stored datapoint"""
        try:
            cmd = [
                "solana", "program", "invoke",
                "--program-id", self.program_id,
                "--accounts", f"datapoint=<DATAPOINT_ACCOUNT>",
                "--data", "get_last_datapoint",
                "--url", self.rpc_url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            # Parse the result (this would need proper deserialization)
            return {"status": "success", "data": result.stdout}
            
        except subprocess.CalledProcessError as e:
            print(f"Failed to get last datapoint: {e.stderr}")
            return {"status": "error", "error": e.stderr}
        except Exception as e:
            print(f"Error getting last datapoint: {e}")
            return {"status": "error", "error": str(e)}

    def get_datapoint_batch(self, start_timestamp: int, end_timestamp: int) -> Dict:
        """Get datapoints within a timestamp range"""
        try:
            cmd = [
                "solana", "program", "invoke",
                "--program-id", self.program_id,
                "--accounts", f"datapoint=<DATAPOINT_ACCOUNT>",
                "--data", f"get_datapoint_batch {start_timestamp} {end_timestamp}",
                "--url", self.rpc_url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return {"status": "success", "data": result.stdout}
            
        except subprocess.CalledProcessError as e:
            print(f"Failed to get datapoint batch: {e.stderr}")
            return {"status": "error", "error": e.stderr}
        except Exception as e:
            print(f"Error getting datapoint batch: {e}")
            return {"status": "error", "error": str(e)}

    def store_current_sbtc_datapoint(self) -> str:
        """Get current SBTC value and store it as a datapoint"""
        try:
            sbtc_value, btc_price, data_points_used = self.get_sbtc_value_from_api()
            return self.store_datapoint(sbtc_value, btc_price, data_points_used)
        except Exception as e:
            print(f"Error storing current SBTC datapoint: {e}")
            raise

def main():
    """Main function for testing the datapoint client"""
    client = SolanaDatapointClient()
    
    print("SBTC Datapoint Client")
    print("====================")
    
    try:
        # Test storing a datapoint
        print("\n1. Storing current SBTC datapoint...")
        tx_signature = client.store_current_sbtc_datapoint()
        print(f"Transaction signature: {tx_signature}")
        
        # Test getting last datapoint
        print("\n2. Getting last datapoint...")
        last_datapoint = client.get_last_datapoint()
        print(f"Last datapoint: {json.dumps(last_datapoint, indent=2)}")
        
        # Test getting datapoint batch (last 24 hours)
        print("\n3. Getting datapoint batch (last 24 hours)...")
        end_time = int(time.time())
        start_time = end_time - (24 * 60 * 60)  # 24 hours ago
        batch = client.get_datapoint_batch(start_time, end_time)
        print(f"Datapoint batch: {json.dumps(batch, indent=2)}")
        
    except Exception as e:
        print(f"Error in main: {e}")

if __name__ == "__main__":
    main()

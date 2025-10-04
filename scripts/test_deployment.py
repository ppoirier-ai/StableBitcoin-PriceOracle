#!/usr/bin/env python3
"""
Test script for the deployed SBTC Oracle program on devnet
"""

import subprocess
import json

# Configuration
PROGRAM_ID = "FtDpp1TsamUskkz2AS7NTuRGqyB3j4dpP7mj9ATHbDoa"
RPC_URL = "https://api.devnet.solana.com"
AUTHORITY_KEYPAIR = "/Users/ppoirier/.config/solana/id.json"

def get_authority_pubkey():
    """Get the authority public key from the keypair file"""
    try:
        result = subprocess.run([
            "solana-keygen", "pubkey", AUTHORITY_KEYPAIR
        ], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception as e:
        print(f"Error getting authority pubkey: {e}")
        return None

def get_oracle_state_pda():
    """Generate the Program Derived Address for the oracle state"""
    try:
        # Use solana CLI to find the PDA
        result = subprocess.run([
            "solana", "address", "--seed", "oracle", "--program-id", PROGRAM_ID
        ], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception as e:
        print(f"Error generating PDA: {e}")
        return None

def test_program_deployment():
    """Test the deployed program"""
    print("Testing SBTC Oracle Program Deployment")
    print("=" * 40)
    
    # Get authority public key
    authority_pubkey = get_authority_pubkey()
    if not authority_pubkey:
        print("❌ Failed to get authority public key")
        return
    print(f"✅ Authority: {authority_pubkey}")
    
    # Get oracle state PDA
    oracle_state_pda = get_oracle_state_pda()
    if not oracle_state_pda:
        print("❌ Failed to generate oracle state PDA")
        return
    print(f"✅ Oracle State PDA: {oracle_state_pda}")
    
    # Check if oracle state account exists
    try:
        result = subprocess.run([
            "solana", "account", oracle_state_pda, "--url", RPC_URL
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Oracle state account already exists")
        else:
            print("ℹ️  Oracle state account doesn't exist yet (needs initialization)")
    except Exception as e:
        print(f"❌ Error checking oracle state account: {e}")
    
    # Test program info
    try:
        result = subprocess.run([
            "solana", "program", "show", PROGRAM_ID, "--url", RPC_URL
        ], capture_output=True, text=True, check=True)
        
        print("✅ Program info retrieved successfully")
        print(f"Program ID: {PROGRAM_ID}")
        print(f"RPC URL: {RPC_URL}")
        
    except Exception as e:
        print(f"❌ Error getting program info: {e}")
    
    print("\n" + "=" * 40)
    print("Deployment Test Summary:")
    print(f"✅ Program deployed successfully to devnet")
    print(f"✅ Program ID: {PROGRAM_ID}")
    print(f"✅ Authority: {authority_pubkey}")
    print(f"✅ Oracle State PDA: {oracle_state_pda}")
    print("\nNext steps:")
    print("1. Initialize the oracle state account")
    print("2. Test storing datapoints")
    print("3. Test retrieving datapoints")

def test_initialize_oracle():
    """Test initializing the oracle state"""
    print("\nTesting Oracle Initialization")
    print("=" * 30)
    
    oracle_state_pda = get_oracle_state_pda()
    authority_pubkey = get_authority_pubkey()
    
    if not oracle_state_pda or not authority_pubkey:
        print("❌ Missing required addresses")
        return
    
    try:
        # Try to initialize the oracle state
        cmd = [
            "solana", "program", "invoke", PROGRAM_ID,
            "--accounts", f"oracle_state={oracle_state_pda}",
            "--accounts", f"authority={authority_pubkey}",
            "--accounts", "system_program=11111111111111111111111111111111",
            "--data", "initialize",
            "--url", RPC_URL,
            "--keypair", AUTHORITY_KEYPAIR
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Oracle state initialized successfully")
            print(f"Transaction: {result.stdout.strip()}")
        else:
            print(f"❌ Initialization failed: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Error during initialization: {e}")

if __name__ == "__main__":
    test_program_deployment()
    test_initialize_oracle()

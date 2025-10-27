#!/usr/bin/env python3
"""
Test script for new config format:
{
  "last_sync_config": "timestamp",
  "auto_start": true,
  "miners": [...]
}
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:9098"

def test_new_config_format():
    """Test updating config with new format"""
    
    # New format with wrapper object
    config = {
        "last_sync_config": datetime.now().isoformat(),
        "auto_start": True,
        "miners": [
            {
                "coin_name": "vrsc",
                "mining_tool": "ccminer",
                "config": {
                    "pools": [
                        {
                            "name": "AP",
                            "url": "stratum+tcp://ap.luckpool.net:3956",
                            "timeout": 150,
                            "disabled": 0
                        }
                    ],
                    "user": "RCtqovjA8xLBxdQoHJcepDBd9h6Lh7pPxp.worker1",
                    "algo": "verus",
                    "threads": 8,
                    "cpu-priority": 1
                },
                "required_files": ["ccminer"],
                "auto_start": False
            },
            {
                "coin_name": "dero",
                "mining_tool": "astrominer",
                "config": "-w deroi1qyzlxxgq2weyqlxg5u4tkng2lf5rktwanqhse2hwm577ps22zv2x2q9pvfz92 -r dero.rabidmining.com:10300 -m 8",
                "required_files": ["astrominer"],
                "auto_start": True
            }
        ]
    }
    
    print("=" * 70)
    print("📤 Sending config update with NEW FORMAT")
    print("=" * 70)
    print(f"last_sync_config: {config['last_sync_config']}")
    print(f"auto_start: {config['auto_start']}")
    print(f"miners count: {len(config['miners'])}")
    print()
    
    response = requests.post(
        f"{BASE_URL}/api/update-config",
        json=config,
        headers={"Content-Type": "application/json"}
    )
    
    result = response.json()
    print(f"✅ Response:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print()
    
    return result

def test_get_status():
    """Test getting status with last_sync_config"""
    
    print("=" * 70)
    print("📊 Getting ALL miners status")
    print("=" * 70)
    
    response = requests.get(f"{BASE_URL}/api/status")
    result = response.json()
    
    print(f"✅ Response:")
    print(f"last_sync_config: {result.get('last_sync_config')}")
    print(f"Total miners: {len(result.get('miners', []))}")
    print()
    
    for miner in result.get('miners', []):
        print(f"  - {miner['name']}:")
        print(f"      Status: {miner['status']}")
        print(f"      Coin: {miner['coin_name']}")
        print(f"      Tool: {miner['mining_tool']}")
        print(f"      PID: {miner.get('pid')}")
        print(f"      Hash Rate: {miner.get('hash_rate')} H/s")
        print(f"      Last Sync Config: {miner.get('last_sync_config')}")
        print()
    
    return result

def test_get_single_status():
    """Test getting single miner status"""
    
    print("=" * 70)
    print("📊 Getting SINGLE miner status (vrsc)")
    print("=" * 70)
    
    response = requests.get(f"{BASE_URL}/api/status?name=vrsc")
    result = response.json()
    
    print(f"✅ Response:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print()
    
    return result

def main():
    print("\n")
    print("🚀 " * 35)
    print("Testing NEW Config Format")
    print("🚀 " * 35)
    print("\n")
    
    try:
        # Test 1: Update config with new format
        print("\nTEST 1: Update Config with New Format")
        print("-" * 70)
        test_new_config_format()
        
        import time
        time.sleep(3)
        
        # Test 2: Get all status
        print("\nTEST 2: Get All Miners Status")
        print("-" * 70)
        test_get_status()
        
        # Test 3: Get single miner status
        print("\nTEST 3: Get Single Miner Status")
        print("-" * 70)
        test_get_single_status()
        
        print("\n" + "=" * 70)
        print("✅ All tests completed!")
        print("=" * 70)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to server at " + BASE_URL)
        print("   Make sure the mining manager is running!")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()

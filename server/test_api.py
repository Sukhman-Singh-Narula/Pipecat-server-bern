#!/usr/bin/env python3
"""
Test script to validate our enhanced API endpoints
"""

import json
import requests
import time

def test_endpoints():
    """Test the enhanced API endpoints"""
    base_url = "http://localhost:7860"
    
    print("🧪 Testing Enhanced Pipecat Server API Endpoints")
    print("=" * 50)
    
    try:
        # Test root endpoint
        print("\n1. Testing root endpoint...")
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Root endpoint works - Server: {data.get('message', 'Unknown')}")
            print(f"   Features: {len(data.get('features', []))} features available")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
        
        # Test health endpoint
        print("\n2. Testing health endpoint...")
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Health check works - Status: {health.get('status', 'Unknown')}")
            print(f"   ESP32 mode: {health.get('esp32_mode', False)}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
        
        # Test docs endpoint
        print("\n3. Testing documentation endpoint...")
        response = requests.get(f"{base_url}/docs")
        if response.status_code == 200:
            print("✅ FastAPI docs endpoint works")
        else:
            print(f"❌ Docs endpoint failed: {response.status_code}")
        
        # Test enhanced users endpoint structure
        print("\n4. Testing enhanced users endpoint structure...")
        response = requests.get(f"{base_url}/users/")
        print(f"   Enhanced Users endpoint: {response.status_code} (expected 200 if no users)")
        
        # Test episodes endpoint structure  
        print("\n5. Testing episodes endpoint structure...")
        response = requests.get(f"{base_url}/episodes/")
        print(f"   Episodes endpoint: {response.status_code} (expected 200 if no episodes)")
        
        # Test conversations endpoint structure
        print("\n6. Testing conversations endpoint structure...")
        response = requests.get(f"{base_url}/conversations/stats/overview")
        print(f"   Conversations endpoint: {response.status_code} (expected 200)")
        
        print("\n🎉 API endpoint validation complete!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on port 7860.")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    test_endpoints()

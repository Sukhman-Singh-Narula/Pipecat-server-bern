#!/usr/bin/env python3

"""
Test script for the new add-devices endpoint
"""

import requests
import json

def test_add_devices_endpoint():
    """Test the /api/add-devices endpoint"""
    
    # Test the endpoint (assuming server is running on localhost:7860)
    url = "http://localhost:7862/api/add-devices"
    
    try:
        print("Testing /api/add-devices endpoint...")
        print(f"POST {url}")
        
        response = requests.post(url)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ SUCCESS!")
            print(f"Message: {data.get('message')}")
            print(f"Total Created: {data.get('total_created')}")
            print("\nCreated Devices:")
            for device in data.get('devices', []):
                print(f"  - Device ID: {device['device_id']}")
                print(f"    Name: {device['name']}")
                print(f"    Email: {device['email']}")
                print(f"    Age: {device['age']}")
                print(f"    Season: {device['season']}, Episode: {device['episode']}")
                print()
        else:
            print(f"\n❌ ERROR: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the server is running on localhost:7860")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_add_devices_endpoint()

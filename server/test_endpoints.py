#!/usr/bin/env python3
"""
Test script for Enhanced Pipecat Server endpoints
"""

import requests
import json
import sys

BASE_URL = "http://127.0.0.1:7860"

def test_endpoint(method, endpoint, data=None, expected_status=200):
    """Test an endpoint and return result"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url)
        elif method.upper() == "POST":
            response = requests.post(url, json=data)
        else:
            response = requests.request(method, url, json=data)
        
        success = response.status_code == expected_status
        
        print(f"{'✅' if success else '❌'} {method.upper()} {endpoint}")
        print(f"   Status: {response.status_code}")
        
        try:
            result = response.json()
            print(f"   Response: {json.dumps(result, indent=2)[:200]}...")
        except:
            print(f"   Response: {response.text[:200]}...")
        
        print()
        return success
        
    except Exception as e:
        print(f"❌ {method.upper()} {endpoint}")
        print(f"   Error: {e}")
        print()
        return False

def main():
    """Run all endpoint tests"""
    print("🚀 Testing Enhanced Pipecat Server Endpoints")
    print("=" * 50)
    
    tests = [
        # Basic endpoints
        ("GET", "/", None, 200),
        ("GET", "/health", None, 200),
        ("GET", "/docs", None, 200),
        
        # WebRTC endpoints (most important for ESP32)
        ("GET", "/client", None, 200),
        ("POST", "/api/offer", {"type": "offer", "sdp": "v=0\\r\\no=test"}, 200),
        
        # Auth endpoints
        ("POST", "/auth/validate-device-id?device_id=TEST1234", None, 200),
        ("POST", "/auth/validate-device-id?device_id=INVALID", None, 200),
        ("GET", "/auth/verify/TEST1234", None, 200),
        
        # User endpoints (these might fail due to service issues, but should be accessible)
        ("GET", "/users/TEST1234", None, 404),  # Expect 404 for non-existent user
        
        # Prompt endpoints
        ("GET", "/prompts/", None, 200),
    ]
    
    passed = 0
    total = len(tests)
    
    for method, endpoint, data, expected_status in tests:
        if test_endpoint(method, endpoint, data, expected_status):
            passed += 1
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Your server is ready for ESP32 devices.")
    else:
        print("⚠️  Some tests failed. Check the server logs for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

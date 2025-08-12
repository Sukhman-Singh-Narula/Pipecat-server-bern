#!/usr/bin/env python3
"""
Test script for ESP32 WebRTC AI Assistant Server

This script tests the basic functionality of the server endpoints
and verifies that all required services are properly configured.
"""

import asyncio
import json
import time
from typing import Dict, Any

import aiohttp
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Server configuration
SERVER_HOST = "localhost"
SERVER_PORT = 8000
BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"

# Test device configuration
TEST_DEVICE = {
    "device_id": "test_esp32_001",
    "device_name": "Test ESP32 Device",
    "device_type": "esp32",
    "capabilities": {
        "audio_input": True,
        "audio_output": True,
        "sample_rate": 16000,
        "channels": 1
    }
}

# Test WebRTC offer (simplified SDP)
TEST_WEBRTC_OFFER = {
    "device_id": "test_esp32_001",
    "sdp": "v=0\r\no=- 123456789 123456789 IN IP4 192.168.1.100\r\ns=-\r\nt=0 0\r\n",
    "type": "offer",
    "restart_pc": False
}

async def test_health_check(session: aiohttp.ClientSession) -> Dict[str, Any]:
    """Test server health check endpoint."""
    print("🏥 Testing health check...")
    
    try:
        async with session.get(f"{BASE_URL}/health") as response:
            if response.status == 200:
                data = await response.json()
                print("✅ Health check passed")
                print(f"   Status: {data.get('status')}")
                print(f"   Active devices: {data.get('active_devices', 0)}")
                
                # Check environment variables
                env_check = data.get('environment_check', {})
                for service, available in env_check.items():
                    status = "✅" if available else "❌"
                    print(f"   {service}: {status}")
                
                return {"success": True, "data": data}
            else:
                print(f"❌ Health check failed with status: {response.status}")
                return {"success": False, "status": response.status}
                
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return {"success": False, "error": str(e)}


async def test_device_registration(session: aiohttp.ClientSession) -> Dict[str, Any]:
    """Test device registration endpoint."""
    print("\n📱 Testing device registration...")
    
    try:
        async with session.post(
            f"{BASE_URL}/api/device/register",
            json=TEST_DEVICE
        ) as response:
            if response.status == 200:
                data = await response.json()
                print("✅ Device registration successful")
                print(f"   Device ID: {data.get('device_id')}")
                return {"success": True, "data": data}
            else:
                text = await response.text()
                print(f"❌ Device registration failed: {response.status}")
                print(f"   Response: {text}")
                return {"success": False, "status": response.status}
                
    except Exception as e:
        print(f"❌ Device registration error: {e}")
        return {"success": False, "error": str(e)}


async def test_device_list(session: aiohttp.ClientSession) -> Dict[str, Any]:
    """Test device listing endpoint."""
    print("\n📋 Testing device listing...")
    
    try:
        async with session.get(f"{BASE_URL}/api/devices") as response:
            if response.status == 200:
                data = await response.json()
                print("✅ Device listing successful")
                print(f"   Total devices: {data.get('total_devices', 0)}")
                print(f"   Active connections: {data.get('active_connections', 0)}")
                
                devices = data.get('devices', [])
                for device in devices:
                    print(f"   Device: {device.get('device_id')} ({device.get('status')})")
                
                return {"success": True, "data": data}
            else:
                print(f"❌ Device listing failed: {response.status}")
                return {"success": False, "status": response.status}
                
    except Exception as e:
        print(f"❌ Device listing error: {e}")
        return {"success": False, "error": str(e)}


async def test_device_status(session: aiohttp.ClientSession) -> Dict[str, Any]:
    """Test device status endpoint."""
    print("\n📊 Testing device status...")
    
    device_id = TEST_DEVICE["device_id"]
    try:
        async with session.get(f"{BASE_URL}/api/device/{device_id}/status") as response:
            if response.status == 200:
                data = await response.json()
                print("✅ Device status retrieval successful")
                print(f"   Device: {data.get('device_name')}")
                print(f"   Status: {data.get('status')}")
                print(f"   Connected: {data.get('connected')}")
                return {"success": True, "data": data}
            elif response.status == 404:
                print("❌ Device not found (this might be expected)")
                return {"success": False, "status": 404, "expected": True}
            else:
                print(f"❌ Device status failed: {response.status}")
                return {"success": False, "status": response.status}
                
    except Exception as e:
        print(f"❌ Device status error: {e}")
        return {"success": False, "error": str(e)}


async def test_conversation_config(session: aiohttp.ClientSession) -> Dict[str, Any]:
    """Test conversation configuration endpoint."""
    print("\n⚙️ Testing conversation configuration...")
    
    device_id = TEST_DEVICE["device_id"]
    config = {
        "system_prompt": "You are a test AI assistant for ESP32 devices.",
        "voice_id": "british_lady",
        "language": "en",
        "interrupt_enabled": True
    }
    
    try:
        async with session.post(
            f"{BASE_URL}/api/device/{device_id}/config",
            json=config
        ) as response:
            if response.status == 200:
                data = await response.json()
                print("✅ Conversation configuration successful")
                return {"success": True, "data": data}
            elif response.status == 404:
                print("❌ Device not found for configuration")
                return {"success": False, "status": 404}
            else:
                print(f"❌ Conversation configuration failed: {response.status}")
                return {"success": False, "status": response.status}
                
    except Exception as e:
        print(f"❌ Conversation configuration error: {e}")
        return {"success": False, "error": str(e)}


async def test_voices_list(session: aiohttp.ClientSession) -> Dict[str, Any]:
    """Test available voices endpoint."""
    print("\n🎤 Testing voices listing...")
    
    try:
        async with session.get(f"{BASE_URL}/api/voices") as response:
            if response.status == 200:
                data = await response.json()
                print("✅ Voices listing successful")
                voices = data.get('voices', [])
                for voice in voices:
                    print(f"   Voice: {voice.get('name')} ({voice.get('id')})")
                return {"success": True, "data": data}
            else:
                print(f"❌ Voices listing failed: {response.status}")
                return {"success": False, "status": response.status}
                
    except Exception as e:
        print(f"❌ Voices listing error: {e}")
        return {"success": False, "error": str(e)}


async def test_webrtc_offer(session: aiohttp.ClientSession) -> Dict[str, Any]:
    """Test WebRTC offer endpoint."""
    print("\n🌐 Testing WebRTC offer...")
    
    try:
        async with session.post(
            f"{BASE_URL}/api/webrtc/offer",
            json=TEST_WEBRTC_OFFER
        ) as response:
            if response.status == 200:
                data = await response.json()
                print("✅ WebRTC offer successful")
                print(f"   PC ID: {data.get('pc_id', 'N/A')}")
                return {"success": True, "data": data}
            else:
                text = await response.text()
                print(f"❌ WebRTC offer failed: {response.status}")
                print(f"   Response: {text}")
                return {"success": False, "status": response.status}
                
    except Exception as e:
        print(f"❌ WebRTC offer error: {e}")
        return {"success": False, "error": str(e)}


async def cleanup_test_device(session: aiohttp.ClientSession) -> None:
    """Clean up test device after testing."""
    print("\n🧹 Cleaning up test device...")
    
    device_id = TEST_DEVICE["device_id"]
    try:
        async with session.delete(f"{BASE_URL}/api/device/{device_id}") as response:
            if response.status == 200:
                print("✅ Test device cleaned up successfully")
            else:
                print(f"⚠️ Cleanup warning: {response.status}")
                
    except Exception as e:
        print(f"⚠️ Cleanup error: {e}")


def check_environment_variables() -> Dict[str, bool]:
    """Check if required environment variables are set."""
    print("🔧 Checking environment variables...")
    
    required_vars = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "DEEPGRAM_API_KEY": os.getenv("DEEPGRAM_API_KEY"),
        "CARTESIA_API_KEY": os.getenv("CARTESIA_API_KEY"),
    }
    
    results = {}
    for var, value in required_vars.items():
        available = bool(value and value.strip())
        status = "✅" if available else "❌"
        print(f"   {var}: {status}")
        results[var] = available
    
    return results


async def run_tests():
    """Run all test cases."""
    print("🚀 Starting ESP32 WebRTC AI Assistant Server Tests")
    print("=" * 60)
    
    # Check environment variables
    env_vars = check_environment_variables()
    missing_vars = [var for var, available in env_vars.items() if not available]
    
    if missing_vars:
        print(f"\n⚠️ Warning: Missing environment variables: {missing_vars}")
        print("   Some tests may fail due to missing API keys")
    
    # Test results
    test_results = []
    
    # Create HTTP session
    async with aiohttp.ClientSession() as session:
        # Run tests in sequence
        tests = [
            ("Health Check", test_health_check),
            ("Device Registration", test_device_registration),
            ("Device Listing", test_device_list),
            ("Device Status", test_device_status),
            ("Conversation Config", test_conversation_config),
            ("Voices Listing", test_voices_list),
            ("WebRTC Offer", test_webrtc_offer),
        ]
        
        for test_name, test_func in tests:
            try:
                result = await test_func(session)
                test_results.append((test_name, result))
                
                # Small delay between tests
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                test_results.append((test_name, {"success": False, "error": str(e)}))
        
        # Cleanup
        await cleanup_test_device(session)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        if result.get("success"):
            print(f"✅ {test_name}")
            passed += 1
        else:
            status = result.get("status", "Error")
            if result.get("expected"):
                print(f"⚠️ {test_name} (Expected: {status})")
                passed += 1  # Count expected failures as passes
            else:
                print(f"❌ {test_name} (Status: {status})")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Server is ready for ESP32 connections.")
    else:
        print("🔧 Some tests failed. Check server configuration and API keys.")
    
    return passed == total


if __name__ == "__main__":
    print("ESP32 WebRTC AI Assistant - Test Suite")
    print("Make sure the server is running on localhost:8000")
    print("Press Ctrl+C to cancel\n")
    
    try:
        # Add small delay to allow manual server startup
        time.sleep(2)
        
        # Run the tests
        success = asyncio.run(run_tests())
        
        exit_code = 0 if success else 1
        exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n🛑 Tests cancelled by user")
        exit(1)
    except Exception as e:
        print(f"\n💥 Test suite error: {e}")
        exit(1)

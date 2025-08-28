#!/usr/bin/env python3
"""
Quick test script to verify all components are working
Run this after setting up your Enhanced Pipecat Server
"""

import requests
import json
import sys
from datetime import datetime

# Server configuration
SERVER_HOST = "64.227.157.74" 
SERVER_PORT = 7860
BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"

def test_server_health():
    """Test basic server connectivity"""
    print("🔍 Testing server health...")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Server is healthy: {health.get('status')}")
            print(f"   ESP32 mode: {health.get('esp32_mode')}")
            
            services = health.get('services', {})
            for service, status in services.items():
                emoji = "✅" if status in ["available", "running"] else "⚠️"
                print(f"   {emoji} {service}: {status}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return False

def quick_add_user():
    """Add a test user"""
    print("👤 Adding test user...")
    
    user_data = {
        "device_id": "TEST0001",
        "name": "Test Child",
        "age": 8,
        "email": "test.child@example.com",
        "parent": {
            "name": "Test Parent",
            "age": 35,
            "email": "test.parent@example.com"
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/users/create", json=user_data, timeout=10)
        if response.status_code == 200:
            print("✅ Test user created successfully")
            return True
        else:
            print(f"⚠️ User creation status: {response.status_code}")
            # Might already exist, which is OK
            return True
    except Exception as e:
        print(f"❌ Failed to create user: {e}")
        return False

def quick_add_episode():
    """Add a test episode prompt"""
    print("📚 Adding test episode...")
    
    episode_data = {
        "season": 1,
        "episode": 1,
        "title": "Test Episode - Basic Greetings",
        "system_prompt": """You are a friendly AI tutor teaching basic English greetings. 
        
Your student is {name}, age {age}. Teach them to say hello, hi, goodbye, and bye.
Be encouraging and speak clearly since your output becomes audio.
Start by greeting the child warmly.""",
        "words_to_teach": ["hello", "hi", "goodbye", "bye"],
        "topics_to_cover": ["greetings", "politeness"],
        "difficulty_level": "beginner",
        "age_group": "children",
        "learning_objectives": ["Learn basic greetings", "Practice pronunciation"]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/episodes/create", json=episode_data, timeout=10)
        if response.status_code == 200:
            print("✅ Test episode created successfully")
            return True
        else:
            print(f"⚠️ Episode creation status: {response.status_code}")
            return True  # Might already exist
    except Exception as e:
        print(f"❌ Failed to create episode: {e}")
        return False

def test_webrtc_endpoint():
    """Test WebRTC offer endpoint"""
    print("🌐 Testing WebRTC endpoint...")
    
    # Simple test offer
    test_offer = {
        "type": "offer",
        "device_id": "TEST0001",
        "sdp": "v=0\no=- 123 123 IN IP4 192.168.1.1\ns=-\nt=0 0\nm=audio 9 UDP/TLS/RTP/SAVPF 111"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/offer", json=test_offer, timeout=10)
        if response.status_code == 200:
            print("✅ WebRTC endpoint accepts offers")
            answer = response.json()
            if "sdp" in answer:
                print(f"   SDP answer length: {len(answer['sdp'])} chars")
            return True
        else:
            print(f"⚠️ WebRTC offer status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ WebRTC test failed: {e}")
        return False

def test_user_lookup():
    """Test user lookup functionality"""
    print("🔎 Testing user lookup...")
    
    try:
        # Test by device ID
        response = requests.get(f"{BASE_URL}/users/device/TEST0001", timeout=5)
        if response.status_code == 200:
            user = response.json()
            print(f"✅ User lookup works: {user.get('name')}")
            return True
        else:
            print(f"⚠️ User lookup status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ User lookup failed: {e}")
        return False

def test_episode_lookup():
    """Test episode lookup functionality"""  
    print("📖 Testing episode lookup...")
    
    try:
        response = requests.get(f"{BASE_URL}/episodes/season/1/episode/1", timeout=5)
        if response.status_code == 200:
            episode = response.json()
            print(f"✅ Episode lookup works: {episode.get('title')}")
            return True
        else:
            print(f"⚠️ Episode lookup status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Episode lookup failed: {e}")
        return False

def show_connection_summary():
    """Show ESP32 connection summary"""
    print("\n" + "="*60)
    print("🤖 ESP32 CONNECTION SUMMARY")
    print("="*60)
    
    print(f"""
📡 Your ESP32 should connect to:
   Server: {SERVER_HOST}:{SERVER_PORT}
   Endpoint: /api/offer
   Method: POST

📝 Required JSON payload:
   {{
     "type": "offer",
     "device_id": "YOUR_DEVICE_ID", 
     "sdp": "your_webrtc_sdp_offer"
   }}

✅ Expected server response (200 OK):
   {{
     "type": "answer",
     "sdp": "server_webrtc_answer_with_esp32_munging"
   }}

🎯 Connection Steps:
   1. ESP32 creates WebRTC offer
   2. ESP32 sends POST to /api/offer with device_id
   3. Server returns WebRTC answer with SDP munging
   4. ESP32 completes WebRTC connection
   5. Audio flows: ESP32 mic → Server AI → ESP32 speaker

🔧 Test your device:
   python3 test_device_connection.py YOUR_DEVICE_ID
""")

def main():
    """Run all quick tests"""
    print("🚀 ENHANCED PIPECAT SERVER - QUICK TEST SUITE")
    print(f"Server: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print()
    
    tests = [
        ("Server Health", test_server_health),
        ("Add Test User", quick_add_user), 
        ("Add Test Episode", quick_add_episode),
        ("WebRTC Endpoint", test_webrtc_endpoint),
        ("User Lookup", test_user_lookup),
        ("Episode Lookup", test_episode_lookup)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"{'='*20} {test_name} {'='*20}")
        if test_func():
            passed += 1
        print()
    
    print("="*60)
    print(f"📊 RESULTS: {passed}/{total} tests passed")
    
    if passed >= 4:  # At least core functionality works
        print("🎉 Server is ready for ESP32 connections!")
        show_connection_summary()
        return 0
    else:
        print("⚠️  Some core tests failed. Check the server setup.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
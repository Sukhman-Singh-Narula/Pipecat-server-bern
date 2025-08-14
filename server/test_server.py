#!/usr/bin/env python3
"""
Test script for the Enhanced Pipecat Server
This script demonstrates the key functionalities
"""

import asyncio
import aiohttp
import json
from datetime import datetime


class ServerTester:
    def __init__(self, base_url="http://localhost:7860"):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_server_health(self):
        """Test server health check"""
        print("🔍 Testing server health...")
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Server is healthy: {data['status']}")
                    return True
                else:
                    print(f"❌ Server health check failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Failed to connect to server: {e}")
            return False
    
    async def test_user_registration(self):
        """Test user registration"""
        print("\n👤 Testing user registration...")
        
        user_data = {
            "device_id": "TEST1234",
            "name": "Test User",
            "age": 25
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/auth/register",
                json=user_data
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    print(f"✅ User registered successfully: {data['device_id']}")
                    return True
                elif response.status == 409:
                    print("ℹ️  User already exists, continuing...")
                    return True
                else:
                    error_data = await response.json()
                    print(f"❌ Registration failed: {error_data}")
                    return False
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return False
    
    async def test_get_user(self):
        """Test getting user information"""
        print("\n📊 Testing get user information...")
        
        try:
            async with self.session.get(f"{self.base_url}/users/TEST1234") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ User info retrieved: Season {data['season']}, Episode {data['episode']}")
                    return True
                else:
                    error_data = await response.json()
                    print(f"❌ Failed to get user: {error_data}")
                    return False
        except Exception as e:
            print(f"❌ Get user error: {e}")
            return False
    
    async def test_create_prompt(self):
        """Test creating a system prompt"""
        print("\n📝 Testing system prompt creation...")
        
        prompt_data = {
            "season": 1,
            "episode": 1,
            "prompt": "You are a friendly English tutor helping beginners learn basic vocabulary. Be encouraging and patient.",
            "prompt_type": "learning",
            "metadata": {
                "created_by": "test_script",
                "difficulty": "beginner"
            }
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/prompts/",
                json=prompt_data
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    print(f"✅ System prompt created: Season {data['season']}, Episode {data['episode']}")
                    return True
                else:
                    error_data = await response.json()
                    print(f"❌ Prompt creation failed: {error_data}")
                    return False
        except Exception as e:
            print(f"❌ Prompt creation error: {e}")
            return False
    
    async def test_get_prompt(self):
        """Test getting a system prompt"""
        print("\n🔍 Testing get system prompt...")
        
        try:
            async with self.session.get(f"{self.base_url}/prompts/1/1") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Prompt retrieved: {data['prompt_length']} characters, type: {data['prompt_type']}")
                    return True
                else:
                    error_data = await response.json()
                    print(f"❌ Failed to get prompt: {error_data}")
                    return False
        except Exception as e:
            print(f"❌ Get prompt error: {e}")
            return False
    
    async def test_update_progress(self):
        """Test updating user progress"""
        print("\n📈 Testing progress update...")
        
        progress_data = {
            "words_learnt": ["hello", "goodbye", "thank you"],
            "topics_learnt": ["greetings", "basic politeness"]
        }
        
        try:
            async with self.session.put(
                f"{self.base_url}/users/TEST1234/progress",
                json=progress_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Progress updated: {data['words_learnt_count']} words, {data['topics_learnt_count']} topics")
                    return True
                else:
                    error_data = await response.json()
                    print(f"❌ Progress update failed: {error_data}")
                    return False
        except Exception as e:
            print(f"❌ Progress update error: {e}")
            return False
    
    async def test_get_statistics(self):
        """Test getting user statistics"""
        print("\n📊 Testing user statistics...")
        
        try:
            async with self.session.get(f"{self.base_url}/users/TEST1234/statistics") as response:
                if response.status == 200:
                    data = await response.json()
                    learning_stats = data['learning_stats']
                    print(f"✅ Statistics retrieved: {learning_stats['total_words_learnt']} words learned")
                    return True
                else:
                    error_data = await response.json()
                    print(f"❌ Failed to get statistics: {error_data}")
                    return False
        except Exception as e:
            print(f"❌ Statistics error: {e}")
            return False
    
    async def test_season_overview(self):
        """Test getting season overview"""
        print("\n📚 Testing season overview...")
        
        try:
            async with self.session.get(f"{self.base_url}/prompts/1") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Season overview: {data['completed_episodes']}/{data['total_episodes']} episodes")
                    return True
                else:
                    error_data = await response.json()
                    print(f"❌ Failed to get season overview: {error_data}")
                    return False
        except Exception as e:
            print(f"❌ Season overview error: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🧪 Starting Enhanced Pipecat Server Tests")
        print("=" * 50)
        
        tests = [
            self.test_server_health,
            self.test_user_registration,
            self.test_get_user,
            self.test_create_prompt,
            self.test_get_prompt,
            self.test_update_progress,
            self.test_get_statistics,
            self.test_season_overview
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if await test():
                    passed += 1
                await asyncio.sleep(0.5)  # Small delay between tests
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {e}")
        
        print("\n" + "=" * 50)
        print(f"📋 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Your enhanced server is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the server logs and configuration.")
        
        return passed == total


async def main():
    """Main test function"""
    print(f"Starting tests at {datetime.now()}")
    
    async with ServerTester() as tester:
        success = await tester.run_all_tests()
    
    return success


if __name__ == "__main__":
    import sys
    
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test runner failed: {e}")
        sys.exit(1)

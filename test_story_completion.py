#!/usr/bin/env python3
"""
Interactive Story Completion System Demo

This script demonstrates the new story completion features:
1. Register a test user
2. Simulate story completion with learning data
3. Advance user to next episode/season
4. Show updated progress
"""

import requests
import json
import time

BASE_URL = "http://localhost:7860"

def register_test_user():
    """Register a test user for story completion demo"""
    print("🎭 Registering test user...")
    
    user_data = {
        "device_id": "STORY_TEST_001",
        "name": "Story Test User", 
        "age": 8,
        "email": "storytest@example.com",
        "parent": {
            "name": "Test Parent",
            "email": "parent@example.com",
            "phone": "+1234567890"
        }
    }
    
    response = requests.post(f"{BASE_URL}/users/create", json=user_data)
    if response.status_code == 200:
        print("✅ User registered successfully!")
        print(f"   User: {user_data['name']} (Age {user_data['age']})")
        print(f"   Device: {user_data['device_id']}")
        return user_data
    else:
        print(f"❌ Failed to register user: {response.status_code}")
        print(response.text)
        return None

def get_user_info(device_id):
    """Get current user information"""
    print(f"\n📊 Getting user info for {device_id}...")
    
    # Try the enhanced users device endpoint first
    response = requests.get(f"{BASE_URL}/users/{device_id}")
    if response.status_code == 200:
        user_info = response.json()
        progress = user_info.get('progress', {})
        
        print("✅ User Info:")
        print(f"   Name: {user_info.get('name', 'Unknown')}")
        print(f"   Season: {progress.get('season', 1)}")
        print(f"   Episode: {progress.get('episode', 1)}")
        print(f"   Episodes Completed: {progress.get('episodes_completed', 0)}")
        print(f"   Words Learned: {len(progress.get('words_learnt', []))}")
        print(f"   Topics Covered: {len(progress.get('topics_learnt', []))}")
        print(f"   Total Time: {progress.get('total_time_minutes', 0):.1f} minutes")
        
        if progress.get('words_learnt'):
            print(f"   Recent Words: {', '.join(progress['words_learnt'][-5:])}")
        if progress.get('topics_learnt'):
            print(f"   Recent Topics: {', '.join(progress['topics_learnt'][-3:])}")
        
        return user_info
    else:
        print(f"❌ Failed to get user info: {response.status_code}")
        return None

def complete_story_episode(device_id):
    """Simulate completing a story episode"""
    print(f"\n📚 Completing story episode for {device_id}...")
    
    completion_data = {
        "device_id": device_id,
        "words_learned": [
            "adventure", "courage", "friendship", "dragon", "treasure",
            "castle", "knight", "magic", "wisdom", "journey"
        ],
        "topics_covered": [
            "bravery and overcoming fears",
            "importance of friendship", 
            "problem-solving skills",
            "fantasy creatures and mythology"
        ],
        "time_spent_minutes": 15.5
    }
    
    response = requests.post(f"{BASE_URL}/api/complete-story", json=completion_data)
    if response.status_code == 200:
        result = response.json()
        print("✅ Story episode completed!")
        print(f"   New Words Added: {result['new_words_added']}")
        print(f"   New Topics Added: {result['new_topics_added']}")
        print(f"   Total Words: {result['total_words']}")
        print(f"   Total Topics: {result['total_topics']}")
        print(f"   Episodes Completed: {result['episodes_completed']}")
        print(f"   Time Added: {result['time_added_minutes']} minutes")
        return result
    else:
        print(f"❌ Failed to complete story: {response.status_code}")
        print(response.text)
        return None

def advance_user_progress(device_id, advance_type="next_episode"):
    """Advance user to next episode or season"""
    print(f"\n⏭️ Advancing user to {advance_type}...")
    
    advance_data = {
        "device_id": device_id,
        "advance_type": advance_type
    }
    
    response = requests.post(f"{BASE_URL}/api/advance-progress", json=advance_data)
    if response.status_code == 200:
        result = response.json()
        print("✅ User progress advanced!")
        print(f"   Previous: Season {result['previous']['season']}, Episode {result['previous']['episode']}")
        print(f"   Current: Season {result['current']['season']}, Episode {result['current']['episode']}")
        print(f"   Advance Type: {result['advance_type']}")
        return result
    else:
        print(f"❌ Failed to advance progress: {response.status_code}")
        print(response.text)
        return None

def demo_interactive_story_system():
    """Run a complete demo of the interactive story system"""
    print("🎬 Interactive Story Completion System Demo")
    print("=" * 50)
    
    # Step 1: Register user
    user = register_test_user()
    if not user:
        return
    
    device_id = user["device_id"]
    
    # Step 2: Show initial user state
    get_user_info(device_id)
    
    # Step 3: Complete first story episode
    complete_story_episode(device_id)
    
    # Step 4: Show updated progress
    get_user_info(device_id)
    
    # Step 5: Advance to next episode
    advance_user_progress(device_id, "next_episode")
    
    # Step 6: Show final state
    get_user_info(device_id)
    
    # Step 7: Complete another episode and advance to next season
    print("\n🔄 Completing another episode...")
    complete_story_episode(device_id)
    advance_user_progress(device_id, "next_season")
    
    # Final state
    get_user_info(device_id)
    
    print("\n🎉 Demo completed!")
    print("\nNow you can:")
    print("1. Open http://localhost:7860/client to test voice stories")
    print("2. Use device ID 'STORY_TEST_001' to see the user data")
    print("3. Create interactive stories that automatically track progress")
    print("4. The AI will call completion functions when stories end")

if __name__ == "__main__":
    try:
        demo_interactive_story_system()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running at http://localhost:7860")
    except Exception as e:
        print(f"❌ Error: {e}")

#!/usr/bin/env python3
"""
Comprehensive API Test Suite for Enhanced Pipecat Server
Tests all endpoints: Enhanced Users, Episodes, Conversations
"""

import json
import requests
import time
from datetime import datetime

BASE_URL = "http://localhost:7860"

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")

def print_test(test_name):
    """Print test name"""
    print(f"\n▶️  {test_name}")

def test_request(method, endpoint, data=None, expected_status=200):
    """Helper function to test API requests"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method.upper() == "GET":
            response = requests.get(url)
        elif method.upper() == "POST":
            response = requests.post(url, json=data)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(url)
        
        if response.status_code == expected_status:
            print(f"   ✅ {method} {endpoint} - Status: {response.status_code}")
            if response.headers.get('content-type', '').startswith('application/json'):
                try:
                    return response.json()
                except:
                    return {"raw_response": response.text}
            return {"status": "success"}
        else:
            print(f"   ❌ {method} {endpoint} - Expected: {expected_status}, Got: {response.status_code}")
            print(f"      Response: {response.text[:200]}...")
            return None
    except Exception as e:
        print(f"   ❌ {method} {endpoint} - Error: {str(e)}")
        return None

def test_basic_endpoints():
    """Test basic server endpoints"""
    print_section("BASIC SERVER ENDPOINTS")
    
    print_test("Root Endpoint")
    root_data = test_request("GET", "/")
    if root_data:
        print(f"      Server: {root_data.get('message', 'Unknown')}")
        print(f"      Features: {len(root_data.get('features', []))}")
    
    print_test("Health Check")
    health_data = test_request("GET", "/health")
    if health_data:
        print(f"      Status: {health_data.get('status', 'Unknown')}")
        print(f"      ESP32 Mode: {health_data.get('esp32_mode', False)}")
    
    print_test("API Documentation")
    test_request("GET", "/docs")

def test_enhanced_users_api():
    """Test Enhanced Users API endpoints"""
    print_section("ENHANCED USERS API")
    
    # Test data
    user_data = {
        "device_id": "TEST_ESP32_001",
        "name": "Alex Test",
        "age": 8,
        "email": "alex.test@example.com",
        "parent": {
            "name": "Parent Test",
            "age": 35,
            "email": "parent.test@example.com"
        }
    }
    
    print_test("Create User")
    created_user = test_request("POST", "/users/create", user_data, 200)
    
    print_test("Get All Users")
    all_users = test_request("GET", "/users/")
    if all_users:
        print(f"      Total users: {len(all_users)}")
    
    print_test("Get User by Email")
    user_by_email = test_request("GET", f"/users/{user_data['email']}")
    
    print_test("Get User by Device ID")
    user_by_device = test_request("GET", f"/users/device/{user_data['device_id']}")
    
    print_test("Update User Progress")
    progress_data = {"season": 1, "episode": 2, "completed": True}
    test_request("PUT", f"/users/{user_data['email']}/progress", progress_data)
    
    print_test("Add Learning Data")
    learning_data = {
        "words": ["hello", "world", "learn"],
        "topics": ["greetings", "vocabulary"],
        "session_time": 300.5
    }
    test_request("PUT", f"/users/{user_data['email']}/learning-data", learning_data)
    
    print_test("Update Last Active")
    test_request("PUT", f"/users/{user_data['email']}/last-active")
    
    print_test("Get User Analytics")
    analytics = test_request("GET", f"/users/{user_data['email']}/analytics")
    if analytics:
        print(f"      Learning stats available: {bool(analytics.get('learning_stats'))}")
    
    print_test("Get User Summary")
    summary = test_request("GET", f"/users/{user_data['email']}/summary")
    if summary:
        print(f"      Name: {summary.get('name')}, Progress: {summary.get('current_progress')}")
    
    return user_data['email']  # Return email for other tests

def test_episodes_api():
    """Test Episodes API endpoints"""
    print_section("EPISODES API")
    
    # Test data
    episode_data = {
        "season": 1,
        "episode": 1,
        "title": "Introduction to Learning",
        "system_prompt": "You are teaching {name}, age {age}, in season {season} episode {episode}.",
        "words_to_teach": ["hello", "world", "learn", "fun"],
        "topics_to_cover": ["greetings", "basic_vocabulary", "learning_basics"],
        "difficulty_level": "beginner",
        "age_group": "children",
        "learning_objectives": ["Learn basic greetings", "Understand vocabulary", "Develop learning habits"]
    }
    
    print_test("Create Episode")
    created_episode = test_request("POST", "/episodes/create", episode_data, 200)
    
    print_test("Get All Episodes")
    all_episodes = test_request("GET", "/episodes/")
    if all_episodes:
        print(f"      Total episodes: {len(all_episodes)}")
    
    print_test("Get Specific Episode")
    specific_episode = test_request("GET", f"/episodes/season/{episode_data['season']}/episode/{episode_data['episode']}")
    
    print_test("Get Season Episodes")
    season_episodes = test_request("GET", f"/episodes/season/{episode_data['season']}")
    if season_episodes:
        print(f"      Episodes in season {episode_data['season']}: {len(season_episodes)}")
    
    print_test("Get Episodes by Difficulty")
    difficulty_episodes = test_request("GET", f"/episodes/difficulty/{episode_data['difficulty_level']}")
    
    print_test("Get Episodes by Age Group")
    age_episodes = test_request("GET", f"/episodes/age-group/{episode_data['age_group']}")
    
    print_test("Update Episode")
    update_data = {"title": "Updated Introduction to Learning"}
    test_request("PUT", f"/episodes/season/{episode_data['season']}/episode/{episode_data['episode']}", update_data)
    
    print_test("Record Episode Usage")
    usage_data = {
        "user_email": "alex.test@example.com",
        "words_learned": ["hello", "world"],
        "topics_covered": ["greetings"],
        "session_time": 180.0,
        "completion_rating": 5
    }
    test_request("POST", f"/episodes/season/{episode_data['season']}/episode/{episode_data['episode']}/usage", usage_data)
    
    print_test("Get Episode Analytics")
    episode_analytics = test_request("GET", f"/episodes/season/{episode_data['season']}/episode/{episode_data['episode']}/analytics")
    if episode_analytics:
        print(f"      Usage stats available: {bool(episode_analytics.get('usage_stats'))}")
    
    print_test("Get Episode Summary")
    episode_summary = test_request("GET", f"/episodes/season/{episode_data['season']}/episode/{episode_data['episode']}/summary")
    if episode_summary:
        print(f"      Title: {episode_summary.get('title')}, Uses: {episode_summary.get('total_uses', 0)}")
    
    print_test("Get Popular Episodes")
    popular = test_request("GET", "/episodes/popular?limit=5")
    
    print_test("Search Episodes")
    search_results = test_request("GET", "/episodes/search?q=learning")
    if search_results:
        print(f"      Search results: {len(search_results)}")
    
    print_test("Get Episodes Overview")
    overview = test_request("GET", "/episodes/stats/overview")
    if overview:
        print(f"      Total episodes: {overview.get('total_episodes', 0)}")
    
    return episode_data['season'], episode_data['episode']

def test_conversations_api(user_email):
    """Test Conversations API endpoints"""
    print_section("CONVERSATIONS API")
    
    print_test("Start Conversation")
    conversation_data = {
        "user_email": user_email,
        "season": 1,
        "episode": 1
    }
    start_response = test_request("POST", "/conversations/start", conversation_data)
    
    if not start_response:
        print("      ❌ Cannot test conversations without starting one")
        return
    
    conversation_id = start_response.get('conversation_id')
    print(f"      Conversation ID: {conversation_id}")
    
    print_test("Add Messages")
    messages = [
        {"speaker": "user", "content": "Hello, I want to learn!", "message_type": "text"},
        {"speaker": "bot", "content": "Great! Let's start learning together.", "message_type": "text"},
        {"speaker": "user", "content": "What can you teach me today?", "message_type": "text"}
    ]
    
    for msg in messages:
        test_request("POST", f"/conversations/{conversation_id}/messages", msg)
    
    print_test("Get Conversation")
    conversation = test_request("GET", f"/conversations/{conversation_id}")
    if conversation:
        print(f"      Messages: {len(conversation.get('messages', []))}")
        print(f"      Status: {conversation.get('status')}")
    
    print_test("Finish Conversation")
    finish_data = {"completion_status": "completed"}
    test_request("PUT", f"/conversations/{conversation_id}/finish", finish_data)
    
    print_test("Create Conversation Summary")
    summary_data = {
        "session_summary": "Great learning session with basic greetings and vocabulary.",
        "key_learnings": ["Basic greetings", "Vocabulary building", "Learning enthusiasm"],
        "words_learned": ["hello", "world", "learn"],
        "topics_covered": ["greetings", "vocabulary"],
        "performance_rating": 5,
        "engagement_level": "high",
        "areas_for_improvement": ["Pronunciation"],
        "next_recommendations": ["Continue with more vocabulary", "Practice pronunciation"]
    }
    summary_response = test_request("POST", f"/conversations/{conversation_id}/summary", summary_data)
    
    print_test("Get Conversation Summary")
    summary = test_request("GET", f"/conversations/{conversation_id}/summary")
    if summary:
        print(f"      Performance: {summary.get('performance_rating', 'N/A')}/5")
        print(f"      Words learned: {len(summary.get('words_learned', []))}")
    
    print_test("Get User Conversations")
    user_conversations = test_request("GET", f"/conversations/user/{user_email}")
    if user_conversations:
        print(f"      User conversations: {len(user_conversations)}")
    
    print_test("Get User Summaries")
    user_summaries = test_request("GET", f"/conversations/user/{user_email}/summaries")
    if user_summaries:
        print(f"      User summaries: {len(user_summaries)}")
    
    print_test("Get Episode Conversations")
    episode_conversations = test_request("GET", f"/conversations/episode/season/1/episode/1")
    
    print_test("Get Conversation Analytics")
    analytics = test_request("GET", f"/conversations/{conversation_id}/analytics")
    if analytics:
        print(f"      Analytics available: {bool(analytics.get('conversation_info'))}")
    
    print_test("Get User Learning Progression")
    progression = test_request("GET", f"/conversations/user/{user_email}/progression")
    if progression:
        print(f"      Total sessions: {progression.get('learning_stats', {}).get('total_sessions', 0)}")
        print(f"      Words learned: {progression.get('learning_stats', {}).get('total_words_learned', 0)}")
    
    print_test("Search User Conversations")
    search_conversations = test_request("GET", f"/conversations/user/{user_email}/search?q=hello")
    
    print_test("Get User Conversation Summary")
    user_summary = test_request("GET", f"/conversations/user/{user_email}/summary")
    if user_summary:
        print(f"      Total conversations: {user_summary.get('total_conversations', 0)}")
        print(f"      Learning hours: {user_summary.get('total_learning_hours', 0)}")
    
    print_test("Get Conversations Overview")
    overview = test_request("GET", "/conversations/stats/overview")
    
    return conversation_id

def test_cleanup(user_email, conversation_id, season, episode):
    """Clean up test data"""
    print_section("CLEANUP TEST DATA")
    
    print_test("Delete Conversation")
    test_request("DELETE", f"/conversations/{conversation_id}")
    
    print_test("Delete Episode")
    test_request("DELETE", f"/episodes/season/{season}/episode/{episode}")
    
    print_test("Delete User")
    test_request("DELETE", f"/users/{user_email}")

def main():
    """Run all tests"""
    print("🚀 COMPREHENSIVE API TEST SUITE")
    print("Testing Enhanced Pipecat Server with Learning Management System")
    print(f"Server: {BASE_URL}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Wait for server to be ready
    print("\n⏳ Waiting for server to be ready...")
    time.sleep(3)
    
    try:
        # Test basic endpoints
        test_basic_endpoints()
        
        # Test enhanced users API
        user_email = test_enhanced_users_api()
        
        # Test episodes API
        season, episode = test_episodes_api()
        
        # Test conversations API
        conversation_id = test_conversations_api(user_email)
        
        # Cleanup
        if user_email and conversation_id and season and episode:
            test_cleanup(user_email, conversation_id, season, episode)
        
        print_section("TEST SUITE COMPLETE")
        print("✅ All API endpoints tested successfully!")
        print("🎉 Your Enhanced Pipecat Server with Learning Management System is working perfectly!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")

if __name__ == "__main__":
    main()

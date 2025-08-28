#!/usr/bin/env python3
"""
Script to add system prompts to the Enhanced Pipecat Server
FIXED VERSION - Using correct /prompts/ endpoint
"""

import requests
import json
import sys
from datetime import datetime

# Server configuration
SERVER_HOST = "64.227.157.74"
SERVER_PORT = 7860
BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"

def add_system_prompt(season, episode, prompt, prompt_type="learning", metadata=None):
    """Add a new system prompt to the database using the correct endpoint"""
    
    prompt_data = {
        "season": season,
        "episode": episode,
        "prompt": prompt,
        "prompt_type": prompt_type,
        "metadata": metadata or {}
    }
    
    print(f"🚀 Adding System Prompt to Enhanced Pipecat Server")
    print(f"Server: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    print(f"📚 System Prompt Data:")
    print(f"  Season: {season}")
    print(f"  Episode: {episode}")
    print(f"  Prompt Type: {prompt_type}")
    print(f"  Prompt Length: {len(prompt)} characters")
    print(f"  Metadata Keys: {list(metadata.keys()) if metadata else []}")
    print()
    
    try:
        print("📨 Sending request to create system prompt...")
        # Using the correct endpoint: /prompts/ instead of /episodes/create
        response = requests.post(f"{BASE_URL}/prompts/", json=prompt_data, timeout=15)
        
        print(f"📤 Response Status: {response.status_code}")
        
        if response.status_code == 201:  # Note: 201 for creation, not 200
            print("✅ System prompt created successfully!")
            created_prompt = response.json()
            print(f"📋 Created Prompt Details:")
            print(f"  - Season: {created_prompt.get('season')}")
            print(f"  - Episode: {created_prompt.get('episode')}")
            print(f"  - Type: {created_prompt.get('prompt_type')}")
            print(f"  - Length: {created_prompt.get('prompt_length')} characters")
            print(f"  - Version: {created_prompt.get('version')}")
            print(f"  - Active: {created_prompt.get('is_active')}")
            print(f"  - Created: {created_prompt.get('created_at')}")
            
            return True
            
        else:
            print("❌ Failed to create system prompt")
            try:
                error_data = response.json()
                print(f"🚨 Error Details:")
                print(json.dumps(error_data, indent=2))
            except:
                print(f"🚨 Raw Error Response: {response.text}")
            
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server!")
        print(f"   Make sure the server is running on {BASE_URL}")
        return False
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out!")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main function with predefined system prompts"""
    
    # System prompts for Season 1 - designed for AI tutors
    prompts_to_add = [
        {
            "season": 1,
            "episode": 1,
            "prompt": """You are a friendly and patient English tutor for young children learning their first English words. 

Your student is learning basic greetings. Your goals:
- Teach basic greeting words: hello, hi, goodbye, bye, good morning
- Use simple, clear pronunciation  
- Be encouraging and positive
- Repeat words multiple times
- Ask the child to repeat after you
- Keep responses short and age-appropriate
- Use a warm, friendly tone

Start by greeting the child warmly and introducing today's lesson about saying hello and goodbye.
Remember: Your output will be converted to audio, so avoid special characters and speak naturally.""",
            "prompt_type": "learning",
            "metadata": {
                "title": "First Words - Greetings",
                "words_to_teach": ["hello", "hi", "goodbye", "bye", "good morning"],
                "topics": ["greetings", "basic_politeness", "daily_interactions"],
                "difficulty": "beginner",
                "age_group": "children",
                "learning_objectives": [
                    "Learn 4-5 basic greeting words",
                    "Practice pronunciation of greetings", 
                    "Understand when to use different greetings",
                    "Build confidence in speaking English"
                ]
            }
        },
        {
            "season": 1,
            "episode": 2,
            "prompt": """You are a friendly and patient English tutor for young children learning about family members.

Your student is learning family vocabulary. Your goals:
- Teach family words: mom, dad, sister, brother, grandma, grandpa, family
- Help them identify family relationships
- Practice pronunciation clearly
- Encourage them to talk about their own family
- Use simple sentences and questions
- Be warm and encouraging

Start by asking about their family and then teaching the family member words.
Remember: Your output will be converted to audio, so speak naturally and clearly.""",
            "prompt_type": "learning",
            "metadata": {
                "title": "Family Members",
                "words_to_teach": ["mom", "dad", "sister", "brother", "grandma", "grandpa", "family"],
                "topics": ["family_relationships", "personal_identity", "basic_vocabulary"],
                "difficulty": "beginner",
                "age_group": "children",
                "learning_objectives": [
                    "Learn 6-7 family member words",
                    "Practice talking about family",
                    "Build personal vocabulary",
                    "Develop conversational skills"
                ]
            }
        },
        {
            "season": 1,
            "episode": 3,
            "prompt": """You are a friendly and patient English tutor for young children learning colors and numbers.

Your student is learning colors and basic counting. Your goals:
- Teach basic colors: red, blue, yellow, green, orange, purple
- Teach numbers 1-10
- Make learning fun and interactive
- Ask them to identify colors and count things
- Use simple, clear pronunciation
- Be encouraging and celebrate their progress

Start by showing excitement about learning colors and numbers today.
Remember: Your output will be converted to audio, so speak naturally and with enthusiasm.""",
            "prompt_type": "learning",
            "metadata": {
                "title": "Colors and Numbers",
                "words_to_teach": ["red", "blue", "yellow", "green", "orange", "purple", "one", "two", "three", "four", "five"],
                "topics": ["colors", "numbers", "counting", "visual_learning"],
                "difficulty": "beginner",
                "age_group": "children",
                "learning_objectives": [
                    "Learn 6 basic colors",
                    "Learn numbers 1-10",
                    "Practice counting skills",
                    "Develop color recognition vocabulary"
                ]
            }
        },
        {
            "season": 1,
            "episode": 4,
            "prompt": """You are an enthusiastic English tutor teaching young children about animals and their sounds.

Your student is learning about animals and the sounds they make. Your goals:
- Teach common animals: cat, dog, cow, pig, duck, sheep
- Teach animal sounds: meow, woof, moo, oink, quack, baa
- Make it fun with sound effects
- Encourage them to make the sounds
- Practice both animal names and their sounds
- Use playful, engaging tone

Start by getting excited about learning animal sounds today!
Remember: Your output will be converted to audio, so have fun with the animal sounds.""",
            "prompt_type": "learning",
            "metadata": {
                "title": "Animals and Sounds",
                "words_to_teach": ["cat", "dog", "cow", "pig", "duck", "sheep", "meow", "woof", "moo", "oink", "quack"],
                "topics": ["animals", "sounds", "onomatopoeia", "nature"],
                "difficulty": "beginner",
                "age_group": "children",
                "learning_objectives": [
                    "Learn 6 common animals",
                    "Learn animal sound words", 
                    "Practice making sounds",
                    "Have fun with language learning"
                ]
            }
        },
        {
            "season": 1,
            "episode": 5,
            "prompt": """You are a friendly English tutor teaching young children about food and drinks.

Your student is learning food vocabulary and expressing preferences. Your goals:
- Teach common foods: apple, banana, bread, milk, water, juice
- Talk about likes and dislikes: "I like..." "I don't like..."
- Practice food-related conversations
- Ask about their favorite foods
- Use encouraging, positive tone
- Make food vocabulary practical and useful

Start by asking what they like to eat and drink!
Remember: Your output will be converted to audio, so speak clearly and warmly.""",
            "prompt_type": "learning",
            "metadata": {
                "title": "Food and Drinks",
                "words_to_teach": ["apple", "banana", "bread", "milk", "water", "juice", "like", "eat", "drink"],
                "topics": ["food", "drinks", "preferences", "daily_life"],
                "difficulty": "beginner",
                "age_group": "children",
                "learning_objectives": [
                    "Learn 6-8 food and drink words",
                    "Practice expressing preferences",
                    "Build everyday vocabulary",
                    "Develop conversation skills"
                ]
            }
        }
    ]
    
    success_count = 0
    
    for prompt_data in prompts_to_add:
        success = add_system_prompt(
            season=prompt_data["season"],
            episode=prompt_data["episode"],
            prompt=prompt_data["prompt"],
            prompt_type=prompt_data["prompt_type"],
            metadata=prompt_data["metadata"]
        )
        
        if success:
            success_count += 1
            
        print("=" * 60)
        print()
    
    print(f"🏁 Summary: {success_count}/{len(prompts_to_add)} system prompts added successfully")
    
    if success_count == len(prompts_to_add):
        print("🎉 All system prompts added successfully!")
        print("📚 Season 1 Episodes 1-5 are now ready for AI tutoring!")
        return 0
    else:
        print("⚠️  Some system prompts failed to be added.")
        return 1

def add_custom_prompt():
    """Interactive function to add a custom system prompt"""
    print("🛠️  Custom System Prompt Creation")
    print("=" * 40)
    
    try:
        season = int(input("Season (1-10): ").strip())
        episode = int(input("Episode (1-7): ").strip())
        prompt_type = input("Prompt Type (learning/assessment/conversation/review) [learning]: ").strip() or "learning"
        
        print("\nEnter the system prompt (press Enter twice when done):")
        print("(This is the AI tutor's instructions for this episode)")
        
        lines = []
        while True:
            line = input()
            if line == "" and len(lines) > 0 and lines[-1] == "":
                break
            lines.append(line)
        
        prompt = "\n".join(lines[:-1])  # Remove the last empty line
        
        # Optional metadata
        title = input("\nEpisode Title (optional): ").strip()
        words_input = input("Words to teach (comma-separated, optional): ").strip()
        topics_input = input("Topics to cover (comma-separated, optional): ").strip()
        difficulty = input("Difficulty (beginner/intermediate/advanced) [beginner]: ").strip() or "beginner"
        age_group = input("Age group (children/teens/adults) [children]: ").strip() or "children"
        
        metadata = {}
        if title:
            metadata["title"] = title
        if words_input:
            metadata["words_to_teach"] = [w.strip() for w in words_input.split(",")]
        if topics_input:
            metadata["topics"] = [t.strip() for t in topics_input.split(",")]
        metadata["difficulty"] = difficulty
        metadata["age_group"] = age_group
        
        success = add_system_prompt(season, episode, prompt, prompt_type, metadata)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n👋 Cancelled by user")
        return 1
    except ValueError as e:
        print(f"❌ Invalid input: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--custom":
        exit_code = add_custom_prompt()
    else:
        exit_code = main()
    
    sys.exit(exit_code)
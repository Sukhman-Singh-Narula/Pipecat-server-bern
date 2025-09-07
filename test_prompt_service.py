#!/usr/bin/env python3
"""
Simple test script to debug the prompt service issue
"""
import os
import sys
import traceback

# Add the server directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

async def test_prompt_service():
    """Test the prompt service directly"""
    try:
        from services.prompt_service import get_prompt_service
        
        print("🔍 Testing PromptService...")
        prompt_service = get_prompt_service()
        
        print("📡 Attempting to get system prompt for season 1, episode 1...")
        prompt_response = await prompt_service.get_system_prompt(1, 1)
        
        print("✅ Success! Got prompt response:")
        print(f"  Season: {prompt_response.season}")
        print(f"  Episode: {prompt_response.episode}")
        print(f"  Prompt Type: {prompt_response.prompt_type}")
        print(f"  Prompt Length: {prompt_response.prompt_length}")
        print(f"  Has Content: {hasattr(prompt_response, 'prompt') and prompt_response.prompt is not None}")
        if hasattr(prompt_response, 'prompt') and prompt_response.prompt:
            print(f"  Content Preview: {prompt_response.prompt[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"💥 Error: {e}")
        print("📊 Full traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(test_prompt_service())
    if success:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n❌ Test failed!")

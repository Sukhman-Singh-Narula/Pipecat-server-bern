#!/usr/bin/env python3

"""
Simple test to verify ElevenLabs TTS integration works
"""

import os
import asyncio
import aiohttp
from pipecat.services.elevenlabs.tts import ElevenLabsHttpTTSService

async def test_elevenlabs():
    # Load environment variables
    api_key = os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID")
    
    print(f"API Key: {api_key[:10] if api_key else 'None'}...")
    print(f"Voice ID: {voice_id}")
    
    if not api_key or api_key.startswith("dummy"):
        print("WARNING: Using dummy API key - this won't work for real requests")
        print("Please set ELEVENLABS_API_KEY to your actual ElevenLabs API key")
        return
    
    if not voice_id or voice_id.startswith("dummy"):
        print("WARNING: Using dummy voice ID - this won't work for real requests")
        print("Please set ELEVENLABS_VOICE_ID to your actual ElevenLabs voice ID")
        return
    
    # Test the service initialization
    async with aiohttp.ClientSession() as session:
        try:
            tts = ElevenLabsHttpTTSService(
                session=session,
                api_key=api_key,
                voice_id=voice_id,
            )
            print("✅ ElevenLabs TTS service initialized successfully!")
            
        except Exception as e:
            print(f"❌ Error initializing ElevenLabs TTS service: {e}")

if __name__ == "__main__":
    # Load environment from .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(test_elevenlabs())

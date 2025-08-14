#!/usr/bin/env python3

"""
Simple test to identify specific errors
"""

import asyncio
import aiohttp
import json

async def test_user_endpoint():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://127.0.0.1:7860/users/TEST1234') as response:
                print(f'Status: {response.status}')
                text = await response.text()
                print(f'Response: {text}')
                return response.status == 200
    except Exception as e:
        print(f'Error: {e}')
        return False

async def main():
    print('Testing user endpoint...')
    await test_user_endpoint()

if __name__ == "__main__":
    asyncio.run(main())

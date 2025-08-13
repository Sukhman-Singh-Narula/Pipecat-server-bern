#!/usr/bin/env python3

"""
Quick setup script for the minimalistic Pipecat server.
This script helps you get started quickly by checking dependencies
and providing setup instructions.
"""

import subprocess
import sys
import os

def check_python_version():
    """Check if Python version is 3.10 or higher."""
    if sys.version_info < (3, 10):
        print("❌ Python 3.10 or higher is required.")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version}")
    return True

def check_env_file():
    """Check if .env file exists and has required keys."""
    if not os.path.exists('.env'):
        print("❌ .env file not found.")
        print("Please copy .env.example to .env and add your API keys.")
        return False
    
    with open('.env', 'r') as f:
        content = f.read()
    
    required_keys = ['OPENAI_API_KEY', 'DEEPGRAM_API_KEY', 'CARTESIA_API_KEY']
    missing_keys = []
    
    for key in required_keys:
        if f"{key}=your_" in content or f"{key}=..." in content:
            missing_keys.append(key)
    
    if missing_keys:
        print("⚠️  Please set these API keys in your .env file:")
        for key in missing_keys:
            print(f"   - {key}")
        return False
    
    print("✅ .env file configured")
    return True

def install_dependencies():
    """Install required dependencies."""
    print("Installing dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def main():
    print("🤖 Pipecat Server Setup")
    print("=" * 30)
    
    if not check_python_version():
        sys.exit(1)
    
    if not check_env_file():
        print("\nTo continue:")
        print("1. Copy .env.example to .env")
        print("2. Edit .env and add your API keys")
        print("3. Run this script again")
        sys.exit(1)
    
    if install_dependencies():
        print("\n🎉 Setup complete!")
        print("\nTo run the bot:")
        print("  python bot.py")
        print("\nTo run with Daily transport:")
        print("  python bot.py --transport daily")
    else:
        print("\n❌ Setup failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()

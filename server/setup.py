#!/usr/bin/env python3

"""
Enhanced setup script for the Pipecat server.
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
        if f"{key}=your_" in content or f"{key}=..." in content or key not in content:
            missing_keys.append(key)
    
    if missing_keys:
        print("⚠️  Please set these API keys in your .env file:")
        for key in missing_keys:
            print(f"   - {key}")
        return False
    
    print("✅ .env file configured")
    return True

def check_firebase_setup():
    """Check Firebase configuration."""
    if os.path.exists('firebase-credentials.json'):
        print("✅ Firebase credentials found")
        return True
    else:
        print("⚠️  Firebase credentials not found")
        print("   The server will use local JSON storage instead")
        print("   For full functionality, add firebase-credentials.json")
        return False

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

def create_local_storage_files():
    """Create local storage files if they don't exist."""
    local_files = ['local_users.json', 'local_prompts.json']
    
    for file_name in local_files:
        if not os.path.exists(file_name):
            with open(file_name, 'w') as f:
                f.write('{}')
            print(f"✅ Created {file_name}")

def main():
    print("🚀 Enhanced Pipecat Server Setup")
    print("=" * 40)
    
    if not check_python_version():
        sys.exit(1)
    
    if not check_env_file():
        print("\nTo continue:")
        print("1. Copy .env.example to .env")
        print("2. Edit .env and add your API keys")
        print("3. Run this script again")
        sys.exit(1)
    
    # Check Firebase (not required)
    firebase_available = check_firebase_setup()
    
    if install_dependencies():
        create_local_storage_files()
        
        print("\n🎉 Setup complete!")
        print("\nYour enhanced server includes:")
        print("  🎤 WebRTC audio streaming")
        print("  👤 User registration and management")
        print("  📚 Episode-based system prompts")
        print("  📊 Learning progress tracking")
        print("  🔥 Firebase integration" + (" (configured)" if firebase_available else " (using local storage)"))
        
        print("\nTo run the server:")
        print("  # WebRTC (recommended for ESP32)")
        print("  python bot.py --transport webrtc --host 0.0.0.0 --esp32")
        print("  ")
        print("  # Daily transport")
        print("  python bot.py --transport daily --host 0.0.0.0")
        
        print("\nTo test the server:")
        print("  python test_server.py")
        
        print("\nAPI Documentation:")
        print("  http://localhost:7860/docs (after starting server)")
        
    else:
        print("\n❌ Setup failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()

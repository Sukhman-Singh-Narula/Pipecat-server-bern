# 🔥 Firebase Setup Guide for ESP32 Authentication

## Issue: Authentication data not saving to Firebase

Your authentication system is currently using in-memory storage instead of Firebase because the Firebase credentials are not properly configured.

## 🔧 Firebase Configuration Steps

### Step 1: Get Firebase Credentials
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project (or create one)
3. Go to **Project Settings** → **Service Accounts**
4. Click **"Generate new private key"**
5. Download the JSON file

### Step 2: Setup Credentials File
1. Rename the downloaded file to `firebase-credentials.json`
2. Place it in your project root: `/Users/sukhmansinghnarula/Documents/Code/Bern/pipecat server/firebase-credentials.json`

### Step 3: Update Environment Variables
Your `.env` file already has:
```
FIREBASE_CREDENTIALS_PATH=firebase-credentials.json
```

### Step 4: Firebase Database Structure
The authentication system will create these collections:
```
firestore/
├── claim_tokens/          # Temporary claim tokens
├── device_registrations/  # ESP32 device info  
├── device_sessions/       # JWT sessions
└── user_device_bindings/  # User-device relationships
```

## 🔍 Current Status Check

Run this command to check if Firebase is working:
```bash
cd "/Users/sukhmansinghnarula/Documents/Code/Bern/pipecat server/server"
"../venv/bin/python" -c "
from services.firebase_service import FirebaseService
fs = FirebaseService()
print('Firebase enabled:', fs.use_firebase)
print('Storage type:', 'Firebase' if fs.use_firebase else 'In-memory')
"
```

## 🛠️ Test Firebase Connection

After setting up Firebase credentials, test the connection:
```bash
cd "/Users/sukhmansinghnarula/Documents/Code/Bern/pipecat server/server"
"../venv/bin/python" -c "
import asyncio
from services.firebase_service import get_firebase_service

async def test_firebase():
    fs = get_firebase_service()
    if fs.use_firebase:
        # Test write
        await fs.set_document('test', 'connection_test', {'timestamp': '$(date)', 'status': 'connected'})
        print('✅ Firebase write test successful')
        
        # Test read
        doc = await fs.get_document('test', 'connection_test')
        print('✅ Firebase read test successful:', doc)
    else:
        print('❌ Firebase not connected - using in-memory storage')

asyncio.run(test_firebase())
"
```

## 🔄 Restart Server After Firebase Setup

Once Firebase is configured:
1. Stop the current server
2. Restart with: `cd server && ../venv/bin/python run_server.py`
3. You should see: `🔥 Firebase integration enabled`

## 📊 Verify Authentication Data in Firebase

After Firebase is working, test the authentication flow and check your Firebase console:

1. **Firestore Database** → **Data**
2. Look for collections: `claim_tokens`, `device_registrations`, `device_sessions`, `user_device_bindings`
3. You should see your test data appear there

## ⚠️ Security Note

Make sure to add `firebase-credentials.json` to your `.gitignore` file to avoid committing sensitive credentials to your repository.

```bash
echo "firebase-credentials.json" >> .gitignore
```

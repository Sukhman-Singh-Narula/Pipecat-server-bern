#!/usr/bin/env python3
"""
Debug script to check Firebase prompt data structure
"""
import os
import sys
import json

# Add the server directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

from services.firebase_service import get_firebase_service

def debug_firebase_data():
    """Check what's actually in Firebase"""
    try:
        firebase_service = get_firebase_service()
        
        if not firebase_service.use_firebase:
            print("❌ Firebase is not enabled")
            return
            
        print("🔍 Checking Firebase prompts collection...")
        
        # Get all documents in the prompts collection
        docs = firebase_service.db.collection('prompts').stream()
        
        documents_found = 0
        for doc in docs:
            documents_found += 1
            print(f"\n📄 Document ID: {doc.id}")
            data = doc.to_dict()
            print(f"📊 Data structure:")
            print(json.dumps(data, indent=2, default=str))
            print("-" * 50)
            
        if documents_found == 0:
            print("❌ No documents found in 'prompts' collection")
        else:
            print(f"✅ Found {documents_found} documents")
            
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_firebase_data()

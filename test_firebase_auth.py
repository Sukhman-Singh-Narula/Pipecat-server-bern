#!/usr/bin/env python3
"""
Test authentication with real Firebase
"""
import sys
import os
import asyncio
sys.path.append('/Users/sukhmansinghnarula/Documents/Code/Bern/pipecat server/server')

from services.auth_service import get_auth_service
from loguru import logger

async def test_auth_with_firebase():
    """Test authentication flow with Firebase"""
    try:
        logger.info("🔄 Testing authentication with Firebase...")
        
        # Get auth service
        auth_service = get_auth_service()
        logger.info(f"✅ Auth service initialized")
        logger.info(f"📊 Firebase enabled: {hasattr(auth_service, 'firebase_service') and auth_service.firebase_service.use_firebase}")
        
        # Test 1: Generate claim token
        logger.info("\n📱 Test 1: Generate claim token")
        email = "test@example.com"
        claim_token = await auth_service.generate_claim_token_for_user(email)
        logger.info(f"✅ Claim token generated: {claim_token.token}")
        
        # Test 2: Register device  
        logger.info("\n🔧 Test 2: Register device")
        mac_address = "AA:BB:CC:DD:EE:FF"
        hardware_id = "ESP32_FIREBASE_TEST"
        device_reg = await auth_service.register_new_device(mac_address, hardware_id, "1.0.0")
        logger.info(f"✅ Device registered: {device_reg.device_id}")
        
        # Test 3: Claim device
        logger.info("\n🔗 Test 3: Claim device")
        result = await auth_service.claim_device_with_token(
            device_reg.device_id, 
            mac_address, 
            claim_token.token
        )
        logger.info(f"✅ Device claimed: {result}")
        
        # Test 4: Authenticate device
        logger.info("\n🔐 Test 4: Authenticate device")
        auth_result = await auth_service.authenticate_device_and_get_jwt(
            device_reg.device_id,
            mac_address
        )
        logger.info(f"✅ Device authenticated: {auth_result['success']}")
        if auth_result['success']:
            logger.info(f"🎫 JWT token received: {auth_result['jwt_token'][:50]}...")
        
        # Test 5: Check Firebase data
        logger.info("\n🔍 Test 5: Check Firebase collections")
        if hasattr(auth_service, 'firebase_service') and auth_service.firebase_service.use_firebase:
            # Check if device registration is in Firebase
            device_doc = await auth_service.firebase_service.get_document("device_registrations", device_reg.device_id)
            if device_doc:
                logger.info(f"✅ Device found in Firebase: {device_doc.get('device_id')}")
            else:
                logger.warning("⚠️ Device not found in Firebase")
            
            # Check if user binding is in Firebase
            binding_id = f"{email}_{device_reg.device_id}"
            binding_doc = await auth_service.firebase_service.get_document("user_device_bindings", binding_id)
            if binding_doc:
                logger.info(f"✅ User binding found in Firebase: {binding_doc.get('email')}")
            else:
                logger.warning("⚠️ User binding not found in Firebase")
        else:
            logger.warning("⚠️ Firebase not enabled - using in-memory storage")
            
        logger.info("\n🎉 Authentication test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Authentication test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_auth_with_firebase())

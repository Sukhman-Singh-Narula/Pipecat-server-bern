#!/usr/bin/env python3
"""
Simple test server for authentication endpoints
"""
import sys
import os
sys.path.append('server')

from fastapi import FastAPI, HTTPException, Request
import uvicorn
from loguru import logger
import json

# Import our auth components
from server.models.auth_models import ClaimToken, DeviceRegistration, DeviceSession, UserDeviceBinding
from server.services.auth_service import AuthenticationService
from mock_firebase import MockFirebaseService

app = FastAPI(title="Authentication Test Server", version="1.0.0")

# Initialize auth service with mock firebase service
mock_firebase = MockFirebaseService()
auth_service = AuthenticationService(firebase_service=mock_firebase)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Authentication Server is running", "status": "healthy"}

# =============================================================================
# AUTHENTICATION ENDPOINTS
# =============================================================================

# Mobile app endpoints
@app.post("/api/auth/generate-claim-token")
async def generate_claim_token(request: Request):
    """Generate claim token for mobile app user"""
    try:
        body = await request.json()
        email = body.get("email")
        
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")
        
        claim_token = await auth_service.generate_claim_token_for_user(email)
        
        return {
            "success": True,
            "claim_token": claim_token.token,
            "expires_at": claim_token.expires_at.isoformat(),
            "expires_in_minutes": 5
        }
        
    except Exception as e:
        logger.error(f"Error generating claim token: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/auth/user-devices/{email}")
async def get_user_devices(email: str):
    """Get all devices claimed by user"""
    try:
        devices = await auth_service.get_user_devices(email)
        
        return {
            "success": True,
            "email": email,
            "devices": devices,
            "total_devices": len(devices)
        }
        
    except Exception as e:
        logger.error(f"Error getting user devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ESP32 device endpoints
@app.post("/api/device/register")
async def register_device(request: Request):
    """Register new ESP32 device"""
    try:
        body = await request.json()
        mac_address = body.get("mac_address")
        hardware_id = body.get("hardware_id") 
        firmware_version = body.get("firmware_version", "1.0.0")
        
        if not mac_address or not hardware_id:
            raise HTTPException(status_code=400, detail="MAC address and hardware ID are required")
        
        device_reg = await auth_service.register_new_device(mac_address, hardware_id, firmware_version)
        
        return {
            "success": True,
            "device_id": device_reg.device_id,
            "status": device_reg.status.value,
            "message": "Device registered successfully"
        }
        
    except Exception as e:
        logger.error(f"Error registering device: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/device/claim")
async def claim_device(request: Request):
    """Claim device with claim token"""
    try:
        body = await request.json()
        device_id = body.get("device_id")
        mac_address = body.get("mac_address")
        claim_token = body.get("claim_token")
        
        if not all([device_id, mac_address, claim_token]):
            raise HTTPException(status_code=400, detail="Device ID, MAC address, and claim token are required")
        
        result = await auth_service.claim_device_with_token(device_id, mac_address, claim_token)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error claiming device: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/device/authenticate")
async def authenticate_device(request: Request):
    """Authenticate device and provide JWT"""
    try:
        body = await request.json()
        device_id = body.get("device_id")
        mac_address = body.get("mac_address")
        
        if not device_id or not mac_address:
            raise HTTPException(status_code=400, detail="Device ID and MAC address are required")
        
        result = await auth_service.authenticate_device_and_get_jwt(device_id, mac_address)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=401, detail=result["error"])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error authenticating device: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/device/verify")
async def verify_device(request: Request):
    """Verify device JWT token"""
    try:
        body = await request.json()
        jwt_token = body.get("jwt_token")
        hashed_device_id = body.get("hashed_device_id")
        
        if not jwt_token or not hashed_device_id:
            raise HTTPException(status_code=400, detail="JWT token and hashed device ID are required")
        
        result = await auth_service.verify_device_jwt(jwt_token, hashed_device_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=401, detail=result["error"])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying device: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/device/heartbeat")
async def device_heartbeat(request: Request):
    """Update device heartbeat"""
    try:
        body = await request.json()
        device_id = body.get("device_id")
        hashed_device_id = body.get("hashed_device_id")
        
        if not device_id or not hashed_device_id:
            raise HTTPException(status_code=400, detail="Device ID and hashed device ID are required")
        
        result = await auth_service.device_heartbeat(device_id, hashed_device_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating heartbeat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Admin/utility endpoints
@app.get("/api/device/check/{device_id}")
async def check_device_validity(device_id: str):
    """Check if device is valid and active"""
    try:
        is_valid = await auth_service.is_device_valid_and_active(device_id)
        device_reg = await auth_service.get_device_registration(device_id)
        
        if device_reg:
            return {
                "device_id": device_id,
                "is_valid": is_valid,
                "status": device_reg.status.value,
                "claimed_by": device_reg.claimed_by_email,
                "last_seen": device_reg.last_seen.isoformat() if device_reg.last_seen else None
            }
        else:
            return {
                "device_id": device_id,
                "is_valid": False,
                "status": "not_found",
                "claimed_by": None,
                "last_seen": None
            }
        
    except Exception as e:
        logger.error(f"Error checking device validity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/device/active")
async def get_active_devices():
    """Get all active devices"""
    try:
        active_devices = await auth_service.get_active_devices()
        
        return {
            "success": True,
            "active_devices": active_devices,
            "total_active": len(active_devices)
        }
        
    except Exception as e:
        logger.error(f"Error getting active devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    logger.info("Starting Authentication Test Server...")
    uvicorn.run(app, host="0.0.0.0", port=8080)

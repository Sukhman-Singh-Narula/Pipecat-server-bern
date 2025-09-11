"""
Simple Authentication service for ESP32-Firebase integration
"""

import jwt
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Any
from loguru import logger

from models.auth_models import ClaimToken, DeviceRegistration, DeviceStatus, ClaimTokenStatus, SessionStatus


def get_auth_service():
    """Get authentication service with Firebase"""
    from services.firebase_service import get_firebase_service
    firebase_service = get_firebase_service()
    return AuthenticationService(firebase_service)


class AuthenticationService:
    """Simple authentication service for ESP32 devices"""
    
    def __init__(self, firebase_service):
        self.firebase = firebase_service
        self.jwt_secret = "esp32_auth_secret_2025"
        
        # Collections
        self.claim_tokens_collection = "claim_tokens"
        self.device_registrations_collection = "device_registrations" 
        self.device_sessions_collection = "device_sessions"
        self.user_device_bindings_collection = "user_device_bindings"

    async def generate_claim_token_for_user(self, email: str) -> ClaimToken:
        """Generate claim token for mobile app user"""
        try:
            # Generate token
            token_string = secrets.token_urlsafe(32)
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(minutes=5)
            
            # Create token object
            claim_token = ClaimToken(
                token=token_string,
                email=email,
                created_at=now,
                expires_at=expires_at,
                status=ClaimTokenStatus.ACTIVE,
                device_id=None,
                used_at=None
            )
            
            # Store in Firebase
            await self.firebase.set_document(
                self.claim_tokens_collection,
                token_string,
                {
                    "token": token_string,
                    "email": email,
                    "created_at": now.isoformat(),
                    "expires_at": expires_at.isoformat(),
                    "status": ClaimTokenStatus.ACTIVE.value,
                    "device_id": None,
                    "used_at": None
                }
            )
            
            logger.info(f"Generated claim token for {email}")
            return claim_token
            
        except Exception as e:
            logger.error(f"Error generating claim token: {e}")
            raise

    async def register_new_device(self, mac_address: str, hardware_id: str, firmware_version: str = "1.0.0") -> DeviceRegistration:
        """Register new ESP32 device"""
        try:
            # Generate device ID
            device_id = f"esp32_{secrets.token_hex(6)}"
            now = datetime.now(timezone.utc)
            
            # Create device registration
            device_reg = DeviceRegistration(
                device_id=device_id,
                mac_address=mac_address,
                hardware_id=hardware_id,
                created_at=now,
                status=DeviceStatus.REGISTERED,
                claimed_by_email=None,
                claimed_at=None,
                last_seen=None,
                device_name=None,
                firmware_version=firmware_version
            )
            
            # Store in Firebase
            await self.firebase.set_document(
                self.device_registrations_collection,
                device_id,
                {
                    "device_id": device_id,
                    "mac_address": mac_address,
                    "hardware_id": hardware_id,
                    "created_at": now.isoformat(),
                    "status": DeviceStatus.REGISTERED.value,
                    "claimed_by_email": None,
                    "claimed_at": None,
                    "last_seen": None,
                    "device_name": None,
                    "firmware_version": firmware_version
                }
            )
            
            logger.info(f"Registered device: {device_id}")
            return device_reg
            
        except Exception as e:
            logger.error(f"Error registering device: {e}")
            raise

    async def get_device_registration(self, device_id: str) -> Optional[DeviceRegistration]:
        """Get device registration from Firebase"""
        try:
            data = await self.firebase.get_document(self.device_registrations_collection, device_id)
            if not data:
                return None
                
            return DeviceRegistration(
                device_id=data["device_id"],
                mac_address=data["mac_address"],
                hardware_id=data["hardware_id"],
                created_at=datetime.fromisoformat(data["created_at"].replace('Z', '+00:00')),
                status=DeviceStatus(data["status"]),
                claimed_by_email=data.get("claimed_by_email"),
                claimed_at=datetime.fromisoformat(data["claimed_at"].replace('Z', '+00:00')) if data.get("claimed_at") else None,
                last_seen=datetime.fromisoformat(data["last_seen"].replace('Z', '+00:00')) if data.get("last_seen") else None,
                device_name=data.get("device_name"),
                firmware_version=data.get("firmware_version", "1.0.0")
            )
        except Exception as e:
            logger.error(f"Error getting device {device_id}: {e}")
            return None

    async def claim_device_with_token(self, device_id: str, mac_address: str, claim_token: str) -> Dict[str, Any]:
        """Claim device with token"""
        try:
            # Get token data
            token_data = await self.firebase.get_document(self.claim_tokens_collection, claim_token)
            if not token_data:
                return {"success": False, "error": "Invalid claim token"}
                
            # Check token expiry
            now = datetime.now(timezone.utc)
            expires_at = datetime.fromisoformat(token_data["expires_at"].replace('Z', '+00:00'))
            if expires_at < now:
                return {"success": False, "error": "Token expired"}
                
            # Get device
            device_reg = await self.get_device_registration(device_id)
            if not device_reg or device_reg.mac_address != mac_address:
                return {"success": False, "error": "Device not found or MAC mismatch"}
                
            # Claim device
            await self.firebase.update_document(
                self.device_registrations_collection,
                device_id,
                {
                    "status": DeviceStatus.CLAIMED.value,
                    "claimed_by_email": token_data["email"],
                    "claimed_at": now.isoformat()
                }
            )
            
            # Mark token as used
            await self.firebase.update_document(
                self.claim_tokens_collection,
                claim_token,
                {
                    "status": ClaimTokenStatus.USED.value,
                    "device_id": device_id,
                    "used_at": now.isoformat()
                }
            )
            
            # Create binding
            binding_id = f"{token_data['email']}_{device_id}"
            await self.firebase.set_document(
                self.user_device_bindings_collection,
                binding_id,
                {
                    "email": token_data["email"],
                    "device_id": device_id,
                    "bound_at": now.isoformat(),
                    "status": "active"
                }
            )
            
            return {
                "success": True,
                "message": "Device claimed successfully",
                "email": token_data["email"],
                "device_id": device_id,
                "claimed_at": now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error claiming device: {e}")
            return {"success": False, "error": str(e)}

    async def authenticate_device_and_get_jwt(self, device_id: str, mac_address: str) -> Dict[str, Any]:
        """Authenticate device and get JWT"""
        try:
            # Get device
            device_reg = await self.get_device_registration(device_id)
            if not device_reg:
                return {"success": False, "error": "Device not found"}
            
            if device_reg.mac_address != mac_address:
                return {"success": False, "error": "MAC address mismatch"}
                
            if device_reg.status != DeviceStatus.CLAIMED:
                return {"success": False, "error": "Device not claimed"}
            
            # Generate JWT
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(hours=24)
            hashed_device_id = hashlib.sha256(device_id.encode()).hexdigest()[:16]
            
            payload = {
                "device_id": device_id,
                "hashed_device_id": hashed_device_id,
                "email": device_reg.claimed_by_email,
                "iat": now.timestamp(),
                "exp": expires_at.timestamp()
            }
            
            jwt_token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
            
            # Store session
            await self.firebase.set_document(
                self.device_sessions_collection,
                hashed_device_id,
                {
                    "session_id": str(uuid.uuid4()),
                    "device_id": device_id,
                    "hashed_device_id": hashed_device_id,
                    "email": device_reg.claimed_by_email,
                    "jwt_token": jwt_token,
                    "created_at": now.isoformat(),
                    "expires_at": expires_at.isoformat(),
                    "last_heartbeat": now.isoformat(),
                    "status": SessionStatus.ACTIVE.value
                }
            )
            
            # Update device status
            await self.firebase.update_document(
                self.device_registrations_collection,
                device_id,
                {
                    "status": DeviceStatus.ACTIVE.value,
                    "last_seen": now.isoformat()
                }
            )
            
            return {
                "success": True,
                "jwt_token": jwt_token,
                "expires_at": expires_at.isoformat(),
                "hashed_device_id": hashed_device_id,
                "email": device_reg.claimed_by_email
            }
            
        except Exception as e:
            logger.error(f"Error authenticating device: {e}")
            return {"success": False, "error": str(e)}

    async def verify_device_jwt(self, jwt_token: str, hashed_device_id: str) -> Dict[str, Any]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(jwt_token, self.jwt_secret, algorithms=["HS256"])
            
            if payload.get("hashed_device_id") != hashed_device_id:
                return {"success": False, "error": "Device ID mismatch"}
                
            return {
                "success": True,
                "device_id": payload.get("device_id"),
                "email": payload.get("email"),
                "expires_at": datetime.fromtimestamp(payload.get("exp")).isoformat()
            }
            
        except jwt.ExpiredSignatureError:
            return {"success": False, "error": "Token expired"}
        except jwt.InvalidTokenError:
            return {"success": False, "error": "Invalid token"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def device_heartbeat(self, device_id: str, hashed_device_id: str) -> Dict[str, Any]:
        """Update device heartbeat"""
        try:
            now = datetime.now(timezone.utc)
            
            # Update device last seen
            await self.firebase.update_document(
                self.device_registrations_collection,
                device_id,
                {"last_seen": now.isoformat()}
            )
            
            # Update session heartbeat
            session_data = await self.firebase.get_document(self.device_sessions_collection, hashed_device_id)
            if session_data:
                await self.firebase.update_document(
                    self.device_sessions_collection,
                    hashed_device_id,
                    {
                        "last_heartbeat": now.isoformat(),
                        "status": SessionStatus.ACTIVE.value
                    }
                )
                
                return {
                    "success": True,
                    "last_heartbeat": now.isoformat(),
                    "status": "active"
                }
            else:
                return {"success": False, "error": "Session not found"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def is_device_valid_and_active(self, device_id: str) -> bool:
        """Check if device is valid and active"""
        device_reg = await self.get_device_registration(device_id)
        return device_reg is not None and device_reg.status in [DeviceStatus.CLAIMED, DeviceStatus.ACTIVE]

    async def get_active_devices(self) -> List[Dict[str, Any]]:
        """Get all active devices"""
        try:
            sessions_data = await self.firebase.query_collection(
                self.device_sessions_collection,
                filters=[{"field": "status", "operator": "==", "value": SessionStatus.ACTIVE.value}]
            )
            
            return [
                {
                    "device_id": session.get("device_id"),
                    "email": session.get("email"),
                    "last_heartbeat": session.get("last_heartbeat"),
                    "status": "active"
                }
                for session in sessions_data
            ]
        except Exception as e:
            logger.error(f"Error getting active devices: {e}")
            return []

    async def get_user_devices(self, email: str) -> List[Dict[str, Any]]:
        """Get devices for user"""
        try:
            bindings = await self.firebase.query_collection(
                self.user_device_bindings_collection,
                filters=[{"field": "email", "operator": "==", "value": email}]
            )
            
            devices = []
            for binding in bindings:
                device_id = binding.get("device_id")
                if device_id:
                    device_data = await self.firebase.get_document(self.device_registrations_collection, device_id)
                    if device_data:
                        devices.append({
                            "device_id": device_data["device_id"],
                            "hardware_id": device_data["hardware_id"],
                            "status": device_data["status"],
                            "claimed_at": device_data.get("claimed_at"),
                            "last_seen": device_data.get("last_seen")
                        })
            
            return devices
        except Exception as e:
            logger.error(f"Error getting user devices: {e}")
            return []

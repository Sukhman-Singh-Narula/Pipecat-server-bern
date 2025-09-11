"""
Authentication models for ESP32-mobile app ecosystem
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import secrets
import uuid

class DeviceStatus(Enum):
    REGISTERED = "registered"      # Device exists but not claimed
    CLAIMED = "claimed"           # Device claimed by user but offline
    ACTIVE = "active"            # Device online and active
    INACTIVE = "inactive"        # Device offline/disconnected
    SUSPENDED = "suspended"      # Device disabled by admin

class ClaimTokenStatus(Enum):
    ACTIVE = "active"
    USED = "used"
    EXPIRED = "expired"

class SessionStatus(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"

@dataclass
class ClaimToken:
    """Temporary token for device claiming"""
    token: str
    email: str
    created_at: datetime
    expires_at: datetime
    status: ClaimTokenStatus = ClaimTokenStatus.ACTIVE
    device_id: Optional[str] = None
    used_at: Optional[datetime] = None
    
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        return self.status == ClaimTokenStatus.ACTIVE and not self.is_expired()

@dataclass
class DeviceRegistration:
    """Device registration in database"""
    device_id: str
    mac_address: str
    hardware_id: str  # Unique hardware identifier
    created_at: datetime
    status: DeviceStatus = DeviceStatus.REGISTERED
    claimed_by_email: Optional[str] = None
    claimed_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    device_name: Optional[str] = None
    firmware_version: Optional[str] = None
    
    def get_hashed_id(self) -> str:
        """Get hashed device ID for security"""
        return hashlib.sha256(f"{self.device_id}:{self.mac_address}".encode()).hexdigest()[:16]

@dataclass
class DeviceSession:
    """Active device session with JWT"""
    device_id: str
    hashed_device_id: str
    email: str
    jwt_token: str
    created_at: datetime
    expires_at: datetime
    last_heartbeat: datetime
    status: DeviceStatus = DeviceStatus.ACTIVE
    
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
    
    def needs_heartbeat(self, heartbeat_interval_minutes: int = 5) -> bool:
        """Check if device needs to send heartbeat"""
        return datetime.utcnow() - self.last_heartbeat > timedelta(minutes=heartbeat_interval_minutes)

@dataclass
class UserDeviceBinding:
    """User's claimed devices"""
    email: str
    device_id: str
    device_name: str
    claimed_at: datetime
    is_primary: bool = False
    settings: Dict[str, Any] = field(default_factory=dict)

def generate_claim_token(email: str, expiry_minutes: int = 5) -> ClaimToken:
    """Generate a new claim token for user"""
    token = secrets.token_urlsafe(32)
    now = datetime.utcnow()
    expires = now + timedelta(minutes=expiry_minutes)
    
    return ClaimToken(
        token=token,
        email=email,
        created_at=now,
        expires_at=expires
    )

def generate_device_id() -> str:
    """Generate unique device ID"""
    return f"esp32_{uuid.uuid4().hex[:12]}"

def hash_device_credentials(device_id: str, mac_address: str) -> str:
    """Create secure hash for device authentication"""
    return hashlib.sha256(f"{device_id}:{mac_address}:device_auth".encode()).hexdigest()

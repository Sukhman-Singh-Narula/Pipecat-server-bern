# ESP32-Mobile App Authentication API Documentation

## Overview
This authentication system provides secure device claiming and JWT-based authentication for ESP32 devices and mobile applications. The system supports:

- **Claim Token System**: Mobile apps generate temporary tokens for device claiming
- **Device Registration**: ESP32 devices register themselves with hardware details
- **Device Claiming**: ESP32 devices are bound to user email addresses via claim tokens
- **JWT Authentication**: Secure session management with long-lived tokens
- **Heartbeat System**: Active device monitoring and session management

## Base URL
```
http://localhost:8080
```

## Authentication Flow

### 1. Mobile App → Generate Claim Token
### 2. ESP32 Device → Register
### 3. ESP32 Device → Claim with Token
### 4. ESP32 Device → Authenticate & Get JWT
### 5. ESP32 Device → Send Periodic Heartbeats

---

## 📱 Mobile App Endpoints

### Generate Claim Token
Generate a temporary token for claiming ESP32 devices (5-minute expiry).

**Endpoint:** `POST /api/auth/generate-claim-token`

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "claim_token": "avx4CJFlBpht9pNXTdXzEAp1OmTkzIMKNSq05nOBbRI",
  "expires_at": "2025-09-11T17:45:31.332143",
  "expires_in_minutes": 5
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8080/api/auth/generate-claim-token" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

### Get User Devices
Retrieve all devices claimed by a specific user.

**Endpoint:** `GET /api/auth/user-devices/{email}`

**Response:**
```json
{
  "success": true,
  "email": "user@example.com",
  "devices": [
    {
      "device_id": "esp32_078adce91f14",
      "status": "active",
      "claimed_at": "2025-09-11T17:40:45.675154",
      "last_seen": "2025-09-11T17:42:06.372397"
    }
  ],
  "total_devices": 1
}
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8080/api/auth/user-devices/user@example.com"
```

---

## 🔧 ESP32 Device Endpoints

### Register Device
Register a new ESP32 device in the system.

**Endpoint:** `POST /api/device/register`

**Request:**
```json
{
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "hardware_id": "ESP32_TEST_001",
  "firmware_version": "1.2.0"
}
```

**Response:**
```json
{
  "success": true,
  "device_id": "esp32_078adce91f14",
  "status": "registered",
  "message": "Device registered successfully"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8080/api/device/register" \
  -H "Content-Type: application/json" \
  -d '{"mac_address": "AA:BB:CC:DD:EE:FF", "hardware_id": "ESP32_TEST_001", "firmware_version": "1.2.0"}'
```

### Claim Device
Claim an ESP32 device using a mobile app generated claim token.

**Endpoint:** `POST /api/device/claim`

**Request:**
```json
{
  "device_id": "esp32_078adce91f14",
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "claim_token": "avx4CJFlBpht9pNXTdXzEAp1OmTkzIMKNSq05nOBbRI"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Device claimed successfully",
  "email": "user@example.com",
  "device_id": "esp32_078adce91f14",
  "claimed_at": "2025-09-11T17:40:45.675154"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8080/api/device/claim" \
  -H "Content-Type: application/json" \
  -d '{"device_id": "esp32_078adce91f14", "mac_address": "AA:BB:CC:DD:EE:FF", "claim_token": "avx4CJFlBpht9pNXTdXzEAp1OmTkzIMKNSq05nOBbRI"}'
```

### Authenticate Device
Authenticate a claimed ESP32 device and receive a JWT token.

**Endpoint:** `POST /api/device/authenticate`

**Request:**
```json
{
  "device_id": "esp32_078adce91f14",
  "mac_address": "AA:BB:CC:DD:EE:FF"
}
```

**Response:**
```json
{
  "success": true,
  "jwt_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkZXZpY2VfaWQiOiJlc3AzMl8wNzhhZGNlOTFmMTQiLCJoYXNoZWRfZGV2aWNlX2lkIjoiMzNjYzk1N2I5MWJjZGYyNiIsImVtYWlsIjoidGVzdEBleGFtcGxlLmNvbSIsImlhdCI6MTc1NzU5MjY1Ni45MDQ4ODgsImV4cCI6MTc1NzY3OTA1Ni45MDQ4ODh9.Pe21T1FWtNwgWyGufiJJlCjrpgTbG2XSGScs6g__gU0",
  "expires_at": "2025-09-12T17:40:56.904888",
  "hashed_device_id": "33cc957b91bcdf26",
  "email": "user@example.com"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8080/api/device/authenticate" \
  -H "Content-Type: application/json" \
  -d '{"device_id": "esp32_078adce91f14", "mac_address": "AA:BB:CC:DD:EE:FF"}'
```

### Verify Device JWT
Verify the validity of a device JWT token.

**Endpoint:** `POST /api/device/verify`

**Request:**
```json
{
  "jwt_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "hashed_device_id": "33cc957b91bcdf26"
}
```

**Response:**
```json
{
  "success": true,
  "device_id": "esp32_078adce91f14",
  "email": "user@example.com",
  "expires_at": "2025-09-12T17:40:56.904888"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8080/api/device/verify" \
  -H "Content-Type: application/json" \
  -d '{"jwt_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", "hashed_device_id": "33cc957b91bcdf26"}'
```

### Device Heartbeat
Send periodic heartbeat to maintain active device session.

**Endpoint:** `POST /api/device/heartbeat`

**Request:**
```json
{
  "device_id": "esp32_078adce91f14",
  "hashed_device_id": "33cc957b91bcdf26"
}
```

**Response:**
```json
{
  "success": true,
  "last_heartbeat": "2025-09-11T17:42:06.372397",
  "status": "active"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8080/api/device/heartbeat" \
  -H "Content-Type: application/json" \
  -d '{"device_id": "esp32_078adce91f14", "hashed_device_id": "33cc957b91bcdf26"}'
```

---

## 🛠️ Admin/Utility Endpoints

### Check Device Validity
Check if a device is registered, claimed, and active.

**Endpoint:** `GET /api/device/check/{device_id}`

**Response:**
```json
{
  "device_id": "esp32_078adce91f14",
  "is_valid": true,
  "status": "active",
  "claimed_by": "user@example.com",
  "last_seen": "2025-09-11T17:42:06.372397"
}
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8080/api/device/check/esp32_078adce91f14"
```

### Get Active Devices
Retrieve all currently active ESP32 devices.

**Endpoint:** `GET /api/device/active`

**Response:**
```json
{
  "success": true,
  "active_devices": [
    {
      "device_id": "esp32_078adce91f14",
      "email": "user@example.com",
      "last_heartbeat": "2025-09-11T17:42:06.372397",
      "status": "active"
    }
  ],
  "total_active": 1
}
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8080/api/device/active"
```

---

## 📋 Complete Authentication Workflow

### Step 1: Mobile App - Generate Claim Token
```bash
curl -X POST "http://localhost:8080/api/auth/generate-claim-token" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

### Step 2: ESP32 - Register Device
```bash
curl -X POST "http://localhost:8080/api/device/register" \
  -H "Content-Type: application/json" \
  -d '{"mac_address": "AA:BB:CC:DD:EE:FF", "hardware_id": "ESP32_TEST_001", "firmware_version": "1.2.0"}'
```

### Step 3: ESP32 - Claim Device
```bash
curl -X POST "http://localhost:8080/api/device/claim" \
  -H "Content-Type: application/json" \
  -d '{"device_id": "esp32_078adce91f14", "mac_address": "AA:BB:CC:DD:EE:FF", "claim_token": "avx4CJFlBpht9pNXTdXzEAp1OmTkzIMKNSq05nOBbRI"}'
```

### Step 4: ESP32 - Authenticate & Get JWT
```bash
curl -X POST "http://localhost:8080/api/device/authenticate" \
  -H "Content-Type: application/json" \
  -d '{"device_id": "esp32_078adce91f14", "mac_address": "AA:BB:CC:DD:EE:FF"}'
```

### Step 5: ESP32 - Send Heartbeats (Every 5 minutes)
```bash
curl -X POST "http://localhost:8080/api/device/heartbeat" \
  -H "Content-Type: application/json" \
  -d '{"device_id": "esp32_078adce91f14", "hashed_device_id": "33cc957b91bcdf26"}'
```

---

## 🔒 Security Features

- **Claim Token Expiry**: 5-minute validity window for device claiming
- **JWT Authentication**: Secure 24-hour sessions with signed tokens
- **Device Binding**: Devices are permanently bound to user email addresses
- **MAC Address Validation**: Hardware-level device verification
- **Hashed Device IDs**: Additional security layer for device identification
- **Session Management**: Automatic cleanup of inactive devices
- **Heartbeat Monitoring**: Real-time device activity tracking

---

## 📊 Status Codes

- **200**: Success
- **400**: Bad Request (missing parameters, invalid token, etc.)
- **401**: Unauthorized (invalid JWT, expired token)
- **404**: Not Found (device not found)
- **500**: Internal Server Error

---

## 🔧 Testing the API

The authentication system has been successfully tested with all endpoints working correctly. You can use the provided cURL commands to test the complete authentication flow from mobile app token generation to ESP32 device authentication and heartbeat monitoring.

**Server Status**: ✅ All endpoints tested and working
**Authentication Flow**: ✅ Complete workflow verified
**Security**: ✅ JWT tokens, hashed IDs, and expiry working
**Device Management**: ✅ Registration, claiming, and heartbeat system operational

# Add Devices Endpoint Documentation

## Overview

The `/api/add-devices` endpoint creates three new device IDs with default user data in the Firebase database.

## Endpoint Details

- **URL**: `/api/add-devices`
- **Method**: `POST`
- **Description**: Create three new device IDs with default user data
- **Authentication**: None required

## Request

### Headers
```
Content-Type: application/json
```

### Body
No request body required - this endpoint automatically creates 3 devices.

## Response

### Success Response (200 OK)

```json
{
    "status": "success",
    "message": "Successfully created 3 new device IDs",
    "devices": [
        {
            "device_id": "device_a1b2c3d4",
            "name": "User c3d4",
            "email": "device_a1b2c3d4@example.com",
            "age": 8,
            "season": 1,
            "episode": 1
        },
        {
            "device_id": "device_e5f6g7h8",
            "name": "User g7h8",
            "email": "device_e5f6g7h8@example.com",
            "age": 8,
            "season": 1,
            "episode": 1
        },
        {
            "device_id": "device_i9j0k1l2",
            "name": "User k1l2",
            "email": "device_i9j0k1l2@example.com",
            "age": 8,
            "season": 1,
            "episode": 1
        }
    ],
    "total_created": 3
}
```

### Error Response (500 Internal Server Error)

```json
{
    "detail": "Error message describing what went wrong"
}
```

## Default User Data Structure

Each created device gets the following default data:

```json
{
    "device_id": "device_xxxxxxxx",
    "name": "User xxxx",
    "age": 8,
    "email": "device_xxxxxxxx@example.com",
    "progress": {
        "season": 1,
        "episode": 1,
        "episodes_completed": 0,
        "words_learnt": [],
        "topics_learnt": [],
        "total_time_minutes": 0
    },
    "created_at": "2025-09-08T01:00:00.000Z",
    "last_seen": "2025-09-08T01:00:00.000Z",
    "status": "active"
}
```

## Usage Examples

### cURL

```bash
curl -X POST http://localhost:7860/api/add-devices \
  -H "Content-Type: application/json"
```

### Python (requests)

```python
import requests

response = requests.post('http://localhost:7860/api/add-devices')
data = response.json()

for device in data['devices']:
    print(f"Created device: {device['device_id']}")
```

### JavaScript (fetch)

```javascript
fetch('http://localhost:7860/api/add-devices', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    }
})
.then(response => response.json())
.then(data => {
    console.log('Created devices:', data.devices);
});
```

## Testing

Use the provided test script:

```bash
python test_add_devices.py
```

This will test the endpoint and display the created devices.

## Notes

- Device IDs are automatically generated using UUID format: `device_xxxxxxxx`
- Each device gets a unique name based on the last 4 characters of the device ID
- All devices start at Season 1, Episode 1
- Default age is set to 8 years
- Email addresses use the device ID with `@example.com` domain
- Data is stored in the Firebase "users" collection with device_id as the document ID

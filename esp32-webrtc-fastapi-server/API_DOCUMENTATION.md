# ESP32 WebRTC FastAPI Server API Documentation

## Overview
This FastAPI server enables WebRTC communication with ESP32 devices. It processes audio input and provides AI-powered voice responses using Google's Gemini Multimodal Live service.

## Base URL
```
http://localhost:7860
```

## Endpoints

### 1. Root Endpoint
**GET /** 

Returns basic server information and available endpoints.

**Response:**
```json
{
    "message": "ESP32 WebRTC FastAPI Server",
    "version": "1.0.0",
    "endpoints": {
        "/api/offer": "POST - Send WebRTC offer to establish connection"
    }
}
```

### 2. WebRTC Offer Endpoint
**POST /api/offer**

This is the main endpoint for establishing WebRTC connections with ESP32 devices.

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
    "sdp": "<SDP_OFFER_STRING>",
    "type": "offer",
    "pc_id": "<OPTIONAL_PEER_CONNECTION_ID>"
}
```

**Parameters:**
- `sdp` (string, required): The Session Description Protocol offer from the ESP32
- `type` (string, required): Must be "offer"
- `pc_id` (string, optional): Peer connection ID for reusing existing connections

**Response (Success):**
```json
{
    "sdp": "<SDP_ANSWER_STRING>",
    "type": "answer",
    "pc_id": "<PEER_CONNECTION_ID>"
}
```

**Response (Error):**
```json
{
    "error": "<ERROR_MESSAGE>"
}
```

## ESP32 Integration Guide

### 1. WebRTC Setup on ESP32

Your ESP32 should:
1. Create a WebRTC peer connection
2. Generate an SDP offer
3. Send the offer to this server's `/api/offer` endpoint
4. Process the SDP answer returned by the server
5. Establish the WebRTC connection

### 2. Audio Format Requirements

The server expects audio in the following format:
- **Sample Rate**: 16 kHz
- **Channels**: Mono (1 channel)
- **Encoding**: PCM
- **Bit Depth**: 16-bit

### 3. Example ESP32 HTTP Request

```cpp
// Example ESP32 code snippet
#include <HTTPClient.h>
#include <ArduinoJson.h>

void sendWebRTCOffer(String sdpOffer) {
    HTTPClient http;
    http.begin("http://YOUR_SERVER_IP:7860/api/offer");
    http.addHeader("Content-Type", "application/json");
    
    // Create JSON payload
    DynamicJsonDocument doc(4096);
    doc["sdp"] = sdpOffer;
    doc["type"] = "offer";
    // Optional: doc["pc_id"] = "your_custom_id";
    
    String jsonString;
    serializeJson(doc, jsonString);
    
    int httpResponseCode = http.POST(jsonString);
    
    if (httpResponseCode > 0) {
        String response = http.getString();
        // Parse the SDP answer from response
        DynamicJsonDocument responseDoc(4096);
        deserializeJson(responseDoc, response);
        String sdpAnswer = responseDoc["sdp"];
        String pcId = responseDoc["pc_id"];
        
        // Use sdpAnswer to complete WebRTC connection
        processSDPAnswer(sdpAnswer);
    }
    
    http.end();
}
```

### 4. Voice Activity Detection (VAD)

The server uses Silero VAD (Voice Activity Detection) to:
- Detect when speech starts and stops
- Reduce unnecessary processing of silence
- Improve response timing

### 5. AI Response Flow

1. ESP32 sends audio → Server receives via WebRTC
2. Server processes audio through VAD
3. Audio is transcribed and sent to Gemini AI
4. AI generates text response
5. Text is converted to speech
6. Audio response is sent back to ESP32 via WebRTC

### 6. Logging and Debugging

The server provides detailed logging for troubleshooting:
- Connection establishment events
- Audio processing status
- AI service interactions
- Error conditions

Log levels can be controlled via command line:
```bash
# Debug level (default)
python server.py

# Verbose/Trace level
python server.py -v
```

### 7. Environment Variables

Create a `.env` file in the server directory:
```env
GOOGLE_API_KEY=your_google_api_key_here
```

Required for Gemini AI service integration.

### 8. Connection Management

- Multiple ESP32 devices can connect simultaneously
- Each connection gets a unique `pc_id`
- Connections are automatically cleaned up when devices disconnect
- Server supports connection reuse via `pc_id`

### 9. Error Handling

Common error scenarios:
- Invalid SDP format → 500 error with details
- Missing required fields → 500 error with details
- Network connectivity issues → Connection timeout
- AI service unavailable → Processing errors

All errors are logged with detailed information for debugging.

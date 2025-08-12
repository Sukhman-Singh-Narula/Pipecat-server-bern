# ESP32 WebRTC AI Assistant Server

A FastAPI server that enables ESP32 devices to connect via WebRTC and have real-time audio conversations with an AI assistant using the Pipecat framework.

## Features

- **WebRTC Audio Communication**: Real-time bidirectional audio streaming
- **Conversational AI**: Powered by OpenAI GPT models
- **Speech Recognition**: Using Deepgram STT service
- **Text-to-Speech**: Using Cartesia TTS service
- **Voice Activity Detection**: For natural conversation flow and interruption handling
- **Device Management**: Track and manage multiple ESP32 devices
- **RESTful API**: Full API for device registration and management
- **Scalable Architecture**: Support for multiple concurrent connections

## Prerequisites

### API Keys Required

1. **OpenAI API Key** - For conversational AI
   - Get it from: https://platform.openai.com/api-keys
   
2. **Deepgram API Key** - For speech-to-text
   - Get it from: https://console.deepgram.com/
   
3. **Cartesia API Key** - For text-to-speech
   - Get it from: https://cartesia.ai/

### Hardware Requirements

**For ESP32 Client:**
- ESP32 development board
- I2S microphone (e.g., INMP441)
- I2S audio amplifier with speaker (e.g., MAX98357A)
- WiFi connection

**For Server:**
- Computer/server with Python 3.10+
- Network connectivity
- Sufficient CPU/memory for AI processing

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd pipecat-server
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Or using pipenv
pipenv install -r requirements.txt

# Or using conda
conda env create -f environment.yml
```

### 3. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your API keys
nano .env
```

Required environment variables:
```env
OPENAI_API_KEY=your_openai_api_key_here
DEEPGRAM_API_KEY=your_deepgram_api_key_here
CARTESIA_API_KEY=your_cartesia_api_key_here
```

### 4. Run the Server

```bash
# Basic run
python esp32_webrtc_server.py

# With custom host and port
python esp32_webrtc_server.py --host 0.0.0.0 --port 8000

# Development mode with auto-reload
python esp32_webrtc_server.py --reload --log-level debug
```

The server will start and be available at:
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Device Management**: http://localhost:8000/api/devices

## API Endpoints

### Device Management

- `POST /api/device/register` - Register a new ESP32 device
- `GET /api/devices` - List all registered devices
- `GET /api/device/{device_id}/status` - Get device status
- `DELETE /api/device/{device_id}` - Disconnect and unregister device

### WebRTC Communication

- `POST /api/webrtc/offer` - Handle WebRTC offer from ESP32
- `POST /api/device/{device_id}/config` - Update conversation config

### Utility

- `GET /health` - Server health check
- `GET /api/voices` - List available TTS voices

## ESP32 Client Setup

### 1. Hardware Connections

**I2S Microphone (INMP441):**
```
ESP32    INMP441
-----    -------
3.3V  -> VDD
GND   -> GND
GPIO32-> SD
GPIO15-> WS
GPIO14-> SCK
GND   -> L/R
```

**I2S Audio Amplifier (MAX98357A):**
```
ESP32     MAX98357A
-----     ---------
3.3V   -> VIN
GND    -> GND
GPIO25 -> DIN
GPIO26 -> BCLK
GPIO27 -> LRC
```

### 2. Arduino IDE Setup

1. Install ESP32 board support
2. Install required libraries:
   - `WiFi` (built-in)
   - `HTTPClient` (built-in)
   - `ArduinoJson`
   - `WebSocketsClient`

### 3. Configure and Upload

1. Open `esp32_client_example.ino`
2. Update WiFi credentials
3. Update server IP address
4. Upload to ESP32

## Usage Examples

### Basic Device Registration

```python
import requests

# Register a new device
response = requests.post("http://localhost:8000/api/device/register", json={
    "device_id": "esp32_001",
    "device_name": "Kitchen Assistant",
    "device_type": "esp32",
    "capabilities": {
        "audio_input": True,
        "audio_output": True,
        "sample_rate": 16000
    }
})

print(response.json())
```

### Update Conversation Configuration

```python
import requests

# Update device conversation settings
response = requests.post("http://localhost:8000/api/device/esp32_001/config", json={
    "system_prompt": "You are a kitchen assistant. Help with cooking and recipes.",
    "voice_id": "british_lady",
    "language": "en",
    "interrupt_enabled": True
})

print(response.json())
```

### WebRTC Offer Example

```python
import requests

# Send WebRTC offer (typically done by ESP32)
response = requests.post("http://localhost:8000/api/webrtc/offer", json={
    "device_id": "esp32_001",
    "sdp": "v=0...",  # SDP offer from ESP32
    "type": "offer"
})

print("WebRTC Answer:", response.json())
```

## Configuration Options

### Conversation Configuration

```python
class ConversationConfig:
    system_prompt: str = "Custom system prompt"
    voice_id: str = "british_lady"  # See available voices at /api/voices
    language: str = "en"
    interrupt_enabled: bool = True
```

### Available Voice Options

- `british_lady` - Professional British female voice
- `american_male` - Friendly American male voice
- `friendly_female` - Warm, friendly female voice

## Monitoring and Debugging

### Health Check

```bash
curl http://localhost:8000/health
```

### View Active Devices

```bash
curl http://localhost:8000/api/devices
```

### Device Status

```bash
curl http://localhost:8000/api/device/esp32_001/status
```

### Logs

The server provides detailed logging. Set log level with:

```bash
python esp32_webrtc_server.py --log-level debug
```

## Troubleshooting

### Common Issues

1. **WebRTC Connection Fails**
   - Check firewall settings
   - Ensure ICE servers are accessible
   - Verify ESP32 and server are on same network

2. **Audio Quality Issues**
   - Check I2S wiring
   - Verify sample rates match
   - Ensure stable power supply

3. **API Key Errors**
   - Verify all required API keys are set
   - Check API key validity and quotas
   - Ensure internet connectivity

### ESP32 Debugging

```cpp
// Enable debug output
Serial.begin(115200);
Serial.setDebugOutput(true);

// Check WiFi connection
Serial.println(WiFi.localIP());
Serial.println(WiFi.RSSI());

// Monitor memory usage
Serial.println(ESP.getFreeHeap());
```

### Server Debugging

```bash
# Run with debug logging
python esp32_webrtc_server.py --log-level debug

# Check API endpoint
curl -v http://localhost:8000/health

# Monitor connections
watch -n 1 'curl -s http://localhost:8000/api/devices | jq'
```

## Advanced Features

### Custom Voice Models

To add custom TTS voices, update the `VOICE_OPTIONS` dictionary in the server:

```python
VOICE_OPTIONS = {
    "custom_voice": "your-custom-voice-id",
    "british_lady": "71a7ad14-091c-4e8e-a314-022ece01c121",
    # ... other voices
}
```

### Database Integration

For persistent device storage, uncomment database dependencies in `requirements.txt` and configure:

```python
# Add to .env
DATABASE_URL=sqlite:///./esp32_devices.db
# or
DATABASE_URL=postgresql://user:password@localhost/esp32_ai
```

### Security Enhancements

1. **Device Authentication**:
   ```python
   # Add API key authentication
   API_KEY=your_secure_api_key
   ```

2. **HTTPS/TLS**:
   ```bash
   # Run with SSL
   uvicorn esp32_webrtc_server:app --ssl-keyfile=key.pem --ssl-certfile=cert.pem
   ```

## Performance Optimization

### Server Optimization

1. **CPU Usage**: Use faster models for development (gpt-3.5-turbo)
2. **Memory**: Monitor WebRTC connection limits
3. **Network**: Configure proper ICE servers for NAT traversal

### ESP32 Optimization

1. **Audio Buffer Size**: Adjust I2S buffer for lower latency
2. **WiFi Power**: Configure power saving modes
3. **Memory Management**: Monitor heap usage

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the BSD 2-Clause License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the Pipecat documentation: https://pipecat.ai/docs
- Review API documentation at `/docs` endpoint

## Acknowledgments

- [Pipecat AI](https://pipecat.ai/) - Conversational AI framework
- [Daily](https://daily.co/) - WebRTC infrastructure
- [OpenAI](https://openai.com/) - Language models
- [Deepgram](https://deepgram.com/) - Speech recognition
- [Cartesia](https://cartesia.ai/) - Text-to-speech

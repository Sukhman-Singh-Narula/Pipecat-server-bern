# Enhanced Pipecat Server

This is an enhanced Pipecat server that includes the original 07-interruptible.py functionality plus comprehensive user management, episode-based system prompts, and Firebase integration.

## 🚀 Features

### Core Audio Features
- **WebRTC Audio Streaming**: Real-time audio with ESP32 devices
- **Voice Interruption**: Silero VAD for natural conversation flow
- **Multi-transport Support**: WebRTC, Daily, and Twilio
- **High-quality TTS**: Cartesia voice synthesis
- **Accurate STT**: Deepgram speech recognition
- **Smart LLM**: OpenAI integration with context management

### Enhanced Management Features
- **User Registration**: Device ID-based user accounts (ABCD1234 format)
- **Episode System**: Season/episode progression (10 seasons, 7 episodes each)
- **Custom System Prompts**: Firebase-stored prompts for each episode
- **Learning Analytics**: Progress tracking, word/topic learning
- **Session Management**: Connection status and duration tracking
- **Data Persistence**: Firebase Firestore integration with local fallback

## 📋 API Endpoints

### Authentication
- `POST /auth/register` - Register new users
- `GET /auth/verify/{device_id}` - Verify device registration
- `POST /auth/validate-device-id` - Validate device ID format

### User Management
- `GET /users/{device_id}` - Get user information
- `GET /users/{device_id}/statistics` - Get learning statistics
- `GET /users/{device_id}/session` - Get session information
- `PUT /users/{device_id}/progress` - Update learning progress
- `POST /users/{device_id}/advance-episode` - Advance to next episode
- `DELETE /users/{device_id}` - Deactivate user account

### System Prompts
- `POST /prompts/` - Create/update system prompts
- `GET /prompts/{season}/{episode}` - Get specific prompt
- `GET /prompts/{season}/{episode}/content` - Get raw prompt content
- `GET /prompts/{season}` - Get season overview
- `GET /prompts/` - Get all seasons overview
- `POST /prompts/validate` - Validate prompt content
- `GET /prompts/search` - Search prompts

### Server Status
- `GET /` - Server information
- `GET /health` - Health check
- `GET /docs` - API documentation

## 🛠 Setup

### 1. Environment Configuration

Copy and configure your environment:
```bash
cp .env.example .env
```

Edit `.env` and set your API keys:
```env
# Required API Keys
OPENAI_API_KEY=your_openai_api_key
DEEPGRAM_API_KEY=your_deepgram_api_key  
CARTESIA_API_KEY=your_cartesia_api_key
DAILY_API_KEY=your_daily_api_key

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=7860
LOG_LEVEL=info

# Firebase (optional - will use local storage if not configured)
FIREBASE_CREDENTIALS_PATH=firebase-credentials.json
```

### 2. Firebase Setup (Optional)

For full functionality, set up Firebase Firestore:

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project
3. Enable Firestore Database
4. Generate service account credentials
5. Download `firebase-credentials.json` to the server directory

**Note**: If Firebase is not configured, the server will automatically use local JSON file storage.

### 3. Install Dependencies

```bash
# Using pip
pip install -r requirements.txt

# Or using the setup script
python setup.py
```

### 4. Run the Server

```bash
# WebRTC (default)
python bot.py --transport webrtc --host 0.0.0.0 --esp32

# Daily
python bot.py --transport daily --host 0.0.0.0

# Twilio  
python bot.py --transport twilio --host 0.0.0.0
```

## 📱 Usage Examples

### Register a User
```bash
curl -X POST "http://localhost:7860/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "ABCD1234",
    "name": "John Doe", 
    "age": 25
  }'
```

### Create System Prompt
```bash
curl -X POST "http://localhost:7860/prompts/" \
  -H "Content-Type: application/json" \
  -d '{
    "season": 1,
    "episode": 1,
    "prompt": "You are a friendly English tutor helping beginners learn basic vocabulary...",
    "prompt_type": "learning"
  }'
```

### Get User Progress
```bash
curl "http://localhost:7860/users/ABCD1234"
```

### Update Learning Progress
```bash
curl -X PUT "http://localhost:7860/users/ABCD1234/progress" \
  -H "Content-Type: application/json" \
  -d '{
    "words_learnt": ["hello", "goodbye", "thank you"],
    "topics_learnt": ["greetings", "basic politeness"]
  }'
```

## 🎯 How It Works

### Episode-Based Learning
1. Users register with a unique device ID
2. Start at Season 1, Episode 1
3. Each episode has a custom system prompt for specific learning goals
4. Progress automatically or manually to next episodes
5. Complete seasons to unlock new content

### System Prompt Integration
- When ESP32 connects, server retrieves user's current episode
- Loads corresponding system prompt from Firebase/local storage
- AI assistant adapts behavior based on learning objectives
- Progress tracking updates as conversations complete

### Data Flow
```
ESP32 Device → WebRTC → Pipecat Server → User Management → Firebase
                ↓                          ↓
           Audio Pipeline              System Prompts
                ↓                          ↓
         Deepgram STT                 OpenAI LLM
                ↓                          ↓
           OpenAI LLM              Cartesia TTS → Audio Output
```

## 🔧 Configuration Options

### Server Settings
- `SERVER_HOST`: Bind address (0.0.0.0 for all interfaces)
- `SERVER_PORT`: Port number (default: 7860)
- `LOG_LEVEL`: Logging verbosity (debug, info, warning, error)
- `DEBUG`: Enable debug mode

### Transport Options
- `--transport webrtc`: Direct WebRTC (recommended for ESP32)
- `--transport daily`: Daily.co integration
- `--transport twilio`: Twilio integration
- `--esp32`: Enable ESP32-specific optimizations
- `--host`: Server host address

## 🐛 Troubleshooting

### Common Issues

**Firebase Connection Failed**
- Server automatically falls back to local JSON storage
- Check `firebase-credentials.json` path and permissions
- Verify Firestore is enabled in Firebase Console

**ESP32 Audio Issues**
- Ensure `--esp32` flag is used with WebRTC transport
- Check network connectivity and firewall settings
- Verify device ID format (4 letters + 4 digits)

**API Key Errors**
- Verify all required API keys are set in `.env`
- Check API key permissions and quotas
- Ensure keys are not expired

### Logs and Debugging
```bash
# Enable debug logging
LOG_LEVEL=debug python bot.py --transport webrtc --esp32

# Check server health
curl http://localhost:7860/health

# View API documentation
open http://localhost:7860/docs
```

## 📚 Development

### Project Structure
```
server/
├── bot.py                 # Enhanced main application
├── models/               # Data models
│   ├── user.py          # User-related models
│   └── system_prompt.py # Prompt models
├── services/            # Business logic
│   ├── firebase_service.py
│   ├── user_service.py
│   └── prompt_service.py
├── routes/              # API endpoints
│   ├── auth.py
│   ├── users.py
│   └── prompts.py
├── utils/               # Utilities
│   ├── exceptions.py
│   ├── validators.py
│   └── logger.py
└── config/              # Configuration
    └── settings.py
```

### Adding New Features
1. Add models to `models/`
2. Implement business logic in `services/`
3. Create API endpoints in `routes/`
4. Update dependencies in `requirements.txt`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes following the existing patterns
4. Test thoroughly
5. Submit a pull request

## 📄 License

BSD 2-Clause License - see original Pipecat license for details.

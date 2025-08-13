# Minimalistic Pipecat Server

This is a minimalistic copy of the Pipecat framework containing only the essential files needed to run the 07-interruptible.py example.

## Setup

1. Copy your environment variables:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your API keys:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `DEEPGRAM_API_KEY`: Your Deepgram API key  
   - `CARTESIA_API_KEY`: Your Cartesia API key
   - `DAILY_API_KEY`: Your Daily API key (if using Daily transport)

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Bot

### WebRTC (Default)
```bash
python bot.py
```

### Daily
```bash
python bot.py --transport daily
```

### Twilio
```bash
python bot.py --transport twilio
```

## What this does

This bot creates an interruptible voice assistant that:
- Uses Deepgram for speech-to-text
- Uses OpenAI for language processing
- Uses Cartesia for text-to-speech
- Supports interruption using Silero VAD
- Works with WebRTC, Daily, or Twilio transports

The bot will introduce itself when a client connects and respond to user input in real-time.

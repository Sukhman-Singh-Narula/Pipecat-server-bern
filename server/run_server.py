#!/usr/bin/env python3

"""
Enhanced Pipecat server with FastAPI, WebRTC, and Firebase integration
Works exactly like 07-interruptible.py but with dynamic system prompts
"""

import os
import asyncio
import uvicorn
import argparse
import sys
import importlib.util
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from loguru import logger
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

# Pipecat imports - exactly like 07-interruptible.py
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.runner.types import RunnerArguments, SmallWebRTCRunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.services.cartesia.tts import CartesiaHttpTTSService
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.network.fastapi_websocket import FastAPIWebsocketParams
from pipecat.transports.services.daily import DailyParams

# Import our enhanced functionality
from config.settings import get_settings, validate_settings
from services.firebase_service import FirebaseService
from utils import setup_logging, handle_generic_error

# Import the new comprehensive API routers
from api.enhanced_users import router as enhanced_users_router
from api.episodes import router as episodes_router
from api.conversations import router as conversations_router

load_dotenv(override=True)

# Global state for managing active sessions - like 07-interruptible.py
active_sessions: Dict[str, Any] = {}
active_transports: Dict[str, BaseTransport] = {}

# Transport params - exactly like 07-interruptible.py
transport_params = {
    "daily": lambda: DailyParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        vad_analyzer=SileroVADAnalyzer(),
    ),
    "twilio": lambda: FastAPIWebsocketParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        vad_analyzer=SileroVADAnalyzer(),
    ),
    "webrtc": lambda: TransportParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        vad_analyzer=SileroVADAnalyzer(),
    ),
}

def get_default_system_prompt() -> str:
    """Default system prompt - exactly like 07-interruptible.py"""
    return "You are a helpful LLM in a WebRTC call. Your goal is to demonstrate your capabilities in a succinct way. Your output will be converted to audio so don't include special characters in your answers. Respond to what the user said in a creative and helpful way."

async def get_enhanced_system_prompt(device_id: str = None) -> str:
    """Get enhanced system prompt based on user data from Firebase"""
    
    if not device_id:
        return get_default_system_prompt()
    
    try:
        # Get Firebase service
        from services.firebase_service import get_firebase_service
        
        firebase_service = get_firebase_service()
        
        # Get user document directly using device_id as document ID
        user_doc = await firebase_service.get_document("users", device_id)
        
        if user_doc:
            # Extract user data from document
            name = user_doc.get('name', 'Student')
            age = user_doc.get('age', 10)
            progress = user_doc.get('progress', {})
            
            # Get current season and episode
            season = progress.get('season', 1)
            episode = progress.get('episode', 1)
            episodes_completed = progress.get('episodes_completed', 0)
            words_learnt = progress.get('words_learnt', [])
            topics_learnt = progress.get('topics_learnt', [])
            
            logger.info(f"Found user for device {device_id}: {name} (age {age}, Season {season}, Episode {episode})")
            
            # Try different system prompt document ID formats
            system_prompt_id_formats = [
                f"season_{season}_episode_{episode}",
                f"s{season}e{episode}",
                f"{season}_{episode}",
                f"season{season}_episode{episode}"
            ]
            
            system_prompt_doc = None
            for prompt_id in system_prompt_id_formats:
                prompt_doc = await firebase_service.get_document("system_prompts", prompt_id)
                if prompt_doc:
                    system_prompt_doc = prompt_doc
                    logger.info(f"Found system prompt with ID: {prompt_id}")
                    break
            
            if system_prompt_doc:
                # Extract system prompt data
                title = system_prompt_doc.get('title', f'Season {season} Episode {episode}')
                content = system_prompt_doc.get('content', '')
                learning_objectives = system_prompt_doc.get('learning_objectives', [])
                words_to_teach = system_prompt_doc.get('words_to_teach', [])
                topics_to_cover = system_prompt_doc.get('topics_to_cover', [])
                difficulty_level = system_prompt_doc.get('difficulty_level', 'beginner')
                
                # Create enhanced system prompt with user context
                enhanced_prompt = f"""You are a friendly AI tutor helping {name} (age {age}) learn English.

Current Episode: {title}
Learning Level: {difficulty_level}
Learning Objectives: {', '.join(learning_objectives) if learning_objectives else 'General English conversation'}
Words to Teach: {', '.join(words_to_teach) if words_to_teach else 'Context-appropriate vocabulary'}
Topics to Cover: {', '.join(topics_to_cover) if topics_to_cover else 'General conversation topics'}

Episode Content:
{content}

Student Context:
- Name: {name}
- Age: {age}
- Device ID: {device_id}
- Current Progress: Season {season}, Episode {episode}
- Episodes Completed: {episodes_completed}
- Words Already Learned: {len(words_learnt)} words ({', '.join(words_learnt[-5:]) if words_learnt else 'none yet'})
- Topics Already Covered: {len(topics_learnt)} topics ({', '.join(topics_learnt[-3:]) if topics_learnt else 'none yet'})

Remember to:
- Use age-appropriate language for a {age}-year-old
- Focus on teaching these specific words: {', '.join(words_to_teach) if words_to_teach else 'vocabulary that comes up naturally'}
- Cover these topics naturally in conversation: {', '.join(topics_to_cover) if topics_to_cover else 'topics of interest to the student'}
- Build on {name}'s previous learning (they've completed {episodes_completed} episodes)
- Keep conversations engaging and interactive
- Provide gentle corrections and encouragement
- Adapt to {name}'s learning pace and interests
- Your output will be converted to audio, so avoid special characters

Start the conversation by greeting {name} warmly and beginning the lesson content."""
                
                logger.info(f"Created enhanced system prompt for {name} - Length: {len(enhanced_prompt)} characters")
                return enhanced_prompt
            
            else:
                # No system prompt found, but we have user data
                logger.warning(f"No system prompt found for Season {season}, Episode {episode}. Using user-specific fallback.")
                
                return f"""You are a friendly AI tutor helping {name} (age {age}) learn English.

Current Progress: Season {season}, Episode {episode}
Previous Learning: {name} has completed {episodes_completed} episodes and learned {len(words_learnt)} words.

Since no specific lesson content is available, please:
- Greet {name} warmly by name
- Review some of the words they've learned: {', '.join(words_learnt[-5:]) if words_learnt else 'basic vocabulary'}
- Have a conversation appropriate for a {age}-year-old
- Introduce some new age-appropriate vocabulary
- Keep the lesson engaging and interactive
- Provide gentle corrections and encouragement
- Your output will be converted to audio, so avoid special characters

Start by asking {name} how they're feeling today and what they'd like to talk about."""
        
        else:
            logger.warning(f"No user document found for device {device_id}")
            # Fallback to device-specific but generic prompt
            return f"""You are a friendly AI tutor helping a student learn English.

Device: {device_id}

Please introduce yourself and start a conversational English lesson.

Remember to:
- Use simple, clear language
- Be encouraging and patient
- Ask questions to keep the conversation interactive
- Provide gentle corrections when needed
- Make learning fun and engaging
- Your output will be converted to audio, so avoid special characters

Start by asking the student their name and what they'd like to learn about today."""
    
    except Exception as e:
        logger.error(f"Error creating enhanced system prompt for {device_id}: {e}")
        # Ultimate fallback
        return get_default_system_prompt()

async def get_system_prompt_for_user(device_id: str) -> str:
    """Get user-specific system prompt based on their season/episode progress"""
    return await get_enhanced_system_prompt(device_id)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Enhanced Pipecat Server starting up...")
    
    # Validate settings on startup
    settings = get_settings()
    validate_settings()
    
    logger.info(f"✅ Server configured - App: {settings.app_name} v{settings.app_version}")
    logger.info(f"📊 Debug mode: {settings.debug}")
    
    # Initialize services
    firebase_service = FirebaseService()
    if hasattr(firebase_service, 'use_firebase') and firebase_service.use_firebase:
        logger.info("🔥 Firebase integration enabled")
    else:
        logger.info("💾 Using local storage (Firebase disabled)")
    
    yield
    
    # Shutdown
    logger.info("👋 Enhanced Pipecat Server shutting down...")

def create_enhanced_app() -> FastAPI:
    """Create enhanced FastAPI application with all features"""
    
    settings = get_settings()
    
    app = FastAPI(
        title="Enhanced Pipecat Server",
        version="1.0.0",
        description="""
        ## Enhanced Pipecat Server with User Management
        
        A comprehensive Pipecat server with:
        - **WebRTC Audio**: Real-time audio streaming with ESP32 devices
        - **User Management**: Device registration and progress tracking  
        - **Episode System**: Season/episode progression with custom prompts
        - **Firebase Integration**: User data and prompt storage
        - **Learning Analytics**: Progress tracking and statistics
        
        ### Getting Started:
        1. Register a user with POST /auth/register
        2. Upload system prompts with POST /prompts/
        3. Connect ESP32 via WebRTC audio at /client
        4. Monitor progress with GET /users/{device_id}
        """,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
        debug=settings.debug
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include the new comprehensive API routers
    app.include_router(enhanced_users_router, tags=["Enhanced Users"])
    app.include_router(episodes_router, tags=["Episode Prompts"])
    app.include_router(conversations_router, tags=["Conversations"])
    
    # Enhanced root endpoint
    @app.get("/", 
             summary="Server status",
             description="Get enhanced server status and information")
    async def root():
        """Root endpoint returning enhanced server status"""
        settings = get_settings()
        
        return {
            "message": "Enhanced Pipecat Server is running",
            "version": "1.0.0",
            "status": "healthy",
            "features": [
                "WebRTC audio streaming",
                "User registration and management",
                "Episode-based system prompts",
                "Learning progress tracking",
                "Firebase data storage",
                "ESP32 device support"
            ],
            "endpoints": {
                "documentation": "/docs",
                "webrtc_client": "/client",
                "health_check": "/health",
                "user_auth": "/auth/register",
                "user_management": "/users/{device_id}",
                "prompt_management": "/prompts/"
            },
            "configuration": {
                "app_name": settings.app_name,
                "version": settings.app_version,
                "debug": settings.debug
            }
        }
    
    # Health check endpoint
    @app.get("/health",
             summary="Health check",
             description="Check server health and status with ESP32 support")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "esp32_mode": ESP32_MODE,
            "esp32_host": ESP32_HOST if ESP32_MODE else None,
            "sdp_munging": "enabled" if ESP32_MODE else "disabled",
            "services": {
                "firebase": "available",
                "enhanced_users": "running", 
                "episodes": "running",
                "conversations": "running",
                "openai": "available" if os.getenv("OPENAI_API_KEY") else "missing",
                "deepgram": "available" if os.getenv("DEEPGRAM_API_KEY") else "missing",
                "cartesia": "available" if os.getenv("CARTESIA_API_KEY") else "missing"
            }
        }

    # Import WebRTC static files and client from Pipecat
    from fastapi.staticfiles import StaticFiles
    from pathlib import Path
    
    # Add WebRTC client interface (mirroring what bot.py does)
    try:
        # Try to find the WebRTC client dist directory in common locations
        potential_paths = [
            # ESP-IDF environment paths
            "/Users/sukhmansinghnarula/.espressif/python_env/idf6.0_py3.13_env/lib/python3.13/site-packages/pipecat_ai_small_webrtc_prebuilt/client/dist",
            # Standard Python package paths for your server environment
            "/root/Pipecat-server-bern/venv/lib/python3.12/site-packages/pipecat_ai_small_webrtc_prebuilt/client/dist",
            "/usr/local/lib/python3.12/site-packages/pipecat_ai_small_webrtc_prebuilt/client/dist",
            # Try to find via site-packages dynamically
            f"{sys.prefix}/lib/python3.12/site-packages/pipecat_ai_small_webrtc_prebuilt/client/dist",
            f"{sys.prefix}/lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages/pipecat_ai_small_webrtc_prebuilt/client/dist",
            # Local paths
            "./client/dist",
            "../client/dist",
            "./static/client",
            "../static/client"
        ]
        
        # Try to get path from importlib (Python 3.9+)
        try:
            import importlib.util
            spec = importlib.util.find_spec('pipecat_ai_small_webrtc_prebuilt')
            if spec and spec.origin:
                pkg_dir = os.path.dirname(spec.origin)
                client_path = os.path.join(pkg_dir, 'client', 'dist')
                potential_paths.insert(0, client_path)
                logger.info(f"Added importlib-detected path: {client_path}")
        except Exception as e:
            logger.warning(f"Could not detect package path via importlib: {e}")
            pass
        
        dist_dir = None
        for path in potential_paths:
            abs_path = os.path.abspath(path)
            if Path(abs_path).exists():
                dist_dir = abs_path
                logger.info(f"Found WebRTC client dist directory at: {dist_dir}")
                break
        
        if dist_dir:
            app.mount("/client", StaticFiles(directory=dist_dir, html=True), name="webrtc_client")
            logger.info("✅ WebRTC client interface mounted at /client")
        else:
            logger.warning("WebRTC client dist directory not found in any expected location")
            logger.info("Available paths checked:")
            for path in potential_paths:
                exists = "✅" if Path(path).exists() else "❌"
                logger.info(f"  {exists} {path}")
            
            # Create a fallback /client endpoint that redirects to /test
            @app.get("/client", response_class=HTMLResponse)
            async def client_fallback():
                return HTMLResponse(content="""
                <!DOCTYPE html>
                <html>
                <head><title>WebRTC Client - Redirecting</title></head>
                <body>
                    <h1>WebRTC Client</h1>
                    <p>The official WebRTC client is not available. Redirecting to test client...</p>
                    <script>
                        setTimeout(() => {
                            window.location.href = '/test';
                        }, 2000);
                    </script>
                    <p><a href="/test">Click here if not redirected automatically</a></p>
                </body>
                </html>
                """)
            logger.info("✅ Created fallback /client endpoint redirecting to /test")
            
    except Exception as e:
        logger.warning(f"Could not mount WebRTC client: {e}")
        
        # Create a fallback /client endpoint even on error
        @app.get("/client", response_class=HTMLResponse)
        async def client_error_fallback():
            return HTMLResponse(content="""
            <!DOCTYPE html>
            <html>
            <head><title>WebRTC Client - Error</title></head>
            <body>
                <h1>WebRTC Client Error</h1>
                <p>Could not load the official WebRTC client interface.</p>
                <p><a href="/test">Use the ESP32 test client instead</a></p>
                <p><a href="/docs">View API documentation</a></p>
            </body>
            </html>
            """)
        logger.info("✅ Created error fallback /client endpoint")
    
    # Add test page for ESP32 debugging
    @app.get("/test", response_class=HTMLResponse)
    async def test_page():
        """Serve ESP32 WebRTC test page"""
        return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ESP32 WebRTC Test - Fixed</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f5f5f5; }
        .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, button { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; }
        button { background: #007bff; color: white; cursor: pointer; margin-top: 10px; }
        button:hover { background: #0056b3; }
        button:disabled { background: #ccc; cursor: not-allowed; }
        .status { padding: 10px; border-radius: 5px; margin: 10px 0; }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .warning { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
        .info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        #audioLevel { width: 100%; height: 20px; background: #f0f0f0; border: 1px solid #ccc; margin-top: 10px; }
        #audioLevelBar { height: 100%; background: #4CAF50; width: 0%; transition: width 0.1s; }
        .logs { background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; padding: 15px; height: 200px; overflow-y: auto; font-family: monospace; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎙️ ESP32 WebRTC Test Client</h1>
        <p>This page tests WebRTC connections to debug ESP32 communication issues.</p>
        
        <div class="form-group">
            <label for="deviceId">ESP32 Device ID:</label>
            <input type="text" id="deviceId" value="ESPX3001" placeholder="Enter your ESP32 device ID">
        </div>
        
        <div class="form-group">
            <button onclick="testMicrophone()">🎤 Test Microphone Access</button>
            <div id="audioLevel">
                <div id="audioLevelBar"></div>
            </div>
            <small>Audio level indicator (speak to test microphone)</small>
        </div>
        
        <div class="form-group">
            <button onclick="connectWebRTC()" id="connectBtn">🔗 Start WebRTC Connection</button>
            <button onclick="disconnect()" id="disconnectBtn" disabled>❌ Disconnect</button>
        </div>
        
        <div id="status"></div>
        
        <h3>📋 Connection Logs:</h3>
        <div id="logs" class="logs"></div>
    </div>

    <script>
        let pc = null;
        let localStream = null;
        let audioContext = null;
        let analyser = null;
        let microphone = null;
        let connected = false;

        function log(message, type = 'info') {
            const logs = document.getElementById('logs');
            const timestamp = new Date().toLocaleTimeString();
            const logEntry = document.createElement('div');
            logEntry.style.color = type === 'error' ? 'red' : type === 'success' ? 'green' : type === 'warning' ? 'orange' : 'black';
            logEntry.textContent = `[${timestamp}] ${message}`;
            logs.appendChild(logEntry);
            logs.scrollTop = logs.scrollHeight;
            console.log(`[${type.toUpperCase()}] ${message}`);
        }

        function showStatus(message, type) {
            const status = document.getElementById('status');
            status.innerHTML = `<div class="${type}">${message}</div>`;
        }

        async function testMicrophone() {
            try {
                log('Testing microphone access...', 'info');
                
                // Request microphone permission with better constraints
                const stream = await navigator.mediaDevices.getUserMedia({
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true,
                        sampleRate: 48000
                    }
                });

                log('✅ Microphone access granted!', 'success');
                showStatus('✅ Microphone access successful! Audio level monitoring started.', 'success');

                // Set up audio level monitoring
                audioContext = new AudioContext();
                analyser = audioContext.createAnalyser();
                microphone = audioContext.createMediaStreamSource(stream);
                
                microphone.connect(analyser);
                analyser.fftSize = 256;
                
                const bufferLength = analyser.frequencyBinCount;
                const dataArray = new Uint8Array(bufferLength);

                function updateAudioLevel() {
                    analyser.getByteFrequencyData(dataArray);
                    let sum = 0;
                    for (let i = 0; i < bufferLength; i++) {
                        sum += dataArray[i];
                    }
                    const average = sum / bufferLength;
                    const percentage = (average / 255) * 100;
                    
                    document.getElementById('audioLevelBar').style.width = percentage + '%';
                    
                    if (!connected) {
                        requestAnimationFrame(updateAudioLevel);
                    }
                }
                updateAudioLevel();

                // Store stream for WebRTC
                localStream = stream;
                
            } catch (error) {
                log(`❌ Microphone access failed: ${error.message}`, 'error');
                showStatus(`❌ Microphone access denied: ${error.message}`, 'error');
            }
        }

        async function connectWebRTC() {
            const deviceId = document.getElementById('deviceId').value.trim();
            if (!deviceId) {
                showStatus('❌ Please enter a device ID', 'error');
                return;
            }

            if (!localStream) {
                showStatus('❌ Please test microphone first', 'error');
                return;
            }

            try {
                document.getElementById('connectBtn').disabled = true;
                log(`Starting WebRTC connection for device: ${deviceId}`, 'info');

                // Create peer connection with proper configuration
                pc = new RTCPeerConnection({
                    iceServers: [
                        { urls: 'stun:stun.l.google.com:19302' }
                    ]
                });

                // Add local stream
                localStream.getTracks().forEach(track => {
                    pc.addTrack(track, localStream);
                    log(`Added ${track.kind} track to peer connection`, 'info');
                });

                // Handle remote stream
                pc.ontrack = (event) => {
                    log(`Received remote ${event.track.kind} track`, 'success');
                    if (event.track.kind === 'audio') {
                        const audio = document.createElement('audio');
                        audio.srcObject = event.streams[0];
                        audio.autoplay = true;
                        audio.controls = true;
                        document.body.appendChild(audio);
                        log('✅ Audio element created for bot speech', 'success');
                    }
                };

                // Handle ICE candidates
                pc.onicecandidate = (event) => {
                    if (event.candidate) {
                        log(`ICE candidate: ${event.candidate.candidate}`, 'info');
                    } else {
                        log('All ICE candidates have been sent', 'info');
                    }
                };

                pc.onconnectionstatechange = () => {
                    log(`Connection state: ${pc.connectionState}`, 'info');
                    if (pc.connectionState === 'connected') {
                        connected = true;
                        showStatus('✅ WebRTC connection established!', 'success');
                        document.getElementById('disconnectBtn').disabled = false;
                    } else if (pc.connectionState === 'failed') {
                        showStatus('❌ WebRTC connection failed', 'error');
                        disconnect();
                    }
                };

                // Create offer
                const offer = await pc.createOffer({
                    offerToReceiveAudio: true,
                    offerToReceiveVideo: false
                });
                
                await pc.setLocalDescription(offer);
                log('Created and set local offer', 'info');

                // Send offer to server with device ID
                const response = await fetch('/api/offer', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Device-ID': deviceId
                    },
                    body: JSON.stringify({
                        device_id: deviceId,
                        type: 'offer',
                        sdp: offer.sdp
                    })
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const answer = await response.json();
                log('Received answer from server', 'success');

                await pc.setRemoteDescription(new RTCSessionDescription({
                    type: 'answer',
                    sdp: answer.sdp
                }));
                
                log('✅ WebRTC handshake completed!', 'success');
                showStatus('🔄 Connecting... Check for audio from the AI assistant.', 'info');

            } catch (error) {
                log(`❌ WebRTC connection failed: ${error.message}`, 'error');
                showStatus(`❌ Connection failed: ${error.message}`, 'error');
                document.getElementById('connectBtn').disabled = false;
            }
        }

        function disconnect() {
            if (pc) {
                pc.close();
                pc = null;
                log('WebRTC connection closed', 'info');
            }
            
            if (localStream) {
                localStream.getTracks().forEach(track => track.stop());
                localStream = null;
                log('Local media stream stopped', 'info');
            }

            if (audioContext) {
                audioContext.close();
                audioContext = null;
            }

            connected = false;
            document.getElementById('connectBtn').disabled = false;
            document.getElementById('disconnectBtn').disabled = true;
            document.getElementById('audioLevelBar').style.width = '0%';
            showStatus('Connection closed', 'info');
        }

        // Auto-test microphone on page load
        window.addEventListener('load', () => {
            log('🚀 ESP32 WebRTC Test Client loaded', 'info');
            log('Click "Test Microphone Access" first, then "Start WebRTC Connection"', 'info');
        });
    </script>
</body>
</html>
        """)
    
    # WebRTC offer endpoint - exactly like 07-interruptible.py approach with ESP32 support
    @app.post("/api/offer",
              summary="WebRTC offer handler", 
              description="Handle WebRTC offer from ESP32 devices with custom prompts and SDP munging")
    async def handle_webrtc_offer(request: Request, background_tasks: BackgroundTasks):
        """Handle WebRTC offers exactly like 07-interruptible.py but with Firebase integration and ESP32 support"""
        try:
            body = await request.json()
            
            # Extract device ID from multiple sources
            device_id = (
                body.get("device_id") or 
                request.headers.get("X-Device-ID") or
                request.query_params.get("device_id") or
                None
            )
            
            logger.info(f"Received WebRTC offer from device: {device_id}")
            
            # Store session info
            session_id = f"webrtc_{device_id or 'unknown'}_{len(active_sessions)}"
            active_sessions[session_id] = {
                "device_id": device_id,
                "created_at": datetime.now(timezone.utc),
                "status": "connecting",
                "type": "webrtc"
            }
            
            # Create WebRTC connection with ESP32 support - like the working examples
            from pipecat.transports.network.webrtc_connection import SmallWebRTCConnection
            from pipecat.runner.utils import smallwebrtc_sdp_munging
            from pipecat.runner.types import SmallWebRTCRunnerArguments
            
            # Create connection and get answer
            webrtc_connection = SmallWebRTCConnection()
            offer_sdp = body.get("sdp", "")
            offer_type = body.get("type", "offer")
            
            await webrtc_connection.initialize(offer_sdp, offer_type)
            answer = webrtc_connection.get_answer()
            
            # Apply ESP32 SDP munging for compatibility - CRUCIAL for ESP32!
            if ESP32_MODE and ESP32_HOST and ESP32_HOST not in ["localhost", "127.0.0.1", "0.0.0.0"]:
                logger.info(f"Applying ESP32 SDP munging for host: {ESP32_HOST}")
                answer["sdp"] = smallwebrtc_sdp_munging(answer["sdp"], ESP32_HOST)
            else:
                # Fallback: try to get host from environment or request
                host = request.headers.get("Host", "").split(":")[0]
                if not host or host in ["localhost", "127.0.0.1", "0.0.0.0"]:
                    host = os.getenv("SERVER_HOST", "64.227.157.74")
                
                if ESP32_MODE and host and host not in ["localhost", "127.0.0.1", "0.0.0.0"]:
                    logger.info(f"Applying ESP32 SDP munging for fallback host: {host}")
                    answer["sdp"] = smallwebrtc_sdp_munging(answer["sdp"], host)
                elif ESP32_MODE:
                    # If we're in ESP32 mode but don't have a valid host, disable SDP munging
                    logger.warning(f"ESP32 mode enabled but no valid host found (current: {host}). Skipping SDP munging.")
                    logger.info("Consider starting server with: --host 64.227.157.74 --esp32")
            
            # Create proper runner args for SmallWebRTC
            runner_args = SmallWebRTCRunnerArguments(webrtc_connection=webrtc_connection)
            runner_args.handle_sigint = False
            runner_args.pipeline_idle_timeout_secs = 60  # Increased timeout for better stability
            
            # Start the enhanced bot in background - exactly like working examples
            background_tasks.add_task(enhanced_bot_webrtc, runner_args, device_id)
            
            # Update session status
            active_sessions[session_id]["status"] = "connected"
            
            logger.info(f"WebRTC connection established for ESP32 device: {device_id}")
            
            # Return the munged SDP answer for ESP32 compatibility
            return answer
            
        except Exception as e:
            logger.error(f"Error handling WebRTC offer: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # WebRTC client info endpoint
    @app.get("/client-info",
             summary="WebRTC client info",
             description="Get WebRTC client connection information")
    async def webrtc_client_info():
        """Get WebRTC client information"""
        return {
            "webrtc_client": "/client",
            "offer_endpoint": "/api/offer",
            "instructions": "ESP32 devices should send WebRTC offers to /api/offer",
            "browser_client": "Open /client in browser for testing"
        }
    
    return app

async def run_enhanced_bot(transport: BaseTransport, runner_args: RunnerArguments, device_id: str = None):
    """Enhanced bot function - exactly like 07-interruptible.py but with Firebase integration"""
    logger.info(f"Starting enhanced bot for device: {device_id}")
    
    conversation_id = None
    user = None
    firebase_service = None
    
    try:
        # Initialize conversation tracking if device_id is provided
        if device_id:
            from services.firebase_service import get_firebase_service
            from services.enhanced_user_service import EnhancedUserService
            from services.conversation_service import ConversationService
            
            firebase_service = get_firebase_service()
            user_service = EnhancedUserService(firebase_service)
            conversation_service = ConversationService(firebase_service)
            
            # Get user and start conversation session
            user = await user_service.get_user_by_device_id(device_id)
            if user:
                # Start a conversation session
                conversation_id = f"{user.email}_{user.progress.season}_{user.progress.episode}_{int(datetime.now(timezone.utc).timestamp())}"
                
                from models.conversation import ConversationTranscript
                transcript = ConversationTranscript(
                    conversation_id=conversation_id,
                    user_email=user.email,
                    season=user.progress.season,
                    episode=user.progress.episode
                )
                
                await firebase_service.set_document(
                    "conversation_transcripts",
                    conversation_id,
                    transcript.to_dict()
                )
                
                logger.info(f"Started conversation session {conversation_id} for user {user.email}")

        # Services - exactly like 07-interruptible.py
        stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_API_KEY"))

        # Debug: Check if API key is loaded
        cartesia_api_key = os.getenv("CARTESIA_API_KEY")
        logger.info(f"Cartesia API key loaded: {cartesia_api_key[:10] if cartesia_api_key else 'None'}...")

        tts = CartesiaHttpTTSService(
            api_key=cartesia_api_key,
            voice_id="71a7ad14-091c-4e8e-a314-022ece01c121",  # British Reading Lady
        )

        llm = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY"))

        # Get enhanced system prompt based on user data
        system_prompt = await get_enhanced_system_prompt(device_id)
        
        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
        ]

        context = OpenAILLMContext(messages)
        context_aggregator = llm.create_context_aggregator(context)

        # Pipeline - exactly like 07-interruptible.py
        pipeline = Pipeline(
            [
                transport.input(),  # Transport user input
                stt,
                context_aggregator.user(),  # User responses
                llm,  # LLM
                tts,  # TTS
                transport.output(),  # Transport bot output
                context_aggregator.assistant(),  # Assistant spoken responses
            ]
        )

        task = PipelineTask(
            pipeline,
            params=PipelineParams(
                enable_metrics=True,
                enable_usage_metrics=True,
            ),
            idle_timeout_secs=runner_args.pipeline_idle_timeout_secs,
        )

        @transport.event_handler("on_client_connected")
        async def on_client_connected(transport, client):
            logger.info(f"Client connected - device: {device_id}")
            # Update user last seen if device_id provided  
            if device_id:
                try:
                    # For now, just log the connection - user service integration can be added later
                    logger.info(f"Device {device_id} connected and active")
                except Exception as e:
                    logger.warning(f"Failed to update last seen for {device_id}: {e}")
            
            # Kick off the conversation - exactly like 07-interruptible.py
            messages.append({"role": "system", "content": "Please introduce yourself to the user."})
            await task.queue_frames([context_aggregator.user().get_context_frame()])

        @transport.event_handler("on_client_disconnected")
        async def on_client_disconnected(transport, client):
            logger.info(f"Client disconnected - device: {device_id}")
            
            # Finalize conversation session if it exists
            if device_id and conversation_id and firebase_service:
                try:
                    # Get conversation transcript and create summary
                    transcript_doc = await firebase_service.get_document("conversation_transcripts", conversation_id)
                    if transcript_doc:
                        conversation_messages = []
                        for msg in messages[1:]:  # Skip system prompt
                            conversation_messages.append(msg)
                        
                        # Update transcript with conversation messages
                        transcript_doc['messages'] = conversation_messages
                        transcript_doc['ended_at'] = datetime.now(timezone.utc).isoformat()
                        
                        await firebase_service.update_document("conversation_transcripts", conversation_id, transcript_doc)
                        
                        # Update user progress if appropriate
                        if user:
                            logger.info(f"Conversation {conversation_id} completed for user {user.email}")
                            # TODO: Add logic to determine if episode was completed and update progress
                            
                except Exception as e:
                    logger.error(f"Failed to finalize conversation {conversation_id}: {e}")
            
            # Clean up session
            if device_id and device_id in active_sessions:
                del active_sessions[device_id]
            if device_id and device_id in active_transports:
                del active_transports[device_id]
            await task.cancel()

        runner = PipelineRunner(handle_sigint=runner_args.handle_sigint)
        await runner.run(task)
        
    except Exception as e:
        logger.error(f"Error in enhanced bot: {e}")
        if device_id and device_id in active_sessions:
            del active_sessions[device_id]
        if device_id and device_id in active_transports:
            del active_transports[device_id]
        raise

async def enhanced_bot(runner_args: RunnerArguments, device_id: str = None):
    """Enhanced bot entry point - like 07-interruptible.py but with device_id"""
    transport = await create_transport(runner_args, transport_params)
    active_transports[device_id or "default"] = transport
    await run_enhanced_bot(transport, runner_args, device_id)

async def enhanced_bot_webrtc(runner_args: SmallWebRTCRunnerArguments, device_id: str = None):
    """Enhanced bot entry point for WebRTC connections with Firebase integration"""
    from pipecat.transports.network.small_webrtc import SmallWebRTCTransport
    from pipecat.runner.utils import _get_transport_params
    
    # Get transport params for webrtc - exactly like working examples
    transport_params_obj = _get_transport_params("webrtc", transport_params)
    
    # Create WebRTC transport from connection
    transport = SmallWebRTCTransport(runner_args.webrtc_connection, transport_params_obj)
    
    # Store in active transports
    active_transports[device_id or "default"] = transport
    
    # Run the enhanced bot with WebRTC transport
    await run_enhanced_bot(transport, runner_args, device_id)

# Create the enhanced app
app = create_enhanced_app()

# Global ESP32 mode flag
ESP32_MODE = False
ESP32_HOST = None

def main():
    global ESP32_MODE, ESP32_HOST
    
    parser = argparse.ArgumentParser(description="Enhanced Pipecat Server - 07-interruptible.py Compatible")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=7860, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--log-level", default="info", help="Log level")
    parser.add_argument("--esp32", action="store_true", help="Enable ESP32 mode with SDP munging")
    
    args = parser.parse_args()
    
    # Set global ESP32 mode
    ESP32_MODE = args.esp32
    ESP32_HOST = args.host
    
    # Validate ESP32 requirements
    if args.esp32 and args.host in ["localhost", "127.0.0.1"]:
        logger.error("For ESP32, you need to specify `--host IP` so we can do SDP munging.")
        sys.exit(1)
    
    print(f"🚀 Starting Enhanced Pipecat Server (07-interruptible.py compatible)...")
    print(f"   Host: {args.host}")
    print(f"   Port: {args.port}")
    print(f"   Log Level: {args.log_level}")
    print(f"   Reload: {args.reload}")
    if args.esp32:
        print(f"🤖 ESP32 mode enabled with SDP munging for host: {args.host}")
    
    # Run the server directly
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level=args.log_level,
        reload=args.reload,
        access_log=True
    )

if __name__ == "__main__":
    main()

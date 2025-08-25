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
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from loguru import logger
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# Pipecat imports - exactly like 07-interruptible.py
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.services.cartesia.tts import CartesiaHttpTTSService
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.network.fastapi_websocket import FastAPIWebsocketParams
from pipecat.transports.services.daily import DailyParams

# Import our enhanced functionality
from config.settings import get_settings, validate_settings
from routes import auth_router, users_router, prompts_router
from services import get_firebase_service, get_user_service, get_prompt_service
from utils import setup_logging, handle_generic_error
from utils.exceptions import UserNotFoundException

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
    """Get enhanced system prompt based on Firebase user data with templating"""
    try:
        if not device_id:
            return get_default_system_prompt()
        
        user_service = get_user_service()
        prompt_service = get_prompt_service()
        
        # Get user data from Firebase
        user_response = await user_service.get_user(device_id)
        season = user_response.season
        episode = user_response.episode
        user_name = getattr(user_response, 'name', 'friend')
        user_age = getattr(user_response, 'age', 'young learner')
        
        logger.info(f"User {device_id} ({user_name}, age {user_age}) is on Season {season}, Episode {episode}")
        
        # Get episode-specific prompt
        prompt_response = await prompt_service.get_prompt(season, episode)
        
        # Template the prompt with user data
        if prompt_response and prompt_response.content:
            templated_prompt = prompt_response.content.format(
                name=user_name,
                age=user_age,
                season=season,
                episode=episode
            )
            logger.info(f"Using custom templated prompt for {device_id} - Season {season}, Episode {episode}")
            return templated_prompt
        else:
            # Fallback with user info - enhanced default prompt
            enhanced_prompt = f"""You are a helpful AI tutor in a WebRTC call with {user_name}, age {user_age}. 
You are currently on Season {season}, Episode {episode} of their learning journey. 
Your goal is to provide educational content appropriate for their level in a succinct way. 
Your output will be converted to audio so don't include special characters in your answers. 
Respond to what the user said in a creative and helpful way."""
            logger.info(f"Using enhanced default prompt for {device_id}")
            return enhanced_prompt
            
    except UserNotFoundException:
        logger.warning(f"User {device_id} not found, using default system prompt")
        return get_default_system_prompt()
    except Exception as e:
        logger.error(f"Error getting enhanced system prompt for {device_id}: {e}")
        return get_default_system_prompt()

async def get_system_prompt_for_user(device_id: str) -> str:
    """Get user-specific system prompt based on their season/episode progress"""
    return await get_enhanced_system_prompt(device_id)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    setup_logging()
    logger.info("🚀 Enhanced Pipecat Server starting up...")
    
    # Validate settings on startup
    settings = get_settings()
    validate_settings()
    
    logger.info(f"✅ Server configured - App: {settings.app_name} v{settings.app_version}")
    logger.info(f"📊 Debug mode: {settings.debug}")
    
    # Initialize services
    firebase_service = get_firebase_service()
    if firebase_service.use_firebase:
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
    
    # Include enhanced routers (prefixes are already defined in router files)
    app.include_router(auth_router, tags=["authentication"])
    app.include_router(users_router, tags=["users"])
    app.include_router(prompts_router, tags=["prompts"])
    
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
                "firebase": "available" if get_firebase_service().use_firebase else "local_storage",
                "user_service": "running",
                "prompt_service": "running",
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
            "/Users/sukhmansinghnarula/.espressif/python_env/idf6.0_py3.13_env/lib/python3.13/site-packages/pipecat_ai_small_webrtc_prebuilt/client/dist",
            "./client/dist",
            "../client/dist"
        ]
        
        dist_dir = None
        for path in potential_paths:
            if Path(path).exists():
                dist_dir = path
                break
        
        if dist_dir:
            logger.info(f"Found WebRTC client dist directory at: {dist_dir}")
            app.mount("/client", StaticFiles(directory=dist_dir, html=True), name="webrtc_client")
            logger.info("✅ WebRTC client interface mounted at /client")
        else:
            logger.warning("WebRTC client dist directory not found in any expected location")
            
    except Exception as e:
        logger.warning(f"Could not mount WebRTC client: {e}")
    
    # WebRTC offer endpoint - exactly like 07-interruptible.py approach with ESP32 support
    @app.post("/api/offer",
              summary="WebRTC offer handler", 
              description="Handle WebRTC offer from ESP32 devices with custom prompts and SDP munging")
    async def handle_webrtc_offer(request: Request, background_tasks: BackgroundTasks):
        """Handle WebRTC offers exactly like 07-interruptible.py but with Firebase integration and ESP32 support"""
        try:
            body = await request.json()
            device_id = body.get("device_id") or request.headers.get("X-Device-ID")
            
            logger.info(f"Received WebRTC offer from device: {device_id}")
            
            # Create runner args - exactly like 07-interruptible.py
            runner_args = RunnerArguments(
                transport="webrtc",
                host="0.0.0.0",
                port=7860,
                pipeline_idle_timeout_secs=30,
                handle_sigint=False
            )
            
            # Store session info
            session_id = f"webrtc_{device_id or 'unknown'}_{len(active_sessions)}"
            active_sessions[session_id] = {
                "device_id": device_id,
                "created_at": datetime.utcnow(),
                "status": "connecting",
                "type": "webrtc"
            }
            
            # Create WebRTC connection with ESP32 support
            from pipecat.transports.network.webrtc_connection import SmallWebRTCConnection
            from pipecat.runner.utils import smallwebrtc_sdp_munging
            
            # Create connection and get answer
            webrtc_connection = SmallWebRTCConnection()
            offer_sdp = body.get("sdp", "")
            offer_type = body.get("type", "offer")
            
            await webrtc_connection.initialize(offer_sdp, offer_type)
            answer = webrtc_connection.get_answer()
            
            # Apply ESP32 SDP munging for compatibility - CRUCIAL for ESP32!
            if ESP32_MODE and ESP32_HOST and ESP32_HOST not in ["localhost", "127.0.0.1"]:
                logger.info(f"Applying ESP32 SDP munging for host: {ESP32_HOST}")
                answer["sdp"] = smallwebrtc_sdp_munging(answer["sdp"], ESP32_HOST)
            else:
                # Fallback: try to get host from environment or request
                host = request.headers.get("Host", "").split(":")[0]
                if not host or host in ["localhost", "127.0.0.1"]:
                    host = os.getenv("SERVER_HOST", "64.227.157.74")
                
                if ESP32_MODE and host and host not in ["localhost", "127.0.0.1"]:
                    logger.info(f"Applying ESP32 SDP munging for fallback host: {host}")
                    answer["sdp"] = smallwebrtc_sdp_munging(answer["sdp"], host)
            
            # Start the enhanced bot in background - exactly like 07-interruptible.py flow
            background_tasks.add_task(enhanced_bot, runner_args, device_id)
            
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
                user_service = get_user_service()
                await user_service.update_last_active(device_id)
            except Exception as e:
                logger.warning(f"Failed to update last seen for {device_id}: {e}")
        
        # Kick off the conversation - exactly like 07-interruptible.py
        messages.append({"role": "system", "content": "Please introduce yourself to the user."})
        await task.queue_frames([context_aggregator.user().get_context_frame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info(f"Client disconnected - device: {device_id}")
        # Clean up session
        if device_id and device_id in active_sessions:
            del active_sessions[device_id]
        if device_id and device_id in active_transports:
            del active_transports[device_id]
        await task.cancel()

    runner = PipelineRunner(handle_sigint=runner_args.handle_sigint)

    await runner.run(task)

async def enhanced_bot(runner_args: RunnerArguments, device_id: str = None):
    """Enhanced bot entry point - like 07-interruptible.py but with device_id"""
    transport = await create_transport(runner_args, transport_params)
    active_transports[device_id or "default"] = transport
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

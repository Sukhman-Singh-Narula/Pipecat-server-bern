#!/usr/bin/env python3

"""
Enhanced Pipecat server with FastAPI, WebRTC, and Firebase integration
"""

import os
import asyncio
import uvicorn
import argparse
from contextlib import asynccontextmanager
from datetime import datetime

from dotenv import load_dotenv
from loguru import logger
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.runner.types import RunnerArguments
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.network.fastapi_websocket import FastAPIWebsocketParams
from pipecat.transports.services.daily import DailyParams
from pipecat.transports.network.small_webrtc import SmallWebRTCTransport

# Import our enhanced functionality
from config.settings import get_settings, validate_settings
from routes import auth_router, users_router, prompts_router
from services import get_firebase_service, get_user_service, get_prompt_service
from utils import setup_logging, handle_generic_error
from utils.exceptions import UserNotFoundException

load_dotenv(override=True)

# Transport configuration
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
    )
}

async def get_system_prompt_for_user(device_id: str) -> str:
    """Get user-specific system prompt based on their season/episode progress"""
    if not device_id:
        return get_default_system_prompt()
    
    try:
        user_service = get_user_service()
        prompt_service = get_prompt_service()
        
        # Get user's current season and episode
        user_response = await user_service.get_user(device_id)
        season = user_response.season
        episode = user_response.episode
        
        logger.info(f"User {device_id} is on Season {season}, Episode {episode}")
        
        # Get the appropriate system prompt
        prompt_response = await prompt_service.get_prompt(season, episode)
        
        if prompt_response and prompt_response.content:
            logger.info(f"Found custom prompt for Season {season}, Episode {episode}")
            return prompt_response.content
        else:
            logger.info(f"No custom prompt found for Season {season}, Episode {episode}, using default")
            return get_default_system_prompt()
            
    except UserNotFoundException:
        logger.warning(f"User {device_id} not found, using default system prompt")
        return get_default_system_prompt()
    except Exception as e:
        logger.error(f"Error getting system prompt for user {device_id}: {e}")
        return get_default_system_prompt()

def get_default_system_prompt() -> str:
    """Default system prompt when no custom prompt is found"""
    return """You are an AI tutor helping students learn complex concepts. 
    You should be encouraging, clear, and provide examples when explaining difficult topics.
    Always ask follow-up questions to ensure the student understands the material."""

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
             description="Check server health and status")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "firebase": "available" if get_firebase_service().use_firebase else "local_storage",
                "user_service": "running",
                "prompt_service": "running",
                "openai": "available" if os.getenv("OPENAI_API_KEY") else "missing",
                "deepgram": "available" if os.getenv("DEEPGRAM_API_KEY") else "missing",
                "elevenlabs": "available" if os.getenv("ELEVENLABS_API_KEY") else "missing"
            }
        }

    # WebRTC offer endpoint for ESP32 devices
    @app.post("/api/offer",
              summary="WebRTC offer handler", 
              description="Handle WebRTC offer from ESP32 devices with custom prompts")
    async def handle_webrtc_offer(offer_data: dict):
        """Handle WebRTC offer from ESP32 devices with dynamic system prompts"""
        try:
            logger.info(f"Received WebRTC offer from ESP32: {offer_data}")
            
            # Extract device_id from offer data if provided
            device_id = offer_data.get("device_id")
            if not device_id:
                # Try to extract from other fields if needed
                device_id = offer_data.get("metadata", {}).get("device_id")
            
            logger.info(f"Processing WebRTC offer for device: {device_id}")
            
            # Import necessary classes for WebRTC
            from pipecat.transports.network.webrtc_connection import SmallWebRTCConnection
            from pipecat.runner.utils import _get_transport_params
            
            # Get transport params for webrtc
            transport_params_obj = _get_transport_params("webrtc", transport_params)
            logger.debug(f"Using transport params for webrtc")
            
            # Create WebRTC connection
            connection = SmallWebRTCConnection()
            await connection.initialize(offer_data.get("sdp", ""), offer_data.get("type", "offer"))
            
            # Get the answer
            answer = connection.get_answer()
            
            # Create transport
            transport = SmallWebRTCTransport(connection, transport_params_obj)
            
            # Create runner args
            from types import SimpleNamespace
            runner_args = SimpleNamespace(
                transport="webrtc",
                log_level="info",
                pipeline_idle_timeout_secs=30,
                handle_sigint=False
            )
            
            # Start the bot pipeline in the background with custom system prompt  
            asyncio.create_task(run_enhanced_bot(transport, runner_args, device_id))
            
            logger.info(f"WebRTC connection established for device: {device_id}")
            return answer
                
        except Exception as e:
            logger.error(f"Error handling WebRTC offer: {e}")
            raise HTTPException(status_code=500, detail=f"WebRTC offer failed: {str(e)}")

    # Client endpoint for WebRTC connection
    @app.get("/client",
             summary="WebRTC client page",
             description="WebRTC client interface for testing")
    async def webrtc_client():
        """WebRTC client interface"""
        return {
            "message": "WebRTC client endpoint",
            "instructions": "Use this endpoint to connect your ESP32 device",
            "offer_endpoint": "/api/offer"
        }
    
    return app

async def run_enhanced_bot(transport: BaseTransport, runner_args: RunnerArguments, device_id: str = None):
    """Enhanced bot with dynamic system prompts based on user progress"""
    logger.info(f"Starting enhanced bot for device: {device_id}")

    stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_API_KEY"))

    tts = ElevenLabsTTSService(
        api_key=os.getenv("ELEVENLABS_API_KEY"),
        voice_id="pNInz6obpgDQGcFmaJgB"  # ElevenLabs: Adam voice (free)
    )

    llm = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY"))

    # Get user-specific system prompt based on their progress
    system_prompt = await get_system_prompt_for_user(device_id) if device_id else get_default_system_prompt()
    
    logger.info(f"Using system prompt for device {device_id}: {system_prompt[:100]}...")

    # Initialize with custom system prompt
    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
    ]

    context = OpenAILLMContext(messages)
    context_aggregator = llm.create_context_aggregator(context)

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
        logger.info(f"Client connected - Device ID: {device_id}")
        
        if device_id:
            try:
                # Update user's last active time
                user_service = get_user_service()
                try:
                    user_response = await user_service.get_user(device_id)
                    logger.info(f"User {device_id} reconnected - Season {user_response.season}, Episode {user_response.episode}")
                    
                    # Update last active time
                    await user_service.update_last_active(device_id)
                    
                except UserNotFoundException:
                    logger.warning(f"Connected device {device_id} not registered")
                
            except Exception as e:
                logger.error(f"Failed to update user info: {e}")
        
        # Kick off the conversation with introduction
        messages.append({"role": "system", "content": "Please introduce yourself to the user."})
        await task.queue_frames([context_aggregator.user().get_context_frame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info(f"Client disconnected - Device ID: {device_id}")
        await task.cancel()

    runner = PipelineRunner(handle_sigint=runner_args.handle_sigint)
    await runner.run(task)

# Create the enhanced app
app = create_enhanced_app()

def main():
    parser = argparse.ArgumentParser(description="Enhanced Pipecat Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=7860, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--log-level", default="info", help="Log level")
    
    args = parser.parse_args()
    
    print(f"🚀 Starting Enhanced Pipecat Server...")
    print(f"   Host: {args.host}")
    print(f"   Port: {args.port}")
    print(f"   Log Level: {args.log_level}")
    print(f"   Reload: {args.reload}")
    
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

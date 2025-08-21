#
# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

import os
import asyncio
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
from pipecat.runner.utils import create_transport
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
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

# We store functions so objects (e.g. SileroVADAnalyzer) don't get
# instantiated. The function will be called when the desired transport gets
# selected.
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


async def get_system_prompt_for_user(device_id: str) -> str:
    """
    Get system prompt for user based on their current episode
    
    Args:
        device_id: User's device ID
        
    Returns:
        str: System prompt content
    """
    try:
        user_service = get_user_service()
        prompt_service = get_prompt_service()
        
        # Get user's current progress
        user_response = await user_service.get_user(device_id)
        season = user_response.season
        episode = user_response.episode
        
        # Get system prompt for current episode
        prompt_content = await prompt_service.get_prompt_content(season, episode)
        
        logger.info(f"Retrieved system prompt for {device_id}: Season {season}, Episode {episode}")
        return prompt_content
        
    except UserNotFoundException:
        logger.warning(f"User {device_id} not found, using default prompt")
        return get_default_system_prompt()
    except Exception as e:
        logger.error(f"Failed to get system prompt for {device_id}: {e}")
        return get_default_system_prompt()


def get_default_system_prompt() -> str:
    """Get default system prompt when user-specific prompt is not available"""
    return """You are a helpful LLM in a WebRTC call. Your goal is to demonstrate your capabilities in a succinct way. Your output will be converted to audio so don't include special characters in your answers. Respond to what the user said in a creative and helpful way."""


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    logger.info(f"Starting enhanced bot")

    stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_API_KEY"))

    tts = ElevenLabsTTSService(
        api_key=os.getenv("ELEVENLABS_API_KEY"),
        voice_id="pNInz6obpgDQGcFmaJgB"  # ElevenLabs: Adam voice (free)
    )

    llm = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY"))

    # Initialize with default message - will be updated when client connects
    messages = [
        {
            "role": "system",
            "content": get_default_system_prompt(),
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
        logger.info(f"Client connected")
        
        # Try to get device ID from client info (this is a simplified approach)
        # In a real implementation, you'd get this from authentication or query params
        device_id = getattr(client, 'device_id', None)
        
        if device_id:
            try:
                # Get user-specific system prompt
                user_prompt = await get_system_prompt_for_user(device_id)
                
                # Update the system message
                messages[0]["content"] = user_prompt
                
                # Update user's last active time
                user_service = get_user_service()
                try:
                    user_response = await user_service.get_user(device_id)
                    logger.info(f"User {device_id} reconnected - Season {user_response.season}, Episode {user_response.episode}")
                except UserNotFoundException:
                    logger.warning(f"Connected device {device_id} not registered")
                
            except Exception as e:
                logger.error(f"Failed to setup user-specific prompt: {e}")
        
        # Kick off the conversation.
        messages.append({"role": "system", "content": "Please introduce yourself to the user."})
        await task.queue_frames([context_aggregator.user().get_context_frame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info(f"Client disconnected")
        await task.cancel()

    runner = PipelineRunner(handle_sigint=runner_args.handle_sigint)

    await runner.run(task)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    
    # Startup
    logger.info("🚀 Starting Enhanced Pipecat Server...")
    
    try:
        # Validate configuration
        if not validate_settings():
            raise Exception("Configuration validation failed")
        
        # Initialize logging
        settings = get_settings()
        setup_logging(settings.log_level)
        logger.info("✅ Logging initialized")
        
        # Initialize services
        firebase_service = get_firebase_service()
        logger.info("✅ Firebase service initialized")
        
        user_service = get_user_service()
        logger.info("✅ User service initialized")
        
        prompt_service = get_prompt_service()
        logger.info("✅ Prompt service initialized")
        
        logger.info("🎯 Enhanced server startup completed successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    finally:
        # Shutdown
        logger.info("🛑 Shutting down Enhanced Pipecat Server...")
        logger.info("✅ Server shutdown completed")


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
              description="Handle WebRTC offer from ESP32 devices")
    async def handle_webrtc_offer(offer_data: dict):
        """Handle WebRTC offer from ESP32 devices"""
        try:
            logger.info(f"Received WebRTC offer from ESP32: {offer_data}")
            
            # For now, return a basic WebRTC answer
            # This endpoint needs to be integrated with the actual pipecat WebRTC transport
            # when a client connects via WebRTC
            
            answer = {
                "type": "answer",
                "sdp": offer_data.get("sdp", ""),
                "status": "accepted",
                "message": "WebRTC offer received and processed"
            }
            
            logger.info(f"Returning WebRTC answer: {answer}")
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


# Create the enhanced app
app = create_enhanced_app()


async def bot(runner_args: RunnerArguments):
    """Main bot entry point compatible with Pipecat Cloud."""
    transport = await create_transport(runner_args, transport_params)
    await run_bot(transport, runner_args)


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()

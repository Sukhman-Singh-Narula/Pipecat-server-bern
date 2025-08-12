#!/usr/bin/env python3
"""
Simple ESP32 WebRTC Conversational AI Server

A minimal FastAPI server for WebRTC audio conversation with AI.
"""

import argparse
import asyncio
import os
from contextlib import asynccontextmanager
from typing import Dict

import uvicorn
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from loguru import logger
from pydantic import BaseModel

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.transports.base_transport import TransportParams
from pipecat.transports.network.small_webrtc import SmallWebRTCTransport
from pipecat.transports.network.webrtc_connection import IceServer, SmallWebRTCConnection

# Load environment variables
load_dotenv(override=True)

# FastAPI app instance
app = FastAPI(title="ESP32 WebRTC AI Assistant")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store WebRTC connections
pcs_map: Dict[str, SmallWebRTCConnection] = {}

# ICE servers for WebRTC connection
ice_servers = [
    IceServer(urls="stun:stun.l.google.com:19302"),
]

# Pydantic models
class WebRTCOfferRequest(BaseModel):
    sdp: str
    type: str = "offer"
    restart_pc: bool = False


async def create_conversation_pipeline(
    webrtc_connection: SmallWebRTCConnection,
    device_id: str,
    config: ConversationConfig
) -> PipelineTask:
    """Create a conversational AI pipeline for the device."""
    
    logger.info(f"Creating conversation pipeline for device: {device_id}")
    
    # Create transport using WebRTC connection
    transport = SmallWebRTCTransport(
        webrtc_connection=webrtc_connection,
        params=TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer() if config.interrupt_enabled else None,
        ),
    )

    # Initialize services
    try:
        # Speech-to-Text service
        stt = DeepgramSTTService(
            api_key=os.getenv("DEEPGRAM_API_KEY"),
            model="nova-2",
            language=config.language,
        )

        # Text-to-Speech service
        voice_id = config.voice_id or VOICE_OPTIONS["british_lady"]
        tts = CartesiaTTSService(
            api_key=os.getenv("CARTESIA_API_KEY"),
            voice_id=voice_id,
        )

        # Language Model service
        llm = OpenAILLMService(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini",  # Use cost-effective model
        )

    except Exception as e:
        logger.error(f"Failed to initialize AI services: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize AI services. Check API keys."
        )

    # Setup conversation context
    system_prompt = config.system_prompt or DEFAULT_SYSTEM_PROMPT
    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
    ]

    context = OpenAILLMContext(messages)
    context_aggregator = llm.create_context_aggregator(context)

    # Create pipeline
    pipeline = Pipeline([
        transport.input(),           # Audio input from ESP32
        stt,                        # Speech-to-Text
        context_aggregator.user(),  # User message processing
        llm,                        # Language model
        tts,                        # Text-to-Speech
        transport.output(),         # Audio output to ESP32
        context_aggregator.assistant(),  # Assistant message processing
    ])

    # Create pipeline task
    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
        idle_timeout_secs=300,  # 5 minutes timeout
    )

    # Event handlers
    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info(f"ESP32 device {device_id} connected")
        device_sessions[device_id] = {
            "connected_at": asyncio.get_event_loop().time(),
            "status": "connected"
        }
        # Welcome message
        welcome_msg = "Hello! I'm your AI assistant. How can I help you today?"
        messages.append({"role": "assistant", "content": welcome_msg})
        await task.queue_frames([context_aggregator.user().get_context_frame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info(f"ESP32 device {device_id} disconnected")
        if device_id in device_sessions:
            device_sessions[device_id]["status"] = "disconnected"
        await task.cancel()

    return task


async def run_device_conversation(
    webrtc_connection: SmallWebRTCConnection,
    device_id: str,
    config: ConversationConfig
):
    """Run conversation pipeline for a specific device."""
    try:
        task = await create_conversation_pipeline(webrtc_connection, device_id, config)
        
        runner = PipelineRunner(handle_sigint=False)
        await runner.run(task)
        
    except Exception as e:
        logger.error(f"Error in conversation pipeline for device {device_id}: {e}")
        # Clean up connection
        if device_id in device_connections:
            await device_connections[device_id].disconnect()
            del device_connections[device_id]


# API Routes

@app.get("/", include_in_schema=False)
async def root_redirect():
    """Redirect root to API documentation."""
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "ESP32 WebRTC AI Assistant",
        "active_devices": len(device_connections),
        "environment_check": {
            "openai_api_key": bool(os.getenv("OPENAI_API_KEY")),
            "deepgram_api_key": bool(os.getenv("DEEPGRAM_API_KEY")),
            "cartesia_api_key": bool(os.getenv("CARTESIA_API_KEY")),
        }
    }


@app.post("/api/device/register")
async def register_device(request: DeviceRegistrationRequest):
    """Register a new ESP32 device."""
    logger.info(f"Registering device: {request.device_id}")
    
    device_sessions[request.device_id] = {
        "device_name": request.device_name or f"ESP32-{request.device_id[:8]}",
        "device_type": request.device_type,
        "capabilities": request.capabilities or {},
        "registered_at": asyncio.get_event_loop().time(),
        "status": "registered"
    }
    
    return {
        "success": True,
        "device_id": request.device_id,
        "message": "Device registered successfully"
    }


@app.post("/api/webrtc/offer")
async def handle_webrtc_offer(request: WebRTCOfferRequest, background_tasks: BackgroundTasks):
    """Handle WebRTC offer from ESP32 device."""
    device_id = request.device_id
    logger.info(f"Received WebRTC offer from device: {device_id}")
    
    try:
        # Check if connection already exists
        if device_id in device_connections and not request.restart_pc:
            # Renegotiate existing connection
            connection = device_connections[device_id]
            logger.info(f"Renegotiating existing connection for device: {device_id}")
            await connection.renegotiate(
                sdp=request.sdp,
                type=request.type,
                restart_pc=request.restart_pc,
            )
        else:
            # Create new connection
            connection = SmallWebRTCConnection(ice_servers)
            await connection.initialize(sdp=request.sdp, type=request.type)
            
            # Setup disconnect handler
            @connection.event_handler("closed")
            async def handle_disconnected(webrtc_connection: SmallWebRTCConnection):
                logger.info(f"Cleaning up connection for device: {device_id}")
                device_connections.pop(device_id, None)
                if device_id in device_sessions:
                    device_sessions[device_id]["status"] = "disconnected"
            
            # Store connection
            device_connections[device_id] = connection
            
            # Start conversation pipeline in background
            config = ConversationConfig()  # Use default config
            background_tasks.add_task(run_device_conversation, connection, device_id, config)
        
        # Get answer SDP
        answer = device_connections[device_id].get_answer()
        logger.info(f"Sending WebRTC answer to device: {device_id}")
        
        return answer
        
    except Exception as e:
        logger.error(f"Error handling WebRTC offer from device {device_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to establish WebRTC connection: {str(e)}"
        )


@app.post("/api/device/{device_id}/config")
async def update_device_config(device_id: str, config: ConversationConfig):
    """Update conversation configuration for a specific device."""
    if device_id not in device_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Store config for device (implement persistent storage if needed)
    device_sessions[device_id]["config"] = config.dict()
    
    return {
        "success": True,
        "device_id": device_id,
        "message": "Configuration updated successfully"
    }


@app.get("/api/devices")
async def list_devices():
    """List all registered devices and their status."""
    devices = []
    for device_id, session in device_sessions.items():
        devices.append({
            "device_id": device_id,
            "device_name": session.get("device_name", f"ESP32-{device_id[:8]}"),
            "status": session.get("status", "unknown"),
            "connected": device_id in device_connections,
            "registered_at": session.get("registered_at"),
        })
    
    return {
        "devices": devices,
        "total_devices": len(devices),
        "active_connections": len(device_connections)
    }


@app.get("/api/device/{device_id}/status")
async def get_device_status(device_id: str):
    """Get status of a specific device."""
    if device_id not in device_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    session = device_sessions[device_id]
    return {
        "device_id": device_id,
        "device_name": session.get("device_name"),
        "status": session.get("status"),
        "connected": device_id in device_connections,
        "config": session.get("config", {}),
        "registered_at": session.get("registered_at"),
        "connected_at": session.get("connected_at"),
    }


@app.delete("/api/device/{device_id}")
async def disconnect_device(device_id: str):
    """Disconnect and unregister a device."""
    if device_id in device_connections:
        await device_connections[device_id].disconnect()
        del device_connections[device_id]
    
    if device_id in device_sessions:
        del device_sessions[device_id]
    
    return {
        "success": True,
        "device_id": device_id,
        "message": "Device disconnected and unregistered"
    }


@app.get("/api/voices")
async def list_available_voices():
    """List available TTS voices."""
    return {
        "voices": [
            {"id": voice_id, "name": name.replace("_", " ").title()}
            for name, voice_id in VOICE_OPTIONS.items()
        ]
    }


# Lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info("Starting ESP32 WebRTC AI Assistant Server")
    
    # Validate environment variables
    required_env_vars = ["OPENAI_API_KEY", "DEEPGRAM_API_KEY", "CARTESIA_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {missing_vars}")
        logger.warning("Some features may not work properly")
    
    yield  # Run application
    
    # Cleanup on shutdown
    logger.info("Shutting down ESP32 WebRTC AI Assistant Server")
    cleanup_tasks = [conn.disconnect() for conn in device_connections.values()]
    if cleanup_tasks:
        await asyncio.gather(*cleanup_tasks, return_exceptions=True)
    device_connections.clear()
    device_sessions.clear()


app.router.lifespan_context = lifespan


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ESP32 WebRTC AI Assistant Server")
    parser.add_argument(
        "--host", 
        default="0.0.0.0", 
        help="Host for HTTP server (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port for HTTP server (default: 8000)"
    )
    parser.add_argument(
        "--reload", 
        action="store_true", 
        help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--log-level", 
        default="info", 
        choices=["debug", "info", "warning", "error"],
        help="Log level (default: info)"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        level=args.log_level.upper(),
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    logger.info(f"Starting server on {args.host}:{args.port}")
    
    uvicorn.run(
        "esp32_webrtc_server:app" if args.reload else app,
        host="64.",
        port=8000,
        reload=args.reload,
        log_level=args.log_level
    )

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
app = FastAPI(title="Simple WebRTC AI Assistant")

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


async def run_conversation(webrtc_connection: SmallWebRTCConnection):
    """Run AI conversation pipeline."""
    logger.info("Starting AI conversation")

    # Create transport using WebRTC connection
    transport = SmallWebRTCTransport(
        webrtc_connection=webrtc_connection,
        params=TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
        ),
    )

    # Initialize AI services
    stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_API_KEY"))
    
    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY"),
        voice_id="71a7ad14-091c-4e8e-a314-022ece01c121",  # British Reading Lady
    )

    llm = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY"))

    # Conversation context
    messages = [
        {
            "role": "system",
            "content": "You are a helpful AI assistant. Your responses will be converted to audio so speak naturally and keep responses concise. Respond to what the user said in a helpful way.",
        },
    ]

    context = OpenAILLMContext(messages)
    context_aggregator = llm.create_context_aggregator(context)

    # Create pipeline
    pipeline = Pipeline([
        transport.input(),           # Audio input
        stt,                        # Speech-to-Text
        context_aggregator.user(),  # User message processing
        llm,                        # Language model
        tts,                        # Text-to-Speech
        transport.output(),         # Audio output
        context_aggregator.assistant(),  # Assistant message processing
    ])

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
    )

    # Event handlers
    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Client connected")
        # Welcome message
        messages.append({"role": "system", "content": "Please introduce yourself to the user."})
        await task.queue_frames([context_aggregator.user().get_context_frame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Client disconnected")
        await task.cancel()

    runner = PipelineRunner(handle_sigint=False)
    await runner.run(task)


# API Routes
@app.post("/api/offer")
async def handle_webrtc_offer(request: WebRTCOfferRequest, background_tasks: BackgroundTasks):
    """Handle WebRTC offer and create AI conversation."""
    pc_id = request.dict().get("pc_id", None)
    
    logger.info(f"Received WebRTC offer")
    
    if pc_id and pc_id in pcs_map:
        # Renegotiate existing connection
        pipecat_connection = pcs_map[pc_id]
        logger.info(f"Reusing existing connection for pc_id: {pc_id}")
        await pipecat_connection.renegotiate(
            sdp=request.sdp,
            type=request.type,
            restart_pc=request.restart_pc,
        )
    else:
        # Create new connection
        pipecat_connection = SmallWebRTCConnection(ice_servers)
        await pipecat_connection.initialize(sdp=request.sdp, type=request.type)

        @pipecat_connection.event_handler("closed")
        async def handle_disconnected(webrtc_connection: SmallWebRTCConnection):
            logger.info(f"Discarding peer connection for pc_id: {webrtc_connection.pc_id}")
            pcs_map.pop(webrtc_connection.pc_id, None)

        # Start AI conversation in background
        background_tasks.add_task(run_conversation, pipecat_connection)

    answer = pipecat_connection.get_answer()
    # Store connection
    pcs_map[answer["pc_id"]] = pipecat_connection

    return answer


@app.get("/")
async def root():
    """Simple status endpoint."""
    return {
        "status": "running",
        "message": "Simple WebRTC AI Assistant Server",
        "active_connections": len(pcs_map)
    }


# Lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info("Starting Simple WebRTC AI Assistant Server")
    yield  # Run application
    
    # Cleanup on shutdown
    logger.info("Shutting down server")
    cleanup_tasks = [pc.disconnect() for pc in pcs_map.values()]
    if cleanup_tasks:
        await asyncio.gather(*cleanup_tasks, return_exceptions=True)
    pcs_map.clear()


app.router.lifespan_context = lifespan


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple WebRTC AI Assistant Server")
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
        "--log-level", 
        default="info", 
        choices=["debug", "info", "warning", "error"],
        help="Log level (default: info)"
    )
    
    args = parser.parse_args()
    
    logger.info(f"Starting server on {args.host}:{args.port}")
    
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level=args.log_level
    )

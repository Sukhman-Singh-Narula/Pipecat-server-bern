import os
import sys
import asyncio
from contextlib import asynccontextmanager
from typing import Dict

from dotenv import load_dotenv
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
from loguru import logger
from pipecat.transports.network.webrtc_connection import IceServer, SmallWebRTCConnection
from pipecat.transports.network.small_webrtc import SmallWebRTCTransport
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.services.gemini_multimodal_live import GeminiMultimodalLiveLLMService
from pipecat.transports.base_transport import TransportParams

load_dotenv(override=True)

app = FastAPI()

pcs_map: Dict[str, SmallWebRTCConnection] = {}

ice_servers = [
    IceServer(urls="stun:stun.l.google.com:19302"),
]

SYSTEM_INSTRUCTION = """
You are Gemini Chatbot, a friendly, helpful robot.\n\nYour goal is to demonstrate your capabilities in a succinct way.\n\nYour output will be converted to audio so don't include special characters in your answers.\n\nRespond to what the user said in a creative and helpful way. Keep your responses brief. One or two sentences at most.
"""

async def run_bot(webrtc_connection):
    logger.info(f"[run_bot] Initializing Pipecat transport for pc_id={webrtc_connection.pc_id}")
    pipecat_transport = SmallWebRTCTransport(
        webrtc_connection=webrtc_connection,
        params=TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
            audio_out_10ms_chunks=2,
        ),
    )

    llm = GeminiMultimodalLiveLLMService(
        api_key=os.getenv("GOOGLE_API_KEY"),
        voice_id="Puck",
        transcribe_user_audio=True,
        transcribe_model_audio=True,
        system_instruction=SYSTEM_INSTRUCTION,
    )

    context = OpenAILLMContext([
        {"role": "user", "content": "Start by greeting the user warmly and introducing yourself."},
    ])
    context_aggregator = llm.create_context_aggregator(context)

    pipeline = Pipeline([
        pipecat_transport.input(),
        context_aggregator.user(),
        llm,
        pipecat_transport.output(),
        context_aggregator.assistant(),
    ])

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
    )

    @pipecat_transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info(f"[on_client_connected] Client connected: {client}")
        await task.queue_frames([context_aggregator.user().get_context_frame()])

    @pipecat_transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info(f"[on_client_disconnected] Client disconnected: {client}")
        await task.cancel()

    runner = PipelineRunner(handle_sigint=False)
    logger.info(f"[run_bot] Starting pipeline runner for pc_id={webrtc_connection.pc_id}")
    await runner.run(task)
    logger.info(f"[run_bot] Pipeline runner finished for pc_id={webrtc_connection.pc_id}")

@app.post("/api/offer")
async def offer(request: dict, background_tasks: BackgroundTasks):
    pc_id = request.get("pc_id")
    logger.info(f"[offer] Received offer for pc_id={pc_id}")
    try:
        if pc_id and pc_id in pcs_map:
            pipecat_connection = pcs_map[pc_id]
            logger.info(f"[offer] Reusing existing connection for pc_id: {pc_id}")
            await pipecat_connection.renegotiate(sdp=request["sdp"], type=request["type"])
        else:
            pipecat_connection = SmallWebRTCConnection(ice_servers)
            await pipecat_connection.initialize(sdp=request["sdp"], type=request["type"])

            @pipecat_connection.event_handler("closed")
            async def handle_disconnected(webrtc_connection: SmallWebRTCConnection):
                logger.info(f"[handle_disconnected] Discarding peer connection for pc_id: {webrtc_connection.pc_id}")
                pcs_map.pop(webrtc_connection.pc_id, None)

            background_tasks.add_task(run_bot, pipecat_connection)

        answer = pipecat_connection.get_answer()
        pcs_map[answer["pc_id"]] = pipecat_connection
        logger.info(f"[offer] Returning answer for pc_id={answer['pc_id']}")
        return answer
    except Exception as e:
        logger.error(f"[offer] Error handling offer for pc_id={pc_id}: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/")
async def root():
    """Root endpoint - returns basic info about the ESP32 WebRTC server"""
    logger.info("[root] Root endpoint accessed")
    return {
        "message": "ESP32 WebRTC FastAPI Server",
        "version": "1.0.0",
        "endpoints": {
            "/api/offer": "POST - Send WebRTC offer to establish connection"
        }
    }

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("[lifespan] Shutting down, disconnecting all peer connections")
    yield
    coros = [pc.disconnect() for pc in pcs_map.values()]
    await asyncio.gather(*coros)
    pcs_map.clear()

if __name__ == "__main__":
    import argparse
    import uvicorn
    parser = argparse.ArgumentParser(description="ESP32 WebRTC FastAPI Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host for HTTP server (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=7860, help="Port for HTTP server (default: 7860)")
    parser.add_argument("--verbose", "-v", action="count")
    args = parser.parse_args()

    logger.remove(0)
    if args.verbose:
        logger.add(sys.stderr, level="TRACE")
    else:
        logger.add(sys.stderr, level="DEBUG")

    logger.info("[main] Starting ESP32 WebRTC FastAPI Server")
    uvicorn.run(app, host=args.host, port=args.port)

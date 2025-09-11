"""
Conversation API endpoints for managing conversation transcripts and summaries
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

from services.conversation_service import ConversationService
from services.firebase_service import get_firebase_service
from models.conversation import ConversationTranscript, ConversationSummary, ConversationMessage

# Initialize router
router = APIRouter(prefix="/conversations", tags=["Conversations"])

# Dependency to get services
def get_conversation_service():
    firebase_service = get_firebase_service()
    return ConversationService(firebase_service)

# Request/Response Models
class StartConversationRequest(BaseModel):
    user_email: EmailStr
    season: int
    episode: int

class AddMessageRequest(BaseModel):
    speaker: str
    content: str
    message_type: str = "text"

class FinishConversationRequest(BaseModel):
    completion_status: str = "completed"

class CreateSummaryRequest(BaseModel):
    session_summary: str = ""
    key_learnings: List[str] = []
    words_learned: List[str] = []
    topics_covered: List[str] = []
    performance_rating: int = 5
    engagement_level: str = "high"
    areas_for_improvement: List[str] = []
    next_recommendations: List[str] = []

class MessageResponse(BaseModel):
    speaker: str
    content: str
    message_type: str
    timestamp: datetime

class ConversationResponse(BaseModel):
    conversation_id: str
    user_email: str
    season: int
    episode: int
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: Optional[float]
    messages: List[MessageResponse]

class SummaryResponse(BaseModel):
    conversation_id: str
    user_email: str
    season: int
    episode: int
    session_summary: str
    key_learnings: List[str]
    words_learned: List[str]
    topics_covered: List[str]
    performance_rating: int
    engagement_level: str
    areas_for_improvement: List[str]
    next_recommendations: List[str]
    created_at: datetime

@router.post("/start")
async def start_conversation(
    request: StartConversationRequest,
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """Start a new conversation session"""
    try:
        conversation_id = await conversation_service.create_conversation(
            request.user_email, request.season, request.episode
        )
        return {"conversation_id": conversation_id, "message": "Conversation started successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{conversation_id}/messages")
async def add_message(
    conversation_id: str,
    request: AddMessageRequest,
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """Add a message to the conversation"""
    success = await conversation_service.add_message(
        conversation_id, request.speaker, request.content, request.message_type
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to add message")
    return {"message": "Message added successfully"}

@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """Get conversation transcript by ID"""
    conversation = await conversation_service.get_conversation_transcript(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Convert messages to response format
    messages = [
        MessageResponse(
            speaker=msg.speaker,
            content=msg.content,
            message_type=msg.message_type,
            timestamp=msg.timestamp
        )
        for msg in conversation.messages
    ]
    
    return ConversationResponse(
        conversation_id=conversation.conversation_id,
        user_email=conversation.user_email,
        season=conversation.season,
        episode=conversation.episode,
        status=conversation.status,
        start_time=conversation.start_time,
        end_time=conversation.end_time,
        duration_seconds=conversation.duration_seconds,
        messages=messages
    )

@router.put("/{conversation_id}/finish")
async def finish_conversation(
    conversation_id: str,
    request: FinishConversationRequest,
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """Mark conversation as finished"""
    success = await conversation_service.finish_conversation(conversation_id, request.completion_status)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to finish conversation")
    return {"message": "Conversation finished successfully"}

@router.post("/{conversation_id}/summary", response_model=SummaryResponse)
async def create_conversation_summary(
    conversation_id: str,
    request: CreateSummaryRequest,
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """Create a summary for a completed conversation"""
    try:
        summary = await conversation_service.create_conversation_summary(
            conversation_id, request.dict()
        )
        return SummaryResponse(**summary.to_dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{conversation_id}/summary", response_model=SummaryResponse)
async def get_conversation_summary(
    conversation_id: str,
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """Get conversation summary by conversation ID"""
    summary = await conversation_service.get_conversation_summary(conversation_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    return SummaryResponse(**summary.to_dict())

@router.get("/user/{user_email}", response_model=List[ConversationResponse])
async def get_user_conversations(
    user_email: str,
    limit: Optional[int] = Query(None, ge=1, le=100),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """Get all conversations for a user"""
    conversations = await conversation_service.get_user_conversations(user_email, limit)
    
    response_conversations = []
    for conversation in conversations:
        messages = [
            MessageResponse(
                speaker=msg.speaker,
                content=msg.content,
                message_type=msg.message_type,
                timestamp=msg.timestamp
            )
            for msg in conversation.messages
        ]
        
        response_conversations.append(ConversationResponse(
            conversation_id=conversation.conversation_id,
            user_email=conversation.user_email,
            season=conversation.season,
            episode=conversation.episode,
            status=conversation.status,
            start_time=conversation.start_time,
            end_time=conversation.end_time,
            duration_seconds=conversation.duration_seconds,
            messages=messages
        ))
    
    return response_conversations

@router.get("/user/{user_email}/summaries", response_model=List[SummaryResponse])
async def get_user_summaries(
    user_email: str,
    limit: Optional[int] = Query(None, ge=1, le=100),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """Get all conversation summaries for a user"""
    summaries = await conversation_service.get_user_summaries(user_email, limit)
    return [SummaryResponse(**summary.to_dict()) for summary in summaries]

@router.get("/episode/season/{season}/episode/{episode}", response_model=List[ConversationResponse])
async def get_episode_conversations(
    season: int,
    episode: int,
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """Get all conversations for a specific episode"""
    conversations = await conversation_service.get_episode_conversations(season, episode)
    
    response_conversations = []
    for conversation in conversations:
        messages = [
            MessageResponse(
                speaker=msg.speaker,
                content=msg.content,
                message_type=msg.message_type,
                timestamp=msg.timestamp
            )
            for msg in conversation.messages
        ]
        
        response_conversations.append(ConversationResponse(
            conversation_id=conversation.conversation_id,
            user_email=conversation.user_email,
            season=conversation.season,
            episode=conversation.episode,
            status=conversation.status,
            start_time=conversation.start_time,
            end_time=conversation.end_time,
            duration_seconds=conversation.duration_seconds,
            messages=messages
        ))
    
    return response_conversations

@router.get("/{conversation_id}/analytics")
async def get_conversation_analytics(
    conversation_id: str,
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """Get comprehensive analytics for a conversation"""
    analytics = await conversation_service.get_conversation_analytics(conversation_id)
    if not analytics:
        raise HTTPException(status_code=404, detail="Conversation not found or no analytics data")
    return analytics

@router.get("/user/{user_email}/progression")
async def get_user_learning_progression(
    user_email: str,
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """Get user's learning progression across all conversations"""
    progression = await conversation_service.get_user_learning_progression(user_email)
    if not progression:
        raise HTTPException(status_code=404, detail="No learning progression data found")
    return progression

@router.get("/user/{user_email}/search")
async def search_user_conversations(
    user_email: str,
    q: str = Query(..., min_length=2),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """Search user's conversations by content"""
    conversations = await conversation_service.search_conversations(user_email, q)
    
    response_conversations = []
    for conversation in conversations:
        messages = [
            MessageResponse(
                speaker=msg.speaker,
                content=msg.content,
                message_type=msg.message_type,
                timestamp=msg.timestamp
            )
            for msg in conversation.messages
        ]
        
        response_conversations.append(ConversationResponse(
            conversation_id=conversation.conversation_id,
            user_email=conversation.user_email,
            season=conversation.season,
            episode=conversation.episode,
            status=conversation.status,
            start_time=conversation.start_time,
            end_time=conversation.end_time,
            duration_seconds=conversation.duration_seconds,
            messages=messages
        ))
    
    return response_conversations

@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """Delete a conversation and its summary"""
    success = await conversation_service.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete conversation")
    return {"message": "Conversation deleted successfully"}

@router.get("/user/{user_email}/summary")
async def get_user_conversation_summary(
    user_email: str,
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """Get user conversation summary with key metrics"""
    progression = await conversation_service.get_user_learning_progression(user_email)
    if not progression:
        raise HTTPException(status_code=404, detail="No conversation data found")
    
    return {
        "user_email": user_email,
        "total_conversations": progression["learning_stats"]["total_sessions"],
        "completed_conversations": progression["learning_stats"]["completed_sessions"],
        "total_words_learned": progression["learning_stats"]["total_words_learned"],
        "total_topics_covered": progression["learning_stats"]["total_topics_covered"],
        "total_learning_hours": progression["performance"]["total_learning_time_hours"],
        "average_session_minutes": progression["performance"]["average_session_time_minutes"],
        "average_performance": progression["performance"]["average_rating"],
        "last_session": progression["recent_activity"]["last_session"],
        "recent_conversations": progression["recent_activity"]["recent_conversations"]
    }

@router.get("/stats/overview")
async def get_conversations_overview(
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """Get overview statistics for all conversations"""
    # This would require a more complex query to get all conversations
    # For now, we'll return a placeholder
    return {
        "message": "Overview statistics endpoint - requires implementation of get_all_conversations method"
    }

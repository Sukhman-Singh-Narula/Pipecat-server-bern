"""
Episode Prompt API endpoints for learning content management
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from services.episode_prompt_service import EpisodePromptService
from services.firebase_service import get_firebase_service
from models.episode_prompt import EpisodePrompt

# Initialize router
router = APIRouter(prefix="/episodes", tags=["Episode Prompts"])

# Dependency to get services
def get_episode_service():
    firebase_service = get_firebase_service()
    return EpisodePromptService(firebase_service)

# Request/Response Models
class CreateEpisodeRequest(BaseModel):
    season: int
    episode: int
    title: str
    system_prompt: str
    words_to_teach: List[str] = []
    topics_to_cover: List[str] = []
    difficulty_level: str = "intermediate"
    age_group: str = "general"
    learning_objectives: List[str] = []

class UpdateEpisodeRequest(BaseModel):
    title: Optional[str] = None
    system_prompt: Optional[str] = None
    words_to_teach: Optional[List[str]] = None
    topics_to_cover: Optional[List[str]] = None
    difficulty_level: Optional[str] = None
    age_group: Optional[str] = None
    learning_objectives: Optional[List[str]] = None

class RecordUsageRequest(BaseModel):
    user_email: str
    words_learned: List[str] = []
    topics_covered: List[str] = []
    session_time: float = 0.0
    completion_rating: int = 5

class EpisodeResponse(BaseModel):
    season: int
    episode: int
    title: str
    system_prompt: str
    words_to_teach: List[str]
    topics_to_cover: List[str]
    difficulty_level: str
    age_group: str
    learning_objectives: List[str]
    created_at: datetime
    updated_at: Optional[datetime]
    total_uses: int
    total_time_spent: float
    average_session_time: float
    average_rating: float

@router.post("/create", response_model=EpisodeResponse)
async def create_episode_prompt(
    request: CreateEpisodeRequest,
    episode_service: EpisodePromptService = Depends(get_episode_service)
):
    """Create a new episode prompt"""
    try:
        episode = await episode_service.create_episode_prompt(request.dict())
        return EpisodeResponse(**episode.to_dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/season/{season}/episode/{episode}", response_model=EpisodeResponse)
async def get_episode_prompt(
    season: int,
    episode: int,
    episode_service: EpisodePromptService = Depends(get_episode_service)
):
    """Get episode prompt by season and episode"""
    episode_prompt = await episode_service.get_episode_prompt(season, episode)
    if not episode_prompt:
        raise HTTPException(status_code=404, detail="Episode not found")
    return EpisodeResponse(**episode_prompt.to_dict())

@router.get("/season/{season}", response_model=List[EpisodeResponse])
async def get_season_episodes(
    season: int,
    episode_service: EpisodePromptService = Depends(get_episode_service)
):
    """Get all episodes for a specific season"""
    episodes = await episode_service.get_season_episodes(season)
    return [EpisodeResponse(**episode.to_dict()) for episode in episodes]

@router.get("/difficulty/{difficulty_level}", response_model=List[EpisodeResponse])
async def get_episodes_by_difficulty(
    difficulty_level: str,
    episode_service: EpisodePromptService = Depends(get_episode_service)
):
    """Get episodes by difficulty level"""
    episodes = await episode_service.get_episodes_by_difficulty(difficulty_level)
    return [EpisodeResponse(**episode.to_dict()) for episode in episodes]

@router.get("/age-group/{age_group}", response_model=List[EpisodeResponse])
async def get_episodes_by_age_group(
    age_group: str,
    episode_service: EpisodePromptService = Depends(get_episode_service)
):
    """Get episodes by age group"""
    episodes = await episode_service.get_episodes_by_age_group(age_group)
    return [EpisodeResponse(**episode.to_dict()) for episode in episodes]

@router.put("/season/{season}/episode/{episode}")
async def update_episode_prompt(
    season: int,
    episode: int,
    request: UpdateEpisodeRequest,
    episode_service: EpisodePromptService = Depends(get_episode_service)
):
    """Update episode prompt"""
    # Filter out None values
    updates = {k: v for k, v in request.dict().items() if v is not None}
    
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    success = await episode_service.update_episode_prompt(season, episode, updates)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update episode")
    return {"message": "Episode updated successfully"}

@router.post("/season/{season}/episode/{episode}/usage")
async def record_episode_usage(
    season: int,
    episode: int,
    request: RecordUsageRequest,
    episode_service: EpisodePromptService = Depends(get_episode_service)
):
    """Record usage of an episode prompt"""
    success = await episode_service.record_usage(season, episode, request.user_email, request.dict())
    if not success:
        raise HTTPException(status_code=400, detail="Failed to record usage")
    return {"message": "Usage recorded successfully"}

@router.get("/season/{season}/episode/{episode}/analytics")
async def get_episode_analytics(
    season: int,
    episode: int,
    episode_service: EpisodePromptService = Depends(get_episode_service)
):
    """Get comprehensive episode analytics"""
    analytics = await episode_service.get_episode_analytics(season, episode)
    if not analytics:
        raise HTTPException(status_code=404, detail="Episode not found or no analytics data")
    return analytics

@router.get("/", response_model=List[EpisodeResponse])
async def get_all_episodes(
    episode_service: EpisodePromptService = Depends(get_episode_service)
):
    """Get all episode prompts"""
    episodes = await episode_service.get_all_episodes()
    return [EpisodeResponse(**episode.to_dict()) for episode in episodes]

@router.get("/popular", response_model=List[EpisodeResponse])
async def get_popular_episodes(
    limit: int = Query(10, ge=1, le=50),
    episode_service: EpisodePromptService = Depends(get_episode_service)
):
    """Get most popular episodes by usage"""
    episodes = await episode_service.get_popular_episodes(limit)
    return [EpisodeResponse(**episode.to_dict()) for episode in episodes]

@router.get("/search", response_model=List[EpisodeResponse])
async def search_episodes(
    q: str = Query(..., min_length=2),
    episode_service: EpisodePromptService = Depends(get_episode_service)
):
    """Search episodes by title, words, or topics"""
    episodes = await episode_service.search_episodes(q)
    return [EpisodeResponse(**episode.to_dict()) for episode in episodes]

@router.delete("/season/{season}/episode/{episode}")
async def delete_episode_prompt(
    season: int,
    episode: int,
    episode_service: EpisodePromptService = Depends(get_episode_service)
):
    """Delete an episode prompt"""
    success = await episode_service.delete_episode_prompt(season, episode)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete episode")
    return {"message": "Episode deleted successfully"}

@router.get("/season/{season}/episode/{episode}/summary")
async def get_episode_summary(
    season: int,
    episode: int,
    episode_service: EpisodePromptService = Depends(get_episode_service)
):
    """Get episode summary with key metrics"""
    episode_prompt = await episode_service.get_episode_prompt(season, episode)
    if not episode_prompt:
        raise HTTPException(status_code=404, detail="Episode not found")
    
    return {
        "episode_id": f"S{season}E{episode}",
        "title": episode_prompt.title,
        "difficulty_level": episode_prompt.difficulty_level,
        "age_group": episode_prompt.age_group,
        "words_count": len(episode_prompt.words_to_teach),
        "topics_count": len(episode_prompt.topics_to_cover),
        "objectives_count": len(episode_prompt.learning_objectives),
        "total_uses": episode_prompt.total_uses,
        "unique_users": len(episode_prompt.users_completed),
        "average_session_time_minutes": round(episode_prompt.average_session_time / 60, 2),
        "average_rating": round(episode_prompt.average_rating, 2),
        "words_taught_count": len(episode_prompt.words_taught),
        "topics_taught_count": len(episode_prompt.topics_taught),
        "created_at": episode_prompt.created_at,
        "last_used": episode_prompt.last_used
    }

@router.get("/stats/overview")
async def get_episodes_overview(
    episode_service: EpisodePromptService = Depends(get_episode_service)
):
    """Get overview statistics for all episodes"""
    episodes = await episode_service.get_all_episodes()
    
    if not episodes:
        return {
            "total_episodes": 0,
            "total_seasons": 0,
            "total_uses": 0,
            "total_unique_users": 0
        }
    
    total_episodes = len(episodes)
    total_seasons = len(set(ep.season for ep in episodes))
    total_uses = sum(ep.total_uses for ep in episodes)
    
    # Count unique users across all episodes
    all_users = set()
    for episode in episodes:
        all_users.update(episode.users_completed)
    
    difficulty_stats = {}
    age_group_stats = {}
    
    for episode in episodes:
        # Count by difficulty
        diff = episode.difficulty_level
        if diff not in difficulty_stats:
            difficulty_stats[diff] = 0
        difficulty_stats[diff] += 1
        
        # Count by age group
        age = episode.age_group
        if age not in age_group_stats:
            age_group_stats[age] = 0
        age_group_stats[age] += 1
    
    return {
        "total_episodes": total_episodes,
        "total_seasons": total_seasons,
        "total_uses": total_uses,
        "total_unique_users": len(all_users),
        "difficulty_distribution": difficulty_stats,
        "age_group_distribution": age_group_stats,
        "average_uses_per_episode": round(total_uses / total_episodes, 2) if total_episodes > 0 else 0
    }

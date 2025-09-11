"""
Episode Prompt Service for managing learning content
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
from loguru import logger

from models.episode_prompt import EpisodePrompt
from services.firebase_service import FirebaseService

class EpisodePromptService:
    """Service for managing episode prompts and learning content"""
    
    def __init__(self, firebase_service: FirebaseService):
        self.firebase = firebase_service
        self.collection_name = "episode_prompts"
    
    async def create_episode_prompt(self, prompt_data: Dict[str, Any]) -> EpisodePrompt:
        """Create a new episode prompt"""
        try:
            episode_prompt = EpisodePrompt(
                season=prompt_data["season"],
                episode=prompt_data["episode"],
                title=prompt_data["title"],
                system_prompt=prompt_data["system_prompt"],
                words_to_teach=prompt_data.get("words_to_teach", []),
                topics_to_cover=prompt_data.get("topics_to_cover", []),
                difficulty_level=prompt_data.get("difficulty_level", "intermediate"),
                age_group=prompt_data.get("age_group", "general"),
                learning_objectives=prompt_data.get("learning_objectives", [])
            )
            
            # Create document ID as "S{season}E{episode}"
            doc_id = f"S{episode_prompt.season}E{episode_prompt.episode}"
            
            await self.firebase.set_document(
                self.collection_name,
                doc_id,
                episode_prompt.to_dict()
            )
            
            logger.info(f"Created episode prompt: {doc_id}")
            return episode_prompt
            
        except Exception as e:
            logger.error(f"Error creating episode prompt: {e}")
            raise
    
    async def get_episode_prompt(self, season: int, episode: int) -> Optional[EpisodePrompt]:
        """Get episode prompt by season and episode"""
        try:
            doc_id = f"S{season}E{episode}"
            data = await self.firebase.get_document(self.collection_name, doc_id)
            if data:
                return EpisodePrompt.from_dict(data)
            return None
        except Exception as e:
            logger.error(f"Error getting episode prompt S{season}E{episode}: {e}")
            return None
    
    async def get_season_episodes(self, season: int) -> List[EpisodePrompt]:
        """Get all episodes for a specific season"""
        try:
            episodes_data = await self.firebase.query_collection(
                self.collection_name,
                [("season", "==", season)]
            )
            episodes = [EpisodePrompt.from_dict(data) for data in episodes_data]
            # Sort by episode number
            episodes.sort(key=lambda x: x.episode)
            return episodes
        except Exception as e:
            logger.error(f"Error getting season {season} episodes: {e}")
            return []
    
    async def get_episodes_by_difficulty(self, difficulty_level: str) -> List[EpisodePrompt]:
        """Get episodes by difficulty level"""
        try:
            episodes_data = await self.firebase.query_collection(
                self.collection_name,
                [("difficulty_level", "==", difficulty_level)]
            )
            episodes = [EpisodePrompt.from_dict(data) for data in episodes_data]
            # Sort by season and episode
            episodes.sort(key=lambda x: (x.season, x.episode))
            return episodes
        except Exception as e:
            logger.error(f"Error getting episodes by difficulty {difficulty_level}: {e}")
            return []
    
    async def get_episodes_by_age_group(self, age_group: str) -> List[EpisodePrompt]:
        """Get episodes by age group"""
        try:
            episodes_data = await self.firebase.query_collection(
                self.collection_name,
                [("age_group", "==", age_group)]
            )
            episodes = [EpisodePrompt.from_dict(data) for data in episodes_data]
            # Sort by season and episode
            episodes.sort(key=lambda x: (x.season, x.episode))
            return episodes
        except Exception as e:
            logger.error(f"Error getting episodes by age group {age_group}: {e}")
            return []
    
    async def update_episode_prompt(self, season: int, episode: int, updates: Dict[str, Any]) -> bool:
        """Update episode prompt"""
        try:
            doc_id = f"S{season}E{episode}"
            updates["updated_at"] = datetime.utcnow()
            
            await self.firebase.update_document(
                self.collection_name,
                doc_id,
                updates
            )
            
            logger.info(f"Updated episode prompt: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating episode prompt S{season}E{episode}: {e}")
            return False
    
    async def record_usage(self, season: int, episode: int, user_email: str, session_data: Dict[str, Any]) -> bool:
        """Record usage of an episode prompt"""
        try:
            episode_prompt = await self.get_episode_prompt(season, episode)
            if not episode_prompt:
                logger.warning(f"Episode S{season}E{episode} not found for usage recording")
                return False
            
            episode_prompt.record_usage(
                user_email,
                session_data.get("words_learned", []),
                session_data.get("topics_covered", []),
                session_data.get("session_time", 0.0),
                session_data.get("completion_rating", 5)
            )
            
            doc_id = f"S{season}E{episode}"
            await self.firebase.update_document(
                self.collection_name,
                doc_id,
                episode_prompt.to_dict()
            )
            
            logger.info(f"Recorded usage for {doc_id} by {user_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error recording usage for S{season}E{episode}: {e}")
            return False
    
    async def get_episode_analytics(self, season: int, episode: int) -> Dict[str, Any]:
        """Get comprehensive episode analytics"""
        try:
            episode_prompt = await self.get_episode_prompt(season, episode)
            if not episode_prompt:
                return {}
            
            return {
                "episode_info": {
                    "season": episode_prompt.season,
                    "episode": episode_prompt.episode,
                    "title": episode_prompt.title,
                    "difficulty_level": episode_prompt.difficulty_level,
                    "age_group": episode_prompt.age_group
                },
                "content": {
                    "words_to_teach": episode_prompt.words_to_teach,
                    "topics_to_cover": episode_prompt.topics_to_cover,
                    "learning_objectives": episode_prompt.learning_objectives
                },
                "usage_stats": {
                    "total_uses": episode_prompt.total_uses,
                    "unique_users": len(episode_prompt.users_completed),
                    "total_time_spent": round(episode_prompt.total_time_spent, 2),
                    "average_session_time": round(episode_prompt.average_session_time, 2),
                    "average_rating": round(episode_prompt.average_rating, 2)
                },
                "learning_impact": {
                    "words_taught": episode_prompt.words_taught,
                    "topics_taught": episode_prompt.topics_taught,
                    "total_words_count": len(episode_prompt.words_taught),
                    "total_topics_count": len(episode_prompt.topics_taught)
                },
                "timestamps": {
                    "created_at": episode_prompt.created_at,
                    "updated_at": episode_prompt.updated_at,
                    "last_used": episode_prompt.last_used
                }
            }
        except Exception as e:
            logger.error(f"Error getting episode analytics for S{season}E{episode}: {e}")
            return {}
    
    async def get_all_episodes(self) -> List[EpisodePrompt]:
        """Get all episode prompts"""
        try:
            episodes_data = await self.firebase.get_all_documents(self.collection_name)
            episodes = [EpisodePrompt.from_dict(data) for data in episodes_data]
            # Sort by season and episode
            episodes.sort(key=lambda x: (x.season, x.episode))
            return episodes
        except Exception as e:
            logger.error(f"Error getting all episodes: {e}")
            return []
    
    async def get_popular_episodes(self, limit: int = 10) -> List[EpisodePrompt]:
        """Get most popular episodes by usage"""
        try:
            episodes = await self.get_all_episodes()
            # Sort by total uses descending
            episodes.sort(key=lambda x: x.total_uses, reverse=True)
            return episodes[:limit]
        except Exception as e:
            logger.error(f"Error getting popular episodes: {e}")
            return []
    
    async def delete_episode_prompt(self, season: int, episode: int) -> bool:
        """Delete an episode prompt"""
        try:
            doc_id = f"S{season}E{episode}"
            await self.firebase.delete_document(self.collection_name, doc_id)
            logger.info(f"Deleted episode prompt: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting episode prompt S{season}E{episode}: {e}")
            return False
    
    async def search_episodes(self, search_term: str) -> List[EpisodePrompt]:
        """Search episodes by title, words, or topics"""
        try:
            # Get all episodes and filter locally (Firestore full-text search is limited)
            episodes = await self.get_all_episodes()
            search_term_lower = search_term.lower()
            
            matching_episodes = []
            for episode in episodes:
                # Search in title
                if search_term_lower in episode.title.lower():
                    matching_episodes.append(episode)
                    continue
                
                # Search in words to teach
                if any(search_term_lower in word.lower() for word in episode.words_to_teach):
                    matching_episodes.append(episode)
                    continue
                
                # Search in topics to cover
                if any(search_term_lower in topic.lower() for topic in episode.topics_to_cover):
                    matching_episodes.append(episode)
                    continue
                
                # Search in learning objectives
                if any(search_term_lower in obj.lower() for obj in episode.learning_objectives):
                    matching_episodes.append(episode)
                    continue
            
            return matching_episodes
        except Exception as e:
            logger.error(f"Error searching episodes with term '{search_term}': {e}")
            return []

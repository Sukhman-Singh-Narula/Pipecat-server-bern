"""
Enhanced User Service with comprehensive learning analytics
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from loguru import logger

from server.models.enhanced_user import EnhancedUser, UserStatus, Parent, Progress
from server.services.firebase_service import FirebaseService

class EnhancedUserService:
    """Enhanced user service with comprehensive learning tracking"""
    
    def __init__(self, firebase_service: FirebaseService):
        self.firebase = firebase_service
        self.collection_name = "enhanced_users"
    
    async def create_user(self, user_data: Dict[str, Any]) -> EnhancedUser:
        """Create a new enhanced user"""
        try:
            # Create parent object
            parent_data = user_data.get("parent", {})
            parent = Parent(
                name=parent_data.get("name", ""),
                age=parent_data.get("age", 0),
                email=parent_data.get("email", "")
            )
            
            # Create user object
            user = EnhancedUser(
                device_id=user_data["device_id"],
                name=user_data["name"],
                age=user_data["age"],
                email=user_data["email"],
                parent=parent
            )
            
            # Save to Firebase using email as document ID
            await self.firebase.set_document(
                self.collection_name,
                user.email,
                user.to_dict()
            )
            
            logger.info(f"Created enhanced user: {user.email}")
            return user
            
        except Exception as e:
            logger.error(f"Error creating enhanced user: {e}")
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[EnhancedUser]:
        """Get user by email (primary identifier)"""
        try:
            data = await self.firebase.get_document(self.collection_name, email)
            if data:
                return EnhancedUser.from_dict(data)
            return None
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None
    
    async def get_user_by_device_id(self, device_id: str) -> Optional[EnhancedUser]:
        """Get user by device ID"""
        try:
            users = await self.firebase.query_collection(
                self.collection_name,
                [("device_id", "==", device_id)]
            )
            if users:
                return EnhancedUser.from_dict(users[0])
            return None
        except Exception as e:
            logger.error(f"Error getting user by device_id {device_id}: {e}")
            return None
    
    async def update_user_progress(self, email: str, season: int, episode: int, completed: bool = False) -> bool:
        """Update user's learning progress"""
        try:
            user = await self.get_user_by_email(email)
            if not user:
                logger.warning(f"User {email} not found for progress update")
                return False
            
            user.update_progress(season, episode, completed)
            
            await self.firebase.update_document(
                self.collection_name,
                email,
                user.to_dict()
            )
            
            logger.info(f"Updated progress for {email}: S{season}E{episode}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user progress: {e}")
            return False
    
    async def add_learning_data(self, email: str, words: List[str], topics: List[str], session_time: float) -> bool:
        """Add learning data from a completed session"""
        try:
            user = await self.get_user_by_email(email)
            if not user:
                logger.warning(f"User {email} not found for learning data update")
                return False
            
            user.add_learning_data(words, topics, session_time)
            
            await self.firebase.update_document(
                self.collection_name,
                email,
                user.to_dict()
            )
            
            logger.info(f"Added learning data for {email}: {len(words)} words, {len(topics)} topics")
            return True
            
        except Exception as e:
            logger.error(f"Error adding learning data: {e}")
            return False
    
    async def update_last_active(self, email: str) -> bool:
        """Update user's last active timestamp"""
        try:
            await self.firebase.update_document(
                self.collection_name,
                email,
                {"last_active": datetime.utcnow()}
            )
            return True
        except Exception as e:
            logger.error(f"Error updating last active for {email}: {e}")
            return False
    
    async def get_all_users(self) -> List[EnhancedUser]:
        """Get all users"""
        try:
            users_data = await self.firebase.get_all_documents(self.collection_name)
            return [EnhancedUser.from_dict(data) for data in users_data]
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []
    
    async def get_users_by_status(self, status: UserStatus) -> List[EnhancedUser]:
        """Get users by status"""
        try:
            users_data = await self.firebase.query_collection(
                self.collection_name,
                [("status", "==", status.value)]
            )
            return [EnhancedUser.from_dict(data) for data in users_data]
        except Exception as e:
            logger.error(f"Error getting users by status {status}: {e}")
            return []
    
    async def get_user_analytics(self, email: str) -> Dict[str, Any]:
        """Get comprehensive user analytics"""
        try:
            user = await self.get_user_by_email(email)
            if not user:
                return {}
            
            total_episodes = user.progress.episodes_completed
            avg_session_time = user.total_time / max(total_episodes, 1)
            
            return {
                "user_info": {
                    "name": user.name,
                    "age": user.age,
                    "status": user.status.value
                },
                "progress": {
                    "current_season": user.progress.season,
                    "current_episode": user.progress.episode,
                    "episodes_completed": user.progress.episodes_completed
                },
                "learning_stats": {
                    "total_words_learned": len(user.words_learnt),
                    "total_topics_covered": len(user.topics_learnt),
                    "words_learned": user.words_learnt,
                    "topics_learned": user.topics_learnt
                },
                "time_analytics": {
                    "total_time_seconds": user.total_time,
                    "total_time_hours": round(user.total_time / 3600, 2),
                    "average_session_time": round(avg_session_time, 2),
                    "created_at": user.created_at,
                    "last_active": user.last_active,
                    "last_completed_episode": user.last_completed_episode
                },
                "parent_info": {
                    "name": user.parent.name,
                    "age": user.parent.age,
                    "email": user.parent.email
                }
            }
        except Exception as e:
            logger.error(f"Error getting user analytics for {email}: {e}")
            return {}
    
    async def delete_user(self, email: str) -> bool:
        """Delete a user"""
        try:
            await self.firebase.delete_document(self.collection_name, email)
            logger.info(f"Deleted user: {email}")
            return True
        except Exception as e:
            logger.error(f"Error deleting user {email}: {e}")
            return False

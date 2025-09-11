"""
User service for managing user operations
"""
from datetime import datetime
from typing import Optional, List

from models.user import User, UserRegistrationRequest, UserResponse, SessionInfo
from services.firebase_service import get_firebase_service
from utils.exceptions import ValidationException, UserNotFoundException
from utils.validators import DeviceValidator, SecurityValidator
from utils.logger import LoggerMixin


class UserService(LoggerMixin):
    """Service for user management operations"""
    
    def __init__(self):
        super().__init__()
        self.firebase_service = get_firebase_service()
    
    async def register_user(self, user_data: UserRegistrationRequest) -> UserResponse:
        """
        Register a new user
        
        Args:
            user_data: User registration data
            
        Returns:
            UserResponse: Created user response
            
        Raises:
            ValidationException: If validation fails
            UserAlreadyExistsException: If user already exists
        """
        # Validate device ID
        if not DeviceValidator.validate_device_id(user_data.device_id):
            error_msg = DeviceValidator.get_device_validation_error(user_data.device_id)
            raise ValidationException(error_msg, "device_id", user_data.device_id)
        
        # Validate name
        is_valid, error_msg = SecurityValidator.validate_name(user_data.name)
        if not is_valid:
            raise ValidationException(error_msg, "name", user_data.name)
        
        # Validate age
        is_valid, error_msg = SecurityValidator.validate_age(user_data.age)
        if not is_valid:
            raise ValidationException(error_msg, "age", str(user_data.age))
        
        # Create user
        user = await self.firebase_service.create_user(
            device_id=user_data.device_id,
            name=user_data.name,
            age=user_data.age
        )
        
        return UserResponse.from_user(user)
    
    async def get_user(self, device_id: str) -> UserResponse:
        """
        Get user by device ID
        
        Args:
            device_id: Device ID to look up
            
        Returns:
            UserResponse: User response data
            
        Raises:
            ValidationException: If device ID is invalid
            UserNotFoundException: If user not found
        """
        # Validate device ID
        if not DeviceValidator.validate_device_id(device_id):
            error_msg = DeviceValidator.get_device_validation_error(device_id)
            raise ValidationException(error_msg, "device_id", device_id)
        
        user = await self.firebase_service.get_user(device_id)
        return UserResponse.from_user(user)
    
    async def update_user_progress(self, device_id: str, words_learnt: Optional[List[str]] = None, 
                                  topics_learnt: Optional[List[str]] = None) -> UserResponse:
        """
        Update user learning progress
        
        Args:
            device_id: Device ID
            words_learnt: New words learned
            topics_learnt: New topics learned
            
        Returns:
            UserResponse: Updated user response
        """
        # Get existing user
        user = await self.firebase_service.get_user(device_id)
        
        # Update progress
        if words_learnt:
            # Add new words (avoid duplicates)
            existing_words = set(user.progress.words_learnt)
            new_words = [word for word in words_learnt if word not in existing_words]
            user.progress.words_learnt.extend(new_words)
        
        if topics_learnt:
            # Add new topics (avoid duplicates)
            existing_topics = set(user.progress.topics_learnt)
            new_topics = [topic for topic in topics_learnt if topic not in existing_topics]
            user.progress.topics_learnt.extend(new_topics)
        
        # Save updated user
        updated_user = await self.firebase_service.update_user(user)
        return UserResponse.from_user(updated_user)
    
    async def advance_episode(self, device_id: str) -> UserResponse:
        """
        Advance user to next episode/season
        
        Args:
            device_id: Device ID
            
        Returns:
            UserResponse: Updated user response
        """
        # Get existing user
        user = await self.firebase_service.get_user(device_id)
        
        # Advance episode
        advanced_to_new_season = user.progress.advance_episode()
        user.last_completed_episode = datetime.now()
        
        if advanced_to_new_season:
            self.log_info(f"User {device_id} advanced to Season {user.progress.season}")
        else:
            self.log_info(f"User {device_id} advanced to Episode {user.progress.episode}")
        
        # Save updated user
        updated_user = await self.firebase_service.update_user(user)
        return UserResponse.from_user(updated_user)
    
    async def get_user_statistics(self, device_id: str) -> dict:
        """
        Get detailed user statistics
        
        Args:
            device_id: Device ID
            
        Returns:
            dict: User statistics
        """
        user = await self.firebase_service.get_user(device_id)
        
        # Calculate statistics
        total_words = len(user.progress.words_learnt)
        total_topics = len(user.progress.topics_learnt)
        total_hours = round(user.progress.total_time / 3600, 2)
        average_session_time = (user.progress.total_time / max(user.progress.episodes_completed, 1)) if user.progress.episodes_completed > 0 else 0
        
        return {
            "device_id": device_id,
            "learning_stats": {
                "total_words_learnt": total_words,
                "total_topics_learnt": total_topics,
                "episodes_completed": user.progress.episodes_completed,
                "current_season": user.progress.season,
                "current_episode": user.progress.episode
            },
            "time_stats": {
                "total_time_hours": total_hours,
                "average_session_minutes": round(average_session_time / 60, 2)
            },
            "account_info": {
                "created_at": user.created_at,
                "last_active": user.last_active,
                "status": user.status.value
            }
        }
    
    async def get_user_session_info(self, device_id: str, session_duration: float, 
                                   is_connected: bool) -> SessionInfo:
        """
        Get current session information
        
        Args:
            device_id: Device ID
            session_duration: Current session duration in seconds
            is_connected: Whether user is currently connected
            
        Returns:
            SessionInfo: Session information
        """
        user = await self.firebase_service.get_user(device_id)
        
        return SessionInfo(
            device_id=device_id,
            session_duration=session_duration,
            current_season=user.progress.season,
            current_episode=user.progress.episode,
            is_connected=is_connected,
            session_start_time=datetime.now()
        )
    
    async def delete_user(self, device_id: str) -> bool:
        """
        Soft delete user (set status to inactive)
        
        Args:
            device_id: Device ID
            
        Returns:
            bool: True if successful
        """
        user = await self.firebase_service.get_user(device_id)
        user.status = user.status.INACTIVE
        
        await self.firebase_service.update_user(user)
        self.log_info(f"User {device_id} marked as inactive")
        
        return True


# Global service instance
_user_service: Optional[UserService] = None


def get_user_service() -> UserService:
    """Get user service singleton"""
    global _user_service
    if _user_service is None:
        _user_service = UserService()
    return _user_service

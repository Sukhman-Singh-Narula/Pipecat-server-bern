"""
Firebase service for handling database operations
Includes in-memory fallback when Firebase is not available
"""
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List
import json
import os

from config.settings import get_settings
from models.user import User, UserProgress, UserStatus
from models.system_prompt import SystemPrompt, PromptType
from utils.exceptions import (
    FirebaseException, UserNotFoundException, UserAlreadyExistsException,
    SystemPromptNotFoundException
)
from utils.logger import LoggerMixin


class FirebaseService(LoggerMixin):
    """Service for Firebase Firestore operations with in-memory fallback"""
    
    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.db = None
        self.use_firebase = False
        
        # In-memory storage for when Firebase is not available
        self._users: Dict[str, Dict] = {}
        self._prompts: Dict[str, Dict] = {}
        
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK or use in-memory storage"""
        try:
            # Try to initialize Firebase if credentials exist
            if os.path.exists(self.settings.firebase_credentials_path):
                import firebase_admin
                from firebase_admin import credentials, firestore
                
                try:
                    firebase_admin.get_app()
                    self.log_info("Firebase already initialized")
                except ValueError:
                    cred = credentials.Certificate(self.settings.firebase_credentials_path)
                    firebase_admin.initialize_app(cred)
                    self.log_info("Firebase initialized successfully")
                
                self.db = firestore.client()
                self.use_firebase = True
                
            else:
                self.log_warning("Firebase credentials not found, using in-memory storage")
                self._load_local_data()
                
        except Exception as e:
            self.log_warning(f"Firebase initialization failed, using in-memory storage: {e}")
            self._load_local_data()
    
    def _load_local_data(self):
        """Load data from local files if they exist"""
        try:
            users_file = "local_users.json"
            prompts_file = "local_prompts.json"
            
            if os.path.exists(users_file):
                with open(users_file, 'r') as f:
                    self._users = json.load(f)
                self.log_info(f"Loaded {len(self._users)} users from local storage")
            
            if os.path.exists(prompts_file):
                with open(prompts_file, 'r') as f:
                    self._prompts = json.load(f)
                self.log_info(f"Loaded {len(self._prompts)} prompts from local storage")
                
        except Exception as e:
            self.log_warning(f"Failed to load local data: {e}")
    
    def _save_local_data(self):
        """Save data to local files"""
        try:
            with open("local_users.json", 'w') as f:
                json.dump(self._users, f, indent=2, default=str)
            
            with open("local_prompts.json", 'w') as f:
                json.dump(self._prompts, f, indent=2, default=str)
                
        except Exception as e:
            self.log_error(f"Failed to save local data: {e}")
    
    def _user_to_dict(self, user: User) -> Dict[str, Any]:
        """Convert User object to dictionary"""
        # Handle both enum and string status values
        status_value = user.status.value if hasattr(user.status, 'value') else user.status
        
        return {
            "device_id": user.device_id,
            "name": user.name,
            "age": user.age,
            "status": status_value,
            "progress": {
                "season": user.progress.season,
                "episode": user.progress.episode,
                "words_learnt": user.progress.words_learnt,
                "topics_learnt": user.progress.topics_learnt,
                "total_time": user.progress.total_time,
                "episodes_completed": user.progress.episodes_completed
            },
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_active": user.last_active.isoformat() if user.last_active else None,
            "last_completed_episode": user.last_completed_episode.isoformat() if user.last_completed_episode else None
        }
    
    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """Safely parse datetime from various formats"""
        if value is None:
            return None
        
        # If it's already a datetime object, return it
        if isinstance(value, datetime):
            return value
        
        # If it's a string, try to parse it
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                try:
                    # Try other common formats if fromisoformat fails
                    from dateutil.parser import parse
                    return parse(value)
                except:
                    self.logger.warning(f"Failed to parse datetime: {value}")
                    return None
        
        # For any other type (int timestamp, etc.), try to convert
        try:
            # Assume it's a timestamp if it's a number
            if isinstance(value, (int, float)):
                return datetime.fromtimestamp(value)
        except:
            pass
        
        self.logger.warning(f"Unable to parse datetime from: {value} (type: {type(value)})")
        return None
    
    def _dict_to_user(self, data: Dict[str, Any]) -> User:
        """Convert dictionary to User object"""
        progress_data = data.get("progress", {})
        progress = UserProgress(
            season=progress_data.get("season", 1),
            episode=progress_data.get("episode", 1),
            words_learnt=progress_data.get("words_learnt", []),
            topics_learnt=progress_data.get("topics_learnt", []),
            total_time=progress_data.get("total_time", 0.0),
            episodes_completed=progress_data.get("episodes_completed", 0)
        )
        
        return User(
            device_id=data["device_id"],
            name=data["name"],
            age=data["age"],
            status=UserStatus(data.get("status", "active")),
            progress=progress,
            created_at=self._parse_datetime(data.get("created_at")),
            last_active=self._parse_datetime(data.get("last_active")),
            last_completed_episode=self._parse_datetime(data.get("last_completed_episode"))
        )
    
    # User operations
    async def create_user(self, device_id: str, name: str, age: int) -> User:
        """Create a new user"""
        try:
            # Check if user already exists
            existing_user = await self.get_user(device_id, raise_if_not_found=False)
            if existing_user:
                raise UserAlreadyExistsException(device_id)
            
            # Create new user
            user = User(
                device_id=device_id,
                name=name,
                age=age,
                status=UserStatus.ACTIVE,
                progress=UserProgress(),
                created_at=datetime.now(),
                last_active=datetime.now()
            )
            
            if self.use_firebase:
                # Save to Firebase
                user_data = self._user_to_dict(user)
                await asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda: self.db.collection('users').document(device_id).set(user_data)
                )
            else:
                # Save to in-memory storage
                self._users[device_id] = self._user_to_dict(user)
                self._save_local_data()
            
            self.log_info(f"User created: {device_id}")
            return user
            
        except UserAlreadyExistsException:
            raise
        except Exception as e:
            self.log_error(f"Failed to create user {device_id}: {e}", exc_info=True)
            raise FirebaseException("create_user", str(e), "users", device_id)
    
    async def get_user(self, device_id: str, raise_if_not_found: bool = True) -> Optional[User]:
        """Retrieve user"""
        try:
            if self.use_firebase:
                doc_ref = self.db.collection('users').document(device_id)
                doc = await asyncio.get_event_loop().run_in_executor(None, doc_ref.get)
                
                if not doc.exists:
                    if raise_if_not_found:
                        raise UserNotFoundException(device_id)
                    return None
                
                user_data = doc.to_dict()
            else:
                # Get from in-memory storage
                user_data = self._users.get(device_id)
                if not user_data:
                    if raise_if_not_found:
                        raise UserNotFoundException(device_id)
                    return None
            
            return self._dict_to_user(user_data)
            
        except UserNotFoundException:
            raise
        except Exception as e:
            self.log_error(f"Failed to get user {device_id}: {e}", exc_info=True)
            raise FirebaseException("get_user", str(e), "users", device_id)
    
    async def update_user(self, user: User) -> User:
        """Update user data"""
        try:
            user.last_active = datetime.now()
            user_data = self._user_to_dict(user)
            
            if self.use_firebase:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.db.collection('users').document(user.device_id).set(user_data)
                )
            else:
                self._users[user.device_id] = user_data
                self._save_local_data()
            
            self.log_info(f"User updated: {user.device_id}")
            return user
            
        except Exception as e:
            self.log_error(f"Failed to update user {user.device_id}: {e}", exc_info=True)
            raise FirebaseException("update_user", str(e), "users", user.device_id)
    
    async def health_check(self) -> bool:
        """Check if the service is healthy"""
        try:
            if self.use_firebase:
                # Try a simple read operation
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.db.collection('users').limit(1).get()
                )
            return True
        except Exception:
            return False


# Global service instance
_firebase_service: Optional[FirebaseService] = None


def get_firebase_service() -> FirebaseService:
    """Get Firebase service singleton"""
    global _firebase_service
    if _firebase_service is None:
        _firebase_service = FirebaseService()
    return _firebase_service

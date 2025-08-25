"""
Enhanced User model with comprehensive learning data
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

class UserStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    TRIAL = "trial"

@dataclass
class Progress:
    """User's learning progress"""
    season: int = 1
    episode: int = 1
    episodes_completed: int = 0

@dataclass
class Parent:
    """Parent information"""
    name: str
    age: int
    email: str

@dataclass
class EnhancedUser:
    """Enhanced user model with comprehensive learning tracking"""
    
    # Basic Info
    device_id: str
    name: str
    age: int
    email: str  # Primary identifier
    
    # Parent Info
    parent: Parent
    
    # Progress Tracking
    progress: Progress = field(default_factory=Progress)
    
    # Learning Data
    words_learnt: List[str] = field(default_factory=list)
    topics_learnt: List[str] = field(default_factory=list)
    
    # Activity Tracking
    total_time: float = 0.0  # in seconds
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)
    last_completed_episode: Optional[datetime] = None
    
    # Status
    status: UserStatus = UserStatus.ACTIVE
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firebase storage"""
        return {
            "device_id": self.device_id,
            "name": self.name,
            "age": self.age,
            "email": self.email,
            "parent": {
                "name": self.parent.name,
                "age": self.parent.age,
                "email": self.parent.email
            },
            "progress": {
                "season": self.progress.season,
                "episode": self.progress.episode,
                "episodes_completed": self.progress.episodes_completed
            },
            "words_learnt": self.words_learnt,
            "topics_learnt": self.topics_learnt,
            "total_time": self.total_time,
            "created_at": self.created_at,
            "last_active": self.last_active,
            "last_completed_episode": self.last_completed_episode,
            "status": self.status.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EnhancedUser":
        """Create from dictionary (Firebase data)"""
        parent_data = data.get("parent", {})
        progress_data = data.get("progress", {})
        
        return cls(
            device_id=data["device_id"],
            name=data["name"],
            age=data["age"],
            email=data["email"],
            parent=Parent(
                name=parent_data.get("name", ""),
                age=parent_data.get("age", 0),
                email=parent_data.get("email", "")
            ),
            progress=Progress(
                season=progress_data.get("season", 1),
                episode=progress_data.get("episode", 1),
                episodes_completed=progress_data.get("episodes_completed", 0)
            ),
            words_learnt=data.get("words_learnt", []),
            topics_learnt=data.get("topics_learnt", []),
            total_time=data.get("total_time", 0.0),
            created_at=data.get("created_at", datetime.utcnow()),
            last_active=data.get("last_active", datetime.utcnow()),
            last_completed_episode=data.get("last_completed_episode"),
            status=UserStatus(data.get("status", "active"))
        )
    
    def update_progress(self, season: int, episode: int, completed: bool = False):
        """Update user's learning progress"""
        self.progress.season = season
        self.progress.episode = episode
        if completed:
            self.progress.episodes_completed += 1
            self.last_completed_episode = datetime.utcnow()
        self.last_active = datetime.utcnow()
    
    def add_learning_data(self, words: List[str], topics: List[str], session_time: float):
        """Add new learning data from a session"""
        # Add unique words and topics
        for word in words:
            if word not in self.words_learnt:
                self.words_learnt.append(word)
        
        for topic in topics:
            if topic not in self.topics_learnt:
                self.topics_learnt.append(topic)
        
        # Update time
        self.total_time += session_time
        self.last_active = datetime.utcnow()

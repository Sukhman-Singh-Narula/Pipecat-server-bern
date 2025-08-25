"""
Conversation and Transcription models
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

class MessageType(Enum):
    USER = "user"
    AI = "ai"
    SYSTEM = "system"

@dataclass
class ConversationMessage:
    """Individual message in a conversation"""
    speaker: str  # "user", "bot", "system"
    content: str
    message_type: str = "text"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "speaker": self.speaker,
            "content": self.content,
            "message_type": self.message_type,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationMessage":
        return cls(
            speaker=data["speaker"],
            content=data["content"],
            message_type=data.get("message_type", "text"),
            timestamp=data.get("timestamp", datetime.utcnow())
        )

@dataclass
class ConversationTranscript:
    """Complete conversation transcript"""
    
    # Session Info
    conversation_id: str
    user_email: str
    
    # Episode Info
    season: int
    episode: int
    
    # Conversation Data
    messages: List[ConversationMessage] = field(default_factory=list)
    
    # Session Metadata
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    status: str = "active"  # "active", "completed", "interrupted"
    
    def add_message(self, message: ConversationMessage) -> None:
        """Add a message to the conversation"""
        self.messages.append(message)
    
    def finish_conversation(self, completion_status: str = "completed") -> None:
        """Mark conversation as finished"""
        self.end_time = datetime.utcnow()
        self.status = completion_status
        if self.start_time:
            self.duration_seconds = (self.end_time - self.start_time).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firebase storage"""
        return {
            "conversation_id": self.conversation_id,
            "user_email": self.user_email,
            "season": self.season,
            "episode": self.episode,
            "messages": [msg.to_dict() for msg in self.messages],
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "status": self.status
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationTranscript":
        """Create from dictionary (Firebase data)"""
        # Parse datetime strings back to datetime objects
        start_time = data.get("start_time")
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time)
        elif start_time is None:
            start_time = datetime.utcnow()
            
        end_time = data.get("end_time")
        if isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time)
            
        return cls(
            conversation_id=data["conversation_id"],
            user_email=data["user_email"],
            season=data["season"],
            episode=data["episode"],
            messages=[ConversationMessage.from_dict(msg) for msg in data.get("messages", [])],
            start_time=start_time,
            end_time=end_time,
            duration_seconds=data.get("duration_seconds"),
            status=data.get("status", "active")
        )

@dataclass
class ConversationSummary:
    """Summary of a user's conversation session"""
    
    conversation_id: str
    user_email: str
    season: int
    episode: int
    session_summary: str
    key_learnings: List[str] = field(default_factory=list)
    words_learned: List[str] = field(default_factory=list)
    topics_covered: List[str] = field(default_factory=list)
    performance_rating: int = 5
    engagement_level: str = "high"
    areas_for_improvement: List[str] = field(default_factory=list)
    next_recommendations: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "user_email": self.user_email,
            "season": self.season,
            "episode": self.episode,
            "session_summary": self.session_summary,
            "key_learnings": self.key_learnings,
            "words_learned": self.words_learned,
            "topics_covered": self.topics_covered,
            "performance_rating": self.performance_rating,
            "engagement_level": self.engagement_level,
            "areas_for_improvement": self.areas_for_improvement,
            "next_recommendations": self.next_recommendations,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationSummary":
        # Parse datetime string back to datetime object
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.utcnow()
            
        return cls(
            conversation_id=data["conversation_id"],
            user_email=data["user_email"],
            season=data["season"],
            episode=data["episode"],
            session_summary=data.get("session_summary", ""),
            key_learnings=data.get("key_learnings", []),
            words_learned=data.get("words_learned", []),
            topics_covered=data.get("topics_covered", []),
            performance_rating=data.get("performance_rating", 5),
            engagement_level=data.get("engagement_level", "high"),
            areas_for_improvement=data.get("areas_for_improvement", []),
            next_recommendations=data.get("next_recommendations", []),
            created_at=created_at
        )

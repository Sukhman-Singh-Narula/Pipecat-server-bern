"""
Enhanced Episode Prompt model with learning analytics
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field

@dataclass
class EpisodePrompt:
    """Enhanced episode prompt with learning analytics"""
    
    # Episode Identification
    season: int
    episode: int
    
    # Prompt Content
    title: str
    system_prompt: str  # The actual system prompt content
    
    # Learning Content
    words_to_teach: List[str] = field(default_factory=list)
    topics_to_cover: List[str] = field(default_factory=list)
    learning_objectives: List[str] = field(default_factory=list)
    
    # Categorization
    difficulty_level: str = "intermediate"
    age_group: str = "general"
    
    # Analytics and Usage Tracking
    total_uses: int = 0
    users_completed: List[str] = field(default_factory=list)
    total_time_spent: float = 0.0  # Total time across all sessions
    ratings: List[int] = field(default_factory=list)
    
    # Words and topics actually taught (aggregated from usage)
    words_taught: List[str] = field(default_factory=list)
    topics_taught: List[str] = field(default_factory=list)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    @property
    def average_session_time(self) -> float:
        """Calculate average session time"""
        return self.total_time_spent / max(self.total_uses, 1)
    
    @property 
    def average_rating(self) -> float:
        """Calculate average rating"""
        return sum(self.ratings) / len(self.ratings) if self.ratings else 0.0
    
    def record_usage(self, user_email: str, words_learned: List[str], topics_covered: List[str], 
                     session_time: float, rating: int) -> None:
        """Record usage of this episode prompt"""
        self.total_uses += 1
        self.total_time_spent += session_time
        self.last_used = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        if user_email not in self.users_completed:
            self.users_completed.append(user_email)
        
        # Aggregate words and topics taught
        for word in words_learned:
            if word not in self.words_taught:
                self.words_taught.append(word)
        
        for topic in topics_covered:
            if topic not in self.topics_taught:
                self.topics_taught.append(topic)
        
        # Record rating
        self.ratings.append(rating)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firebase storage"""
        return {
            "season": self.season,
            "episode": self.episode,
            "title": self.title,
            "system_prompt": self.system_prompt,
            "words_to_teach": self.words_to_teach,
            "topics_to_cover": self.topics_to_cover,
            "learning_objectives": self.learning_objectives,
            "difficulty_level": self.difficulty_level,
            "age_group": self.age_group,
            "total_uses": self.total_uses,
            "users_completed": self.users_completed,
            "total_time_spent": self.total_time_spent,
            "ratings": self.ratings,
            "words_taught": self.words_taught,
            "topics_taught": self.topics_taught,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_used": self.last_used,
            "average_session_time": self.average_session_time,
            "average_rating": self.average_rating
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EpisodePrompt":
        """Create from dictionary (Firebase data)"""
        return cls(
            season=data["season"],
            episode=data["episode"],
            title=data["title"],
            system_prompt=data["system_prompt"],
            words_to_teach=data.get("words_to_teach", []),
            topics_to_cover=data.get("topics_to_cover", []),
            learning_objectives=data.get("learning_objectives", []),
            difficulty_level=data.get("difficulty_level", "intermediate"),
            age_group=data.get("age_group", "general"),
            total_uses=data.get("total_uses", 0),
            users_completed=data.get("users_completed", []),
            total_time_spent=data.get("total_time_spent", 0.0),
            ratings=data.get("ratings", []),
            words_taught=data.get("words_taught", []),
            topics_taught=data.get("topics_taught", []),
            created_at=data.get("created_at", datetime.utcnow()),
            updated_at=data.get("updated_at"),
            last_used=data.get("last_used")
        )
    
    def get_prompt_id(self) -> str:
        """Get unique prompt identifier"""
        return f"season_{self.season}_episode_{self.episode}"
    
    def increment_usage(self, session_time: float):
        """Update usage statistics"""
        self.times_played += 1
        self.total_time_played += session_time

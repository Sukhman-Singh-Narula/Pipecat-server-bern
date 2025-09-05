"""
System prompt related data models
"""
from pydantic import BaseModel, validator, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class PromptType(str, Enum):
    """Types of system prompts"""
    LEARNING = "learning"
    ASSESSMENT = "assessment"
    CONVERSATION = "conversation"
    REVIEW = "review"


class SystemPromptRequest(BaseModel):
    """Request model for uploading system prompts"""
    season: int = Field(..., ge=1, le=10, description="Season number")
    episode: int = Field(..., ge=1, le=7, description="Episode number")
    prompt: str = Field(..., min_length=10, max_length=5000, description="System prompt text")
    prompt_type: PromptType = Field(default=PromptType.LEARNING, description="Type of prompt")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('prompt')
    def validate_prompt(cls, v):
        if not v.strip():
            raise ValueError('Prompt cannot be empty or whitespace only')
        return v.strip()


class SystemPrompt(BaseModel):
    """Complete system prompt model"""
    season: int
    episode: int
    prompt: str
    prompt_type: PromptType
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    version: int = Field(default=1, description="Prompt version number")
    is_active: bool = Field(default=True, description="Whether prompt is active")
    
    @property
    def prompt_id(self) -> str:
        """Generate unique prompt identifier"""
        return f"season_{self.season}_episode_{self.episode}"
    
    class Config:
        use_enum_values = True


class SystemPromptResponse(BaseModel):
    """Response model for system prompt data"""
    season: int
    episode: int
    prompt: str  # Added the actual prompt content
    prompt_type: str
    prompt_length: int
    version: int
    is_active: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    metadata: Dict[str, Any]
    
    # Add convenience properties for backward compatibility
    @property
    def title(self) -> str:
        """Get title from metadata or generate default"""
        return self.metadata.get('title', f"Season {self.season}, Episode {self.episode}")
    
    @property
    def content(self) -> str:
        """Alias for prompt content"""
        return self.prompt
    
    @classmethod
    def from_system_prompt(cls, prompt: SystemPrompt) -> "SystemPromptResponse":
        """Create response from SystemPrompt model"""
        # Handle prompt_type - it might be a string or enum
        prompt_type_value = prompt.prompt_type
        if hasattr(prompt_type_value, 'value'):
            prompt_type_str = prompt_type_value.value
        else:
            prompt_type_str = str(prompt_type_value)
            
        return cls(
            season=prompt.season,
            episode=prompt.episode,
            prompt=prompt.prompt,  # Include the actual prompt content
            prompt_type=prompt_type_str,
            prompt_length=len(prompt.prompt),
            version=prompt.version,
            is_active=prompt.is_active,
            created_at=prompt.created_at,
            updated_at=prompt.updated_at,
            metadata=prompt.metadata
        )


class PromptValidationResult(BaseModel):
    """Result of prompt validation"""
    is_valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    
    def add_error(self, error: str):
        """Add validation error"""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """Add validation warning"""
        self.warnings.append(warning)
    
    def add_suggestion(self, suggestion: str):
        """Add improvement suggestion"""
        self.suggestions.append(suggestion)


class SeasonOverview(BaseModel):
    """Overview of a complete season"""
    season: int
    total_episodes: int
    completed_episodes: int
    available_prompt_types: list[str]
    last_updated: Optional[datetime]
    
    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage"""
        if self.total_episodes == 0:
            return 0.0
        return (self.completed_episodes / self.total_episodes) * 100

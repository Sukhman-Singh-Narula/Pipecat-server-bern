"""
System prompt service for managing prompts and episodes
"""
from datetime import datetime
from typing import Optional, List, Dict, Any

from models.system_prompt import (
    SystemPrompt, SystemPromptRequest, SystemPromptResponse, 
    PromptType, PromptValidationResult, SeasonOverview
)
from services.firebase_service import get_firebase_service
from utils.exceptions import ValidationException, SystemPromptNotFoundException
from utils.validators import PromptValidator
from utils.logger import LoggerMixin


class PromptService(LoggerMixin):
    """Service for system prompt management"""
    
    def __init__(self):
        super().__init__()
        self.firebase_service = get_firebase_service()
        
        # In-memory storage for prompts when Firebase is not available
        self._prompts: Dict[str, SystemPrompt] = {}
    
    def _get_prompt_key(self, season: int, episode: int) -> str:
        """Generate key for prompt storage"""
        return f"s{season}e{episode}"
    
    def clear_cache(self) -> None:
        """Clear the in-memory prompt cache"""
        self._prompts.clear()
        self.log_info("Prompt cache cleared")
    
    def invalidate_prompt_cache(self, season: int, episode: int) -> None:
        """Invalidate cache for a specific prompt"""
        prompt_key = self._get_prompt_key(season, episode)
        if prompt_key in self._prompts:
            del self._prompts[prompt_key]
            self.log_info(f"Cache invalidated for prompt S{season}E{episode}")
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Get cache status information"""
        return {
            "cached_prompts": len(self._prompts),
            "prompt_keys": list(self._prompts.keys()),
            "firebase_enabled": self.firebase_service.use_firebase
        }
    
    async def create_system_prompt(self, prompt_request: SystemPromptRequest) -> SystemPromptResponse:
        """
        Create or update a system prompt
        
        Args:
            prompt_request: Prompt creation request
            
        Returns:
            SystemPromptResponse: Created/updated prompt response
        """
        # Validate season and episode
        is_valid, error_msg = PromptValidator.validate_season_episode(
            prompt_request.season, prompt_request.episode
        )
        if not is_valid:
            raise ValidationException(error_msg)
        
        # Validate prompt content
        is_valid, error_msg = PromptValidator.validate_prompt_content(prompt_request.prompt)
        if not is_valid:
            raise ValidationException(error_msg)
        
        # Create prompt object
        prompt = SystemPrompt(
            season=prompt_request.season,
            episode=prompt_request.episode,
            prompt=prompt_request.prompt,
            prompt_type=prompt_request.prompt_type,
            metadata=prompt_request.metadata or {},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Store prompt
        prompt_key = self._get_prompt_key(prompt.season, prompt.episode)
        
        if self.firebase_service.use_firebase:
            # Store in Firebase
            prompt_data = self._prompt_to_dict(prompt)
            try:
                import asyncio
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.firebase_service.db.collection('prompts').document(prompt_key).set(prompt_data)
                )
            except Exception as e:
                self.log_error(f"Failed to save prompt to Firebase: {e}")
                # Fall back to in-memory storage
                self._prompts[prompt_key] = prompt
        else:
            # Store in memory
            self._prompts[prompt_key] = prompt
            # Save to local storage
            self.firebase_service._save_local_data()
        
        self.log_info(f"System prompt created: Season {prompt.season}, Episode {prompt.episode}")
        return SystemPromptResponse.from_system_prompt(prompt)
    
    async def get_system_prompt(self, season: int, episode: int) -> SystemPromptResponse:
        """
        Get system prompt for specific season and episode
        Always fetches fresh data from Firebase when available
        
        Args:
            season: Season number
            episode: Episode number
            
        Returns:
            SystemPromptResponse: Prompt response
        """
        # Validate season and episode
        is_valid, error_msg = PromptValidator.validate_season_episode(season, episode)
        if not is_valid:
            raise ValidationException(error_msg)
        
        prompt_key = self._get_prompt_key(season, episode)
        
        if self.firebase_service.use_firebase:
            # Always fetch fresh from Firebase - don't use cache
            try:
                import asyncio
                doc_ref = self.firebase_service.db.collection('prompts').document(prompt_key)
                doc = await asyncio.get_event_loop().run_in_executor(None, doc_ref.get)
                
                if not doc.exists:
                    raise SystemPromptNotFoundException(season, episode)
                
                prompt_data = doc.to_dict()
                prompt = self._dict_to_prompt(prompt_data)
                
                # Update cache with fresh data
                self._prompts[prompt_key] = prompt
                self.log_info(f"Fetched fresh prompt from Firebase: S{season}E{episode}")
                
            except Exception as e:
                if isinstance(e, SystemPromptNotFoundException):
                    raise
                self.log_error(f"Failed to get prompt from Firebase: {e}")
                raise SystemPromptNotFoundException(season, episode)
        else:
            # Get from memory (local storage mode)
            prompt = self._prompts.get(prompt_key)
            if not prompt:
                raise SystemPromptNotFoundException(season, episode)
        
        return SystemPromptResponse.from_system_prompt(prompt)
    
    async def get_prompt_content(self, season: int, episode: int) -> str:
        """
        Get raw prompt content for OpenAI integration
        
        Args:
            season: Season number
            episode: Episode number
            
        Returns:
            str: Raw prompt content
        """
        prompt_response = await self.get_system_prompt(season, episode)
        
        # Get the actual prompt object to return content
        prompt_key = self._get_prompt_key(season, episode)
        
        if self.firebase_service.use_firebase:
            try:
                import asyncio
                doc_ref = self.firebase_service.db.collection('prompts').document(prompt_key)
                doc = await asyncio.get_event_loop().run_in_executor(None, doc_ref.get)
                prompt_data = doc.to_dict()
                return prompt_data.get('prompt', '')
            except Exception:
                raise SystemPromptNotFoundException(season, episode)
        else:
            prompt = self._prompts.get(prompt_key)
            if not prompt:
                raise SystemPromptNotFoundException(season, episode)
            return prompt.prompt
    
    async def get_season_overview(self, season: int) -> SeasonOverview:
        """
        Get overview of a complete season
        
        Args:
            season: Season number
            
        Returns:
            SeasonOverview: Season overview
        """
        episodes_found = 0
        available_types = set()
        last_updated = None
        
        # Check episodes 1-7
        for episode in range(1, 8):
            try:
                prompt_response = await self.get_system_prompt(season, episode)
                episodes_found += 1
                available_types.add(prompt_response.prompt_type)
                
                if prompt_response.updated_at:
                    if not last_updated or prompt_response.updated_at > last_updated:
                        last_updated = prompt_response.updated_at
                        
            except SystemPromptNotFoundException:
                continue
        
        return SeasonOverview(
            season=season,
            total_episodes=7,
            completed_episodes=episodes_found,
            available_prompt_types=list(available_types),
            last_updated=last_updated
        )
    
    async def get_all_seasons_overview(self) -> List[SeasonOverview]:
        """
        Get overview of all seasons
        
        Returns:
            List[SeasonOverview]: List of season overviews
        """
        overviews = []
        
        # Check seasons 1-10
        for season in range(1, 11):
            try:
                overview = await self.get_season_overview(season)
                if overview.completed_episodes > 0:  # Only include seasons with content
                    overviews.append(overview)
            except Exception as e:
                self.log_warning(f"Failed to get overview for season {season}: {e}")
                continue
        
        return overviews
    
    def validate_prompt_content(self, prompt: str) -> PromptValidationResult:
        """
        Validate prompt content and provide suggestions
        
        Args:
            prompt: Prompt content to validate
            
        Returns:
            PromptValidationResult: Validation result
        """
        result = PromptValidationResult(is_valid=True)
        
        # Basic validation
        if len(prompt.strip()) < 10:
            result.add_error("Prompt must be at least 10 characters long")
        
        if len(prompt) > 5000:
            result.add_error("Prompt must be no more than 5000 characters")
        
        # Content suggestions
        if "You are" not in prompt:
            result.add_suggestion("Consider starting with 'You are...' to define the AI's role")
        
        if not any(word in prompt.lower() for word in ["goal", "objective", "purpose"]):
            result.add_suggestion("Consider including the goal or purpose of the conversation")
        
        if len(prompt) < 100:
            result.add_warning("Short prompts may not provide enough context")
        
        if prompt.count("?") == 0:
            result.add_suggestion("Consider adding questions to encourage interaction")
        
        return result
    
    async def update_prompt_metadata(self, season: int, episode: int, metadata: Dict[str, Any]) -> SystemPromptResponse:
        """
        Update prompt metadata
        
        Args:
            season: Season number
            episode: Episode number
            metadata: New metadata
            
        Returns:
            SystemPromptResponse: Updated prompt response
        """
        # Get existing prompt
        prompt_key = self._get_prompt_key(season, episode)
        
        if self.firebase_service.use_firebase:
            try:
                import asyncio
                doc_ref = self.firebase_service.db.collection('prompts').document(prompt_key)
                doc = await asyncio.get_event_loop().run_in_executor(None, doc_ref.get)
                
                if not doc.exists:
                    raise SystemPromptNotFoundException(season, episode)
                
                prompt_data = doc.to_dict()
                prompt = self._dict_to_prompt(prompt_data)
            except Exception as e:
                if isinstance(e, SystemPromptNotFoundException):
                    raise
                raise SystemPromptNotFoundException(season, episode)
        else:
            prompt = self._prompts.get(prompt_key)
            if not prompt:
                raise SystemPromptNotFoundException(season, episode)
        
        # Update metadata
        prompt.metadata.update(metadata)
        prompt.updated_at = datetime.now()
        prompt.version += 1
        
        # Save updated prompt
        if self.firebase_service.use_firebase:
            try:
                import asyncio
                prompt_data = self._prompt_to_dict(prompt)
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.firebase_service.db.collection('prompts').document(prompt_key).set(prompt_data)
                )
            except Exception as e:
                self.log_error(f"Failed to update prompt in Firebase: {e}")
        else:
            self._prompts[prompt_key] = prompt
        
        return SystemPromptResponse.from_system_prompt(prompt)
    
    async def deactivate_prompt(self, season: int, episode: int) -> bool:
        """
        Deactivate a system prompt
        
        Args:
            season: Season number
            episode: Episode number
            
        Returns:
            bool: True if successful
        """
        await self.update_prompt_metadata(season, episode, {"is_active": False})
        return True
    
    async def search_prompts(self, query: Optional[str] = None, 
                           prompt_type: Optional[PromptType] = None,
                           season: Optional[int] = None) -> List[SystemPromptResponse]:
        """
        Search prompts based on criteria
        
        Args:
            query: Text to search in prompt content
            prompt_type: Filter by prompt type
            season: Filter by season
            
        Returns:
            List[SystemPromptResponse]: Matching prompts
        """
        results = []
        
        # This is a simplified search - in a real implementation,
        # you'd use proper search functionality
        prompts_to_search = []
        
        if season:
            # Search specific season
            for episode in range(1, 8):
                try:
                    prompt_response = await self.get_system_prompt(season, episode)
                    prompts_to_search.append(prompt_response)
                except SystemPromptNotFoundException:
                    continue
        else:
            # Search all seasons
            overviews = await self.get_all_seasons_overview()
            for overview in overviews:
                for episode in range(1, 8):
                    try:
                        prompt_response = await self.get_system_prompt(overview.season, episode)
                        prompts_to_search.append(prompt_response)
                    except SystemPromptNotFoundException:
                        continue
        
        # Filter results
        for prompt_response in prompts_to_search:
            if prompt_type and prompt_response.prompt_type != prompt_type.value:
                continue
            
            # For query search, we'd need the actual content
            # This is simplified - you'd implement proper text search
            
            results.append(prompt_response)
        
        return results
    
    async def get_prompt_analytics(self, season: int, episode: int) -> dict:
        """
        Get analytics for a specific prompt
        
        Args:
            season: Season number
            episode: Episode number
            
        Returns:
            dict: Prompt analytics
        """
        prompt_response = await self.get_system_prompt(season, episode)
        
        return {
            "season": season,
            "episode": episode,
            "prompt_stats": {
                "character_count": prompt_response.prompt_length,
                "version": prompt_response.version,
                "type": prompt_response.prompt_type,
                "is_active": prompt_response.is_active
            },
            "metadata": prompt_response.metadata,
            "timestamps": {
                "created_at": prompt_response.created_at,
                "updated_at": prompt_response.updated_at
            }
        }
    
    def _prompt_to_dict(self, prompt: SystemPrompt) -> Dict[str, Any]:
        """Convert SystemPrompt to dictionary"""
        # Handle both enum and string prompt_type values
        prompt_type_value = prompt.prompt_type.value if hasattr(prompt.prompt_type, 'value') else prompt.prompt_type
        
        return {
            "season": prompt.season,
            "episode": prompt.episode,
            "prompt": prompt.prompt,
            "prompt_type": prompt_type_value,
            "metadata": prompt.metadata,
            "created_at": prompt.created_at.isoformat() if prompt.created_at else None,
            "updated_at": prompt.updated_at.isoformat() if prompt.updated_at else None,
            "version": prompt.version,
            "is_active": prompt.is_active
        }
    
    def _dict_to_prompt(self, data: Dict[str, Any]) -> SystemPrompt:
        """Convert dictionary to SystemPrompt"""
        return SystemPrompt(
            season=data["season"],
            episode=data["episode"],
            prompt=data["prompt"],
            prompt_type=PromptType(data["prompt_type"]),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            version=data.get("version", 1),
            is_active=data.get("is_active", True)
        )


# Global service instance
_prompt_service: Optional[PromptService] = None


def get_prompt_service() -> PromptService:
    """Get prompt service singleton"""
    global _prompt_service
    if _prompt_service is None:
        _prompt_service = PromptService()
    return _prompt_service

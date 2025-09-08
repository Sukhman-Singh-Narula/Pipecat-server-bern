"""
System prompt management routes
"""
from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from server.models.system_prompt import (
    SystemPromptRequest, SystemPromptResponse, PromptValidationResult,
    SeasonOverview, PromptType
)
from server.services.prompt_service import get_prompt_service, PromptService
from server.utils.exceptions import (
    ValidationException, SystemPromptNotFoundException,
    handle_validation_error, handle_generic_error
)


router = APIRouter(prefix="/prompts", tags=["System Prompts"])


def get_prompt_service_dependency():
    """Dependency to get prompt service"""
    return get_prompt_service()


class PromptValidationRequest(BaseModel):
    """Request model for prompt validation"""
    prompt: str


class MetadataUpdateRequest(BaseModel):
    """Request model for updating prompt metadata"""
    metadata: Dict[str, Any]


@router.post("/",
             response_model=SystemPromptResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Create system prompt",
             description="Upload a new system prompt for a specific season and episode")
async def create_system_prompt(prompt_request: SystemPromptRequest, prompt_service: PromptService = Depends(get_prompt_service_dependency)):
    """
    Create or update a system prompt
    
    - **season**: Season number (1-10)
    - **episode**: Episode number (1-7)
    - **prompt**: System prompt content (10-5000 characters)
    - **prompt_type**: Type of prompt (learning, assessment, conversation, review)
    - **metadata**: Additional metadata (optional)
    """
    try:
        prompt_response = await prompt_service.create_system_prompt(prompt_request)
        return prompt_response
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=handle_validation_error(e)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=handle_generic_error(e)
        )


@router.get("/{season}/{episode}",
            response_model=SystemPromptResponse,
            summary="Get system prompt",
            description="Retrieve system prompt for specific season and episode")
async def get_system_prompt(season: int, episode: int, prompt_service: PromptService = Depends(get_prompt_service_dependency)):
    """
    Get system prompt for a specific season and episode
    
    - **season**: Season number
    - **episode**: Episode number
    """
    try:
        prompt_response = await prompt_service.get_system_prompt(season, episode)
        return prompt_response
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=handle_validation_error(e)
        )
    
    except SystemPromptNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "System Prompt Not Found",
                "message": e.message,
                "season": season,
                "episode": episode,
                "code": e.error_code
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=handle_generic_error(e)
        )


@router.get("/{season}/{episode}/content",
            summary="Get prompt content",
            description="Get raw prompt content for OpenAI (internal use)")
async def get_prompt_content(season: int, episode: int, prompt_service: PromptService = Depends(get_prompt_service_dependency)):
    """
    Get raw prompt content for OpenAI integration
    
    - **season**: Season number
    - **episode**: Episode number
    """
    try:
        content = await prompt_service.get_prompt_content(season, episode)
        
        return {
            "season": season,
            "episode": episode,
            "content": content,
            "character_count": len(content)
        }
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=handle_validation_error(e)
        )
    
    except SystemPromptNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "System Prompt Not Found",
                "message": e.message,
                "season": season,
                "episode": episode
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=handle_generic_error(e)
        )


@router.get("/{season}",
            response_model=SeasonOverview,
            summary="Get season overview",
            description="Get overview of all episodes in a season")
async def get_season_overview(season: int, prompt_service: PromptService = Depends(get_prompt_service_dependency)):
    """
    Get overview of a complete season
    
    - **season**: Season number
    """
    try:
        overview = await prompt_service.get_season_overview(season)
        return overview
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=handle_generic_error(e)
        )


@router.get("/",
            response_model=List[SeasonOverview],
            summary="Get all seasons overview",
            description="Get overview of all seasons")
async def get_all_seasons_overview(prompt_service: PromptService = Depends(get_prompt_service_dependency)):
    """
    Get overview of all seasons with completion statistics
    """
    try:
        overviews = await prompt_service.get_all_seasons_overview()
        return overviews
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=handle_generic_error(e)
        )


@router.post("/validate",
             response_model=PromptValidationResult,
             summary="Validate prompt content",
             description="Validate prompt content and get improvement suggestions")
async def validate_prompt(validation_request: PromptValidationRequest, prompt_service: PromptService = Depends(get_prompt_service_dependency)):
    """
    Validate prompt content and provide suggestions for improvement
    
    - **prompt**: Prompt content to validate
    """
    try:
        validation_result = prompt_service.validate_prompt_content(validation_request.prompt)
        return validation_result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=handle_generic_error(e)
        )


@router.get("/search",
            response_model=List[SystemPromptResponse],
            summary="Search prompts",
            description="Search prompts by content, type, or season")
async def search_prompts(
    query: Optional[str] = Query(None, description="Text to search in prompt content"),
    prompt_type: Optional[PromptType] = Query(None, description="Filter by prompt type"),
    season: Optional[int] = Query(None, description="Filter by season"),
    prompt_service: PromptService = Depends(get_prompt_service_dependency)
):
    """
    Search prompts based on various criteria
    
    - **query**: Text to search in prompt content (optional)
    - **prompt_type**: Filter by prompt type (optional)
    - **season**: Filter by season (optional)
    """
    try:
        results = await prompt_service.search_prompts(
            query=query,
            prompt_type=prompt_type,
            season=season
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=handle_generic_error(e)
        )


@router.get("/types",
            summary="Get prompt types",
            description="Get list of available prompt types")
async def get_prompt_types():
    """
    Get list of available prompt types
    """
    return {
        "prompt_types": [
            {
                "value": prompt_type.value,
                "description": f"{prompt_type.value.title()} type prompt"
            }
            for prompt_type in PromptType
        ]
    }

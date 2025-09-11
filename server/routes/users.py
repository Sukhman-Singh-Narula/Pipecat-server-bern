"""
User management routes
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from pydantic import BaseModel

from models.user import UserResponse, SessionInfo
from services.user_service import get_user_service, UserService
from utils.exceptions import (
    ValidationException, UserNotFoundException,
    handle_validation_error, handle_user_error, handle_generic_error
)


router = APIRouter(prefix="/users", tags=["Users"])


def get_user_service_dependency():
    """Dependency to get user service"""
    return get_user_service()


class ProgressUpdateRequest(BaseModel):
    """Request model for updating user progress"""
    words_learnt: Optional[List[str]] = None
    topics_learnt: Optional[List[str]] = None


@router.get("/{device_id}",
            response_model=UserResponse,
            summary="Get user information",
            description="Retrieve detailed information for a specific user")
async def get_user(device_id: str, user_service: UserService = Depends(get_user_service_dependency)):
    """
    Get comprehensive user information including progress and statistics
    
    - **device_id**: Unique device identifier
    """
    try:
        user_response = await user_service.get_user(device_id)
        return user_response
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=handle_validation_error(e)
        )
    
    except UserNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=handle_user_error(e)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=handle_generic_error(e)
        )


@router.get("/{device_id}/statistics",
            summary="Get user statistics",
            description="Get comprehensive statistics for a user")
async def get_user_statistics(device_id: str, user_service: UserService = Depends(get_user_service_dependency)):
    """
    Get detailed statistics for a user including learning progress and time tracking
    
    - **device_id**: Unique device identifier
    """
    try:
        statistics = await user_service.get_user_statistics(device_id)
        return statistics
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=handle_validation_error(e)
        )
    
    except UserNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=handle_user_error(e)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=handle_generic_error(e)
        )


@router.get("/{device_id}/session",
            summary="Get current session information",
            description="Get information about the user's current session")
async def get_session_info(device_id: str, user_service: UserService = Depends(get_user_service_dependency)):
    """
    Get current session information including connection status and duration
    
    - **device_id**: Unique device identifier
    """
    try:
        # For now, we'll return basic session info since we don't have WebSocket tracking
        session_info = await user_service.get_user_session_info(
            device_id=device_id,
            session_duration=0.0,  # Would be calculated from WebSocket connection
            is_connected=False     # Would be determined from active connections
        )
        
        return session_info
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=handle_validation_error(e)
        )
    
    except UserNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=handle_user_error(e)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=handle_generic_error(e)
        )


@router.put("/{device_id}/progress",
            response_model=UserResponse,
            summary="Update user progress",
            description="Update user's learning progress with new words or topics")
async def update_progress(device_id: str, progress_update: ProgressUpdateRequest, user_service: UserService = Depends(get_user_service_dependency)):
    """
    Update user's learning progress
    
    - **device_id**: Unique device identifier
    - **words_learnt**: List of new words learned
    - **topics_learnt**: List of new topics learned
    """
    try:
        updated_user = await user_service.update_user_progress(
            device_id=device_id,
            words_learnt=progress_update.words_learnt,
            topics_learnt=progress_update.topics_learnt
        )
        
        return updated_user
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=handle_validation_error(e)
        )
    
    except UserNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=handle_user_error(e)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=handle_generic_error(e)
        )


@router.post("/{device_id}/advance-episode",
             response_model=UserResponse,
             summary="Advance to next episode",
             description="Manually advance user to next episode/season")
async def advance_episode(device_id: str, user_service: UserService = Depends(get_user_service_dependency)):
    """
    Manually advance user to the next episode or season
    
    - **device_id**: Unique device identifier
    
    Note: This is typically done automatically when conversations complete
    """
    try:
        updated_user = await user_service.advance_episode(device_id)
        return updated_user
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=handle_validation_error(e)
        )
    
    except UserNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=handle_user_error(e)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=handle_generic_error(e)
        )


@router.delete("/{device_id}",
               summary="Delete user account",
               description="Soft delete user account (deactivate)")
async def delete_user(device_id: str, user_service: UserService = Depends(get_user_service_dependency)):
    """
    Soft delete user account (sets status to inactive)
    
    - **device_id**: Unique device identifier
    """
    try:
        success = await user_service.delete_user(device_id)
        
        if success:
            return {"message": "User account deactivated successfully", "device_id": device_id}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "Failed to delete user account"}
            )
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=handle_validation_error(e)
        )
    
    except UserNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=handle_user_error(e)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=handle_generic_error(e)
        )

"""
Enhanced User API endpoints for comprehensive user management
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

from server.services.enhanced_user_service import EnhancedUserService
from server.services.firebase_service import get_firebase_service
from server.models.enhanced_user import EnhancedUser, UserStatus

# Initialize router
router = APIRouter(prefix="/users", tags=["Enhanced Users"])

# Dependency to get services
def get_user_service():
    firebase_service = get_firebase_service()
    return EnhancedUserService(firebase_service)

# Request/Response Models
class CreateUserRequest(BaseModel):
    device_id: str
    name: str
    age: int
    email: EmailStr
    parent: Dict[str, Any]

class UpdateProgressRequest(BaseModel):
    season: int
    episode: int
    completed: bool = False

class AddLearningDataRequest(BaseModel):
    words: List[str]
    topics: List[str]
    session_time: float

class UserResponse(BaseModel):
    device_id: str
    name: str
    age: int
    email: str
    status: str
    created_at: datetime
    last_active: Optional[datetime]
    parent: Dict[str, Any]
    progress: Dict[str, Any]
    words_learnt: List[str]
    topics_learnt: List[str]
    total_time: float

@router.post("/create", response_model=UserResponse)
async def create_user(
    request: CreateUserRequest,
    user_service: EnhancedUserService = Depends(get_user_service)
):
    """Create a new enhanced user"""
    try:
        user = await user_service.create_user(request.dict())
        return UserResponse(**user.to_dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{email}", response_model=UserResponse)
async def get_user(
    email: str,
    user_service: EnhancedUserService = Depends(get_user_service)
):
    """Get user by email"""
    user = await user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**user.to_dict())

@router.get("/device/{device_id}", response_model=UserResponse)
async def get_user_by_device(
    device_id: str,
    user_service: EnhancedUserService = Depends(get_user_service)
):
    """Get user by device ID"""
    user = await user_service.get_user_by_device_id(device_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**user.to_dict())

@router.put("/{email}/progress")
async def update_user_progress(
    email: str,
    request: UpdateProgressRequest,
    user_service: EnhancedUserService = Depends(get_user_service)
):
    """Update user's learning progress"""
    success = await user_service.update_user_progress(
        email, request.season, request.episode, request.completed
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update progress")
    return {"message": "Progress updated successfully"}

@router.put("/{email}/learning-data")
async def add_learning_data(
    email: str,
    request: AddLearningDataRequest,
    user_service: EnhancedUserService = Depends(get_user_service)
):
    """Add learning data for a user"""
    success = await user_service.add_learning_data(
        email, request.words, request.topics, request.session_time
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to add learning data")
    return {"message": "Learning data added successfully"}

@router.put("/{email}/last-active")
async def update_last_active(
    email: str,
    user_service: EnhancedUserService = Depends(get_user_service)
):
    """Update user's last active timestamp"""
    success = await user_service.update_last_active(email)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update last active")
    return {"message": "Last active updated successfully"}

@router.get("/", response_model=List[UserResponse])
async def get_all_users(
    user_service: EnhancedUserService = Depends(get_user_service)
):
    """Get all users"""
    users = await user_service.get_all_users()
    return [UserResponse(**user.to_dict()) for user in users]

@router.get("/status/{status}", response_model=List[UserResponse])
async def get_users_by_status(
    status: str,
    user_service: EnhancedUserService = Depends(get_user_service)
):
    """Get users by status"""
    try:
        user_status = UserStatus(status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    users = await user_service.get_users_by_status(user_status)
    return [UserResponse(**user.to_dict()) for user in users]

@router.get("/{email}/analytics")
async def get_user_analytics(
    email: str,
    user_service: EnhancedUserService = Depends(get_user_service)
):
    """Get comprehensive user analytics"""
    analytics = await user_service.get_user_analytics(email)
    if not analytics:
        raise HTTPException(status_code=404, detail="User not found or no analytics data")
    return analytics

@router.delete("/{email}")
async def delete_user(
    email: str,
    user_service: EnhancedUserService = Depends(get_user_service)
):
    """Delete a user"""
    success = await user_service.delete_user(email)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete user")
    return {"message": "User deleted successfully"}

@router.get("/{email}/summary")
async def get_user_summary(
    email: str,
    user_service: EnhancedUserService = Depends(get_user_service)
):
    """Get user summary with key metrics"""
    user = await user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "name": user.name,
        "age": user.age,
        "status": user.status.value,
        "current_progress": f"S{user.progress.season}E{user.progress.episode}",
        "episodes_completed": user.progress.episodes_completed,
        "total_words_learned": len(user.words_learnt),
        "total_topics_covered": len(user.topics_learnt),
        "total_learning_hours": round(user.total_time / 3600, 2),
        "last_active": user.last_active,
        "parent_name": user.parent.name,
        "parent_email": user.parent.email
    }

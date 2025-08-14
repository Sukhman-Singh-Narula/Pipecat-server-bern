"""
Routes package initialization
"""
from .auth import router as auth_router
from .users import router as users_router
from .prompts import router as prompts_router

__all__ = ["auth_router", "users_router", "prompts_router"]

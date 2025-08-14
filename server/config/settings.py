"""
Application settings and configuration
"""
try:
    from pydantic_settings import BaseSettings
    from pydantic import Field
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings, Field
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # App information
    app_name: str = Field(default="Pipecat Enhanced Server", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server configuration  
    host: str = Field(default="0.0.0.0", env="SERVER_HOST")
    port: int = Field(default=7860, env="SERVER_PORT")
    log_level: str = Field(default="info", env="LOG_LEVEL")
    
    # API Keys
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    deepgram_api_key: str = Field(..., env="DEEPGRAM_API_KEY")
    cartesia_api_key: str = Field(..., env="CARTESIA_API_KEY")
    daily_api_key: Optional[str] = Field(None, env="DAILY_API_KEY")
    
    # Firebase configuration
    firebase_credentials_path: str = Field(
        default="firebase-credentials.json", 
        env="FIREBASE_CREDENTIALS_PATH"
    )
    
    # Security settings
    cors_origins: list = Field(default=["*"], env="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")
    
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings singleton"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def validate_settings() -> bool:
    """Validate required settings"""
    try:
        settings = get_settings()
        
        # Check required API keys
        required_keys = [
            settings.openai_api_key,
            settings.deepgram_api_key,
            settings.cartesia_api_key
        ]
        
        for key in required_keys:
            if not key or key.startswith("your_") or key == "...":
                print("❌ Missing or invalid API keys in .env file")
                return False
        
        # Check Firebase credentials
        if not os.path.exists(settings.firebase_credentials_path):
            print(f"⚠️  Firebase credentials file not found: {settings.firebase_credentials_path}")
            print("Some features may not work without Firebase")
        
        return True
        
    except Exception as e:
        print(f"❌ Settings validation failed: {e}")
        return False

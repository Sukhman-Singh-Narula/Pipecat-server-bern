"""
Validators for input validation
"""
import re
from typing import Optional


class DeviceValidator:
    """Device ID validation utilities"""
    
    @staticmethod
    def validate_device_id(device_id: str) -> bool:
        """
        Validate device ID format
        
        Args:
            device_id: Device ID to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not isinstance(device_id, str):
            return False
        
        return bool(re.match(r'^[A-Z]{4}\d{4}$', device_id))
    
    @staticmethod
    def get_device_validation_error(device_id: str) -> str:
        """
        Get specific validation error message for device ID
        
        Args:
            device_id: Device ID to validate
            
        Returns:
            str: Error message
        """
        if not isinstance(device_id, str):
            return "Device ID must be a string"
        
        if len(device_id) != 8:
            return "Device ID must be exactly 8 characters long"
        
        if not device_id[:4].isupper() or not device_id[:4].isalpha():
            return "First 4 characters must be uppercase letters"
        
        if not device_id[4:].isdigit():
            return "Last 4 characters must be digits"
        
        return "Device ID format is invalid"


class PromptValidator:
    """System prompt validation utilities"""
    
    @staticmethod
    def validate_season_episode(season: int, episode: int) -> tuple[bool, Optional[str]]:
        """
        Validate season and episode numbers
        
        Args:
            season: Season number
            episode: Episode number
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not isinstance(season, int) or season < 1 or season > 10:
            return False, "Season must be an integer between 1 and 10"
        
        if not isinstance(episode, int) or episode < 1 or episode > 7:
            return False, "Episode must be an integer between 1 and 7"
        
        return True, None
    
    @staticmethod
    def validate_prompt_content(prompt: str) -> tuple[bool, Optional[str]]:
        """
        Validate prompt content
        
        Args:
            prompt: Prompt content to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not isinstance(prompt, str):
            return False, "Prompt must be a string"
        
        prompt = prompt.strip()
        
        if len(prompt) < 10:
            return False, "Prompt must be at least 10 characters long"
        
        if len(prompt) > 5000:
            return False, "Prompt must be no more than 5000 characters long"
        
        return True, None


class SecurityValidator:
    """Security validation utilities"""
    
    @staticmethod
    def sanitize_input(input_str: str) -> str:
        """
        Sanitize input string to prevent injection attacks
        
        Args:
            input_str: Input string to sanitize
            
        Returns:
            str: Sanitized string
        """
        if not isinstance(input_str, str):
            return ""
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\';(){}]', '', input_str)
        
        # Limit length
        sanitized = sanitized[:1000]
        
        # Strip whitespace
        sanitized = sanitized.strip()
        
        return sanitized
    
    @staticmethod
    def validate_name(name: str) -> tuple[bool, Optional[str]]:
        """
        Validate user name
        
        Args:
            name: Name to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not isinstance(name, str):
            return False, "Name must be a string"
        
        name = name.strip()
        
        if len(name) < 1:
            return False, "Name cannot be empty"
        
        if len(name) > 100:
            return False, "Name must be no more than 100 characters"
        
        # Allow letters, spaces, hyphens, and apostrophes
        if not re.match(r"^[a-zA-Z\s\-']+$", name):
            return False, "Name can only contain letters, spaces, hyphens, and apostrophes"
        
        return True, None
    
    @staticmethod
    def validate_age(age: int) -> tuple[bool, Optional[str]]:
        """
        Validate user age
        
        Args:
            age: Age to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not isinstance(age, int):
            return False, "Age must be an integer"
        
        if age < 1 or age > 120:
            return False, "Age must be between 1 and 120"
        
        return True, None

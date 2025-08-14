"""
Custom exceptions for the application
"""


class ValidationException(Exception):
    """Raised when validation fails"""
    def __init__(self, message: str, field: str = None, value: str = None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(self.message)


class UserNotFoundException(Exception):
    """Raised when user is not found"""
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.message = f"User with device ID '{device_id}' not found"
        super().__init__(self.message)


class UserAlreadyExistsException(Exception):
    """Raised when user already exists"""
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.message = f"User with device ID '{device_id}' already exists"
        super().__init__(self.message)


class SystemPromptNotFoundException(Exception):
    """Raised when system prompt is not found"""
    def __init__(self, season: int, episode: int):
        self.season = season
        self.episode = episode
        self.message = f"System prompt for Season {season}, Episode {episode} not found"
        self.error_code = "PROMPT_NOT_FOUND"
        super().__init__(self.message)


class FirebaseException(Exception):
    """Raised when Firebase operations fail"""
    def __init__(self, operation: str, error: str, collection: str = None, document: str = None):
        self.operation = operation
        self.error = error
        self.collection = collection
        self.document = document
        self.message = f"Firebase {operation} failed: {error}"
        super().__init__(self.message)


class RateLimitException(Exception):
    """Raised when rate limit is exceeded"""
    def __init__(self, limit: int, window: int):
        self.limit = limit
        self.window = window
        self.message = f"Rate limit exceeded: {limit} requests per {window} seconds"
        self.error_code = "RATE_LIMIT_EXCEEDED"
        super().__init__(self.message)


class SecurityException(Exception):
    """Raised when security violations occur"""
    def __init__(self, violation_type: str, identifier: str, details: dict = None):
        self.violation_type = violation_type
        self.identifier = identifier
        self.details = details or {}
        self.message = f"Security violation: {violation_type}"
        self.error_code = "SECURITY_VIOLATION"
        super().__init__(self.message)


# Error handlers
def handle_validation_error(exc: ValidationException) -> dict:
    """Handle validation errors"""
    return {
        "error": "Validation Error",
        "message": exc.message,
        "field": exc.field,
        "value": exc.value
    }


def handle_user_error(exc: Exception) -> dict:
    """Handle user-related errors"""
    if isinstance(exc, UserNotFoundException):
        return {
            "error": "User Not Found",
            "message": exc.message,
            "device_id": exc.device_id
        }
    elif isinstance(exc, UserAlreadyExistsException):
        return {
            "error": "User Already Exists",
            "message": exc.message,
            "device_id": exc.device_id
        }
    else:
        return handle_generic_error(exc)


def handle_generic_error(exc: Exception) -> dict:
    """Handle generic errors"""
    return {
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
        "type": type(exc).__name__
    }

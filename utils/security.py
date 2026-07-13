"""
Security utilities: input validation, token verification, rate limiting.
"""
import re
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

class SecurityValidator:
    """Input validation and security checks."""
    
    MAX_MESSAGE_LENGTH = 2000
    MIN_MESSAGE_LENGTH = 1
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]{3,20}$')
    TOKEN_PATTERN = re.compile(r'^[a-fA-F0-9]{64}$')  # Mock SHA256 hex
    
    @staticmethod
    def validate_message(msg: str) -> Tuple[bool, str]:
        """Validate user message."""
        msg = msg.strip() if msg else ""
        
        if not msg or len(msg) < SecurityValidator.MIN_MESSAGE_LENGTH:
            return False, "Message is empty"
        
        if len(msg) > SecurityValidator.MAX_MESSAGE_LENGTH:
            return False, f"Message exceeds {SecurityValidator.MAX_MESSAGE_LENGTH} characters"
        
        # Check for suspicious patterns (basic)
        if any(char in msg for char in ['\x00', '\x1b']):  # Null, escape chars
            return False, "Message contains invalid characters"
        
        return True, ""
    
    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """Validate username format."""
        if not SecurityValidator.USERNAME_PATTERN.match(username or ""):
            return False, "Username must be 3-20 alphanumeric characters"
        return True, ""
    
    @staticmethod
    def validate_token(token: str) -> Tuple[bool, str]:
        """Validate token format (mock JWT check)."""
        if not SecurityValidator.TOKEN_PATTERN.match(token or ""):
            return False, "Invalid token format"
        return True, ""
    
    @staticmethod
    def sanitize_message(msg: str) -> str:
        """Remove/escape potentially harmful characters."""
        # Strip control characters
        msg = ''.join(c for c in msg if ord(c) >= 32 or c in '\t\n\r')
        return msg[:SecurityValidator.MAX_MESSAGE_LENGTH]

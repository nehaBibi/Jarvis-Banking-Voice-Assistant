import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

class SecurityValidator:
    
    MAX_MESSAGE_LENGTH = 2000
    MIN_MESSAGE_LENGTH = 1
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]{3,20}$')
    
    @staticmethod
    def validate_message(msg: str) -> Tuple[bool, str]:
        msg = msg.strip() if msg else ""
        
        if not msg or len(msg) < SecurityValidator.MIN_MESSAGE_LENGTH:
            return False, "Message is empty"
        
        if len(msg) > SecurityValidator.MAX_MESSAGE_LENGTH:
            return False, f"Message exceeds {SecurityValidator.MAX_MESSAGE_LENGTH} characters"
        
        if any(char in msg for char in ['\x00', '\x1b']):
            return False, "Message contains invalid characters"
        
        return True, ""
    
    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        if not SecurityValidator.USERNAME_PATTERN.match(username or ""):
            return False, "Username must be 3-20 alphanumeric characters"
        return True, ""
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email or ""):
            return False, "Invalid email format"
        return True, ""
    
    @staticmethod
    def sanitize_message(msg: str) -> str:
        msg = ''.join(c for c in msg if ord(c) >= 32 or c in '\t\n\r')
        return msg[:SecurityValidator.MAX_MESSAGE_LENGTH]
    
    @staticmethod
    def sanitize_html(html: str) -> str:
        html = html.replace('<', '&lt;').replace('>', '&gt;')
        html = html.replace('"', '&quot;').replace("'", '&#x27;')
        return html
    
    @staticmethod
    def check_pii(message: str) -> bool:
        pii_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',
            r'\b\d{16}\b',
            r'\bSSN\b|\bsocial security\b',
            r'\bPIN\b|\bpassword\b',
            r'\bCVV\b|\bCSC\b'
        ]
        
        for pattern in pii_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                logger.warning(f"PII detected in message")
                return True
        
        return False

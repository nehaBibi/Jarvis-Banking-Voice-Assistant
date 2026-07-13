"""
Logging and observability utilities.
"""
import logging
import json
from datetime import datetime

def setup_logging(app, log_level=logging.INFO):
    """Configure structured logging for Flask app."""
    
    # Root logger config
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # App logger
    app.logger.setLevel(log_level)
    
    return app.logger

def log_request(logger, method: str, path: str, user_id: str = "anon"):
    """Log incoming request."""
    logger.info(f"REQUEST: {method} {path} user={user_id}")

def log_chat_interaction(logger, user_id: str, message: str, agent_name: str, response: str, latency_ms: float, safe: bool):
    """Log chat interaction (without sensitive data)."""
    msg_hash = hash(message) % 10000  # Simple hash for obfuscation
    log_entry = {
        "event": "chat_interaction",
        "user_id": user_id,
        "message_hash": msg_hash,
        "agent": agent_name,
        "response_len": len(response),
        "latency_ms": latency_ms,
        "safe": safe,
        "timestamp": datetime.utcnow().isoformat()
    }
    logger.info(json.dumps(log_entry))

def log_security_event(logger, event_type: str, user_id: str, details: str):
    """Log security events."""
    log_entry = {
        "event": "security",
        "type": event_type,
        "user_id": user_id,
        "details": details,
        "timestamp": datetime.utcnow().isoformat()
    }
    logger.warning(json.dumps(log_entry))

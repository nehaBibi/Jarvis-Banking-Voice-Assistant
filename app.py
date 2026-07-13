"""
Jarvis Banking AI - Flask Backend
MVP application with mock authentication, BFS/A* agents, and core chat endpoints.
Integrates with MySQL database for real financing products.
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib
import time
import os
from datetime import datetime, timedelta
from functools import wraps

from agents import AgentManager
from utils.security import SecurityValidator
from utils.logging import setup_logging, log_request, log_chat_interaction, log_security_event
from utils.classifier import QueryClassifier
from utils.database import DatabaseConnection, init_database

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
app.config['JSON_SORT_KEYS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024  # 16KB max request
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
app.config['DEBUG'] = DEBUG

# Initialize logging
logger = setup_logging(app)

# Initialize Database
logger.info("Initializing database connection...")
if not init_database():
    logger.warning("⚠️  Database initialization failed. Some features may not work.")
else:
    logger.info("✅ Database ready")

# Initialize Agent Manager
agent_manager = AgentManager()
app.config['AGENT_MANAGER'] = agent_manager

# Simple in-memory token store (MVP only)
TOKEN_STORE = {}
TOKEN_EXPIRY_HOURS = 1

# ========== UTILITIES ==========

def _generate_token(user_id: str) -> str:
    """Generate mock JWT-like token (SHA256 hex)."""
    payload = f"{user_id}:{int(time.time())}"
    return hashlib.sha256(payload.encode()).hexdigest()

def _verify_token(token: str) -> tuple:
    """Verify token. Returns (is_valid, user_id)."""
    if token not in TOKEN_STORE:
        return False, None
    
    data = TOKEN_STORE[token]
    if datetime.utcnow() > data['expires']:
        del TOKEN_STORE[token]
        return False, None
    
    return True, data['user_id']

def _require_auth(f):
    """Decorator to require Bearer token."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            log_security_event(logger, 'auth_missing', 'anon', 'No Bearer token')
            return jsonify({"error": "Missing authorization header"}), 401
        
        token = auth_header.split(' ', 1)[1]
        is_valid, user_id = _verify_token(token)
        if not is_valid:
            log_security_event(logger, 'auth_invalid', 'anon', f'Invalid token: {token[:8]}...')
            return jsonify({"error": "Invalid or expired token"}), 401
        
        # Pass user_id to the route
        kwargs['user_id'] = user_id
        kwargs['token'] = token
        return f(*args, **kwargs)
    
    return decorated_function

# ========== ROUTES ==========

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "uptime_s": int(time.time()),
        "agents": agent_manager.list_agents(),
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected"
    }), 200

@app.route('/auth', methods=['POST'])
def login():
    """Mock authentication endpoint."""
    try:
        data = request.get_json() or {}
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        log_request(logger, 'POST', '/auth', username)
        logger.info(f"Login attempt: username={username}")
        
        # Validate input
        is_valid, err_msg = SecurityValidator.validate_username(username)
        if not is_valid:
            logger.warning(f"Invalid username format: {username} - {err_msg}")
            log_security_event(logger, 'auth_invalid_username', username, err_msg)
            return jsonify({"error": f"Invalid username: {err_msg}"}), 400
        
        # MVP: Accept any password for demo user
        if not password:
            logger.warning(f"Empty password for user: {username}")
            log_security_event(logger, 'auth_empty_password', username, 'Empty password')
            return jsonify({"error": "Password required"}), 400
        
        # Generate token
        token = _generate_token(username)
        expires = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS)
        TOKEN_STORE[token] = {'user_id': username, 'expires': expires}
        
        logger.info(f"✅ User authenticated: {username}")
        
        return jsonify({
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": TOKEN_EXPIRY_HOURS * 3600,
            "user": {
                "id": username,
                "name": username.capitalize(),
                "role": "customer"
            }
        }), 200
    
    except Exception as e:
        logger.error(f"❌ Auth endpoint error: {str(e)}", exc_info=True)
        return jsonify({"error": "Authentication error"}), 500

@app.route('/chat', methods=['POST'])
@_require_auth
def chat(user_id, token):
    """Main chat endpoint with intelligent agent routing."""
    data = request.get_json() or {}
    user_message = data.get('message', '').strip()
    agent_override = data.get('agent', None)  # Optional agent switch
    session_id = data.get('session_id', 'default')
    
    log_request(logger, 'POST', '/chat', user_id)
    
    # Validate message
    is_valid, err_msg = SecurityValidator.validate_message(user_message)
    if not is_valid:
        log_security_event(logger, 'chat_invalid_input', user_id, err_msg)
        return jsonify({"error": err_msg}), 400
    
    # Sanitize message
    user_message = SecurityValidator.sanitize_message(user_message)
    
    try:
        # Classify query to determine appropriate agent
        query_type, intent, is_sensitive = QueryClassifier.classify(user_message)
        
        # Determine which agent to use
        if agent_override:
            # User explicitly requested an agent
            agent = agent_manager.get_agent(agent_override)
            logger.info(f"Using override agent: {agent_override}")
        elif query_type == "complex":
            # Complex query -> use A* (informed search)
            agent = agent_manager.get_agent("astar")
            logger.info(f"Complex query detected, routing to A* agent (intent: {intent})")
        else:
            # Simple query or unknown -> use BFS (uninformed search)
            agent = agent_manager.get_agent("bfs")
            logger.info(f"Simple query, routing to BFS agent (intent: {intent})")
        
        # Measure latency
        start_time = time.time()
        
        # Process message through agent
        context = {
            'user_token': token,
            'user_id': user_id,
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat(),
            'query_type': query_type,
            'intent': intent
        }
        agent_response = agent.handle(user_message, context)
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Log interaction
        log_chat_interaction(
            logger,
            user_id,
            user_message,
            agent.name,
            agent_response['reply'],
            latency_ms,
            agent_response.get('safe', True)
        )
        
        # Build response
        response = {
            "reply": agent_response['reply'],
            "agent": agent.name,
            "query_type": query_type,
            "intent": intent,
            "safe": agent_response.get('safe', True),
            "score": agent_response.get('score', 0.0),
            "metadata": {
                "session_id": session_id,
                "latency_ms": round(latency_ms, 2),
                "timestamp": datetime.utcnow().isoformat(),
                "routing": f"{query_type} -> {agent.name}"
            }
        }
        
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route('/agent/config', methods=['GET'])
@_require_auth
def agent_config(user_id, token):
    """Get available agents and current configuration."""
    return jsonify({
        "available_agents": agent_manager.list_agents(),
        "default_agent": agent_manager.default_agent,
        "description": "Agents: BFS (uninformed search) for simple queries, A* (informed search) for complex queries"
    }), 200

@app.route('/agent/config', methods=['POST'])
@_require_auth
def agent_config_update(user_id, token):
    """Update default agent (admin endpoint in prod)."""
    data = request.get_json() or {}
    agent_name = data.get('default_agent', '').strip()
    
    if not agent_name or agent_name not in agent_manager.list_agents():
        return jsonify({"error": f"Invalid agent: {agent_name}"}), 400
    
    agent_manager.set_default(agent_name)
    logger.info(f"Agent switched to: {agent_name} by {user_id}")
    
    return jsonify({
        "default_agent": agent_manager.default_agent,
        "message": f"Default agent set to {agent_name}"
    }), 200

# ========== ERROR HANDLERS ==========

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad request"}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500

# ========== MAIN ==========

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    logger.info(f"Starting Jarvis Banking AI backend on port {port}")
    logger.info("=" * 60)
    logger.info("System Features:")
    logger.info("  ✅ BFS Agent (Uninformed Search) - Simple queries")
    logger.info("  ✅ A* Agent (Informed Search) - Complex queries")
    logger.info("  ✅ Database Integration - Real financing products")
    logger.info("  ✅ Query Classification - Smart routing")
    logger.info("=" * 60)
    app.run(host='0.0.0.0', port=port, debug=DEBUG)

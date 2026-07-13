# Jarvis Banking AI - MVP Implementation

A secure, full-stack banking AI assistant with pluggable search agents, token-based authentication, and voice I/O.

## Project Structure

```
.
├── app.py                      # Flask backend entry point
├── requirements.txt            # Python dependencies
├── .env                        # Configuration (development)
├── index.html                  # Frontend (jQuery + HTML5)
├── agents/
│   ├── __init__.py            # AgentManager registry
│   ├── base.py                # Agent abstract base class
│   ├── bfs.py                 # BFS Agent (MVP, rule-based search)
│   └── astar.py               # A* Agent (skeleton, future)
├── routes/
│   ├── auth.py                # Authentication endpoints (embedded in app.py)
│   └── chat.py                # Chat endpoints (embedded in app.py)
└── utils/
    ├── __init__.py
    ├── security.py            # Input validation, sanitization
    └── logging.py             # Structured logging, observability
```

## Features

### MVP (Current)
✅ **Frontend**
  - HTML5 login screen with mock authentication
  - Real-time chat interface with typing support
  - Voice input/output (Web Speech API)
  - Light/dark theme toggle
  - Session persistence (localStorage)
  - Input XSS protection (HTML escaping)

✅ **Backend**
  - Flask REST API with CORS support
  - Mock JWT-like token authentication (2-hour expiry)
  - BFS Agent: rule-based intent matching for banking queries
  - Pluggable agent architecture for easy extension
  - Request validation and sanitization
  - Restricted topic detection (PII, account numbers, etc.)
  - Structured JSON logging with latency tracking
  - `/health`, `/auth`, `/chat`, `/agent/config` endpoints

✅ **Security**
  - Bearer token-based API authorization
  - Input length limits (2000 chars max)
  - XSS prevention (HTML entity escaping)
  - Safe default responses for restricted topics
  - No sensitive data stored client-side or logged
  - CORS configured

### Future Enhancements
🔄 **A* Agent Integration** - Goal-directed multi-step banking flows
🔄 **Real Authentication** - OAuth2/OIDC integration
🔄 **Database** - Persistent session and audit logs
🔄 **Rate Limiting** - Per-user/IP request throttling
🔄 **Metrics** - Prometheus `/metrics` endpoint
🔄 **Production TLS** - Docker + nginx reverse proxy

---

## Quick Start

### Prerequisites
- Python 3.8+
- pip
- Modern web browser (Chrome, Edge, Firefox)

### Local Development (Windows)

1. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

2. **Start the backend:**
   ```powershell
   python app.py
   ```
   Backend runs on `http://localhost:5000`

3. **Open frontend:**
   - Open `index.html` in your browser (or serve with `python -m http.server 8000`)
   - Navigate to `http://localhost:8000/index.html`

4. **Test login:**
   - Use any username/password (e.g., `demo` / `test`)
   - Click "Login"

5. **Send a message:**
   - Type: "What's my balance?"
   - Bot responds via BFS agent

---

## API Endpoints

### Authentication
**POST** `/auth`
- **Request:** `{ "username": "string", "password": "string" }`
- **Response:** `{ "access_token": "sha256_hex", "expires_in": 3600, "user": { "id", "name", "role" } }`
- **Status:** 200 (success), 400 (invalid input)

### Chat
**POST** `/chat`
- **Headers:** `Authorization: Bearer <token>`
- **Request:** 
  ```json
  {
    "message": "What's my balance?",
    "session_id": "optional_session_id",
    "agent": "bfs"  // or "astar"
  }
  ```
- **Response:**
  ```json
  {
    "reply": "Your account balance is PKR 25,430.",
    "agent": "bfs",
    "safe": true,
    "score": 0.85,
    "metadata": {
      "session_id": "...",
      "latency_ms": 12.5,
      "timestamp": "2026-05-16T..."
    }
  }
  ```
- **Status:** 200 (success), 400 (bad request), 401 (unauthorized), 500 (error)

### Agent Config
**GET** `/agent/config`
- **Headers:** `Authorization: Bearer <token>`
- **Response:** `{ "available_agents": ["bfs", "astar"], "default_agent": "bfs" }`

**POST** `/agent/config` (admin)
- **Headers:** `Authorization: Bearer <token>`
- **Request:** `{ "default_agent": "astar" }`
- **Response:** `{ "default_agent": "astar", "message": "..." }`

### Health
**GET** `/health`
- **Response:** `{ "status": "ok", "uptime_s": 1234, "agents": [...], "timestamp": "..." }`

---

## Agent Architecture

### BFS Agent (MVP)
- **Approach:** Uninformed breadth-first rule matching
- **Implementation:** Simple keyword-based intent router
- **Use Case:** MVP chatbot for common banking queries
- **Features:**
  - Safe/restricted topic detection
  - Intent scoring (0.5–0.85 confidence)
  - Fallback response for unknown queries

```python
# Example usage
agent = BFSAgent()
response = agent.handle("What's my balance?", context={"user_id": "demo"})
print(response["reply"])  # "Your account balance is PKR 25,430."
```

### A* Agent (Skeleton)
- **Approach:** Informed cost + heuristic search for multi-step tasks
- **Use Case:** Future goal-directed flows (e.g., loan applications, multi-step transfers)
- **Status:** Currently returns placeholder. Full implementation requires:
  - State graph modeling
  - Heuristic function design
  - Priority queue (open/closed sets)
  - Cost tracking and path reconstruction

---

## Data Flow

```
Client (Browser)
    ↓ (login)
[POST /auth] → Backend validates → Issues token → Stores in localStorage
    ↓ (send message)
[POST /chat + Bearer token] → Backend validates + sanitizes message
    ↓
AgentManager.get_agent(agent_name) → Select BFS or A*
    ↓
Agent.handle(message, context) → Process query
    ↓
Return response { reply, agent, safe, metadata }
    ↓
Client renders bot message + plays audio (TTS)
```

### Session Management (MVP)
- **Token Storage:** In-memory dict (server), localStorage (client)
- **Session ID:** Generated per conversation (not persisted)
- **Expiry:** 1 hour (TOKEN_EXPIRY_HOURS)
- **Next Steps:** Migrate to Redis/DB for multi-server deployments

### Logging
- **Format:** Structured JSON with timestamp, event type, user_id (pseudonymized)
- **Sensitive Data:** Message body NOT logged; message hash only
- **Security Events:** Auth failures, restricted queries logged at WARNING level

---

## Configuration

### Environment Variables (.env)
```bash
PORT=5000
DEBUG=True
FLASK_ENV=development
API_BASE_URL=http://localhost:5000
DEFAULT_AGENT=bfs
LOG_LEVEL=INFO
```

### Frontend Config (index.html)
- **API_BASE_URL:** Update for production
- **Session Storage:** Uses browser localStorage (6.to secure with httpOnly cookies in prod)

---

## Testing

### Manual Testing
1. **Login Flow:**
   - Clear localStorage: `localStorage.clear()`
   - Reload page, enter credentials, verify token stored

2. **Chat Flow:**
   - Test intent matching: "balance", "loan", "card", "transfer"
   - Test restricted topic: "my SSN is...", expect safe response
   - Check browser console for latency

3. **Voice I/O:**
   - Click microphone, speak: "What's my balance?"
   - Verify transcription in input field
   - Verify bot response is spoken aloud

4. **Agent Switching:**
   - Open DevTools console:
     ```javascript
     $.post('http://localhost:5000/agent/config', 
       JSON.stringify({default_agent: 'astar'}),
       {headers: {'Authorization': 'Bearer YOUR_TOKEN'}})
     ```
   - Send message, verify "astar" in response metadata

### Unit Tests (Example)
```python
# tests/test_bfs_agent.py
from agents.bfs import BFSAgent

def test_balance_intent():
    agent = BFSAgent()
    resp = agent.handle("What's my balance?", {})
    assert resp["safe"] == True
    assert "balance" in resp["reply"].lower()

def test_restricted_topic():
    agent = BFSAgent()
    resp = agent.handle("My SSN is 123-45-6789", {})
    assert resp["safe"] == False
    assert "sensitive" in resp["reply"].lower()
```

---

## Deployment

### Local Development
```powershell
# Terminal 1: Start backend
python app.py

# Terminal 2: Serve frontend (optional)
python -m http.server 8000
```

### Docker (Future)
Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

Build and run:
```bash
docker build -t jarvis-banking-ai .
docker run -p 5000:5000 -e DEBUG=False jarvis-banking-ai
```

### Production Deployment
1. **Backend:** Flask + Gunicorn behind nginx reverse proxy
2. **Frontend:** Static files served by CDN or nginx
3. **TLS:** Enable via reverse proxy (Let's Encrypt)
4. **Secrets:** Move token generation to secure key store
5. **Auth:** Integrate real OIDC provider
6. **Logging:** Ship logs to ELK or CloudWatch
7. **Rate Limiting:** Enable Flask-Limiter per IP/user

---

## API Security Checklist

- ✅ Input validation (length, type)
- ✅ XSS prevention (HTML entity escaping)
- ✅ Bearer token authentication
- ✅ CORS configured
- ✅ Restricted topic filtering
- ⚠️ Rate limiting (implement with Flask-Limiter)
- ⚠️ TLS in production (reverse proxy + Let's Encrypt)
- ⚠️ CSRF protection (add for state-changing endpoints)
- ⚠️ SQL injection (N/A for MVP, add when DB integrated)

---

## Troubleshooting

### "Connection refused" on chat send
- Ensure backend is running: `python app.py` in another terminal
- Check `API_BASE_URL` in `index.html` matches backend port

### CORS errors in browser console
- Backend already has `CORS()` enabled; verify origin is whitelisted

### Token expired (401 error)
- Tokens expire after 1 hour; log out and log back in

### Voice input not working
- Only supported in Chromium browsers (Chrome, Edge)
- Check microphone permissions

### Agent not switching
- Ensure agent name is valid: "bfs" or "astar"
- Check response metadata for agent used

---

## Future Roadmap

**Phase 2 (Week 3)**
- [ ] Implement A* agent with state graph for multi-step tasks
- [ ] Add Redis session store for stateless deployment
- [ ] Implement rate limiting (Flask-Limiter)
- [ ] Add Prometheus metrics endpoint

**Phase 3 (Week 4)**
- [ ] OAuth2/OIDC integration
- [ ] Database backend (PostgreSQL) for audit logs
- [ ] Admin dashboard for agent configuration
- [ ] Alert system for security events

**Phase 4 (Production)**
- [ ] Multi-region deployment (AWS, GCP, Azure)
- [ ] Advanced NLP agent (e.g., Hugging Face transformer)
- [ ] Real transaction simulation (sandbox APIs)
- [ ] Mobile app (React Native)

---

## Support & Contribution

For issues, bugs, or feature requests, please contact the development team or submit a pull request.

**Built with:** Flask, jQuery, HTML5, CSS3, Web Speech API

---

**Last Updated:** May 16, 2026  
**MVP Status:** ✅ Complete and ready for demo  
**Maintainer:** Jarvis Team

# Jarvis Banking AI - Quick Start Guide

## 🚀 Get Running in 5 Minutes

### Step 1: Install Dependencies (Windows PowerShell)
```powershell
pip install -r requirements.txt
```

### Step 2: Start Backend (Windows PowerShell - Terminal 1)
```powershell
python app.py
```
You should see:
```
Starting Jarvis Banking AI backend on port 5000
```

### Step 3: Open Frontend (Windows - Terminal 2 or Browser)
**Option A: Direct file access**
- Double-click `index.html` or open in your browser

**Option B: With local server**
```powershell
python -m http.server 8000
```
Then navigate to: `http://localhost:8000/index.html`

### Step 4: Test Login
1. **Username:** `demo` (or any text)
2. **Password:** `test` (or any text, MVP accepts any password)
3. Click **Login**

### Step 5: Send Your First Message
- Type: `What's my balance?`
- Click **Send** or press `Enter`
- Bot responds with: `Your account balance is PKR 25,430.`

---

## 🎤 Try Voice Features
1. Click the **🎤 microphone button**
2. Speak: "What's my loan rate?"
3. Your speech is transcribed and sent
4. Bot responds with spoken audio

---

## 🔐 Test Authentication

### Valid Intent Examples
- "What's my **balance**?" → Account balance info
- "Tell me about **loans**" → Loan options
- "**Card** services" → Card details
- "**Transfer** money" → Payment instructions
- "Hello" → Greeting response

### Restricted Topic Examples (Safety Check)
Try these - bot will return safe response:
- "My **SSN** is..." → ⚠️ Restricted (returns safe default)
- "My **PIN** is..." → ⚠️ Restricted
- "Account **number** is..." → ⚠️ Restricted

---

## 🧪 Run Tests
```powershell
python tests.py
```

Expected output:
```
==================================================
JARVIS BANKING AI - MVP TEST SUITE
==================================================

✅ test_bfs_agent_balance_intent PASSED
✅ test_bfs_agent_restricted_topic PASSED
✅ test_bfs_agent_fallback PASSED
✅ test_agent_manager_registration PASSED
✅ test_agent_manager_switching PASSED
✅ test_security_validate_message PASSED
✅ test_security_validate_username PASSED
✅ test_security_sanitize_message PASSED

==================================================
RESULTS: 8 passed, 0 failed
==================================================
```

---

## 🐳 Docker Deployment (Optional)

### Build & Run with Docker
```bash
# Build image
docker build -t jarvis-banking-ai .

# Run container
docker run -p 5000:5000 jarvis-banking-ai
```

### Docker Compose (Backend + Frontend + Nginx)
```bash
docker-compose up
```
Access at: `http://localhost`

---

## 📊 Check API Health
```bash
# From terminal
curl http://localhost:5000/health
```

Expected response:
```json
{
  "status": "ok",
  "uptime_s": 1234,
  "agents": ["bfs", "astar"],
  "timestamp": "2026-05-16T..."
}
```

---

## 🔧 Configure

### Backend Configuration (.env)
```bash
PORT=5000
DEBUG=True
DEFAULT_AGENT=bfs
LOG_LEVEL=INFO
```

### Frontend Configuration (index.html)
Find this line and update for production:
```javascript
const API_BASE_URL = 'http://localhost:5000';  // Change this for prod
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **"Connection refused" on chat** | Ensure `python app.py` is running in another terminal |
| **CORS errors in console** | Check both frontend & backend are running locally |
| **Voice not working** | Use Chrome/Edge (not Firefox). Allow microphone permission |
| **Login always fails** | Clear localStorage: `localStorage.clear()` in DevTools console |
| **Token expired (401 error)** | Log out and log back in (1-hour expiry) |

---

## 📝 Architecture Overview

```
┌─────────────┐                 ┌──────────────┐
│   Browser   │                 │   Server     │
│ (index.html)│ ──HTTP/CORS──→ │ (app.py)     │
│             │ ←─ JSON/Auth ─  │              │
└─────────────┘                 └──────────────┘
                                      ↓
                                 ┌────────────┐
                                 │ AgentMgr   │
                                 └────────────┘
                                  ↓         ↓
                            ┌──────┐    ┌──────┐
                            │ BFS  │    │ A*   │
                            │Agent │    │Agent │
                            └──────┘    └──────┘
```

---

## 📚 API Quick Reference

### Login
```bash
curl -X POST http://localhost:5000/auth \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"test"}'
```

### Send Message
```bash
curl -X POST http://localhost:5000/chat \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"message":"What is my balance?"}'
```

### Get Available Agents
```bash
curl -X GET http://localhost:5000/agent/config \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## ✨ Next Steps

1. **Customize responses:** Edit `agents/bfs.py` - INTENT_MAP and RESTRICTED_KEYWORDS
2. **Add new agent:** Create `agents/custom_agent.py` extending `Agent` base class
3. **Connect real backend:** Replace mock responses with actual banking APIs
4. **Add database:** Store conversations, audit logs, user profiles
5. **Deploy to cloud:** Docker → Kubernetes, AWS ECS, Google Cloud Run, etc.

---

## 📖 Documentation

- **README.md** - Comprehensive project guide
- **agents/base.py** - Agent interface and architecture
- **utils/security.py** - Input validation rules
- **app.py** - REST API endpoints

---

**Built in 2 weeks. MVP ready for demo. 🎉**

Need help? Check the README.md or run `python tests.py`

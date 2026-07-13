# Production-Grade Refactor & Stabilization Plan
## Jarvis Banking AI - Flask Backend Architecture

---

## 1. ROOT CAUSE DIAGNOSIS: Login/Auth Instability

### Problem Statement
Login and authentication fail when the Flask app is not actively running (`python app.py`). Frontend shows "Invalid or expired token" errors on restart.

### Root Causes

#### 1.1 In-Memory Token Storage (Critical)
**Issue**: `TOKEN_STORE = {}` is a Python dictionary stored in app memory.
- **Impact**: Lost on every app restart
- **Symptom**: All sessions invalidated after `python app.py` stops/restarts
- **Location**: `app.py` line ~28

**Why It Fails**:
```
Session lifecycle:
1. User logs in → token stored in TOKEN_STORE (RAM)
2. User refreshes browser → token still valid (RAM persists)
3. Developer stops app or it crashes → TOKEN_STORE erased
4. App restarts → TOKEN_STORE = {} (empty)
5. User's saved token now invalid → 401 Unauthorized
```

#### 1.2 Missing App Context Initialization
**Issue**: Flask app context not properly managed across requests.
- **Current**: App initialized inline in `app.py`
- **Problem**: No factory pattern → difficult to create multiple app instances for testing/deployment
- **Impact**: Impossible to isolate state, test independently, or run multiple workers

#### 1.3 Startup Sequencing Issues
**Issue**: Dependencies initialized in arbitrary order:
```python
# Current problematic order:
app = Flask(__name__)
CORS(app)  # No error handling
logger = setup_logging(app)  # Logger created after app
init_database()  # DB connection fails silently
agent_manager = AgentManager()  # Initialized after DB may have failed
```

**Problems**:
- If DB init fails, app still starts (silently using mock data)
- Logger not ready when early errors occur
- No health check for dependencies
- Agents initialized without verifying dependencies

#### 1.4 Session Persistence Not Designed
**Current**: Tokens are short-lived (1 hour) and memory-only
- No server-side session store (Redis/Database)
- No signed cookies for client-side fallback
- No session refresh/renewal mechanism
- Users lose auth on any restart

#### 1.5 Environment & Configuration Issues
**Issue**: Hardcoded values and inconsistent env var handling.
```python
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'  # Fragile parsing
PORT = int(os.getenv('PORT', 5000))  # Could fail if non-integer
DB_HOST = os.getenv('DB_HOST', 'localhost')  # Default works but not obvious
```

**Impact**: Different behavior in dev/staging/prod without explicit config

### Summary of Instability Causes
1. **Stateless auth tokens stored in memory** → lost on restart
2. **No app factory pattern** → difficult to manage initialization
3. **Monolithic initialization** → no dependency isolation
4. **No session storage backend** → can't persist across restarts
5. **Weak configuration management** → inconsistent env handling

---

## 2. PRODUCTION ARCHITECTURE

### 2.1 Architecture Principles
- **App Factory Pattern**: Create Flask app via `create_app()` function
- **Modular Blueprints**: Separate routes by domain (auth, chat, health, admin)
- **Service Layer**: Business logic decoupled from routes
- **Dependency Injection**: Loose coupling between components
- **Configuration Hierarchy**: Dev < Staging < Production
- **Session Persistence**: Redis/Database-backed sessions
- **Health Checks**: Startup validation of all dependencies

### 2.2 High-Level Architecture Diagram
```
┌─────────────────────────────────────────────────────────────┐
│                      NGINX (Reverse Proxy)                   │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                    Frontend (index.html)                     │
│     HTML5 Chat UI + Login + Voice I/O (localStorage)       │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/WebSocket
┌─────────────────────▼───────────────────────────────────────┐
│              Flask App (create_app factory)                  │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Config      │  │  Logger      │  │  Error       │       │
│  │  Manager     │  │  Middleware  │  │  Handlers    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │            Blueprints (Routes)                         │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │ │
│  │  │ Auth Routes  │  │ Chat Routes  │  │ Health     │  │ │
│  │  │ /auth        │  │ /chat        │  │ /health    │  │ │
│  │  │ /logout      │  │ /agent/cfg   │  │ /ready     │  │ │
│  │  └──────────────┘  └──────────────┘  └────────────┘  │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │            Service Layer                               │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │ │
│  │  │ Auth Service │  │ Chat Service │  │ Agent Mgr  │  │ │
│  │  │ (sessions)   │  │ (pipeline)   │  │ (routing)  │  │ │
│  │  └──────────────┘  └──────────────┘  └────────────┘  │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │            Data Layer                                  │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │ │
│  │  │ Database     │  │ Session      │  │ Cache      │  │ │
│  │  │ (MySQL)      │  │ Store        │  │ (Redis)    │  │ │
│  │  └──────────────┘  └──────────────┘  └────────────┘  │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### 2.3 Core Components

#### Config Manager (`config.py`)
```
Responsibilities:
- Load environment variables with validation
- Provide config objects for dev/staging/prod
- Set up logging levels, DB URLs, secret keys
- Initialize feature flags
```

#### App Factory (`app.py`)
```
Responsibilities:
- Create Flask app instance
- Initialize extensions (CORS, logging, error handlers)
- Register blueprints
- Set up dependency injection
- Perform startup validation
```

#### Database Module (`services/db.py`)
```
Responsibilities:
- Connection pooling
- Query execution with parameterization
- Transaction management
- Migration support
- Error handling & retries
```

#### Auth Service (`services/auth.py`)
```
Responsibilities:
- User login/logout
- Token generation (secure)
- Session management (Redis/DB-backed)
- CSRF token generation
- Password hashing (bcrypt)
```

#### Chat Pipeline (`services/chatbot.py`)
```
Responsibilities:
- Query Analyzer: Parse & classify user input
- Decision Engine: Select appropriate agent
- KB Access: Query database for context
- Response Generator: Format & return reply
- Async-safe error handling
```

#### Blueprints (`routes/`)
```
- auth.py: Login, logout, refresh token
- chat.py: Chat endpoint, agent config
- health.py: Health checks, readiness probes
- admin.py: (Future) Admin operations
```

---

## 3. DATABASE INTEGRATION

### 3.1 Connection Management
**Strategy**: Connection pooling with lifecycle management

**Key Features**:
- Max pool size: 10 connections
- Connection timeout: 5 seconds
- Retry logic with exponential backoff
- Automatic reconnection on lost connection
- Graceful shutdown (close all connections)

### 3.2 Query Safety
**All queries use parameterized statements (%):**
```python
cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
```

**Never concatenate user input**:
```python
query = f"SELECT * FROM products WHERE id = {product_id}"  # WRONG!
```

### 3.3 Transaction Management
```python
try:
    conn.begin()
    cursor.execute(query1)
    cursor.execute(query2)
    conn.commit()
except Exception as e:
    conn.rollback()
    raise
```

### 3.4 Migration Strategy
- **Tool**: Alembic (SQLAlchemy) or manual migration files
- **Location**: `migrations/` folder
- **Naming**: `001_create_users.sql`, `002_add_sessions_table.sql`
- **Execution**: Run on startup (via `migrate.py`)
- **Rollback**: Keep down migrations for reversal

### 3.5 Schema
```sql
-- Users table (if needed for real auth)
CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sessions table (for server-side session storage)
CREATE TABLE sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id INT,
    data JSON,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Chat history (audit trail)
CREATE TABLE chat_history (
    chat_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    user_message TEXT,
    agent_name VARCHAR(50),
    bot_response TEXT,
    query_type VARCHAR(50),
    intent VARCHAR(100),
    latency_ms FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products remain (existing)
CREATE TABLE financing_products (
    product_id INT PRIMARY KEY AUTO_INCREMENT,
    product_name VARCHAR(200),
    category VARCHAR(100),
    min_income INT,
    max_tenure_months INT,
    description TEXT,
    markup_type VARCHAR(50)
);
```

---

## 4. AUTHENTICATION & SESSION MANAGEMENT

### 4.1 Authentication Flow
```
1. User submits username/password (POST /auth/login)
   ↓
2. Validate input (length, format, special chars)
   ↓
3. Hash password + compare (bcrypt)
   ↓
4. If valid:
   - Generate secure session ID (uuid4)
   - Store in Redis/DB with expiry (24 hours)
   - Sign cookie with app secret (HttpOnly, Secure, SameSite)
   - Return access_token (for API) + refresh_token
   ↓
5. Client stores token (localStorage) + cookie (browser automatic)
   ↓
6. Future requests include Bearer token OR rely on signed cookie
```

### 4.2 Persistence Across Restarts
**Server-Side Session Store (Redis)**:
```python
SESSION_STORE = redis.Redis(host='localhost', port=6379)
SESSION_STORE.setex(session_id, 86400, json.dumps(user_data))  # 24h expiry
```

**Fallback: Database Session Store**:
```python
INSERT INTO sessions (session_id, user_id, data, expires_at)
VALUES (?, ?, ?, NOW() + INTERVAL 24 HOUR)
```

**Client: Signed Cookies**:
```python
response.set_cookie('session', signed_token, 
    max_age=86400,
    httponly=True,
    secure=True,
    samesite='Lax'
)
```

### 4.3 CSRF Protection
**Strategy**: Double-submit cookie + token in form header
```html
<form>
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
</form>
```

**JavaScript**:
```javascript
const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
fetch('/chat', {
    headers: { 'X-CSRFToken': csrfToken }
})
```

### 4.4 Protected Routes
**Decorator Pattern**:
```python
@auth_bp.route('/protected')
@require_auth()
def protected_endpoint(user_id):
    return jsonify({"user": user_id})
```

**Implementation**:
- Extract token from `Authorization: Bearer <token>` header
- Lookup session in Redis/DB
- Verify not expired
- Inject `user_id` into route kwargs

---

## 5. CHATBOT PIPELINE ARCHITECTURE

### 5.1 Pipeline Components

```
User Input
    ↓
┌─────────────────────────────────────┐
│ 1. Query Analyzer                   │
│  - Tokenize & normalize             │
│  - Detect language                  │
│  - Extract entities                 │
│  - Check length/format              │
└─────────────────┬───────────────────┘
                  ↓
┌─────────────────────────────────────┐
│ 2. Security Filter                  │
│  - Detect PII (SSN, account#, etc)  │
│  - Rate limit check                 │
│  - Blacklist check                  │
│  - XSS/injection detection          │
└─────────────────┬───────────────────┘
                  ↓
┌─────────────────────────────────────┐
│ 3. Query Classifier                 │
│  - Keyword matching                 │
│  - Intent extraction                │
│  - Complexity assessment            │
│  - Agent routing decision           │
└─────────────────┬───────────────────┘
                  ↓
         ┌────────┴─────────┐
         ↓                  ↓
    ┌─────────┐        ┌─────────┐
    │  BFS    │        │  A*     │
    │ Agent   │        │ Agent   │
    └────┬────┘        └────┬────┘
         │                  │
         └────────┬─────────┘
                  ↓
┌─────────────────────────────────────┐
│ 4. Knowledge Base Access            │
│  - Query database                   │
│  - Retrieve products                │
│  - Score matches                    │
│  - Cache results                    │
└─────────────────┬───────────────────┘
                  ↓
┌─────────────────────────────────────┐
│ 5. Response Generator               │
│  - Format answer                    │
│  - Add context/examples             │
│  - Include CTA (call-to-action)     │
│  - Sanitize output                  │
└─────────────────┬───────────────────┘
                  ↓
            Response
```

### 5.2 Agent Types (Informed vs Uninformed)

**BFS Agent (Uninformed Search)**:
- Uses keyword matching + simple rules
- No pre-calculation of optimal path
- Good for straightforward queries: "Tell me about car loans"
- Fast, predictable latency
- Lower context awareness

**A* Agent (Informed Search)**:
- Uses heuristics + cost estimation
- Calculates optimal product match
- Good for complex queries: "I need a loan, eligible for $100k, 5yr tenure"
- Slightly higher latency but smarter matching
- Multi-step reasoning

### 5.3 Async-Safe Implementation
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def handle_chat_async(query, user_id):
    executor = ThreadPoolExecutor(max_workers=5)
    loop = asyncio.get_event_loop()
    
    result = await loop.run_in_executor(
        executor,
        agent.handle,
        query,
        context
    )
    return result
```

### 5.4 Error Handling & Fallbacks
```python
try:
    response = agent.handle(query, context)
except DatabaseError:
    response = {
        "reply": "Database temporarily unavailable. Using cached data.",
        "safe": True,
        "fallback": True
    }
except TimeoutError:
    response = {
        "reply": "Processing took longer than expected. Please try again.",
        "safe": True,
        "timeout": True
    }
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    response = {
        "reply": "I encountered an unexpected error. Please contact support.",
        "safe": True,
        "error": True
    }
```

---

## 6. API ENDPOINTS & ERROR HANDLING

### 6.1 Endpoint Reference

**Health & Status**:
- `GET /health` - Basic health check
- `GET /ready` - Readiness probe (all deps ready?)
- `GET /live` - Liveness probe (still running?)

**Authentication**:
- `POST /auth/login` - Login (username/password)
- `POST /auth/logout` - Logout (invalidate session)
- `POST /auth/refresh` - Refresh expired token
- `POST /auth/csrf-token` - Get CSRF token for forms

**Chat**:
- `POST /chat` - Send message (requires auth)
- `GET /chat/history` - Get chat history (requires auth)
- `POST /chat/clear` - Clear session history

**Agent Configuration**:
- `GET /agent/config` - List available agents
- `POST /agent/config` - Switch default agent (admin only)

**Admin** (future):
- `GET /admin/stats` - Chat statistics
- `GET /admin/logs` - System logs
- `DELETE /admin/sessions/:id` - Force logout user

### 6.2 Response Format (Consistent)
```json
{
  "success": true,
  "data": {
    "key": "value"
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

**Error Response**:
```json
{
  "success": false,
  "error": {
    "code": "AUTH_INVALID_TOKEN",
    "message": "Token expired or invalid",
    "details": "Token expires at 2024-01-15T11:30:00Z"
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

### 6.3 Error Codes
```
1xx - Information
100 - OK (generic success)

2xx - Success
200 - OK
201 - Created
204 - No Content

4xx - Client Error
400 - Bad Request (validation failed)
401 - Unauthorized (missing/invalid token)
403 - Forbidden (insufficient permissions)
404 - Not Found
408 - Request Timeout
409 - Conflict (duplicate entry)
429 - Too Many Requests (rate limit)

5xx - Server Error
500 - Internal Server Error
502 - Bad Gateway (upstream service down)
503 - Service Unavailable
504 - Gateway Timeout
```

### 6.4 Error Handler Middleware
```python
@app.errorhandler(400)
def handle_bad_request(error):
    return error_response(400, "BAD_REQUEST", "Invalid request format")

@app.errorhandler(401)
def handle_unauthorized(error):
    return error_response(401, "AUTH_REQUIRED", "Authentication required")

@app.errorhandler(500)
def handle_internal_error(error):
    logger.error(f"Internal error: {error}")
    return error_response(500, "INTERNAL_ERROR", "Internal server error")
```

### 6.5 CORS & Security Headers
```python
CORS(app, 
    origins=["https://yourdomain.com"],
    methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["X-Request-ID"],
    supports_credentials=True,
    max_age=3600
)

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000'
    return response
```

### 6.7 Logging & Telemetry Hooks
```python
@app.before_request
def log_request_start():
    request.start_time = time.time()
    logger.info(f"→ {request.method} {request.path} from {request.remote_addr}")

@app.after_request
def log_request_end(response):
    duration_ms = (time.time() - request.start_time) * 1000
    logger.info(f"← {request.method} {request.path} {response.status_code} ({duration_ms:.0f}ms)")
    return response
```

---

## 7. TESTING STRATEGY

### 7.1 Testing Pyramid
```
        /\
       /  \  E2E Tests (5%)
      /────\
     /      \  Integration Tests (25%)
    /────────\
   /          \ Unit Tests (70%)
  /────────────\
```

### 7.2 Unit Tests
**Files**: `tests/unit/`

**Coverage Areas**:
- Config loading & validation
- Auth service (token generation, validation)
- Query classifier (intent detection)
- Database utilities (query building, safety)
- Security validators (input sanitization)
- Agent logic (BFS/A* heuristics)

**Example**:
```python
def test_auth_token_generation():
    token = auth_service.generate_token("user123")
    assert len(token) == 32
    assert token.isalnum()

def test_query_classifier_complex_intent():
    query_type, intent, safe = classifier.classify("I want to apply for a loan")
    assert query_type == "complex"
    assert intent == "loan_application"
```

### 7.3 Integration Tests
**Files**: `tests/integration/`

**Coverage Areas**:
- Auth flow (login → chat → logout)
- Chat pipeline (query → agent → response)
- Database operations (insert, update, select)
- Session persistence (restart simulation)
- Agent switching & config

**Example**:
```python
def test_login_and_chat_flow():
    client = app.test_client()
    
    # Login
    resp = client.post('/auth/login', json={'username': 'test', 'password': 'pass'})
    token = resp.json['data']['access_token']
    
    # Chat with token
    resp = client.post('/chat', 
        json={'message': 'Tell me about car loans'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    assert 'reply' in resp.json['data']
```

### 7.4 End-to-End Tests
**Files**: `tests/e2e/`

**Tools**: Selenium/Playwright

**Scenarios**:
- User login → chat → logout (full browser session)
- Chat persistence (refresh page, check history)
- Agent switching via UI
- Error handling (invalid inputs, timeout recovery)

**Example**:
```python
def test_full_user_session():
    driver = webdriver.Chrome()
    driver.get('http://localhost:5000')
    
    # Fill login
    driver.find_element(By.ID, 'username').send_keys('testuser')
    driver.find_element(By.ID, 'password').send_keys('password')
    driver.find_element(By.ID, 'loginBtn').click()
    
    # Wait for chat UI
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'chat-box')))
    
    # Send message
    driver.find_element(By.ID, 'messageInput').send_keys('Car loans?')
    driver.find_element(By.ID, 'sendBtn').click()
    
    # Verify response
    wait.until(EC.text_to_be_present_in_element((By.CLASS_NAME, 'bot'), 'Car'))
```

### 7.5 Test Data Strategy
**Fixtures** (`tests/fixtures/`):
```python
# test_users.json
[
    {"username": "testuser", "password": "testpass123", "role": "customer"},
    {"username": "admin", "password": "adminpass", "role": "admin"}
]

# test_queries.json
[
    {"query": "Tell me about car loans", "type": "simple", "intent": "loan_info"},
    {"query": "Apply for home financing", "type": "complex", "intent": "loan_application"}
]

# test_products.json
[
    {"name": "Car Financing", "category": "Auto", "min_income": 50000},
    {"name": "Home Financing", "category": "Housing", "min_income": 150000}
]
```

**Setup & Teardown**:
```python
@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        load_test_data()
        yield app
        db.session.remove()
        db.drop_all()
```

---

## 8. DEPLOYMENT GUIDANCE

### 8.1 Environment Variables
**Create `.env.example` and `.env` (git-ignored)**:
```env
# App
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=generate-with-secrets.token_urlsafe(32)
PORT=5000

# Database
DB_HOST=db.example.com
DB_PORT=3306
DB_USER=app_user
DB_PASSWORD=secure-password-here
DB_NAME=jarvis_ai_prod

# Session Store (Redis)
REDIS_URL=redis://cache.example.com:6379/0

# Security
CSRF_ENABLED=True
CORS_ORIGINS=https://app.example.com

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/jarvis/app.log

# Features
ENABLE_VOICE=True
AGENTS_MAX_LATENCY_MS=5000
```

### 8.2 Production Config
```python
class ProductionConfig:
    DEBUG = False
    TESTING = False
    JSON_SORT_KEYS = False
    LOGGER_LEVEL = logging.WARNING
    CACHE_TYPE = 'redis'
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
```

### 8.3 Logging Strategy
**Structured JSON Logging**:
```python
import json
import logging

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            'timestamp': record.created,
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        return json.dumps(log_obj)
```

**Outputs**:
- **Console**: INFO+ for terminal viewing
- **File**: ALL levels to `/var/log/jarvis/app.log`
- **CloudWatch/ELK**: Structured logs for analysis

### 8.4 Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=app.py
ENV FLASK_ENV=production

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

CMD ["gunicorn", "--workers=4", "--bind=0.0.0.0:5000", "--timeout=60", "app:app"]
```

**Docker Compose**:
```yaml
version: '3.8'
services:
  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root_secret
      MYSQL_DATABASE: jarvis_ai_prod

  cache:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  web:
    build: .
    ports:
      - "5000:5000"
    depends_on:
      - db
      - cache
    environment:
      DB_HOST: db
      REDIS_URL: redis://cache:6379
```

### 8.5 Kubernetes Deployment
**File**: `k8s/deployment.yaml`
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jarvis-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: jarvis-api
  template:
    metadata:
      labels:
        app: jarvis-api
    spec:
      containers:
      - name: app
        image: jarvis-api:latest
        ports:
        - containerPort: 5000
        env:
        - name: DB_HOST
          valueFrom:
            configMapKeyRef:
              name: jarvis-config
              key: db_host
        livenessProbe:
          httpGet:
            path: /live
            port: 5000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
```

---

## 9. MVP ROADMAP & PHASED DELIVERY

### Phase 1: Core Stability (Weeks 1-2)
**Goal**: Fix auth persistence, modularize architecture

**Deliverables**:
- ✅ App factory pattern (`create_app()`)
- ✅ Config manager (dev/staging/prod)
- ✅ Session persistence (Redis or DB)
- ✅ Dependency initialization with validation
- ✅ Unit tests for core services
- ✅ Docker setup

**Metrics**:
- Auth tokens survive app restart
- All dependencies health-checked on startup
- 100% of unit tests pass

---

### Phase 2: Modular Architecture (Weeks 3-4)
**Goal**: Separate concerns, introduce blueprints

**Deliverables**:
- ✅ Blueprint structure (auth, chat, health)
- ✅ Service layer abstraction
- ✅ Dependency injection setup
- ✅ Consistent error handling
- ✅ Integration tests

**Metrics**:
- Routes organized by domain
- Services testable in isolation
- Integration tests cover main flows

---

### Phase 3: Chatbot Pipeline Enhancement (Weeks 5-6)
**Goal**: Cleaner agent architecture, better response generation

**Deliverables**:
- ✅ Query Analyzer component
- ✅ Enhanced Security Filter
- ✅ Agent Decision Engine
- ✅ Knowledge Base Accessor
- ✅ Response Generator with CTA
- ✅ Async-safe implementation

**Metrics**:
- Agent latency < 1 second (p95)
- 95%+ query classification accuracy
- All responses sanitized

---

### Phase 4: Production Hardening (Weeks 7-8)
**Goal**: Security, logging, monitoring readiness

**Deliverables**:
- ✅ CSRF protection
- ✅ Rate limiting
- ✅ Comprehensive logging
- ✅ Error tracking (Sentry)
- ✅ Performance monitoring
- ✅ Security audit checklist

**Metrics**:
- OWASP Top 10 coverage
- Zero SQL injection vulnerabilities
- 99.9% uptime in staging

---

### Phase 5: Deployment & Docs (Weeks 9-10)
**Goal**: Production-ready, well-documented

**Deliverables**:
- ✅ Kubernetes deployment files
- ✅ CI/CD pipeline (GitHub Actions)
- ✅ Production runbooks
- ✅ API documentation (OpenAPI/Swagger)
- ✅ Troubleshooting guide
- ✅ On-call playbook

**Metrics**:
- Automated tests pass on every commit
- Deployment time < 5 minutes
- Recovery time objective (RTO) < 15 min

---

### Phase 6+: Optional Enhancements
- Voice input/output improvements
- Multi-language support
- Advanced NLP (Hugging Face models)
- Real ML-based agent (replace keyword matching)
- User preference learning
- Admin dashboard
- Analytics & reporting

---

## 10. IMPLEMENTATION CHECKLIST

### Pre-Implementation
- [ ] Review this document with team
- [ ] Set up Git repository with branch protection
- [ ] Configure CI/CD pipeline
- [ ] Create Jira epics for each phase

### Phase 1: Core Stability
- [ ] Create config.py with environment loading
- [ ] Implement create_app() factory function
- [ ] Set up session persistence (Redis or DB)
- [ ] Update database.py with connection pooling
- [ ] Add health check endpoints
- [ ] Write unit tests for core services
- [ ] Docker setup with compose

### Phase 2: Modular Architecture
- [ ] Refactor routes into blueprints (auth, chat)
- [ ] Create services/ directory with business logic
- [ ] Implement dependency injection
- [ ] Add middleware for error handling
- [ ] Write integration tests

### Phase 3: Chatbot Enhancement
- [ ] Split agent logic into pipeline stages
- [ ] Add Query Analyzer component
- [ ] Add Security Filter component
- [ ] Improve Response Generator
- [ ] Add async support

### Phase 4: Production Hardening
- [ ] Add CSRF token middleware
- [ ] Implement rate limiting
- [ ] Set up structured logging
- [ ] Add Sentry integration
- [ ] Security audit & penetration testing

### Phase 5: Deployment
- [ ] Create Kubernetes manifests
- [ ] Set up CI/CD (GitHub Actions / GitLab CI)
- [ ] Write deployment runbooks
- [ ] Create API documentation
- [ ] Set up monitoring/alerting

---

## 11. SUCCESS CRITERIA

**For Production Readiness**:
1. ✅ Auth tokens persist across restarts (verified by test)
2. ✅ All dependencies validated on startup (health check)
3. ✅ Zero in-memory-only state (all persisted)
4. ✅ 100% API endpoint test coverage
5. ✅ OWASP Top 10 vulnerabilities addressed
6. ✅ Comprehensive logging & monitoring
7. ✅ Deployment automated & repeatable
8. ✅ Architecture supports 1000+ concurrent users
9. ✅ Documentation complete & current
10. ✅ Runbook for all common issues

---

**Next Step**: See `REFACTORED_PROJECT_STRUCTURE.md` for detailed folder layout and code examples.

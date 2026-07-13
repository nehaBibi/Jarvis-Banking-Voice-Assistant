# Refactored Project Structure

## Directory Tree

```
jarvis-banking-ai/
│
├── .env                              # Environment variables (git-ignored)
├── .env.example                      # Example env template
├── .gitignore                        # Git ignore rules
├── .flaskenv                         # Flask-specific env
│
├── requirements.txt                  # Python dependencies
├── setup.py                          # Package setup (optional)
├── wsgi.py                           # WSGI entry point (Gunicorn)
│
├── config.py                         # Config manager (dev/staging/prod)
├── app.py                            # App factory & initialization
│
├── index.html                        # Frontend (unchanged)
│
├── app/
│   ├── __init__.py                   # Package init
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py                   # Auth endpoints (/auth/...)
│   │   ├── chat.py                   # Chat endpoints (/chat/...)
│   │   ├── health.py                 # Health endpoints (/health, /ready)
│   │   └── admin.py                  # Admin endpoints (future)
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth.py                   # Auth business logic
│   │   ├── chatbot.py                # Chatbot pipeline
│   │   ├── query_analyzer.py         # Query parsing & analysis
│   │   ├── decision_engine.py        # Agent routing logic
│   │   ├── kb_accessor.py            # Knowledge base queries
│   │   └── response_generator.py     # Response formatting
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py                   # User model (future)
│   │   ├── session.py                # Session model
│   │   └── chat_history.py           # Chat history model
│   │
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── error_handler.py          # Global error handling
│   │   ├── request_logger.py         # Request logging
│   │   └── auth_middleware.py        # Auth validation
│   │
│   └── utils/
│       ├── __init__.py
│       ├── security.py               # Input validation (improved)
│       ├── logging.py                # Structured logging
│       ├── database.py               # DB utilities (refactored)
│       ├── classifier.py             # Query classifier
│       ├── exceptions.py             # Custom exceptions
│       └── decorators.py             # Custom decorators (@require_auth, etc)
│
├── agents/                           # Agent system (unchanged structure)
│   ├── __init__.py
│   ├── base.py                       # Agent ABC
│   ├── bfs.py                        # BFS agent (refactored)
│   ├── astar.py                      # A* agent (refactored)
│   └── manager.py                    # Agent manager
│
├── database/
│   ├── __init__.py
│   ├── connection.py                 # Connection pool management
│   ├── migrations.py                 # Migration runner
│   │
│   └── migrations/
│       ├── 001_init_schema.sql
│       ├── 002_add_sessions_table.sql
│       ├── 003_add_chat_history.sql
│       └── seed_products.sql
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                   # Pytest fixtures
│   │
│   ├── unit/
│   │   ├── test_auth_service.py
│   │   ├── test_query_classifier.py
│   │   ├── test_security.py
│   │   ├── test_agents.py
│   │   └── test_database.py
│   │
│   ├── integration/
│   │   ├── test_auth_flow.py
│   │   ├── test_chat_flow.py
│   │   ├── test_agent_routing.py
│   │   └── test_session_persistence.py
│   │
│   ├── e2e/
│   │   └── test_full_session.py
│   │
│   └── fixtures/
│       ├── test_users.json
│       ├── test_queries.json
│       └── test_products.json
│
├── logs/                             # Log output directory
│   └── app.log
│
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── nginx.conf
│
├── k8s/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── configmap.yaml
│   └── secret.yaml
│
├── scripts/
│   ├── migrate.py                    # Run database migrations
│   ├── seed_db.py                    # Load test/seed data
│   ├── init_redis.py                 # Initialize Redis (if used)
│   └── generate_secret.py            # Generate SECRET_KEY
│
├── PRODUCTION_REFACTOR_PLAN.md       # Architecture & design decisions
├── REFACTORED_PROJECT_STRUCTURE.md   # This file
├── API_REFERENCE.md                  # OpenAPI/Swagger equivalent
├── DEPLOYMENT_GUIDE.md               # Production deployment steps
├── TESTING_GUIDE.md                  # How to run tests
├── TROUBLESHOOTING.md                # Common issues & solutions
└── README.md                         # Overview & quick start
```

---

## Key Files Explained

### Root Level

#### `config.py`
Centralized configuration management for dev/staging/prod.

**Responsibilities**:
- Load `.env` variables with defaults
- Create config objects for each environment
- Validate critical settings on load
- Provide config to app factory

**Example**:
```python
import os
from datetime import timedelta

class Config:
    """Base config"""
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-CHANGE-ME')
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}
```

#### `app.py`
App factory function—creates and initializes Flask app.

**Responsibilities**:
- Create Flask instance
- Register blueprints
- Initialize extensions (CORS, logging)
- Set up middleware & error handlers
- Perform startup validation

**Example**:
```python
from flask import Flask
from flask_cors import CORS
from config import config

def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Register blueprints
    from app.routes import auth_bp, chat_bp, health_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(health_bp)
    
    # Setup error handlers
    setup_error_handlers(app)
    
    # Validate startup
    validate_startup(app)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000)
```

#### `wsgi.py`
Entry point for production WSGI servers (Gunicorn).

```python
from app import create_app

app = create_app('production')

if __name__ == "__main__":
    app.run()
```

---

### app/routes

#### `auth.py`
Authentication endpoints.

**Endpoints**:
- `POST /auth/login` - Login with username/password
- `POST /auth/logout` - Logout (invalidate session)
- `POST /auth/refresh` - Refresh expired token
- `GET /auth/me` - Get current user info

**Key Features**:
- Input validation (length, format)
- Password hashing (bcrypt)
- Session creation & persistence
- CSRF token generation

---

#### `chat.py`
Chat endpoints.

**Endpoints**:
- `POST /chat` - Send message (requires auth)
- `GET /chat/history` - Get user's chat history
- `DELETE /chat/history` - Clear chat history
- `GET /agent/config` - List available agents
- `POST /agent/config` - Switch default agent

**Key Features**:
- Auth middleware verification
- Query classification & routing
- Agent invocation
- Response formatting
- Latency tracking

---

#### `health.py`
Health & readiness endpoints.

**Endpoints**:
- `GET /health` - Basic health check (is app running?)
- `GET /ready` - Readiness probe (all dependencies ready?)
- `GET /live` - Liveness probe (still responsive?)

**Key Features**:
- Dependency validation
- Database connectivity check
- Cache (Redis) check
- Return appropriate HTTP status

---

### app/services

#### `auth.py`
Authentication service—business logic for auth operations.

**Methods**:
- `login(username, password)` - Authenticate user, create session
- `logout(session_id)` - Invalidate session
- `refresh_token(token)` - Renew expired token
- `verify_token(token)` - Check if token valid
- `generate_session_id()` - Create secure session ID

**Key Features**:
- Password hashing (bcrypt)
- Session store (Redis or DB)
- Token signing
- CSRF token generation

---

#### `chatbot.py`
Chatbot pipeline orchestration.

**Methods**:
- `process_message(query, user_id)` - Main entry point
- `analyze_security(query)` - Filter PII/sensitive content
- `classify_query(query)` - Determine intent
- `route_to_agent(query_type)` - Select appropriate agent
- `generate_response(agent_output)` - Format response

**Key Features**:
- Async-safe implementation
- Error handling & fallbacks
- Latency tracking
- Logging & telemetry

---

#### `query_analyzer.py`
Parse and normalize user queries.

**Methods**:
- `tokenize(query)` - Split into tokens
- `normalize(query)` - Lowercase, remove extra whitespace
- `extract_entities(query)` - Find product names, amounts, etc.
- `detect_language(query)` - Language detection

---

#### `decision_engine.py`
Select appropriate agent based on query.

**Methods**:
- `decide_agent(query_type, intent)` - Return agent name
- `get_confidence_score(query, intent)` - Confidence 0-1

**Logic**:
```
IF query_type == "complex":
    ROUTE TO "astar" (informed search)
ELIF query_type == "simple":
    ROUTE TO "bfs" (uninformed search)
ELSE:
    ROUTE TO default_agent
```

---

#### `kb_accessor.py`
Query knowledge base (database) for context.

**Methods**:
- `search_products(search_term)` - Find products
- `get_product_details(product_id)` - Get full details
- `search_by_category(category)` - Filter by type
- `find_eligible_products(user_income)` - Eligibility matching

**Key Features**:
- Database query execution
- Result caching
- Error handling & fallback to mock data

---

#### `response_generator.py`
Format final response for user.

**Methods**:
- `format_product_info(product)` - Format product details
- `add_call_to_action(response)` - Add "How to apply?" link
- `sanitize_output(response)` - Remove HTML, XSS
- `add_metadata(response, latency)` - Add tracing info

---

### app/utils

#### `database.py` (Refactored)
Database utilities—connection pooling, query execution, migrations.

**Classes**:
- `DatabasePool` - Connection pooling with lifecycle
- `QueryBuilder` - Safe parameterized queries
- `Migration` - Migration runner

**Key Features**:
- Connection pooling (max 10)
- Automatic reconnect on lost connection
- Parameterized queries (safety)
- Transaction support (begin/commit/rollback)
- Connection cleanup on shutdown

**Example**:
```python
from app.utils.database import DatabasePool

pool = DatabasePool()

# Safe query
result = pool.execute(
    "SELECT * FROM products WHERE category = %s",
    ("Auto Financing",),
    fetch_one=False
)

# Transaction
with pool.transaction():
    pool.execute("INSERT INTO sessions ...")
    pool.execute("UPDATE users ...")
```

---

#### `security.py` (Improved)
Input validation and sanitization.

**Methods**:
- `validate_username(username)` - Check format
- `validate_message(message)` - Length, special chars
- `validate_email(email)` - Email format
- `sanitize_message(message)` - Remove control chars
- `sanitize_html(html)` - XSS prevention
- `check_pii(message)` - Detect sensitive data

**Example**:
```python
from app.utils.security import SecurityValidator

is_valid, error = SecurityValidator.validate_message(user_input)
if not is_valid:
    return {"error": error}, 400

sanitized = SecurityValidator.sanitize_message(user_input)
```

---

#### `decorators.py`
Custom decorators for routes.

**Decorators**:
- `@require_auth()` - Verify Bearer token
- `@admin_only()` - Admin permission check
- `@rate_limit(calls=100, period=3600)` - Rate limiting
- `@log_request()` - Auto log incoming request
- `@handle_errors()` - Catch & format exceptions

**Example**:
```python
from app.utils.decorators import require_auth, rate_limit

@app.route('/protected')
@require_auth()
@rate_limit(calls=100, period=3600)
def protected(user_id):
    return {"user": user_id}
```

---

### database/

#### `connection.py`
Connection pool management.

**Class**: `DatabasePool`

**Responsibilities**:
- Create/destroy connections
- Maintain pool of reusable connections
- Auto-reconnect on lost connection
- Clean up on app shutdown

**Example**:
```python
from database.connection import DatabasePool

pool = DatabasePool(
    host='localhost',
    user='root',
    password='secret',
    database='jarvis_ai',
    pool_size=10,
    pool_name='jarvis_pool'
)

conn = pool.get_connection()
cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT * FROM products")
result = cursor.fetchall()
pool.return_connection(conn)
```

---

#### `migrations/`
SQL migration files for schema versioning.

**File naming**: `NNN_description.sql` (e.g., `001_init_schema.sql`)

**Pattern**:
```sql
-- 001_init_schema.sql
-- Create initial schema

CREATE TABLE IF NOT EXISTS users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id INT,
    data JSON,
    expires_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS chat_history (
    chat_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    user_message TEXT,
    bot_response TEXT,
    intent VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Migration status
INSERT INTO migrations (migration_name, executed_at) VALUES ('001_init_schema', NOW());
```

**How migrations work**:
```python
from database.migrations import MigrationRunner

runner = MigrationRunner('database/migrations')
runner.run_pending_migrations()  # Runs 001, 002, 003... (skips already run)
```

---

### tests/

#### `conftest.py`
Pytest configuration & shared fixtures.

```python
import pytest
from app import create_app
from database.connection import DatabasePool

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        yield app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def db():
    pool = DatabasePool()
    yield pool
    pool.close_all()

@pytest.fixture
def test_user(db):
    # Create test user in DB
    ...
    yield user
    # Clean up
    ...
```

---

#### Unit Tests (`test_*.py`)
Test individual functions in isolation.

**Examples**:
- `test_auth_service.py` - Test login, token generation, validation
- `test_query_classifier.py` - Test intent classification
- `test_security.py` - Test input validation & sanitization
- `test_agents.py` - Test BFS/A* agent logic
- `test_database.py` - Test query execution, pooling

**Example Test**:
```python
def test_validate_message_too_long(self):
    long_msg = "x" * 3000
    is_valid, error = SecurityValidator.validate_message(long_msg)
    assert not is_valid
    assert "exceeds" in error
```

---

#### Integration Tests
Test multiple components working together.

**Examples**:
- `test_auth_flow.py` - Login → Token → Protected route → Logout
- `test_chat_flow.py` - Login → Send message → Get response
- `test_agent_routing.py` - Query classification → Agent selection
- `test_session_persistence.py` - Create session → Verify survives restart

**Example**:
```python
def test_full_chat_flow(client):
    # Login
    resp = client.post('/auth/login', json={'username': 'test', 'password': 'pass'})
    token = resp.json['data']['access_token']
    
    # Chat
    resp = client.post('/chat',
        json={'message': 'Car loans?'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    assert 'reply' in resp.json['data']
```

---

### docker/

#### `docker-compose.yml`
Orchestration for local development & testing.

```yaml
version: '3.8'
services:
  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: jarvis_ai_test

  cache:
    image: redis:7-alpine

  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      FLASK_ENV: development
      DB_HOST: db
      REDIS_URL: redis://cache:6379
    depends_on:
      - db
      - cache
```

---

### scripts/

#### `migrate.py`
Run database migrations.

```python
from database.migrations import MigrationRunner

runner = MigrationRunner('database/migrations')
runner.run_pending_migrations()
print("Migrations complete!")
```

**Usage**: `python scripts/migrate.py`

---

#### `seed_db.py`
Load seed/test data into database.

```python
from database.connection import DatabasePool

pool = DatabasePool()

products = [
    ('Car Financing', 'Auto', 50000, 60),
    ('Home Financing', 'Housing', 150000, 360),
]

for name, category, min_income, tenure in products:
    pool.execute(
        "INSERT INTO financing_products (product_name, category, min_income, max_tenure_months) VALUES (%s, %s, %s, %s)",
        (name, category, min_income, tenure)
    )

print("Seed data loaded!")
```

**Usage**: `python scripts/seed_db.py`

---

## Migration Checklist

**Step 1**: Create new structure (leave old app.py for reference)

```
Old: app.py (single file)
New: app.py + app/ + config.py
```

**Step 2**: Move code incrementally
- Move routes → `app/routes/`
- Move utilities → `app/utils/`
- Move services → `app/services/`

**Step 3**: Update imports
- In routes: `from app.services import ...`
- In services: `from app.utils import ...`
- In app.py: `from app.routes import ...`

**Step 4**: Test each phase
- Run unit tests after each module move
- Run integration tests after all routes moved
- Run full E2E test suite

**Step 5**: Deploy
- Update `wsgi.py` to point to new `create_app()`
- Update `.env` with new config keys
- Run migrations on production DB
- Deploy with monitoring

---

## Quick Start (New Structure)

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Generate SECRET_KEY
python scripts/generate_secret.py

# Initialize database
python scripts/migrate.py
python scripts/seed_db.py

# Run tests
pytest tests/unit/
pytest tests/integration/

# Run app (development)
python app.py

# Run app (production with Gunicorn)
gunicorn --workers=4 wsgi:app
```

---

**Next Step**: See specific module files in the codebase for implementation details.

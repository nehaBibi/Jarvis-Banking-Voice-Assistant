# Troubleshooting Guide - Jarvis Banking AI

## Common Issues & Solutions

---

## Authentication Issues

### Problem: "Invalid or expired token" After App Restart

**Symptoms**:
- User logged in, app restarted
- Old token now returns 401 Unauthorized
- User forced to login again

**Root Causes**:
1. Using in-memory token store (lost on restart)
2. Session not persisted to Redis/Database
3. Session expiry too short

**Solutions**:

**Option 1: Check Session Store Configuration**
```python
from app.services.auth import AuthService

store = AuthService._get_session_store()
if store is None:
    print("❌ Session store not configured (using in-memory)")
else:
    print("✅ Session store active:", type(store))
```

**Option 2: Enable Redis Session Storage**
```env
REDIS_URL=redis://localhost:6379/0
```

Verify Redis is running:
```bash
redis-cli ping
# Expected: PONG
```

**Option 3: Use Database Session Storage**
```python
# In AuthService.login():
result = AuthService.login('user', 'pass')
token = result['token']

# Insert into database
pool.execute(
    "INSERT INTO sessions (session_id, user_id, token, expires_at) VALUES (%s, %s, %s, %s)",
    (result['session_id'], 'user', token, datetime.utcnow() + timedelta(hours=24))
)
```

**Verification**:
```bash
# 1. Login
TOKEN=$(curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"pass"}' \
  | jq -r '.data.access_token')

# 2. Restart app
# (Stop & start python app.py)

# 3. Try request with same token
curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/chat/history

# Expected: 200 OK (not 401)
```

---

### Problem: "Missing authorization header"

**Symptoms**:
```
{
  "error": {
    "code": "AUTH_REQUIRED",
    "message": "Missing authorization header"
  }
}
```

**Root Causes**:
1. Client not sending Authorization header
2. Header malformed (not "Bearer <token>")
3. Token missing/empty

**Solution**:

Check client code:
```javascript
// ❌ WRONG - no Authorization header
fetch('/chat', {
    method: 'POST',
    body: JSON.stringify({message: 'test'})
});

// ✅ CORRECT - includes Bearer token
fetch('/chat', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({message: 'test'})
});
```

**Curl Example**:
```bash
curl -H "Authorization: Bearer abc123..." http://localhost:5000/chat
```

---

## Database Connection Issues

### Problem: "Database connection failed" / Mock Data Fallback

**Symptoms**:
```
⚠️  Database pool initialization failed: ...
📋 Using mock database fallback
```

**Root Causes**:
1. MySQL not running
2. Wrong hostname/port
3. Wrong credentials
4. Database doesn't exist

**Solutions**:

**Step 1: Verify MySQL Running**
```bash
# Check if MySQL process running
ps aux | grep mysql

# Or check port 3306 listening
netstat -tlnp | grep 3306

# Or try connecting
mysql -u root -p -e "SELECT 1"
```

**Step 2: Check .env Configuration**
```env
DB_HOST=localhost        # Check hostname
DB_PORT=3306            # Check port
DB_USER=root            # Check username
DB_PASSWORD=            # Check password
DB_NAME=jarvis_ai_banking  # Check database name exists
```

**Step 3: Create Database**
```bash
mysql -u root -p -e "CREATE DATABASE jarvis_ai_banking;"

python scripts/migrate.py    # Create tables
python scripts/seed_db.py    # Add sample data
```

**Step 4: Verify Connection**
```bash
# Using Python
python -c "
from app.utils.database import get_pool
pool = get_pool()
print('Mock mode:', pool._is_mock)
result = pool.execute('SELECT 1')
print('Connection working:', result is not None)
"
```

---

### Problem: "No such table: financing_products"

**Symptoms**:
```
Error 1146: Table 'jarvis_ai_banking.financing_products' doesn't exist
```

**Solution**: Run migrations

```bash
python scripts/migrate.py

# Or manually
mysql -u root -p jarvis_ai_banking < database/migrations/001_init_schema.sql
```

---

## Chat Endpoint Issues

### Problem: Chat Returns 500 Internal Error

**Symptoms**:
```json
{
  "success": false,
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Chat processing failed"
  }
}
```

**Root Causes**:
1. Agent module import error
2. Database query failed
3. Unhandled exception in agent

**Solutions**:

**Step 1: Check Logs**
```bash
# View recent logs
tail -50 logs/app.log

# Or in Kubernetes
kubectl logs -l app=jarvis-api --tail=100
```

**Step 2: Check Agent Manager**
```python
from agents import AgentManager

manager = AgentManager()
print("Available agents:", manager.list_agents())

agent = manager.get_agent('bfs')
print("BFS agent loaded:", agent is not None)

response = agent.handle("Car loans", {'user_id': 'test'})
print("Agent response:", response)
```

**Step 3: Test Query Classifier**
```python
from utils.classifier import QueryClassifier

query_type, intent, safe = QueryClassifier.classify("Car loans")
print(f"Query type: {query_type}, Intent: {intent}, Safe: {safe}")
```

**Step 4: Check Database Connection**
```python
from app.utils.database import get_pool

pool = get_pool()
products = pool.execute("SELECT * FROM financing_products")
print(f"Products found: {len(products) if products else 0}")
```

---

### Problem: Chat Response Very Slow (> 5 seconds)

**Symptoms**:
- Chat request times out
- Latency_ms in response > 5000

**Root Causes**:
1. Database query slow
2. Agent heuristic calculation expensive
3. Network latency to external service

**Solutions**:

**Step 1: Check Database Query Performance**
```bash
# MySQL query profiling
mysql -u root -p jarvis_ai_banking -e "
SET profiling = 1;
SELECT * FROM financing_products;
SHOW PROFILE;
"
```

**Step 2: Check Agent Performance**
```python
import time

agent = AgentManager().get_agent('astar')

start = time.time()
response = agent.handle("Apply for a loan", {'user_id': 'test'})
duration = time.time() - start

print(f"Agent response time: {duration*1000:.0f}ms")
```

**Step 3: Add Indexes (if slow queries)**
```sql
CREATE INDEX idx_product_category ON financing_products(category);
CREATE INDEX idx_chat_history_user ON chat_history(user_id, created_at);
```

**Step 4: Increase Agent Max Latency**
```env
AGENTS_MAX_LATENCY_MS=10000  # Increase from 5000
```

---

## Deployment Issues

### Problem: Docker Container Won't Start

**Symptoms**:
```
docker: Error response from daemon: OCI runtime create failed: ...
```

**Solutions**:

**Step 1: Check Logs**
```bash
docker logs <container-id>

# Full error output
docker run -it jarvis-api:latest /bin/bash
```

**Step 2: Verify Image Layers**
```bash
docker history jarvis-api:latest

docker inspect jarvis-api:latest
```

**Step 3: Check Python Environment**
```bash
docker run -it jarvis-api:latest python --version

docker run -it jarvis-api:latest pip list | grep Flask
```

---

### Problem: Kubernetes Pod CrashLoopBackOff

**Symptoms**:
```
STATUS: CrashLoopBackOff
RESTARTS: 5 (0-1 second ago)
```

**Solutions**:

**Step 1: Check Pod Logs**
```bash
kubectl logs <pod-name>

kubectl logs <pod-name> --previous  # Previous crash
```

**Step 2: Check Pod Events**
```bash
kubectl describe pod <pod-name>

# Look for "Events:" section
```

**Step 3: Check Resource Limits**
```bash
kubectl describe pod <pod-name> | grep -A5 "Limits"

# If memory exceeded, increase in deployment.yaml
```

**Step 4: Debug with Interactive Shell**
```bash
kubectl run -it debug --image=jarvis-api:latest -- /bin/bash

# Inside container
python -c "from app import create_app; app = create_app(); print('OK')"
```

---

### Problem: Pods Pending (Not Starting)

**Symptoms**:
```
STATUS: Pending
REASON: Insufficient resources
```

**Solution**: Scale down or provision more cluster resources

```bash
kubectl get nodes

kubectl describe node <node-name>  # See available resources

# Add more nodes or reduce replicas
kubectl scale deployment jarvis-api --replicas=1
```

---

## Performance Issues

### Problem: High Memory Usage

**Symptoms**:
```
Memory limit exceeded (limits: 1Gi)
Pod killed by Kubernetes
```

**Solutions**:

**Step 1: Profile Memory**
```bash
docker run --memory=512m jarvis-api:latest python app.py

# Check swap usage
free -h
```

**Step 2: Check for Memory Leaks**
```python
import tracemalloc

tracemalloc.start()

# Run your code

current, peak = tracemalloc.get_traced_memory()
print(f"Current: {current/1024/1024:.1f}MB")
print(f"Peak: {peak/1024/1024:.1f}MB")
```

**Step 3: Increase Memory Limit**
```yaml
# In k8s/deployment.yaml
resources:
  limits:
    memory: 2Gi  # Increase from 1Gi
```

---

### Problem: High CPU Usage

**Symptoms**:
```
CPU: 500m (50% of 1000m limit)
Throttling: Yes
```

**Solutions**:

**Step 1: Profile CPU**
```bash
docker run --cpus="1.0" jarvis-api:latest python -m cProfile app.py
```

**Step 2: Check Agent Performance**
```python
import cProfile
import pstats

pr = cProfile.Profile()
pr.enable()

# Run agent
agent.handle("query", {})

pr.disable()
ps = pstats.Stats(pr)
ps.sort_stats('cumulative').print_stats(20)
```

**Step 3: Scale Horizontally**
```bash
kubectl scale deployment jarvis-api --replicas=5
```

---

## Security Issues

### Problem: SQL Injection Attempt Detected

**Symptoms**:
```
✗ Input validation failed: suspicious characters detected
```

**Verification**:
```bash
curl -X POST http://localhost:5000/chat \
  -H "Authorization: Bearer token..." \
  -H "Content-Type: application/json" \
  -d '{"message": "test\" OR \"1\"=\"1"}'

# Expected: validation error
```

**Good - parameterized query**:
```python
cursor.execute("SELECT * FROM products WHERE name = %s", (user_input,))
```

**Bad - concatenation (vulnerable)**:
```python
cursor.execute(f"SELECT * FROM products WHERE name = '{user_input}'")
```

---

### Problem: XSS Vulnerability

**Symptoms**:
```javascript
// Attacker sends:
<script>alert('xss')</script>

// App stores and returns it unescaped
<div class="bot">&lt;script&gt;alert('xss')&lt;/script&gt;</div>
```

**Solution**: Always sanitize output

```python
from app.utils.security import SecurityValidator

clean = SecurityValidator.sanitize_html(user_input)
```

---

## Networking Issues

### Problem: CORS Error (Frontend Can't Connect)

**Symptoms**:
```
Access to XMLHttpRequest blocked by CORS policy
```

**Solution**: Configure CORS origins

```env
CORS_ORIGINS=https://app.example.com,https://staging.example.com
```

**Or allow all (development only)**:
```env
CORS_ORIGINS=*
```

**Test with curl**:
```bash
curl -H "Origin: https://app.example.com" \
     -H "Access-Control-Request-Method: POST" \
     http://localhost:5000/chat
```

---

### Problem: Connection Refused to Redis

**Symptoms**:
```
Redis connection refused (127.0.0.1:6379)
Falling back to in-memory session store
```

**Solution**: Start Redis or disable it

**Start Redis**:
```bash
redis-server

# Or with Docker
docker run -d -p 6379:6379 redis:7-alpine
```

**Or disable and use database**:
```env
REDIS_URL=  # Empty to disable
```

---

## Testing Issues

### Problem: Tests Fail Locally but Pass in CI

**Causes**:
1. Different database state
2. Timing issues
3. Environment variable mismatch
4. Missing test fixtures

**Solutions**:

**Use Isolated Test Database**:
```bash
FLASK_ENV=testing pytest tests/
```

**Verify Test Database**:
```python
# In conftest.py
@pytest.fixture(autouse=True)
def setup_teardown():
    # Create test db schema
    init_test_database()
    yield
    # Cleanup
    cleanup_test_database()
```

**Check Environment**:
```bash
echo $FLASK_ENV
echo $DB_HOST

# Should be: testing, localhost
```

---

## Monitoring & Alerting

### Problem: No Logs Being Captured

**Symptoms**:
```
logs/app.log is empty or missing
```

**Solution**:

**Create logs directory**:
```bash
mkdir -p logs
chmod 755 logs
```

**Check log configuration**:
```python
import logging

logger = logging.getLogger(__name__)
logger.info("Test log message")

# Check logs/app.log
tail logs/app.log
```

**Check log level**:
```env
LOG_LEVEL=DEBUG  # Or INFO, WARNING
```

---

## Quick Diagnostic Commands

```bash
# Health check
curl http://localhost:5000/health

# Readiness check
curl http://localhost:5000/ready

# View logs
tail -f logs/app.log

# Check database
mysql -u root -p -e "SELECT COUNT(*) FROM financing_products;"

# Check Redis
redis-cli ping

# Check running processes
ps aux | grep python

# Check port usage
lsof -i :5000

# Monitor system resources
top -u $(whoami)

# Check disk space
df -h

# Check available memory
free -h
```

---

## Getting Help

1. **Check logs first**: `tail logs/app.log`
2. **Search this guide**: Ctrl+F for error message
3. **GitHub Issues**: Check existing issues
4. **Team Slack**: Post error in #dev-help
5. **Create issue**: With logs, steps to reproduce, environment details

---

## Emergency Procedures

### App Completely Down

```bash
# 1. Check if process running
ps aux | grep python

# 2. Check logs for error
tail -100 logs/app.log

# 3. Manually restart
python app.py

# 4. If restart fails, debug:
python -c "from app import create_app; app = create_app()"
```

### Database Connection Lost

```bash
# 1. Verify MySQL running
mysql -u root -p -e "SELECT 1"

# 2. Check connection pool
python scripts/check_db.py

# 3. If lost, reconnect:
# App auto-reconnects on next request
```

### Redis Session Store Down

```bash
# 1. Check Redis
redis-cli ping

# 2. Restart Redis
redis-server

# 3. Or disable (fallback to memory):
# Set REDIS_URL=
```

---

**For more details, see other guides:**
- PRODUCTION_REFACTOR_PLAN.md - Architecture details
- DEPLOYMENT_GUIDE.md - Deployment procedures
- API_REFERENCE.md - Endpoint specifications
- TESTING_GUIDE.md - Testing procedures

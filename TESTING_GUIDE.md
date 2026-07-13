# Testing Guide - Jarvis Banking AI

## Quick Start

```bash
pip install -r requirements-dev.txt
pytest tests/
```

---

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures & setup
├── unit/                    # Individual function tests
│   ├── test_auth_service.py
│   ├── test_security.py
│   └── test_query_classifier.py
├── integration/             # Multi-component workflows
│   ├── test_auth_flow.py
│   ├── test_chat_flow.py
│   └── test_session_persistence.py
└── fixtures/                # Test data
    ├── test_users.json
    └── test_queries.json
```

---

## Running Tests

### All Tests
```bash
pytest tests/ -v
```

### Specific Category
```bash
pytest tests/unit/ -v              # Unit tests only
pytest tests/integration/ -v       # Integration tests
pytest tests/unit/test_auth_service.py -v  # Single file
```

### With Coverage
```bash
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html
```

---

## Unit Tests

Test individual functions in isolation.

### Test Auth Service

**File**: `tests/unit/test_auth_service.py`

```python
import pytest
from app.services.auth import AuthService

def test_login_success():
    result = AuthService.login('testuser', 'password123')
    assert result['success'] == True
    assert 'token' in result
    assert 'session_id' in result

def test_login_missing_username():
    result = AuthService.login('', 'password')
    assert result['success'] == False

def test_token_verification():
    result = AuthService.login('testuser', 'pass')
    token = result['token']
    
    user_info = AuthService.verify_token(token)
    assert user_info is not None
    assert user_info['user_id'] == 'testuser'

def test_token_expiry():
    result = AuthService.login('user', 'pass')
    token = result['token']
    
    AuthService.logout(token)
    
    user_info = AuthService.verify_token(token)
    assert user_info is None
```

### Test Security Validator

**File**: `tests/unit/test_security.py`

```python
from app.utils.security import SecurityValidator

def test_validate_message_valid():
    is_valid, error = SecurityValidator.validate_message("Hello!")
    assert is_valid == True
    assert error == ""

def test_validate_message_empty():
    is_valid, error = SecurityValidator.validate_message("")
    assert is_valid == False
    assert "empty" in error.lower()

def test_validate_message_too_long():
    long_msg = "x" * 3000
    is_valid, error = SecurityValidator.validate_message(long_msg)
    assert is_valid == False
    assert "exceeds" in error

def test_check_pii_ssn():
    has_pii = SecurityValidator.check_pii("My SSN is 123-45-6789")
    assert has_pii == True

def test_sanitize_html():
    dirty = "<script>alert('xss')</script>"
    clean = SecurityValidator.sanitize_html(dirty)
    assert "<script>" not in clean
    assert "&lt;script&gt;" in clean
```

### Test Query Classifier

**File**: `tests/unit/test_query_classifier.py`

```python
from utils.classifier import QueryClassifier

def test_classify_simple_query():
    query_type, intent, safe = QueryClassifier.classify("Tell me about car loans")
    assert query_type == "simple"
    assert intent == "loan_info"
    assert safe == True

def test_classify_complex_query():
    query_type, intent, safe = QueryClassifier.classify("I want to apply for a home loan")
    assert query_type == "complex"
    assert intent == "loan_application"

def test_classify_restricted_query():
    query_type, intent, safe = QueryClassifier.classify("What is my SSN?")
    assert query_type == "restricted"
    assert safe == False
```

---

## Integration Tests

Test multiple components working together.

### Test Auth Flow

**File**: `tests/integration/test_auth_flow.py`

```python
import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app('testing')
    with app.test_client() as client:
        yield client

def test_full_auth_flow(client):
    login_resp = client.post('/auth/login', json={
        'username': 'testuser',
        'password': 'testpass'
    })
    assert login_resp.status_code == 200
    
    data = login_resp.get_json()
    assert data['success'] == True
    token = data['data']['access_token']
    
    logout_resp = client.post('/auth/logout', headers={
        'Authorization': f'Bearer {token}'
    })
    assert logout_resp.status_code == 200

def test_protected_route_requires_auth(client):
    resp = client.post('/chat', json={'message': 'test'})
    assert resp.status_code == 401
    assert 'AUTH_REQUIRED' in resp.get_json()['error']['code']
```

### Test Chat Flow

**File**: `tests/integration/test_chat_flow.py`

```python
@pytest.fixture
def authenticated_client(client):
    resp = client.post('/auth/login', json={
        'username': 'testuser',
        'password': 'testpass'
    })
    token = resp.get_json()['data']['access_token']
    
    def client_with_auth(*args, **kwargs):
        kwargs['headers'] = kwargs.get('headers', {})
        kwargs['headers']['Authorization'] = f'Bearer {token}'
        return client(*args, **kwargs)
    
    return client_with_auth

def test_send_message_and_get_response(authenticated_client):
    resp = authenticated_client.post('/chat', json={
        'message': 'Tell me about car loans',
        'session_id': 'session_test'
    })
    
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] == True
    assert 'reply' in data['data']
    assert 'agent' in data['data']

def test_get_chat_history(authenticated_client):
    authenticated_client.post('/chat', json={
        'message': 'Test message'
    })
    
    resp = authenticated_client.get('/chat/history')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'history' in data['data']

def test_clear_chat_history(authenticated_client):
    authenticated_client.post('/chat', json={
        'message': 'Message to delete'
    })
    
    resp = authenticated_client.delete('/chat/history')
    assert resp.status_code == 200
    
    history_resp = authenticated_client.get('/chat/history')
    history = history_resp.get_json()['data']['history']
    assert len(history) == 0
```

### Test Session Persistence

**File**: `tests/integration/test_session_persistence.py`

```python
def test_session_survives_restart(client):
    from app.services.auth import AuthService
    
    result = AuthService.login('user123', 'pass')
    token = result['token']
    
    user_info = AuthService.verify_token(token)
    assert user_info is not None
    
    AuthService._get_session_store.cache_clear()
    
    user_info_after = AuthService.verify_token(token)
    
    if AuthService._get_session_store() is not None:
        assert user_info_after is not None
```

---

## End-to-End Tests

Test full workflows through browser/client.

### Example E2E Test

**File**: `tests/e2e/test_full_session.py`

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_full_user_session():
    driver = webdriver.Chrome()
    driver.get('http://localhost:5000')
    
    wait = WebDriverWait(driver, 10)
    
    wait.until(EC.presence_of_element_located((By.ID, 'username')))
    
    driver.find_element(By.ID, 'username').send_keys('testuser')
    driver.find_element(By.ID, 'password').send_keys('testpass')
    driver.find_element(By.ID, 'loginBtn').click()
    
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'chat-box')))
    
    driver.find_element(By.ID, 'messageInput').send_keys('Car loans?')
    driver.find_element(By.ID, 'sendBtn').click()
    
    wait.until(EC.text_to_be_present_in_element(
        (By.CLASS_NAME, 'bot'),
        'Car'
    ))
    
    driver.quit()
```

---

## Test Data

### test_users.json
```json
[
  {
    "username": "testuser",
    "password": "testpass123",
    "role": "customer"
  },
  {
    "username": "admin",
    "password": "adminpass",
    "role": "admin"
  }
]
```

### test_queries.json
```json
[
  {
    "query": "Tell me about car loans",
    "expected_type": "simple",
    "expected_intent": "loan_info"
  },
  {
    "query": "I want to apply for a home loan",
    "expected_type": "complex",
    "expected_intent": "loan_application"
  }
]
```

---

## Coverage Goals

| Component | Target | Current |
|-----------|--------|---------|
| Auth Service | 95% | - |
| Chat Routes | 90% | - |
| Security | 95% | - |
| Database | 85% | - |
| Overall | 90% | - |

---

## Continuous Integration

### GitHub Actions Example

Create `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_DATABASE: jarvis_ai_testing
          MYSQL_ROOT_PASSWORD: root

    steps:
    - uses: actions/checkout@v2
    - uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - run: pip install -r requirements-dev.txt
    - run: pytest tests/ --cov=app
    - run: pip install coverage codecov
    - run: codecov
```

---

## Troubleshooting Tests

### Test Database Connection Issues

Set `FLASK_ENV=testing` to use test database:
```bash
FLASK_ENV=testing pytest tests/
```

### Fixture Not Found

Ensure `conftest.py` is in `tests/` directory and imports fixtures.

### Tests Pass Locally but Fail in CI

Check:
- Database credentials match test config
- Redis server running (if testing session store)
- All dependencies in requirements-dev.txt

---

## Best Practices

1. **One assertion per test** (or related assertions)
2. **Use meaningful names**: `test_login_with_valid_credentials`
3. **Setup & cleanup**: Use fixtures for database state
4. **Mock external services**: Use `unittest.mock`
5. **Test both success and failure paths**
6. **Keep tests independent** (no shared state)

---

**See API_REFERENCE.md for endpoint details**

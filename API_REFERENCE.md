# API Reference - Jarvis Banking AI

## Overview

All endpoints follow this response format:

### Success Response
```json
{
  "success": true,
  "data": {
    "key": "value"
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "optional-request-id"
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": "Additional context (optional)"
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "status": 400
  }
}
```

---

## Endpoints

### Health & Status

#### GET /health
Basic health check (app is running).

**Response**: `200 OK`
```json
{
  "success": true,
  "data": {
    "status": "ok",
    "uptime_seconds": 3600
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

---

#### GET /ready
Readiness probe (all dependencies ready).

**Response**: `200 OK` or `503 Service Unavailable`
```json
{
  "success": true,
  "data": {
    "ready": true,
    "database": "connected"
  }
}
```

---

#### GET /live
Liveness probe (still responsive).

**Response**: `200 OK`
```json
{
  "success": true,
  "data": {
    "live": true
  }
}
```

---

### Authentication

#### POST /auth/login
Authenticate user and create session.

**Request**:
```json
{
  "username": "john_doe",
  "password": "secure_password"
}
```

**Response**: `200 OK` or `401 Unauthorized`
```json
{
  "success": true,
  "data": {
    "access_token": "abc123def456...",
    "token_type": "Bearer",
    "expires_in": 86400,
    "user": {
      "id": "john_doe",
      "name": "John Doe",
      "role": "customer"
    }
  }
}
```

**Error Cases**:
- `400 INVALID_USERNAME`: Username format invalid
- `400 INVALID_PASSWORD`: Password required
- `401 AUTH_FAILED`: Invalid credentials

---

#### POST /auth/logout
Logout and invalidate session.

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response**: `200 OK` or `401 Unauthorized`
```json
{
  "success": true,
  "data": {
    "message": "Logged out successfully"
  }
}
```

---

### Chat

#### POST /chat
Send message to chatbot.

**Headers**:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request**:
```json
{
  "message": "Tell me about car loans",
  "session_id": "session_abc123"
}
```

**Response**: `200 OK` or `400/401/500`
```json
{
  "success": true,
  "data": {
    "reply": "Car Financing is designed for purchasing vehicles...",
    "agent": "bfs",
    "query_type": "simple",
    "intent": "loan_info",
    "safe": true
  },
  "meta": {
    "latency_ms": 125.45,
    "session_id": "session_abc123",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

**Error Cases**:
- `400 INVALID_MESSAGE`: Message too long, empty, etc.
- `401 AUTH_REQUIRED`: Missing authorization header
- `401 INVALID_TOKEN`: Token expired or invalid
- `500 INTERNAL_ERROR`: Processing failed

---

#### GET /chat/history
Retrieve user's chat history.

**Headers**:
```
Authorization: Bearer <access_token>
```

**Query Parameters**:
- `limit` (optional, default=50): Number of messages to retrieve

**Response**: `200 OK`
```json
{
  "success": true,
  "data": {
    "history": [
      {
        "chat_id": 1,
        "user_message": "Car loans?",
        "bot_response": "Car Financing...",
        "agent_name": "bfs",
        "query_type": "simple",
        "intent": "loan_info",
        "created_at": "2024-01-15T10:25:00Z"
      }
    ],
    "count": 1
  }
}
```

---

#### DELETE /chat/history
Clear user's chat history.

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response**: `200 OK`
```json
{
  "success": true,
  "data": {
    "message": "Chat history cleared"
  }
}
```

---

### Agent Configuration

#### GET /agent/config
Get available agents and current configuration.

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response**: `200 OK`
```json
{
  "success": true,
  "data": {
    "available_agents": ["bfs", "astar"],
    "default_agent": "bfs",
    "description": "BFS for simple queries, A* for complex"
  }
}
```

---

#### POST /agent/config
Set default agent (admin only in production).

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request**:
```json
{
  "default_agent": "astar"
}
```

**Response**: `200 OK` or `400/403`
```json
{
  "success": true,
  "data": {
    "default_agent": "astar",
    "message": "Default agent set to astar"
  }
}
```

---

## HTTP Status Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created |
| 204 | No Content | Request succeeded, no body |
| 400 | Bad Request | Validation failed |
| 401 | Unauthorized | Authentication required/failed |
| 403 | Forbidden | Permission denied |
| 404 | Not Found | Resource doesn't exist |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Error | Server error |
| 503 | Unavailable | Service down (dependency failed) |

---

## Error Codes

| Code | HTTP | Meaning |
|------|------|---------|
| AUTH_REQUIRED | 401 | Missing authorization header |
| INVALID_TOKEN | 401 | Token invalid/expired |
| AUTH_FAILED | 401 | Credentials invalid |
| INVALID_USERNAME | 400 | Username format invalid |
| INVALID_PASSWORD | 400 | Password missing/invalid |
| INVALID_MESSAGE | 400 | Message validation failed |
| BAD_REQUEST | 400 | Request format invalid |
| FORBIDDEN | 403 | Insufficient permissions |
| NOT_FOUND | 404 | Resource not found |
| INTERNAL_ERROR | 500 | Unexpected server error |

---

## Authentication

All protected endpoints require an `Authorization` header:

```
Authorization: Bearer <access_token>
```

The token is obtained from `/auth/login` and is valid for 24 hours by default.

---

## CORS

Frontend requests from different domains allowed from:
- Development: `*` (all origins)
- Production: Configured in `.env` via `CORS_ORIGINS`

**Headers set automatically**:
- `Access-Control-Allow-Origin`
- `Access-Control-Allow-Methods`
- `Access-Control-Allow-Headers`
- `Access-Control-Allow-Credentials`

---

## Rate Limiting

*Future feature: Not currently implemented in MVP*

Planned limits:
- Login: 5 attempts per minute
- Chat: 100 messages per hour
- Agent config: 10 changes per day

---

## Request IDs

All responses include a `meta.request_id` for tracing:
```json
{
  "meta": {
    "request_id": "req_abc123def456",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

Use this ID when reporting issues to support.

---

## Example Workflows

### Login → Chat → Logout

```bash
# 1. Login
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "password": "pass"}'

# Response:
# {
#   "success": true,
#   "data": {
#     "access_token": "abc123...",
#     "expires_in": 86400
#   }
# }

# 2. Chat with token
curl -X POST http://localhost:5000/chat \
  -H "Authorization: Bearer abc123..." \
  -H "Content-Type: application/json" \
  -d '{"message": "Car loans?"}'

# 3. Logout
curl -X POST http://localhost:5000/auth/logout \
  -H "Authorization: Bearer abc123..."
```

---

## API Changelog

### v1.0 (Current)
- ✅ Authentication (login/logout)
- ✅ Chat endpoint
- ✅ Agent configuration
- ✅ Health checks

### v1.1 (Planned)
- Rate limiting
- CSRF tokens
- User preferences API
- Advanced filtering

---

**For more details, see DEPLOYMENT_GUIDE.md**

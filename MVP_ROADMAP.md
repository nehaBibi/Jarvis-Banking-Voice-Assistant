# Implementation Roadmap & MVP Phases

## Overview

This roadmap describes a phased approach to implementing the production-grade refactor. Each phase builds on the previous one.

---

## Phase 1: Core Stability (Weeks 1-2)

**Goal**: Fix authentication persistence and establish modular architecture foundation.

### Deliverables

1. **Config Manager** (`config.py`)
   - Environment-specific configuration (dev/staging/prod)
   - Centralized setting management
   - Validation on load

2. **App Factory Pattern** (`wsgi.py` + `app.py` refactor)
   - Create Flask app instances via `create_app()`
   - Blueprint registration
   - Dependency initialization with validation
   - Error handler setup

3. **Session Persistence**
   - Store sessions in Redis or database (not in-memory)
   - 24-hour expiry with refresh capability
   - Survive app restart (verified by test)

4. **Database Connection Pooling** (`app/utils/database.py`)
   - Connection pool management (5-10 connections)
   - Automatic reconnect on lost connection
   - Parameterized queries (prevent SQL injection)
   - Mock data fallback

5. **Health Check Endpoints**
   - `/health` - App is running
   - `/ready` - All dependencies ready (DB, Redis)
   - `/live` - Liveness probe

### Testing

- Unit tests: Config loading, session creation
- Integration tests: Auth flow with app restart
- Manual verification: Kill app, restart, old token still works

### Metrics & Success Criteria

- ✅ Auth tokens survive app restart
- ✅ Database connection pooling active (verified via logs)
- ✅ Health endpoints return correct status
- ✅ All unit tests pass
- ✅ No in-memory-only state (except cache)

---

## Phase 2: Modular Architecture (Weeks 3-4)

**Goal**: Separate concerns into routes and services; introduce blueprints.

### Deliverables

1. **Blueprint Structure** (`app/routes/`)
   - `health.py` - Health/readiness routes
   - `auth.py` - Login/logout routes
   - `chat.py` - Chat/history routes
   - Each blueprint independently testable

2. **Service Layer** (`app/services/`)
   - `auth.py` - Authentication business logic
   - `chatbot.py` - Chat orchestration
   - Services decoupled from routes
   - Easy to mock for testing

3. **Consistent Error Handling**
   - Middleware for error interception
   - Standardized error response format
   - Request/response logging middleware

4. **Dependency Injection Setup**
   - Decorators for auth validation (`@require_auth()`)
   - Custom decorators for common patterns
   - Loose coupling between components

5. **Improved Security** (`app/utils/security.py`)
   - Enhanced input validation
   - HTML sanitization
   - PII detection (SSN, account numbers)
   - Rate limiting hooks (for Phase 4)

### Directory Structure After Phase 2

```
app/
├── routes/
│   ├── health.py
│   ├── auth.py
│   └── chat.py
├── services/
│   ├── auth.py
│   └── chatbot.py
└── utils/
    ├── database.py
    ├── security.py
    ├── decorators.py
    └── logging.py
```

### Testing

- Unit tests: Individual routes, services
- Integration tests: Auth → Chat → History
- Security tests: Input validation, XSS, SQL injection

### Metrics & Success Criteria

- ✅ Routes organized by domain
- ✅ Services testable in isolation
- ✅ All auth tests pass (token verification, session lookup)
- ✅ Chat flow tests pass end-to-end
- ✅ Zero hardcoded values (all from config)

---

## Phase 3: Chatbot Pipeline Enhancement (Weeks 5-6)

**Goal**: Cleaner agent architecture, better separation of pipeline stages.

### Deliverables

1. **Query Analyzer** (`app/services/query_analyzer.py`)
   - Tokenization & normalization
   - Entity extraction
   - Language detection
   - Intent pre-scoring

2. **Security Filter** (`app/services/security_filter.py`)
   - PII detection (enhanced)
   - Blacklist checking
   - XSS/injection detection
   - Sensitive topic blocking

3. **Decision Engine** (`app/services/decision_engine.py`)
   - Agent selection logic
   - Confidence scoring
   - Fallback routing
   - Agent availability checking

4. **Knowledge Base Accessor** (`app/services/kb_accessor.py`)
   - Product search (database)
   - Category filtering
   - Result ranking & relevance
   - Cache management (Redis)

5. **Response Generator** (`app/services/response_generator.py`)
   - Format product info
   - Add call-to-action
   - Sanitize output
   - Include metadata (latency, agent, etc.)

6. **Async-Safe Implementation**
   - Non-blocking agent calls
   - Thread pool for long-running operations
   - Timeout handling

### Pipeline Diagram (After Phase 3)

```
User Input
    ↓
Query Analyzer (tokenize, extract entities)
    ↓
Security Filter (PII check, blacklist)
    ↓
Query Classifier (intent extraction)
    ↓
Decision Engine (select BFS or A*)
    ↓
Agent Execution (BFS/A* search)
    ↓
KB Access (search products)
    ↓
Response Generator (format + sanitize)
    ↓
Response to User
```

### Testing

- Unit tests: Each pipeline component
- Integration tests: Full pipeline
- Performance tests: Latency < 1s (p95)
- Agent accuracy tests: Intent classification > 90%

### Metrics & Success Criteria

- ✅ Query classification accuracy > 90%
- ✅ Agent latency p95 < 1 second
- ✅ 100% of responses sanitized (no XSS)
- ✅ All async operations complete without blocking
- ✅ Fallback handling tested

---

## Phase 4: Production Hardening (Weeks 7-8)

**Goal**: Security, monitoring, and production-readiness improvements.

### Deliverables

1. **CSRF Protection**
   - CSRF token generation & validation
   - SameSite cookie settings
   - Form token verification

2. **Rate Limiting**
   - Per-user limits (100 messages/hour)
   - Per-IP limits (1000 requests/hour)
   - Sliding window algorithm
   - Custom rate limit headers

3. **Comprehensive Logging**
   - Structured JSON logging
   - Request/response logging middleware
   - Performance metrics (latency histograms)
   - Security event logging (failed auth, suspicious input)
   - Audit trail for sensitive operations

4. **Error Tracking** (Optional: Sentry)
   - Error aggregation
   - Stack trace capture
   - Environment context
   - Release tracking

5. **Performance Monitoring**
   - Response time histograms
   - Agent latency tracking
   - Database query profiling
   - Memory/CPU usage

6. **Security Audit**
   - OWASP Top 10 checklist
   - Penetration testing (basic)
   - Dependency vulnerability scan
   - Code review checklist

### Security Checklist

- [ ] SQL injection: All queries parameterized
- [ ] XSS: All outputs sanitized
- [ ] CSRF: Tokens implemented
- [ ] Auth: Secure token generation & validation
- [ ] Secrets: Never logged, in-memory secrets cleared
- [ ] Dependencies: No known vulnerabilities (npm audit, safety)
- [ ] Rate limiting: Endpoints protected
- [ ] CORS: Restricted to known domains
- [ ] HTTPS: Enforced in production

### Metrics & Success Criteria

- ✅ OWASP Top 10 coverage: 100%
- ✅ Security scan: Zero critical issues
- ✅ Rate limiting: Active on all endpoints
- ✅ Logging: Structured logs, no PII
- ✅ Monitoring: Dashboards for key metrics

---

## Phase 5: Deployment & Documentation (Weeks 9-10)

**Goal**: Production-ready deployment automation and comprehensive documentation.

### Deliverables

1. **Kubernetes Manifests**
   - Deployment with replicas
   - Service & LoadBalancer
   - ConfigMap & Secrets
   - StatefulSet (for future persistence)
   - Ingress (future)

2. **CI/CD Pipeline** (GitHub Actions)
   - Automated tests on PR
   - Docker image build & push
   - Deployment to staging on merge
   - Deployment to production on tag

3. **Runbooks**
   - Common troubleshooting steps
   - On-call playbook
   - Escalation procedures
   - Incident response

4. **API Documentation** (OpenAPI/Swagger)
   - Auto-generated from code
   - Example requests/responses
   - Authentication details
   - Error codes

5. **Administrator Guide**
   - User management
   - Monitoring dashboards
   - Log queries
   - Alert configuration

6. **Developer Guide**
   - Architecture overview
   - Code patterns & best practices
   - Local setup instructions
   - Testing guide

### Documentation Structure

```
docs/
├── README.md
├── API.md (auto-generated)
├── DEPLOYMENT.md
├── RUNBOOKS.md
├── TROUBLESHOOTING.md
└── DEVELOPER_GUIDE.md
```

### Metrics & Success Criteria

- ✅ Deployment automated (no manual steps)
- ✅ Deployment time < 5 minutes
- ✅ Recovery time objective (RTO) < 15 minutes
- ✅ All endpoints documented
- ✅ 100% team aware of runbooks

---

## Phase 6+: Optional Enhancements

### Voice I/O
- Improve speech recognition accuracy
- Support multiple languages
- Noise cancellation

### Advanced NLP
- Hugging Face model integration
- Fine-tuning on banking queries
- Sentiment analysis

### Analytics & Dashboard
- User engagement metrics
- Popular queries
- Chatbot improvement recommendations
- Admin dashboard

### Real ML Agents
- Replace keyword matching with trained classifiers
- Reinforcement learning for routing optimization
- User preference learning

### Multi-Tenant Support
- Organization isolation
- Custom branding
- Usage tracking per organization

---

## Implementation Checklist

### Pre-Implementation
- [ ] Team alignment on architecture
- [ ] Git repo setup with branch protection
- [ ] CI/CD pipeline scaffolding
- [ ] Database backup procedure documented

### Phase 1: Core Stability

Implement in this order:

1. [ ] Create `config.py` with environment management
2. [ ] Refactor `app.py` to use app factory (`create_app()`)
3. [ ] Implement session persistence (Redis or DB)
4. [ ] Create `app/utils/database.py` with connection pooling
5. [ ] Add health check endpoints
6. [ ] Write unit tests for core services
7. [ ] Docker setup with `docker-compose.yml`
8. [ ] Test: Auth token survives restart
9. [ ] Code review & merge to main
10. [ ] Deploy to staging

### Phase 2: Modular Architecture

1. [ ] Create blueprint structure (`app/routes/`)
2. [ ] Implement service layer (`app/services/`)
3. [ ] Move route logic from `app.py` to blueprints
4. [ ] Implement decorators (`@require_auth`)
5. [ ] Add error handler middleware
6. [ ] Improve security validators
7. [ ] Write integration tests
8. [ ] Test all auth flows
9. [ ] Code review & merge
10. [ ] Deploy to staging

### Phase 3: Chatbot Pipeline

1. [ ] Create pipeline components (`app/services/query_analyzer.py`, etc.)
2. [ ] Refactor agent calling logic
3. [ ] Add async support
4. [ ] Implement KB accessor
5. [ ] Improve response generation
6. [ ] Test pipeline end-to-end
7. [ ] Performance testing (latency < 1s)
8. [ ] Code review & merge
9. [ ] Deploy to staging

### Phase 4: Production Hardening

1. [ ] Implement CSRF tokens
2. [ ] Add rate limiting
3. [ ] Set up structured logging
4. [ ] Configure error tracking (Sentry)
5. [ ] Performance monitoring setup
6. [ ] Security audit & fixes
7. [ ] Penetration testing
8. [ ] Code review & merge
9. [ ] Deploy to staging
10. [ ] Load testing

### Phase 5: Deployment

1. [ ] Create Kubernetes manifests
2. [ ] Set up CI/CD pipeline
3. [ ] Write runbooks
4. [ ] Generate API docs
5. [ ] Write admin guide
6. [ ] Write troubleshooting guide
7. [ ] Team training
8. [ ] Deploy to production
9. [ ] Monitor for 1 week
10. [ ] Post-mortem & refinements

---

## Estimated Timeline

| Phase | Weeks | Team Size |
|-------|-------|-----------|
| Phase 1 | 2 | 1-2 developers |
| Phase 2 | 2 | 1-2 developers |
| Phase 3 | 2 | 1-2 developers |
| Phase 4 | 2 | 2+ developers |
| Phase 5 | 2 | 2+ developers (+ DevOps) |
| **Total** | **10** | **2-3 developers** |

---

## Resource Allocation

### Phase 1
- 1 backend developer (config, app factory, database)
- 1 QA engineer (testing)

### Phase 2
- 1 backend developer (routes, services)
- 1 QA engineer (integration tests)

### Phase 3
- 1 backend developer (pipeline components)
- 1 ML/NLP specialist (agent improvements)

### Phase 4
- 1 backend developer (security, monitoring)
- 1 security engineer (audit)

### Phase 5
- 1 DevOps engineer (K8s, CI/CD)
- 1 backend developer (documentation)
- 1 QA engineer (load testing)

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Database migration issues | Medium | High | Test migrations on staging first |
| Regression in chat quality | Low | High | Comprehensive testing before Phase 3 |
| Performance degradation | Medium | Medium | Load testing in Phase 4 |
| Team ramp-up delay | Low | Medium | Clear documentation, pairing sessions |
| Deployment issues | Low | High | CI/CD automation, runbooks |

---

## Success Metrics

### By End of Phase 1
- Auth tokens persist across restarts
- Zero in-memory-only state
- All health endpoints working
- 90%+ code coverage

### By End of Phase 2
- Routes organized by domain
- Services testable in isolation
- Integration tests passing
- Response consistency verified

### By End of Phase 3
- Query classification accuracy > 90%
- Agent latency p95 < 1 second
- No XSS vulnerabilities
- Full pipeline tested

### By End of Phase 4
- OWASP Top 10 coverage: 100%
- Rate limiting active
- Monitoring dashboards live
- Security audit passed

### By End of Phase 5
- Zero manual deployment steps
- Deployment time < 5 minutes
- RTO < 15 minutes
- Team trained & confident

---

## Communication Plan

- **Weekly**: Team sync (30 min)
- **Sprint**: Bi-weekly sprint planning
- **Stakeholders**: Status update every 2 weeks
- **Post-phase**: Retrospective & lessons learned
- **Documentation**: Update docs as you go (not after)

---

## Next Steps

1. **Review** this roadmap with team
2. **Assign** owners for each phase
3. **Create** Jira epics for phases
4. **Schedule** kickoff meeting
5. **Start** Phase 1 Week 1

---

**Questions?** See PRODUCTION_REFACTOR_PLAN.md for architecture details or TROUBLESHOOTING.md for common issues.

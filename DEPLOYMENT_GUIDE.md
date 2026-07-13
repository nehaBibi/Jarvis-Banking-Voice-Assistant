# Deployment Guide - Jarvis Banking AI

## Pre-Deployment Checklist

- [ ] All tests pass locally (`pytest tests/`)
- [ ] Environment variables documented in `.env.example`
- [ ] Database migrations reviewed and tested
- [ ] Docker image builds successfully
- [ ] Security scan completed (OWASP Top 10)
- [ ] Logging and monitoring configured
- [ ] Backup strategy in place
- [ ] Rollback plan documented

---

## 1. Environment Configuration

### Development (.env)
```env
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=dev-secret-key-change-me
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root
DB_NAME=jarvis_ai_dev
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=DEBUG
CORS_ORIGINS=*
```

### Staging (.env.staging)
```env
FLASK_ENV=staging
FLASK_DEBUG=False
SECRET_KEY=$(openssl rand -hex 32)
DB_HOST=db-staging.example.com
DB_PORT=3306
DB_USER=jarvis_staging
DB_PASSWORD=staging-password-change-me
DB_NAME=jarvis_ai_staging
REDIS_URL=redis://cache-staging.example.com:6379/0
LOG_LEVEL=INFO
CORS_ORIGINS=https://staging.example.com,https://admin.example.com
```

### Production (.env.prod)
```env
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=$(openssl rand -hex 32)
DB_HOST=db-prod.example.com
DB_PORT=3306
DB_USER=jarvis_prod
DB_PASSWORD=prod-password-from-vault
DB_NAME=jarvis_ai_production
REDIS_URL=redis://cache-prod.example.com:6379/0
LOG_LEVEL=WARNING
CORS_ORIGINS=https://app.example.com
```

### Generate Secure Secret Key
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 2. Local Development Setup

### Prerequisites
- Python 3.11+
- MySQL 8.0+
- Redis 7.0+ (optional, for session store)
- Docker (optional, for containerized DB)

### Setup Steps

```bash
git clone https://github.com/yourorg/jarvis-banking-ai.git
cd jarvis-banking-ai

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -r requirements.txt
pip install -r requirements-dev.txt

cp .env.example .env
# Edit .env with your local settings

python scripts/migrate.py
python scripts/seed_db.py

pytest tests/
python app.py
```

**App runs at**: `http://localhost:5000`

---

## 3. Docker Deployment

### Build Docker Image

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=wsgi.py
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

CMD ["gunicorn", "--workers=4", "--bind=0.0.0.0:5000", "--timeout=60", "--access-logfile=-", "--error-logfile=-", "wsgi:app"]
```

### Build & Push

```bash
docker build -t jarvis-api:1.0.0 .

docker tag jarvis-api:1.0.0 registry.example.com/jarvis-api:1.0.0
docker push registry.example.com/jarvis-api:1.0.0
```

### Docker Compose (Local)

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: jarvis_ai_dev
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql

  cache:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      FLASK_ENV: development
      DB_HOST: db
      DB_USER: root
      DB_PASSWORD: root
      REDIS_URL: redis://cache:6379/0
    depends_on:
      - db
      - cache
    volumes:
      - .:/app

volumes:
  mysql_data:
```

### Run Locally with Docker Compose

```bash
docker-compose up -d
docker-compose logs -f web

docker-compose down
```

---

## 4. Kubernetes Deployment

### Prerequisites
- Kubernetes cluster (1.24+)
- kubectl configured
- Container registry access

### Create ConfigMap

```bash
kubectl create configmap jarvis-config \
  --from-literal=FLASK_ENV=production \
  --from-literal=DB_HOST=db-prod.example.com \
  --from-literal=LOG_LEVEL=INFO
```

### Create Secret

```bash
kubectl create secret generic jarvis-secrets \
  --from-literal=SECRET_KEY=$(openssl rand -hex 32) \
  --from-literal=DB_USER=jarvis_prod \
  --from-literal=DB_PASSWORD=<secure-password> \
  --from-literal=REDIS_URL=redis://cache-prod:6379/0
```

### Deployment Manifest

Create `k8s/deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jarvis-api
  labels:
    app: jarvis-api
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
        image: registry.example.com/jarvis-api:1.0.0
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 5000
          name: http
        
        env:
        - name: FLASK_ENV
          valueFrom:
            configMapKeyRef:
              name: jarvis-config
              key: FLASK_ENV
        - name: DB_HOST
          valueFrom:
            configMapKeyRef:
              name: jarvis-config
              key: DB_HOST
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: jarvis-secrets
              key: SECRET_KEY
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: jarvis-secrets
              key: DB_PASSWORD
        
        resources:
          requests:
            cpu: 250m
            memory: 512Mi
          limits:
            cpu: 500m
            memory: 1Gi
        
        livenessProbe:
          httpGet:
            path: /live
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        readinessProbe:
          httpGet:
            path: /ready
            port: http
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
        
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 15"]

---
apiVersion: v1
kind: Service
metadata:
  name: jarvis-api
  labels:
    app: jarvis-api
spec:
  type: LoadBalancer
  selector:
    app: jarvis-api
  ports:
  - port: 80
    targetPort: 5000
    name: http

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: jarvis-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: jarvis-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Deploy to Kubernetes

```bash
kubectl apply -f k8s/deployment.yaml

kubectl get pods -l app=jarvis-api

kubectl logs -l app=jarvis-api

kubectl describe pod <pod-name>
```

---

## 5. Database Migrations

### Run Migrations

```bash
python scripts/migrate.py
```

### Seed Data

```bash
python scripts/seed_db.py
```

### Rollback (if needed)

```sql
-- Manual rollback of latest migration
DROP TABLE chat_history;
DELETE FROM migrations WHERE migration_name = '003_add_chat_history';
```

---

## 6. Production Deployment Steps

### Step 1: Pre-deployment Validation

```bash
pytest tests/ -v

FLASK_ENV=production python -c "from app import create_app; app = create_app('production'); print('✅ App initialization OK')"
```

### Step 2: Build & Push Image

```bash
docker build -t jarvis-api:$(git rev-parse --short HEAD) .
docker push registry.example.com/jarvis-api:$(git rev-parse --short HEAD)
```

### Step 3: Update Kubernetes

```bash
kubectl set image deployment/jarvis-api app=registry.example.com/jarvis-api:$(git rev-parse --short HEAD)

kubectl rollout status deployment/jarvis-api

kubectl get pods -l app=jarvis-api
```

### Step 4: Verify Health

```bash
kubectl exec -it $(kubectl get pods -l app=jarvis-api -o jsonpath='{.items[0].metadata.name}') -- curl http://localhost:5000/health

kubectl logs -l app=jarvis-api --tail=50
```

### Step 5: Rollback (if issues)

```bash
kubectl rollout undo deployment/jarvis-api

kubectl rollout status deployment/jarvis-api
```

---

## 7. Monitoring & Logging

### Application Logs

```bash
kubectl logs -l app=jarvis-api -f

kubectl logs -l app=jarvis-api --since=1h
```

### Metrics

Expose Prometheus metrics at `/metrics` (future enhancement):

```bash
kubectl port-forward svc/jarvis-api 9090:9090

curl http://localhost:9090/metrics
```

### Error Tracking (Optional: Sentry)

```python
import sentry_sdk

sentry_sdk.init(
    dsn="https://...@sentry.io/...",
    environment="production",
    traces_sample_rate=0.1
)
```

---

## 8. Scaling & Performance

### Horizontal Scaling
Already configured via HPA in deployment.yaml
- Min replicas: 3
- Max replicas: 10
- Scale on: CPU 70%, Memory 80%

### Vertical Scaling
Adjust resource requests/limits in deployment.yaml:
```yaml
resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 1000m
    memory: 2Gi
```

### Database Connection Pooling
Already configured in `app/utils/database.py`:
- Pool size: 5 connections
- Automatic reconnect on lost connection

### Redis Caching
Session storage via Redis (if available):
- Fallback to in-memory store if Redis unavailable
- Automatic 24-hour expiry

---

## 9. Security Checklist

- [ ] All environment secrets in Kubernetes secrets (not committed)
- [ ] HTTPS/TLS enforced (Ingress + cert-manager)
- [ ] CORS origins restricted to known domains
- [ ] Rate limiting implemented (future)
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS protection (input sanitization)
- [ ] CSRF token validation (future)
- [ ] Logs do not contain sensitive data
- [ ] Database credentials rotated regularly
- [ ] Container image scanning for vulnerabilities

---

## 10. Troubleshooting

### App won't start
```bash
docker logs <container-id>

kubectl describe pod <pod-name>

kubectl logs <pod-name> --previous
```

### Database connection fails
```bash
kubectl port-forward svc/db 3306:3306

mysql -h 127.0.0.1 -u root -p
```

### High memory usage
```bash
kubectl top pods -l app=jarvis-api

kubectl get hpa jarvis-api-hpa --watch
```

### Slow chat responses
```bash
kubectl logs -l app=jarvis-api | grep latency_ms

kubectl exec -it <pod> -- python -m cProfile app.py
```

---

## 11. Backup & Disaster Recovery

### Database Backup

```bash
mysqldump -h db-prod.example.com -u root -p jarvis_ai_production > backup_$(date +%Y%m%d).sql
```

### Automated Backups (AWS RDS example)

Enable automated backups in AWS console:
- Retention: 30 days
- Backup window: 02:00 UTC

### Restore from Backup

```bash
mysql -h db-prod.example.com -u root -p jarvis_ai_production < backup_20240115.sql
```

---

## 12. CI/CD Pipeline

### GitHub Actions Example

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]
    tags: [v*]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Build Docker Image
      run: |
        docker build -t registry.example.com/jarvis-api:${{ github.sha }} .
        docker push registry.example.com/jarvis-api:${{ github.sha }}
    
    - name: Deploy to Kubernetes
      run: |
        kubectl set image deployment/jarvis-api app=registry.example.com/jarvis-api:${{ github.sha }}
        kubectl rollout status deployment/jarvis-api
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Local dev | `docker-compose up` |
| Run tests | `pytest tests/` |
| Build image | `docker build -t jarvis-api .` |
| Deploy K8s | `kubectl apply -f k8s/deployment.yaml` |
| View logs | `kubectl logs -l app=jarvis-api` |
| Rollback | `kubectl rollout undo deployment/jarvis-api` |
| Scale | `kubectl scale deployment/jarvis-api --replicas=5` |

---

**See PRODUCTION_REFACTOR_PLAN.md for architecture details**

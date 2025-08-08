# 🐳 Docker Deployment Guide

Complete Docker setup for the Threat Modeling Pipeline with production-ready architecture.

## 🚀 Quick Start

**1. Prerequisites:**
```bash
# Ensure Docker and Docker Compose are installed
docker --version
docker-compose --version
```

**2. One-Command Startup:**
```bash
# Start all services
./docker-start.sh

# Or start with local Ollama LLM
./docker-start.sh start-with-ollama
```

**3. Access the Application:**
- **Frontend**: http://localhost:3001
- **API Docs**: http://localhost:8000/docs
- **Task Monitor**: http://localhost:5555

## 🏗️ Architecture

The Docker setup includes **8 services**:

1. **PostgreSQL** - Persistent database storage
2. **Redis** - Message broker and cache
3. **FastAPI API** - Main backend server
4. **Celery Worker** - Background job processing
5. **Celery Beat** - Scheduled task runner (optional)
6. **Celery Flower** - Task monitoring UI
7. **Next.js Frontend** - Web interface
8. **Ollama** - Local LLM (optional)

## 📋 Services Overview

| Service | Port | Purpose | Health Check |
|---------|------|---------|--------------|
| Frontend | 3001 | Web UI | ✅ Built-in |
| API | 8000 | REST API + WebSocket | ✅ Built-in |
| PostgreSQL | 5432 | Database | ✅ Built-in |
| Redis | 6379 | Message Broker | ✅ Built-in |
| Flower | 5555 | Task Monitoring | ✅ Built-in |
| Ollama | 11434 | Local LLM | ⚠️ Optional |

## 🔧 Management Commands

```bash
# Start services
./docker-start.sh start

# Start with local Ollama LLM
./docker-start.sh start-with-ollama

# Stop all services
./docker-start.sh stop

# Restart services
./docker-start.sh restart

# View logs
./docker-start.sh logs

# Check service status
./docker-start.sh status

# Complete cleanup (removes all data!)
./docker-start.sh clean
```

## ⚙️ Configuration

**Environment Variables:**

1. **Copy template**: `cp .env.docker apps/api/.env`
2. **Edit with your API keys**: `nano apps/api/.env`

**Key Settings:**
```env
# Database (auto-configured)
DATABASE_URL=postgresql+asyncpg://threat_user:secure_password_123@postgres:5432/threat_modeling

# LLM Provider API Keys (add yours)
AZURE_OPENAI_API_KEY=your_key_here
SCALEWAY_API_KEY=your_key_here

# Local Ollama (automatic if running)
OLLAMA_BASE_URL=http://ollama:11434
```

## 🔒 Security Features

✅ **Multi-stage Docker builds** for smaller images  
✅ **Non-root users** in all containers  
✅ **Health checks** for all critical services  
✅ **Automatic restarts** with `unless-stopped`  
✅ **Volume isolation** for data persistence  
✅ **Internal networking** between services  

## 📁 Data Persistence

**Volumes Created:**
- `postgres_data` - Database files
- `redis_data` - Redis persistence
- `api_uploads` - Uploaded documents
- `ollama_data` - Local LLM models
- `./inputs` - Input documents (mounted)
- `./outputs` - Generated reports (mounted)

## 🧪 Testing the Setup

**1. Check all services are running:**
```bash
./docker-start.sh status
```

**2. Test API health:**
```bash
curl http://localhost:8000/health
```

**3. Test background jobs:**
```bash
# Create a pipeline
curl -X POST "http://localhost:8000/api/pipeline/create" \
  -H "Content-Type: application/json" \
  -d '{"name": "Docker Test Pipeline"}'

# Queue a background task
curl -X POST "http://localhost:8000/api/tasks/execute-step" \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline_id": "PIPELINE_ID_FROM_ABOVE",
    "step": "dfd_extraction",
    "data": {}
  }'
```

**4. Monitor tasks:**
- Visit http://localhost:5555 for Flower UI
- Check logs: `./docker-start.sh logs`

## 🚨 Troubleshooting

**Services won't start:**
```bash
# Check Docker daemon
sudo systemctl status docker

# Check logs for specific service
docker-compose logs api
docker-compose logs celery-worker
```

**Authentication/Login Failures (500 errors, "login failed"):**
```bash
# Common cause: asyncpg connection pool race conditions
# Quick fix:
docker-compose restart api
sleep 15
docker-compose exec api python -m app.core.init_rbac

# Test login:
curl -X POST http://localhost/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123!"}'

# If persistent, rebuild API:
docker-compose build api --no-cache
docker-compose up -d api
```

**Database connection issues:**
```bash
# For "another operation is in progress" errors:
docker-compose restart api  # Clears connection pool

# Full reset if needed:
docker-compose down -v
./docker-start.sh start
```

**Module Import Errors:**
```bash
# After adding new Python files, rebuild:
docker-compose build api
docker-compose up -d api
```

**Port conflicts:**
```bash
# Check what's using ports
sudo lsof -i :8000
sudo lsof -i :3001
sudo lsof -i :5432
```

**Memory issues:**
```bash
# Increase Docker memory limit in Docker Desktop
# Or reduce Celery worker concurrency in docker-compose.yml
```

## 🔄 Updates & Maintenance

**Update application code:**
```bash
# Rebuild and restart
docker-compose up -d --build
```

**Database migrations:**
```bash
# Migrations run automatically on startup
# Or manually: docker-compose exec api alembic upgrade head
```

**View service logs:**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f celery-worker
```

## 🏢 Enterprise Deployment

**For production deployment:**

1. **Change default passwords** in `docker-compose.yml`
2. **Add SSL/TLS termination** (nginx/traefik)
3. **Configure backup strategy** for PostgreSQL
4. **Set up monitoring** (Prometheus/Grafana)
5. **Add log aggregation** (ELK/Fluentd)
6. **Configure secrets management** (Docker Secrets/Vault)

**Example production adjustments:**
```yaml
# In docker-compose.yml
environment:
  - POSTGRES_PASSWORD_FILE=/run/secrets/postgres_password
secrets:
  postgres_password:
    external: true
```

## 💡 Performance Optimization

**Scaling Celery workers:**
```bash
# Scale to 3 worker instances
docker-compose up -d --scale celery-worker=3
```

**Database tuning:**
```yaml
# In docker-compose.yml postgres service
environment:
  - POSTGRES_SHARED_PRELOAD_LIBRARIES=pg_stat_statements
command: postgres -c max_connections=200 -c shared_buffers=256MB
```

## 🎯 Privacy & Security Benefits

✅ **Complete air-gapped deployment** - No external dependencies required  
✅ **Local LLM support** with Ollama - Keep sensitive data private  
✅ **Persistent local storage** - All data stays on your infrastructure  
✅ **Network isolation** - Services communicate via internal Docker networks  
✅ **Non-root execution** - Enhanced security posture  
✅ **Volume encryption** - Can be added at host level  
✅ **Audit logs** - Full traceability of all operations  

Perfect for **privacy-conscious enterprises**, **government agencies**, and **regulated industries**!

## 🆘 Support

- **Logs**: `./docker-start.sh logs`
- **Status**: `./docker-start.sh status`  
- **Health**: Check http://localhost:8000/health
- **Task Monitor**: http://localhost:5555
- **API Docs**: http://localhost:8000/docs
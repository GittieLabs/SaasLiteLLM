# Docker Deployment Guide

This guide covers Docker setup, configuration, and troubleshooting for the SaaS LiteLLM platform.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Docker Compose Setup](#docker-compose-setup)
- [Service Configuration](#service-configuration)
- [Building Custom Images](#building-custom-images)
- [Production Deployment](#production-deployment)
- [Networking](#networking)
- [Volumes and Persistence](#volumes-and-persistence)
- [Health Checks](#health-checks)
- [Troubleshooting](#troubleshooting)

---

## Overview

The SaaS LiteLLM platform uses Docker for:

1. **Local Development** - Docker Compose with PostgreSQL and Redis
2. **Production Deployment** - Container images for Railway/cloud platforms
3. **Service Isolation** - Separate containers for each component

### Architecture

```
┌─────────────────────┐
│   SaaS API (8003)   │  FastAPI wrapper with job tracking
│  (FastAPI + Python) │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ LiteLLM Proxy (8002)│  Proxy with model routing & caching
│   (LiteLLM Server)  │
└──────────┬──────────┘
           │
      ┌────┴────┐
      ▼         ▼
┌──────────┐ ┌──────────┐
│PostgreSQL│ │  Redis   │
│  (5432)  │ │  (6379)  │
└──────────┘ └──────────┘
```

---

## Quick Start

### Prerequisites

- Docker 20.10+ installed
- Docker Compose 2.0+ installed
- 4GB+ RAM available
- 10GB+ disk space

### One-Command Setup

```bash
# Clone and setup
git clone https://github.com/yourusername/SaasLiteLLM.git
cd SaasLiteLLM

# Setup environment
cp .env.example .env
nano .env  # Add your API keys

# Start everything
./scripts/docker_setup.sh
```

The script will:
1. Start PostgreSQL container
2. Start Redis container
3. Initialize database schema
4. Wait for services to be healthy

### Verify Installation

```bash
# Check all services are running
docker compose ps

# Should show:
# litellm-postgres   running   5432/tcp
# litellm-redis      running   6379/tcp

# Test database connection
docker exec -it litellm-postgres psql -U litellm_user -d litellm -c "SELECT 1;"

# Test Redis connection
docker exec -it litellm-redis redis-cli ping
```

---

## Docker Compose Setup

### Services Overview

The `docker-compose.yml` defines three core services and one optional service:

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| **postgres** | `postgres:15-alpine` | 5432 | Main database |
| **redis** | `redis:7-alpine` | 6380→6379 | Caching & rate limiting |
| **litellm** | `ghcr.io/berriai/litellm:main-latest` | 8002→4000 | LiteLLM proxy |
| **pgadmin** (optional) | `dpage/pgadmin4:latest` | 5050 | Database management UI |

### Complete docker-compose.yml

```yaml
services:
  postgres:
    image: postgres:15-alpine
    container_name: litellm-postgres
    environment:
      POSTGRES_DB: litellm
      POSTGRES_USER: litellm_user
      POSTGRES_PASSWORD: litellm_password
      POSTGRES_HOST_AUTH_METHOD: trust
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U litellm_user -d litellm"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - litellm-network

  redis:
    image: redis:7-alpine
    container_name: litellm-redis
    ports:
      - "6380:6379"  # External 6380 to avoid conflicts
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - litellm-network

  litellm:
    image: ghcr.io/berriai/litellm:main-latest
    container_name: litellm-proxy
    ports:
      - "8002:4000"
    volumes:
      - ./src/config/litellm_config.yaml:/app/config.yaml
    environment:
      DATABASE_URL: postgresql://litellm_user:litellm_password@postgres:5432/litellm
      LITELLM_MASTER_KEY: ${LITELLM_MASTER_KEY:-sk-local-dev-master-key-change-me}
      OPENAI_API_KEY: ${OPENAI_API_KEY:-}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:-}
      REDIS_HOST: redis
      REDIS_PORT: 6379
    command: ["--config", "/app/config.yaml", "--port", "4000", "--detailed_debug"]
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - litellm-network
    restart: unless-stopped

  # Optional: pgAdmin for database management
  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: litellm-pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@litellm.local
      PGADMIN_DEFAULT_PASSWORD: admin
      PGADMIN_CONFIG_SERVER_MODE: 'False'
    ports:
      - "5050:80"
    depends_on:
      - postgres
    networks:
      - litellm-network
    profiles:
      - pgadmin  # Only starts with --profile pgadmin

volumes:
  postgres_data:
  redis_data:

networks:
  litellm-network:
    driver: bridge
```

### Common Commands

```bash
# Start all services
docker compose up -d

# Start with pgAdmin
docker compose --profile pgadmin up -d

# Stop all services
docker compose down

# Stop and remove volumes (CAUTION: deletes data)
docker compose down -v

# View logs
docker compose logs -f

# View logs for specific service
docker compose logs -f postgres
docker compose logs -f redis
docker compose logs -f litellm

# Restart a service
docker compose restart postgres

# Execute command in container
docker compose exec postgres psql -U litellm_user -d litellm
docker compose exec redis redis-cli

# Check service status
docker compose ps
```

---

## Service Configuration

### PostgreSQL Configuration

#### Environment Variables

```yaml
environment:
  POSTGRES_DB: litellm          # Database name
  POSTGRES_USER: litellm_user   # Username
  POSTGRES_PASSWORD: litellm_password  # Password
  POSTGRES_HOST_AUTH_METHOD: trust     # Auth method
```

#### Initialization Script

The `docker/postgres/init.sql` script runs on first startup:

```sql
-- Create user if not exists
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'litellm_user') THEN
      CREATE USER litellm_user WITH PASSWORD 'litellm_password';
   END IF;
END
$$;

-- Grant privileges on database
GRANT ALL PRIVILEGES ON DATABASE litellm TO litellm_user;

-- Connect to litellm database
\c litellm;

-- Grant comprehensive schema privileges
GRANT ALL ON SCHEMA public TO litellm_user;
GRANT CREATE ON SCHEMA public TO litellm_user;
GRANT USAGE ON SCHEMA public TO litellm_user;

-- Grant privileges on existing tables and sequences
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO litellm_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO litellm_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO litellm_user;

-- Grant default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO litellm_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO litellm_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO litellm_user;

-- Make litellm_user the owner of the public schema
ALTER SCHEMA public OWNER TO litellm_user;

-- Create extension for UUID generation if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Basic setup complete
SELECT 'LiteLLM PostgreSQL database initialized successfully!' as message;
```

#### Custom Configuration

To customize PostgreSQL, mount a custom config:

```yaml
postgres:
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    - ./docker/postgres/postgresql.conf:/etc/postgresql/postgresql.conf
  command: postgres -c config_file=/etc/postgresql/postgresql.conf
```

### Redis Configuration

#### Basic Setup

Redis runs with default configuration, suitable for development.

#### Production Configuration

For production, create `docker/redis/redis.conf`:

```conf
# Network
bind 0.0.0.0
port 6379
protected-mode yes

# Security
requirepass your-secure-password

# Memory
maxmemory 512mb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfilename "appendonly.aof"

# Performance
tcp-backlog 511
timeout 0
tcp-keepalive 300
```

Mount configuration:

```yaml
redis:
  volumes:
    - redis_data:/data
    - ./docker/redis/redis.conf:/usr/local/etc/redis/redis.conf
  command: redis-server /usr/local/etc/redis/redis.conf
```

### LiteLLM Configuration

The LiteLLM container uses `src/config/litellm_config.yaml`:

```yaml
# Models are managed via database - add them through the dashboard UI
# Visit http://localhost:8002/ui to add models
model_list: []

# General settings
general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
  database_url: os.environ/DATABASE_URL
  store_model_in_db: true

  # Redis caching
  cache: true
  cache_params:
    type: "redis"
    host: os.environ/REDIS_HOST
    port: os.environ/REDIS_PORT
    password: os.environ/REDIS_PASSWORD
    ttl: 600  # 10 minutes

  # Cost tracking per team
  track_cost_per_deployment: true

# Router settings
router_settings:
  redis_host: os.environ/REDIS_HOST
  redis_port: os.environ/REDIS_PORT
  redis_password: os.environ/REDIS_PASSWORD
  enable_pre_call_checks: true
  routing_strategy: "usage-based-routing"
  num_retries: 3
  timeout: 600
  redis_enabled: true
```

---

## Building Custom Images

### SaaS API Image

The main `Dockerfile` builds the FastAPI SaaS API wrapper:

```dockerfile
# Dockerfile for FastAPI SaaS API Service
# This wraps LiteLLM with job-based cost tracking
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files from project root
COPY pyproject.toml ./
COPY README.md ./

# Copy application code from project root
COPY src/ ./src/

# Install build tools and Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir hatchling && \
    pip install --no-cache-dir .

# Create non-root user for security
RUN useradd -m -u 1000 saasapi && \
    chown -R saasapi:saasapi /app

USER saasapi

# Expose port (Railway will assign PORT env var)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start FastAPI application
# Use Railway's PORT env var if provided, otherwise default to 8000
CMD uvicorn src.saas_api:app --host 0.0.0.0 --port ${PORT:-8000}
```

#### Build and Run

```bash
# Build image
docker build -t saas-api:latest .

# Run locally
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e LITELLM_MASTER_KEY=sk-... \
  -e LITELLM_PROXY_URL=http://litellm:4000 \
  saas-api:latest

# Build for multiple platforms (M1/M2 Macs)
docker buildx build --platform linux/amd64,linux/arm64 -t saas-api:latest .
```

### LiteLLM Proxy Image

The `services/litellm/Dockerfile` builds a custom LiteLLM image:

```dockerfile
# Dockerfile for LiteLLM Proxy Service
# Use the official LiteLLM Docker image
FROM ghcr.io/berriai/litellm:main-latest

# Set working directory
WORKDIR /app

# Copy configuration file
COPY litellm_config.yaml /app/config.yaml

# Expose port (Railway will use PORT env var)
EXPOSE 4000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:4000/health || exit 1

# Start LiteLLM proxy
# Railway provides PORT env var, but LiteLLM uses 4000 by default
CMD ["--config", "/app/config.yaml", "--port", "4000", "--detailed_debug"]
```

#### Build and Run

```bash
# Build image
cd services/litellm
docker build -t litellm-proxy:latest .

# Run locally
docker run -p 4000:4000 \
  -e DATABASE_URL=postgresql://... \
  -e LITELLM_MASTER_KEY=sk-... \
  -e OPENAI_API_KEY=sk-... \
  -v $(pwd)/litellm_config.yaml:/app/config.yaml \
  litellm-proxy:latest
```

### Multi-Stage Builds (Optimization)

For smaller images, use multi-stage builds:

```dockerfile
# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y gcc

# Install Python dependencies
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir hatchling && \
    pip wheel --no-cache-dir --wheel-dir /app/wheels .

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir /wheels/*

# Copy application code
COPY src/ ./src/

# Create non-root user
RUN useradd -m -u 1000 saasapi && \
    chown -R saasapi:saasapi /app

USER saasapi

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD uvicorn src.saas_api:app --host 0.0.0.0 --port ${PORT:-8000}
```

---

## Production Deployment

### Railway Deployment

#### Using Pre-built Images (Recommended)

Deploy from GitHub Container Registry:

```bash
# Railway service configuration
# Image: ghcr.io/yourusername/saaslitellm/saas-api:latest
# Port: 8000
```

Environment variables in Railway:

```bash
DATABASE_URL=${{Postgres.DATABASE_URL}}
LITELLM_MASTER_KEY=sk-prod-your-key
LITELLM_PROXY_URL=http://litellm-proxy.railway.internal:4000
OPENAI_API_KEY=${{OPENAI_API_KEY}}
REDIS_HOST=${{Redis.REDIS_HOST}}
```

#### Build from Source

Railway can build directly from your repository:

1. **Connect GitHub repository**
2. **Set build context:**
   - Root directory: `/`
   - Dockerfile: `/Dockerfile`
3. **Configure environment variables**
4. **Deploy**

### Docker Compose for Production

For VPS or self-hosted deployment:

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: prod-postgres
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - prod-network
    restart: always

  redis:
    image: redis:7-alpine
    container_name: prod-redis
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - prod-network
    restart: always

  litellm:
    image: ghcr.io/berriai/litellm:main-latest
    container_name: prod-litellm
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      LITELLM_MASTER_KEY: ${LITELLM_MASTER_KEY}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      REDIS_HOST: redis
      REDIS_PORT: 6379
      REDIS_PASSWORD: ${REDIS_PASSWORD}
    volumes:
      - ./src/config/litellm_config.yaml:/app/config.yaml
    depends_on:
      - postgres
      - redis
    networks:
      - prod-network
    restart: always

  saas-api:
    image: ghcr.io/yourusername/saaslitellm/saas-api:latest
    container_name: prod-saas-api
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      LITELLM_MASTER_KEY: ${LITELLM_MASTER_KEY}
      LITELLM_PROXY_URL: http://litellm:4000
      REDIS_HOST: redis
      REDIS_PORT: 6379
      REDIS_PASSWORD: ${REDIS_PASSWORD}
      ENVIRONMENT: production
      DEBUG: false
      WORKERS: 4
    depends_on:
      - postgres
      - redis
      - litellm
    networks:
      - prod-network
    restart: always

volumes:
  postgres_data:
  redis_data:

networks:
  prod-network:
    driver: bridge
```

Deploy:

```bash
# Create .env.prod
cp .env.example .env.prod
nano .env.prod  # Set production values

# Deploy
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d

# Monitor
docker compose -f docker-compose.prod.yml logs -f
```

---

## Networking

### Docker Networks

Services communicate via the `litellm-network` bridge network:

```yaml
networks:
  litellm-network:
    driver: bridge
```

**Internal DNS:**
- Services can reach each other by service name
- `postgres` resolves to PostgreSQL container
- `redis` resolves to Redis container
- `litellm` resolves to LiteLLM container

**Example connection strings:**
```bash
# From SaaS API to LiteLLM
LITELLM_PROXY_URL=http://litellm:4000

# From LiteLLM to PostgreSQL
DATABASE_URL=postgresql://litellm_user:litellm_password@postgres:5432/litellm

# From LiteLLM to Redis
REDIS_HOST=redis
REDIS_PORT=6379
```

### Port Mapping

External ports are mapped to avoid conflicts:

| Service | Internal Port | External Port | Purpose |
|---------|--------------|---------------|---------|
| PostgreSQL | 5432 | 5432 | Database access |
| Redis | 6379 | 6380 | Cache access (avoids local Redis) |
| LiteLLM | 4000 | 8002 | Proxy API |
| SaaS API | 8000 | 8003 | Main API |
| pgAdmin | 80 | 5050 | Database UI |

**Access from host:**
```bash
# PostgreSQL
psql postgresql://litellm_user:litellm_password@localhost:5432/litellm

# Redis
redis-cli -h localhost -p 6380

# LiteLLM
curl http://localhost:8002/health

# SaaS API
curl http://localhost:8003/health
```

### Custom Networks

Create isolated networks for different environments:

```yaml
networks:
  backend:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

  frontend:
    driver: bridge
    ipam:
      config:
        - subnet: 172.21.0.0/16

services:
  postgres:
    networks:
      - backend

  saas-api:
    networks:
      - backend
      - frontend
```

---

## Volumes and Persistence

### Named Volumes

Data is persisted using Docker volumes:

```yaml
volumes:
  postgres_data:    # PostgreSQL database files
  redis_data:       # Redis persistence files
```

### Volume Management

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect saaslitellm_postgres_data

# Backup PostgreSQL
docker exec litellm-postgres pg_dump -U litellm_user litellm > backup.sql

# Restore PostgreSQL
docker exec -i litellm-postgres psql -U litellm_user litellm < backup.sql

# Backup Redis
docker exec litellm-redis redis-cli SAVE
docker cp litellm-redis:/data/dump.rdb ./redis-backup.rdb

# Remove volumes (CAUTION: deletes all data)
docker compose down -v
```

### Bind Mounts

For development, mount local files:

```yaml
litellm:
  volumes:
    - ./src/config/litellm_config.yaml:/app/config.yaml  # Config file
    - ./logs:/app/logs  # Log files
```

**Hot reload with bind mounts:**

```yaml
saas-api:
  build: .
  volumes:
    - ./src:/app/src  # Mount source code
  command: uvicorn src.saas_api:app --host 0.0.0.0 --port 8000 --reload
```

---

## Health Checks

### PostgreSQL Health Check

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U litellm_user -d litellm"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 10s
```

**Manual check:**
```bash
docker exec litellm-postgres pg_isready -U litellm_user -d litellm
```

### Redis Health Check

```yaml
healthcheck:
  test: ["CMD", "redis-cli", "ping"]
  interval: 10s
  timeout: 5s
  retries: 5
```

**Manual check:**
```bash
docker exec litellm-redis redis-cli ping
```

### Application Health Check

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  start_period: 40s
  retries: 3
```

**Manual check:**
```bash
curl http://localhost:8000/health
```

### Monitoring Health Status

```bash
# Check all health statuses
docker compose ps

# Watch health status
watch -n 2 'docker compose ps'

# Get detailed health info
docker inspect --format='{{json .State.Health}}' litellm-postgres | jq
```

---

## Troubleshooting

### Container Won't Start

**Check logs:**
```bash
docker compose logs postgres
docker compose logs redis
docker compose logs litellm
```

**Common issues:**

1. **Port already in use**
   ```
   Error: bind: address already in use
   ```
   Solution: Stop conflicting service or change port
   ```bash
   # Find process using port
   lsof -i :5432

   # Kill process or change port in docker-compose.yml
   ports:
     - "5433:5432"  # Use different external port
   ```

2. **Volume permission issues**
   ```
   Error: permission denied
   ```
   Solution: Fix volume permissions
   ```bash
   sudo chown -R $(id -u):$(id -g) ./volumes
   ```

3. **Out of memory**
   ```
   Error: Container killed (OOMKilled)
   ```
   Solution: Increase Docker memory
   ```bash
   # Docker Desktop: Settings → Resources → Memory
   # Or add to docker-compose.yml:
   deploy:
     resources:
       limits:
         memory: 2G
   ```

### Database Connection Issues

**Error:** `FATAL: database "litellm" does not exist`

```bash
# Check if database exists
docker exec litellm-postgres psql -U litellm_user -l

# Create database if missing
docker exec litellm-postgres psql -U postgres -c "CREATE DATABASE litellm;"

# Grant privileges
docker exec litellm-postgres psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE litellm TO litellm_user;"
```

**Error:** `FATAL: role "litellm_user" does not exist`

```bash
# Create user
docker exec litellm-postgres psql -U postgres -c "CREATE USER litellm_user WITH PASSWORD 'litellm_password';"
```

**Error:** `could not connect to server`

```bash
# Check if PostgreSQL is running
docker compose ps postgres

# Check PostgreSQL logs
docker compose logs postgres

# Restart PostgreSQL
docker compose restart postgres

# Check health status
docker inspect --format='{{json .State.Health}}' litellm-postgres
```

### Redis Connection Issues

**Error:** `Error connecting to Redis`

```bash
# Check if Redis is running
docker compose ps redis

# Test Redis connection
docker exec litellm-redis redis-cli ping

# Check Redis logs
docker compose logs redis

# Restart Redis
docker compose restart redis
```

**Error:** `NOAUTH Authentication required`

```bash
# If Redis has password enabled, update config
docker exec litellm-redis redis-cli -a your-password ping
```

### LiteLLM Proxy Issues

**Error:** `Connection refused to LiteLLM proxy`

```bash
# Check if LiteLLM is running
docker compose ps litellm

# Check logs for errors
docker compose logs litellm

# Test LiteLLM health endpoint
curl http://localhost:8002/health

# Verify environment variables
docker compose exec litellm env | grep LITELLM
```

**Error:** `Invalid master key`

```bash
# Check master key configuration
docker compose exec litellm env | grep LITELLM_MASTER_KEY

# Update .env file with correct key
nano .env

# Restart LiteLLM
docker compose restart litellm
```

### Performance Issues

**High CPU usage:**

```bash
# Check resource usage
docker stats

# Limit CPU usage
deploy:
  resources:
    limits:
      cpus: '2.0'
```

**High memory usage:**

```bash
# Check memory usage
docker stats

# Limit memory
deploy:
  resources:
    limits:
      memory: 2G
    reservations:
      memory: 1G
```

**Slow startup:**

```bash
# Increase health check start period
healthcheck:
  start_period: 60s  # Give more time to start
```

### Cleanup and Reset

**Remove everything and start fresh:**

```bash
# Stop all containers
docker compose down

# Remove volumes (CAUTION: deletes all data)
docker compose down -v

# Remove images
docker compose down --rmi all

# Clean up Docker system
docker system prune -a --volumes

# Restart fresh
./scripts/docker_setup.sh
```

**Rebuild images:**

```bash
# Rebuild all images
docker compose build --no-cache

# Rebuild specific service
docker compose build --no-cache saas-api

# Force pull latest base images
docker compose pull
```

### Debugging Tips

**Enter container shell:**

```bash
# PostgreSQL
docker exec -it litellm-postgres bash
psql -U litellm_user -d litellm

# Redis
docker exec -it litellm-redis sh
redis-cli

# LiteLLM (if custom image)
docker exec -it litellm-proxy bash
```

**Check environment variables:**

```bash
# List all environment variables
docker compose exec postgres env
docker compose exec redis env
docker compose exec litellm env
```

**Monitor logs in real-time:**

```bash
# All services
docker compose logs -f

# Specific service with timestamps
docker compose logs -f --timestamps postgres

# Last 100 lines
docker compose logs --tail=100 litellm
```

**Network debugging:**

```bash
# Inspect network
docker network inspect saaslitellm_litellm-network

# Test connectivity between containers
docker compose exec saas-api ping postgres
docker compose exec saas-api ping redis
docker compose exec saas-api nc -zv litellm 4000
```

---

## Best Practices

### Development

1. **Use Docker Compose** for local development
2. **Mount source code** for hot reload
3. **Use named volumes** for data persistence
4. **Enable health checks** to ensure services are ready
5. **Check logs frequently** during development

### Production

1. **Use specific image tags** (not `:latest`)
2. **Enable restart policies** (`restart: always`)
3. **Set resource limits** to prevent resource exhaustion
4. **Use secrets management** for sensitive data
5. **Enable Redis persistence** with AOF
6. **Regular backups** of PostgreSQL data
7. **Monitor health checks** and set up alerts
8. **Use multi-stage builds** for smaller images
9. **Run as non-root user** for security
10. **Keep images updated** for security patches

### Security

1. **Change default passwords** in production
2. **Use strong master keys** (32+ chars)
3. **Enable Redis authentication**
4. **Restrict network access** with firewalls
5. **Use TLS/SSL** for connections
6. **Scan images** for vulnerabilities
7. **Limit container capabilities**
8. **Use Docker secrets** for sensitive data

---

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
- [Redis Docker Image](https://hub.docker.com/_/redis)
- [LiteLLM Docker Image](https://docs.litellm.ai/docs/proxy/deploy#using-docker)
- [Railway Docker Deployment](https://docs.railway.app/deploy/dockerfiles)

---

## Support

For Docker-related issues:

1. Check container logs: `docker compose logs`
2. Verify health checks: `docker compose ps`
3. Review this troubleshooting guide
4. Check [Railway Deployment Guide](railway.md)
5. Create an issue with logs and configuration

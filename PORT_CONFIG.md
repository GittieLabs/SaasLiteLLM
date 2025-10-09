# Port Configuration

## Local Development (Ports to avoid conflicts)

- **LiteLLM Backend**: Port **8002** (configured in `.env`)
- **SaaS API Wrapper**: Port **8003** (configured in startup scripts)
- **PostgreSQL**: Port **5432**
- **Redis**: Port **6380** (avoiding conflict with existing service on 6379)
- **pgAdmin** (optional): Port **5050**

## Production/Railway Deployment

- **LiteLLM Backend**: Port **8000** (standard, set via Railway env)
- **SaaS API**: Deploy separately or use same container on different port

## Quick Start URLs (Local Dev)

- **SaaS API**: http://localhost:8003
- **SaaS API Docs**: http://localhost:8003/docs
- **LiteLLM Admin UI**: http://localhost:8002/ui (internal only)
- **LiteLLM API Docs**: http://localhost:8002/docs
- **pgAdmin**: http://localhost:5050

## Environment Variables

### Local (.env, .env.local)
```bash
PORT=8002  # LiteLLM runs on 8002
REDIS_PORT=6380  # Redis mapped to 6380
```

### Production (Railway)
```bash
PORT=8000  # Standard port for Railway
REDIS_PORT=6379  # Standard Redis port (or from Redis addon)
```

## Why Different Ports?

**Local**: Ports 8000, 8001, and 6379 are already in use by other services on your development machine.

**Production**: Uses standard ports (8000, 6379) as there are no conflicts in isolated Railway containers.

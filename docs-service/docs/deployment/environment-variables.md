# Environment Variables Reference

This document provides a comprehensive reference for all environment variables used in the SaaS LiteLLM platform.

## Table of Contents

- [Required Variables](#required-variables)
- [Optional Variables](#optional-variables)
- [Development Environment](#development-environment)
- [Production Environment](#production-environment)
- [Provider API Keys](#provider-api-keys)
- [Environment File Templates](#environment-file-templates)

## Required Variables

These variables **must** be set for the application to function properly.

### DATABASE_URL

PostgreSQL database connection string.

**Format:**
```bash
DATABASE_URL=postgresql://username:password@host:port/database
```

**Examples:**

Local Development (Docker):
```bash
DATABASE_URL=postgresql://litellm_user:litellm_password@localhost:5432/litellm
```

Railway Production:
```bash
DATABASE_URL=postgresql://postgres:password@db.railway.internal:5432/railway
```

**Notes:**
- Railway provides this automatically when you add a PostgreSQL plugin
- For local development with Docker Compose, use the credentials from `docker-compose.yml`
- Ensure the database exists before starting the application
- The user must have full privileges (CREATE, ALTER, DROP tables)

---

### LITELLM_MASTER_KEY

Master authentication key for administrative access to LiteLLM proxy.

**Format:**
```bash
LITELLM_MASTER_KEY=sk-your-secure-master-key-here
```

**Best Practices:**
- Generate a strong random string (32+ characters)
- Use a password manager to store securely
- Never commit to version control
- Rotate periodically for security

**Generation Example:**
```bash
# Generate a secure key using openssl
openssl rand -base64 32
```

**Usage:**
- Used to access LiteLLM Admin UI at `/ui`
- Required for generating team virtual keys
- Should only be used by system administrators
- Never expose to end users or teams

---

### LITELLM_PROXY_URL

URL where the LiteLLM proxy service is accessible.

**Format:**
```bash
LITELLM_PROXY_URL=http://host:port
```

**Examples:**

Local Development:
```bash
LITELLM_PROXY_URL=http://localhost:8002
```

Railway (Internal):
```bash
LITELLM_PROXY_URL=http://litellm-proxy.railway.internal:4000
```

Docker Compose (Internal):
```bash
LITELLM_PROXY_URL=http://litellm:4000
```

**Notes:**
- This is used by the SaaS API to communicate with LiteLLM backend
- In production, this should be an internal URL (not publicly accessible)
- Railway services can communicate via `.railway.internal` domains
- Port may vary: 4000 (LiteLLM default), 8002 (local dev), 8000 (production)

---

## Optional Variables

These variables provide additional functionality but have sensible defaults.

### Redis Configuration

Redis is used for caching LLM responses and rate limiting.

#### REDIS_HOST

Redis server hostname.

```bash
REDIS_HOST=localhost              # Local development
REDIS_HOST=redis                  # Docker Compose
REDIS_HOST=redis.railway.internal # Railway
```

**Default:** None (Redis features disabled if not set)

---

#### REDIS_PORT

Redis server port.

```bash
REDIS_PORT=6379  # Standard Redis port
```

**Default:** `6379`

---

#### REDIS_PASSWORD

Redis authentication password (if required).

```bash
REDIS_PASSWORD=your-redis-password
```

**Default:** None (for local development without auth)

**Notes:**
- Production Redis should always have authentication enabled
- Railway Redis provides this automatically
- Leave empty for local Docker development

---

### Server Configuration

#### HOST

Server bind address.

```bash
HOST=0.0.0.0  # Listen on all interfaces
HOST=127.0.0.1  # Listen only on localhost
```

**Default:** `0.0.0.0`

**Notes:**
- Use `0.0.0.0` for Docker containers and production
- Use `127.0.0.1` for local development if you want to restrict access

---

#### PORT

Server port number.

```bash
PORT=8000  # Production (Railway)
PORT=8003  # Local SaaS API
PORT=8002  # Local LiteLLM proxy
```

**Default:** `8000`

**Port Convention:**
- **8000**: Production deployment (Railway)
- **8002**: Local LiteLLM proxy
- **8003**: Local SaaS API wrapper
- **5432**: PostgreSQL
- **6379**: Redis
- **5050**: pgAdmin (optional)

---

#### WORKERS

Number of uvicorn worker processes.

```bash
WORKERS=1  # Development
WORKERS=4  # Production (typically CPU count × 2)
```

**Default:** `1`

**Recommendations:**
- Development: `1` (easier debugging)
- Production: `(2 × CPU cores) + 1`
- Railway: Start with `2-4` based on plan

---

#### ENVIRONMENT

Application environment identifier.

```bash
ENVIRONMENT=development
ENVIRONMENT=production
ENVIRONMENT=staging
```

**Default:** `development`

**Effects:**
- Enables/disables debug logging
- Affects error message verbosity
- Used for environment-specific behavior

---

#### DEBUG

Enable debug mode with verbose logging.

```bash
DEBUG=true   # Development
DEBUG=false  # Production
```

**Default:** `false`

**Notes:**
- Enables detailed error messages
- Shows stack traces in responses
- Increases log verbosity
- **Always set to `false` in production**

---

## Provider API Keys

API keys for LLM service providers. At least one provider key is required.

### OPENAI_API_KEY

OpenAI API key for GPT models.

```bash
OPENAI_API_KEY=sk-proj-...your-key-here
```

**Models Supported:**
- `gpt-3.5-turbo`
- `gpt-4`
- `gpt-4-turbo`
- `gpt-4o`
- Other OpenAI models

**Where to get:**
- [OpenAI Platform](https://platform.openai.com/api-keys)

---

### ANTHROPIC_API_KEY

Anthropic API key for Claude models.

```bash
ANTHROPIC_API_KEY=sk-ant-...your-key-here
```

**Models Supported:**
- `claude-3-opus`
- `claude-3-sonnet`
- `claude-3-haiku`
- `claude-3-5-sonnet`
- Other Claude models

**Where to get:**
- [Anthropic Console](https://console.anthropic.com/settings/keys)

---

### Additional Providers

LiteLLM supports 100+ providers. Add keys as needed:

```bash
# Google AI
GEMINI_API_KEY=your-key

# Azure OpenAI
AZURE_API_KEY=your-key
AZURE_API_BASE=https://your-resource.openai.azure.com
AZURE_API_VERSION=2023-05-15

# AWS Bedrock
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION_NAME=us-east-1

# Cohere
COHERE_API_KEY=your-key

# Hugging Face
HUGGINGFACE_API_KEY=your-key
```

Refer to [LiteLLM Providers Documentation](https://docs.litellm.ai/docs/providers) for complete list.

---

## Development Environment

Template for local development with Docker Compose.

### .env.local

```bash
# ==============================================
# SaaS LiteLLM - Local Development Configuration
# ==============================================

# Database Configuration (Docker PostgreSQL)
DATABASE_URL=postgresql://litellm_user:litellm_password@localhost:5432/litellm

# LiteLLM Master Key (for admin access)
LITELLM_MASTER_KEY=sk-local-dev-master-key-change-me

# LiteLLM Proxy URL (internal communication)
LITELLM_PROXY_URL=http://localhost:8002

# API Keys for LLM Providers (add your keys here)
OPENAI_API_KEY=sk-proj-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Redis Configuration (Docker Redis)
REDIS_HOST=localhost
REDIS_PORT=6380  # Note: Mapped to 6380 to avoid conflicts
REDIS_PASSWORD=

# Server Settings (Local Development)
HOST=0.0.0.0
PORT=8003
WORKERS=1
ENVIRONMENT=development
DEBUG=true
```

**Setup:**

1. Copy template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your API keys:
   ```bash
   nano .env
   ```

3. Start Docker services:
   ```bash
   ./scripts/docker_setup.sh
   ```

4. Start application:
   ```bash
   source .venv/bin/activate
   python scripts/start_local.py
   ```

---

## Production Environment

Template for Railway or other cloud deployments.

### .env (Railway)

```bash
# ==============================================
# SaaS LiteLLM - Production Configuration
# ==============================================

# Database Configuration (Railway PostgreSQL)
# Railway provides this automatically when you add PostgreSQL plugin
DATABASE_URL=${{Postgres.DATABASE_URL}}

# LiteLLM Master Key (IMPORTANT: Use a strong key!)
LITELLM_MASTER_KEY=sk-prod-your-secure-master-key-here-32-chars-min

# LiteLLM Proxy URL (Railway internal networking)
# Format: http://service-name.railway.internal:port
LITELLM_PROXY_URL=http://litellm-proxy.railway.internal:4000

# API Keys for LLM Providers
OPENAI_API_KEY=${{OPENAI_API_KEY}}
ANTHROPIC_API_KEY=${{ANTHROPIC_API_KEY}}

# Redis Configuration (Railway Redis)
# Railway provides these when you add Redis plugin
REDIS_HOST=${{Redis.REDIS_HOST}}
REDIS_PORT=${{Redis.REDIS_PORT}}
REDIS_PASSWORD=${{Redis.REDIS_PASSWORD}}

# Server Settings (Production)
HOST=0.0.0.0
PORT=8000
WORKERS=4
ENVIRONMENT=production
DEBUG=false
```

**Railway Setup:**

1. Add these variables in Railway dashboard:
   - Navigate to your service
   - Go to "Variables" tab
   - Click "New Variable" or "Raw Editor"
   - Paste variables

2. Use Railway variable references:
   ```bash
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   REDIS_HOST=${{Redis.REDIS_HOST}}
   ```

3. For sensitive keys, add as secret variables:
   - Use Railway's "Secret" variable type
   - These are encrypted at rest
   - Not visible in logs

**Security Best Practices:**

- Generate strong `LITELLM_MASTER_KEY` (32+ chars)
- Never commit `.env` to version control
- Use environment-specific keys (don't reuse dev keys in prod)
- Rotate keys periodically
- Use Railway's secret variables for sensitive data
- Enable Redis authentication in production
- Monitor usage and set up alerts

---

## Environment File Templates

### Quick Start: Copy and Customize

1. **For Local Development:**
   ```bash
   cp .env.example .env
   nano .env  # Add your API keys
   ```

2. **For Railway:**
   - Copy production template above
   - Paste into Railway Variables editor
   - Replace placeholder values

### .env.example (Starter Template)

The `.env.example` file in the repository root provides a complete template:

```bash
# Database Configuration (Railway PostgreSQL)
DATABASE_URL=postgresql://username:password@host:port/database

# LiteLLM Master Key (generate a secure random string)
LITELLM_MASTER_KEY=your-super-secure-master-key-here

# LiteLLM Proxy URL (for SaaS API to connect to LiteLLM)
# Local: http://localhost:8002
# Railway: http://litellm-proxy.railway.internal:4000
LITELLM_PROXY_URL=http://localhost:8002

# API Keys for LLM Providers
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# Redis Configuration (optional, for caching)
REDIS_HOST=
REDIS_PORT=6379
REDIS_PASSWORD=

# Server Settings
HOST=0.0.0.0
PORT=8000
WORKERS=1
ENVIRONMENT=production
DEBUG=false
```

---

## Validation and Troubleshooting

### Verify Environment Variables

Check if variables are loaded:

```bash
# Using Python
source .venv/bin/activate
python -c "from src.config.settings import settings; print(settings.database_url)"
```

### Common Issues

#### Database Connection Failed

**Error:** `could not connect to server`

**Solutions:**
1. Verify `DATABASE_URL` format
2. Check if PostgreSQL is running:
   ```bash
   docker compose ps postgres
   ```
3. Test connection:
   ```bash
   docker exec -it litellm-postgres psql -U litellm_user -d litellm
   ```

#### LiteLLM Master Key Invalid

**Error:** `Invalid master key`

**Solutions:**
1. Ensure `LITELLM_MASTER_KEY` is set
2. Check for trailing spaces or quotes
3. Verify the key matches in both LiteLLM and SaaS API

#### Redis Connection Failed

**Error:** `Error connecting to Redis`

**Solutions:**
1. Check if Redis is running:
   ```bash
   docker compose ps redis
   ```
2. Verify `REDIS_HOST` and `REDIS_PORT`
3. Test connection:
   ```bash
   docker exec -it litellm-redis redis-cli ping
   ```
4. If Redis is optional, leave variables empty

#### Provider API Key Invalid

**Error:** `Invalid API key for provider`

**Solutions:**
1. Verify key format (should start with `sk-` for most providers)
2. Check key is active in provider dashboard
3. Ensure no extra spaces or newlines
4. Test key directly with provider's API

---

## Environment Variable Precedence

Variables are loaded in this order (last wins):

1. **Default values** in `src/config/settings.py`
2. **Environment variables** from system
3. **`.env` file** in project root
4. **Command line** (if passed explicitly)

Example:
```bash
# .env file has: PORT=8000
# But you can override:
PORT=9000 python scripts/start_local.py  # Uses 9000
```

---

## Security Recommendations

1. **Never commit `.env`** - Add to `.gitignore`
2. **Use strong master keys** - 32+ random characters
3. **Rotate keys regularly** - Especially after team changes
4. **Limit key permissions** - Use read-only keys where possible
5. **Enable Redis auth** - Even in development
6. **Use secrets managers** - For production deployments
7. **Monitor key usage** - Set up alerts for unusual activity
8. **Separate environments** - Different keys for dev/staging/prod

---

## Additional Resources

- [Railway Variables Guide](https://docs.railway.app/develop/variables)
- [LiteLLM Configuration](https://docs.litellm.ai/docs/proxy/configs)
- [PostgreSQL Connection Strings](https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING)
- [Redis Configuration](https://redis.io/docs/management/config/)

---

## Support

For issues with environment variables:

1. Check this documentation
2. Verify `.env.example` template
3. Review [Local Development Guide](../deployment/local-development.md)
4. Review [Railway Deployment Guide](../deployment/railway.md)
5. Create an issue with your configuration (redact sensitive values)

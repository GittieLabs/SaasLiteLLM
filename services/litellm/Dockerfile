# Dockerfile for LiteLLM Proxy Service
# Use the official LiteLLM Docker image
FROM ghcr.io/berriai/litellm:main-latest

# Set working directory
WORKDIR /app

# Copy configuration file from project root
COPY src/config/litellm_config.yaml /app/config.yaml

# Expose port (Railway will use PORT env var)
EXPOSE 4000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:4000/health || exit 1

# Start LiteLLM proxy
# Railway provides PORT env var, but LiteLLM uses 4000 by default
CMD ["--config", "/app/config.yaml", "--port", "4000", "--detailed_debug"]

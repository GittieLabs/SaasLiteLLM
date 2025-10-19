# Dockerfile for LiteLLM Proxy Service
# Use the official LiteLLM Docker image
FROM ghcr.io/berriai/litellm:main-latest

# Set working directory
WORKDIR /app

# Copy configuration file
COPY litellm_config.yaml /app/config.yaml

# Expose port (Railway will use PORT env var)
EXPOSE 4000

# Health check - use PORT env var if available, fallback to 4000
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-4000}/health || exit 1

# Start LiteLLM proxy
# The base image ENTRYPOINT is docker/prod_entrypoint.sh which runs litellm
# We just need to pass arguments via CMD
# Use shell form to allow environment variable expansion
CMD --config /app/config.yaml --port ${PORT:-4000} --detailed_debug

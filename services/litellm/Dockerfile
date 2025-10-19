# Dockerfile for LiteLLM Proxy Service
# Use the official LiteLLM Docker image
FROM ghcr.io/berriai/litellm:main-latest

# Set working directory
WORKDIR /app

# Copy configuration file
COPY litellm_config.yaml /app/config.yaml

# Copy custom entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose port (Railway will use PORT env var)
EXPOSE 4000

# Health check - use PORT env var if available, fallback to 4000
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-4000}/health || exit 1

# Use our custom entrypoint that supports Railway's dynamic PORT env var
ENTRYPOINT ["/app/entrypoint.sh"]

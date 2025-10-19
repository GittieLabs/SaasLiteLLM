#!/bin/sh
# Custom entrypoint for LiteLLM proxy to support Railway's dynamic PORT
# Falls back to port 4000 for local development
exec litellm --config /app/config.yaml --port ${PORT:-4000} --detailed_debug

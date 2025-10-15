#!/bin/bash
# Start script for MkDocs documentation server on Railway

# Use Railway's PORT variable, default to 8004 for local dev
PORT=${PORT:-8004}

echo "Starting MkDocs documentation server on port $PORT..."
python -m http.server $PORT --directory site

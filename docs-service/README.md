# MkDocs Documentation Service

This directory contains the Dockerfile for deploying the SaaS LiteLLM documentation to Railway.

## Railway Configuration

**Service Settings:**
- **Dockerfile Path:** `docs-service/Dockerfile`
- **Root Directory:** (leave empty - uses repository root)

**Environment Variables:**
- None needed - `PORT` is automatically provided by Railway

## Build Process

The Dockerfile will:
1. Install MkDocs and dependencies from `requirements-docs.txt`
2. Copy documentation source from `docs/` directory
3. Build static site with `mkdocs build`
4. Serve the `site/` directory using Python's HTTP server

## Local Testing

From repository root:
```bash
docker build -f docs-service/Dockerfile -t saas-docs .
docker run -p 8004:8004 -e PORT=8004 saas-docs
```

Then visit http://localhost:8004

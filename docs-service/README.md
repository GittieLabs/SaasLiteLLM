# MkDocs Documentation Service

This directory contains everything needed to deploy the SaaS LiteLLM documentation to Railway as a standalone service.

## Directory Structure

```
docs-service/
├── Dockerfile              # Docker build configuration
├── README.md              # This file
├── requirements-docs.txt  # Python dependencies (MkDocs, etc.)
├── mkdocs.yml            # MkDocs configuration
├── start_docs.sh         # Server startup script
└── docs/                 # Documentation source files (Markdown)
```

**Note:** Files in this directory are copies from the repository root to make the service self-contained for Railway deployment.

## Railway Configuration

**Service Settings:**
- **Root Directory:** `docs-service`
- **Dockerfile Path:** `Dockerfile` (relative to root directory)

**Environment Variables:**
- None needed - `PORT` is automatically provided by Railway

## Build Process

The Dockerfile will:
1. Install MkDocs and dependencies from `requirements-docs.txt`
2. Copy documentation source from `docs/` directory
3. Build static site with `mkdocs build`
4. Serve the `site/` directory using Python's HTTP server on `$PORT`

## Local Testing

From this directory:
```bash
docker build -t saas-docs .
docker run -p 8004:8004 -e PORT=8004 saas-docs
```

Then visit http://localhost:8004

## Keeping Files in Sync

When updating documentation:
1. Edit files in the repository root (`../docs/`, `../mkdocs.yml`, etc.)
2. Copy updated files to this directory:
   ```bash
   cp ../requirements-docs.txt ../mkdocs.yml ../start_docs.sh .
   cp -r ../docs .
   ```
3. Commit all changes

# Development Guidelines

## Branch Protection & Workflow

This repository has branch protection rules enabled on `main`. All changes should follow proper Git workflow:

### Standard Development Process

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/bug-description
   ```

2. **Make Changes & Commit**
   ```bash
   git add .
   git commit -m "feat: description of changes"
   ```

3. **Push to Remote**
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Create Pull Request**
   - Go to GitHub repository
   - Create PR from feature branch to `main`
   - Wait for CI/CD checks to pass
   - Request review if needed
   - Merge PR once approved

5. **Update Version Numbers** (if releasing)
   - See versioning section below

### When to Bypass Branch Protection

**ONLY** in emergency situations:
- Critical production bugs
- Security vulnerabilities
- Service outages

If you must bypass:
1. Document the reason in commit message
2. Create a follow-up issue to track
3. Update version numbers immediately after
4. Consider creating a post-incident review

## Versioning

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR** (x.0.0): Breaking changes
- **MINOR** (0.x.0): New features, backward compatible
- **PATCH** (0.0.x): Bug fixes, backward compatible

### Version Files

Update these files when releasing:
- `pyproject.toml` - Backend API version
- `admin-panel/package.json` - Admin panel version

### Example Version Bump

```bash
# For a new feature (minor version)
# pyproject.toml: 0.1.0 → 0.2.0
# package.json: 1.0.0 → 1.1.0

# Commit the version bump
git add pyproject.toml admin-panel/package.json
git commit -m "chore: bump version to 0.2.0 / 1.1.0"
git push
```

## Recent History

### Direct Commits to Main (to be avoided)

- **2025-10-20**: Version bump to 0.2.0 / 1.1.0 (cleanup after emergency fixes)
- **2025-10-20**: Added credential name support for model aliases (bypassed protection)
- **2025-10-20**: Fixed LITELLM_PROXY_URL environment variable (emergency fix)
- **2025-10-20**: Added dark mode and improved button visibility (bypassed protection)
- **2025-10-20**: Added organization dropdown to team creation (bypassed protection)

**Action Items**: Going forward, all non-emergency changes should use feature branches and PRs.

## CI/CD Pipeline

The repository expects the following checks to pass:
- `deploy` - Railway deployment status check

Ensure all checks pass before merging PRs.

## Testing Locally

### Backend (SaaS API)
```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run locally
uvicorn src.main:app --reload
```

### Frontend (Admin Panel)
```bash
cd admin-panel

# Install dependencies
npm install

# Run dev server
npm run dev

# Build for production
npm run build
```

## Deployment

Deployment is automatic via Railway when changes are pushed to `main`:
- **saas-api** service: Deploys backend API
- **saas-admin-panel** service: Deploys admin panel
- **litellm-proxy** service: LiteLLM proxy (separate service)

Monitor deployments: `railway logs`

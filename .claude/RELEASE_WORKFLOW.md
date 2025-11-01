# Release Workflow

This document defines the required workflow for all code changes merged to main.

## ⚠️ MANDATORY: Always Follow This Workflow

Whenever you push commits or merge PRs into main, you **MUST** follow these steps:

### 1. Update Version Numbers

**Before** pushing/merging to main, update version numbers in:

- `pyproject.toml` - Backend version (line 3)
- `admin-panel/package.json` - Admin panel version (line 3)

**Version Bumping Rules:**
- **Patch (x.x.PATCH)** - Bug fixes, documentation updates, small changes
- **Minor (x.MINOR.x)** - New features, non-breaking changes
- **Major (MAJOR.x.x)** - Breaking changes, architectural changes

### 2. Create Git Tag

After changes are merged to main:

```bash
# Patch release (most common)
git tag -a v1.0.X -m "Release v1.0.X - Brief description"

# Minor release
git tag -a v1.X.0 -m "Release v1.X.0 - Brief description"

# Major release
git tag -a vX.0.0 -m "Release vX.0.0 - Brief description"
```

### 3. Push Tag to Remote

```bash
git push origin vX.X.X
```

### 4. Create GitHub Release

```bash
gh release create vX.X.X --title "vX.X.X - Title" --notes "Release notes..."
```

**Release notes should include:**
- 🐛 Bug Fixes
- ✨ New Features
- 📚 Documentation Updates
- 🔧 Version Numbers
- 📝 Files Changed

### 5. Verify Railway Deployment

Check that Railway auto-deployed the changes:

```bash
railway status
railway logs --service saas-api | tail -20
```

**If auto-deploy didn't trigger:**
```bash
railway up --service saas-api
```

## Example Workflow

```bash
# 1. Update versions
# Edit pyproject.toml: version = "1.0.2"
# Edit admin-panel/package.json: "version": "1.3.1"

# 2. Commit version bump
git add pyproject.toml admin-panel/package.json
git commit -m "chore: Bump version to 1.0.2"
git push origin main

# 3. Create and push tag
git tag -a v1.0.2 -m "Release v1.0.2 - Fix XYZ bug"
git push origin v1.0.2

# 4. Create GitHub release
gh release create v1.0.2 --title "v1.0.2 - Bug Fix" --notes "..."

# 5. Verify deployment
railway status
```

## Why This Matters

- **Versioning** - Tracks changes over time
- **Releases** - Provides changelog for users
- **Deployment** - Ensures production is updated
- **Traceability** - Links code changes to releases
- **Documentation** - Release notes explain what changed

## Common Mistakes to Avoid

❌ **DON'T:**
- Push to main without updating version numbers
- Merge PRs without creating a release tag
- Skip GitHub release creation
- Forget to verify Railway deployment

✅ **DO:**
- Update versions in every PR/push to main
- Create descriptive release tags
- Write clear release notes
- Confirm deployment succeeded

## Notes

- The version in `pyproject.toml` should match the git tag
- Admin panel version can be independent if only admin changes
- Always use semantic versioning (MAJOR.MINOR.PATCH)
- Include commit SHAs in release notes for traceability

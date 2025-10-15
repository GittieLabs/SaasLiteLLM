# Branch Protection Setup Guide

This document describes the recommended branch protection rules for the SaasLiteLLM repository to ensure code quality and proper review processes.

## Overview

Branch protection rules help maintain code quality by:
- Requiring pull request reviews before merging
- Preventing accidental force pushes to main
- Ensuring status checks pass before merging
- Preventing direct commits to protected branches

## Recommended Settings for `main` Branch

### Accessing Branch Protection Settings

1. Navigate to: `https://github.com/GittieLabs/SaasLiteLLM/settings/branches`
2. Click "Add branch protection rule" or edit existing rule for `main`
3. Apply the settings below:

### Protection Rule Configuration

#### Branch name pattern
```
main
```

#### Protect matching branches

**Require a pull request before merging** ✅
- Required approvals: **1**
- ✅ Dismiss stale pull request approvals when new commits are pushed
- ✅ Require review from Code Owners (optional - if using CODEOWNERS file)
- ✅ Require approval of the most recent reviewable push
- ❌ Require conversation resolution before merging (optional - helps ensure all comments are addressed)

**Require status checks to pass before merging** ✅
- ✅ Require branches to be up to date before merging
- **Status checks to require**: (these will appear after first runs)
  - `Deploy Documentation` (from `.github/workflows/deploy-docs.yml`)
  - Any CI/CD checks you add later (tests, linting, etc.)

**Require conversation resolution before merging** ❌
- Optional: Enable if you want all review comments resolved before merge

**Require signed commits** ❌
- Optional: Enable for additional security

**Require linear history** ❌
- Optional: Prevents merge commits, enforces rebase/squash

**Require deployments to succeed before merging** ❌
- Not applicable for this project

**Lock branch** ❌
- Don't enable - makes branch read-only

**Do not allow bypassing the above settings** ✅
- Even admins must follow the rules
- Can be unchecked if you need admin bypass capability

**Restrict who can push to matching branches** ❌
- Leave unchecked to allow all collaborators to create PRs
- Optional: Enable and add specific users/teams if needed

**Allow force pushes** ❌
- Prevents rewriting history on main branch

**Allow deletions** ❌
- Prevents accidental deletion of main branch

## Additional Recommendations

### 1. Add CODEOWNERS File (Optional)

Create `.github/CODEOWNERS` to automatically request reviews from specific people:

```
# Default owners for everything
*       @keithelliott

# Specific paths
/docs/  @keithelliott
/src/   @keithelliott
```

### 2. Configure Required Status Checks

After your first PR with tests or CI/CD:
1. Go to branch protection settings
2. Add the status check names that appear
3. Common checks to add:
   - `test` - Unit test suite
   - `lint` - Code quality checks
   - `build` - Build verification

### 3. Repository Settings

Other repository settings to configure:

#### General Settings (`/settings`)
- ❌ Allow merge commits
- ✅ Allow squash merging (recommended)
- ✅ Allow rebase merging (optional)
- ✅ Automatically delete head branches (clean up merged PR branches)

#### Pull Requests (`/settings`)
- ✅ Always suggest updating pull request branches
- ✅ Allow auto-merge
- ❌ Automatically delete head branches (clean up after merge)

## Workflow After Setup

### Creating Changes

1. **Never commit directly to `main`**
   ```bash
   # Instead, create a feature branch
   git checkout -b feature/my-new-feature

   # Make changes and commit
   git add .
   git commit -m "feat: add new feature"

   # Push to your branch
   git push origin feature/my-new-feature
   ```

2. **Create Pull Request**
   - Go to GitHub repository
   - Click "Compare & pull request"
   - Fill out the PR template
   - Request review from maintainers

3. **Address Review Comments**
   - Make requested changes
   - Push additional commits to the same branch
   - Re-request review when ready

4. **Merge**
   - Once approved and status checks pass
   - Use "Squash and merge" (recommended)
   - Delete the feature branch after merge

### For Maintainers

When reviewing PRs:
1. Check code quality and adherence to standards
2. Verify tests pass
3. Test functionality if needed
4. Leave constructive feedback
5. Approve when satisfied
6. Squash and merge

## Emergency Procedures

### Hotfix Process

For critical production fixes:
1. Create `hotfix/*` branch from `main`
2. Make minimal fix
3. Create PR with "HOTFIX" prefix
4. Get expedited review
5. Merge and deploy

### Bypass Protection (Last Resort)

If you absolutely must bypass protection:
1. Go to branch protection settings
2. Temporarily uncheck "Do not allow bypassing"
3. Make the change
4. Re-enable protection immediately
5. Document why bypass was necessary

## Verification

After setting up branch protection:

1. **Test the protection:**
   ```bash
   # Try to push directly to main (should fail)
   git checkout main
   echo "test" >> README.md
   git commit -am "test: should fail"
   git push origin main
   # Expected: Error about branch protection
   ```

2. **Test PR workflow:**
   - Create a feature branch
   - Push changes
   - Create PR
   - Verify you need approval
   - Test merge after approval

## Support

For questions about branch protection:
- GitHub Docs: [About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- Create an issue in the repository

---

**Last Updated**: 2025-10-15
**Version**: 1.0

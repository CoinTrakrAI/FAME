# GitHub Container Registry (GHCR) Setup Guide

## Problem: "denied: installation not allowed to Write organization package"

This error occurs when GitHub Actions cannot write to organization packages in GHCR. This requires **organization-level settings** to be configured.

## Solutions

### Option 1: Enable Organization Settings (Recommended)

1. Go to your GitHub organization: `https://github.com/organizations/CoinTrakrAI/settings/actions`
2. Navigate to **Actions** → **General**
3. Under **Workflow permissions**, ensure:
   - ✅ "Read and write permissions" is selected
   - ✅ "Allow GitHub Actions to create and approve pull requests" is enabled
4. Navigate to **Packages** settings (if available)
5. Ensure package creation is enabled for the organization

### Option 2: Use Personal Access Token (PAT) - Alternative Solution

If organization settings cannot be changed, use a Personal Access Token:

1. **Create a PAT:**
   - Go to: `https://github.com/settings/tokens`
   - Click "Generate new token (classic)"
   - Name: `GHCR_PAT` or `FAME_GHCR_TOKEN`
   - Select scopes:
     - ✅ `write:packages` (required)
     - ✅ `read:packages` (optional, for pulling images)
     - ✅ `delete:packages` (optional, for cleanup)
   - Click "Generate token"
   - **Copy the token immediately** (you won't see it again!)

2. **Add PAT as Secret:**
   - Go to repository: `https://github.com/CoinTrakrAI/FAME/settings/secrets/actions`
   - Click "New repository secret"
   - Name: `GHCR_PAT`
   - Value: (paste the token from step 1)
   - Click "Add secret"

3. **Workflows will automatically use PAT if available:**
   - The workflows check for `GHCR_PAT` secret first
   - If not found, they fall back to `GITHUB_TOKEN`
   - No code changes needed once the secret is added!

## Verification

After making changes:

1. **Trigger a workflow run** (push to main or manually trigger)
2. **Check the workflow logs** for the "Login to GHCR" step
3. **Look for:**
   - ✅ Success: "Login Succeeded" or "Successfully authenticated"
   - ❌ Failure: "denied: installation not allowed..." (still need settings/PAT)

## Current Workflow Configuration

All workflows (`ci.yml`, `deploy-ec2.yml`, `cd.yml`) are configured to:
- ✅ Request `packages: write` permission
- ✅ Request `id-token: write` for OIDC
- ✅ Try `GHCR_PAT` secret first (if available)
- ✅ Fall back to `GITHUB_TOKEN` if PAT not found

## Troubleshooting

### Still Getting "denied" Error?

1. **Check organization permissions:**
   - Ensure you're an organization owner/admin
   - Organization settings → Actions → Workflow permissions must allow write access

2. **Verify PAT:**
   - PAT must have `write:packages` scope
   - PAT must not be expired
   - Secret name must be exactly `GHCR_PAT`

3. **Check workflow permissions:**
   - Workflow files must have `packages: write` in permissions section
   - All workflows have been updated with this permission

4. **Alternative: Use user package instead of organization:**
   - Change image tag from `ghcr.io/cointrakrai/fame-api` to `ghcr.io/YOUR_USERNAME/fame-api`
   - This uses your personal account instead of organization (not recommended for production)

## References

- [GitHub Container Registry Documentation](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [GitHub Actions Permissions](https://docs.github.com/en/actions/security-guides/automatic-token-authentication)
- [Configuring package access for your organization](https://docs.github.com/en/packages/learn-github-packages/configuring-a-packages-access-control-and-visibility)


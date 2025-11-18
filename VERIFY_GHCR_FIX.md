# GHCR Permissions Verification

## ✅ Organization Settings Updated

You've successfully updated:
- ✅ Actions → General → Workflow permissions: **"Read and write permissions"**
- ✅ **"Allow GitHub Actions to create and approve pull requests"** enabled

## ✅ Workflow Configuration Verified

All workflows are configured with:
- ✅ `packages: write` permission at top level
- ✅ Direct `docker login` command authentication
- ✅ PAT fallback support (GHCR_PAT → GITHUB_TOKEN)
- ✅ Proper token logging

## 🧪 Next Steps: Verification

### 1. Trigger a Workflow Run

Push a commit to `main` branch or manually trigger a workflow:

```bash
# Make a small change and push
echo "# Test GHCR fix" >> test.md
git add test.md
git commit -m "Test: Verify GHCR permissions fix"
git push origin main
```

### 2. Monitor the Workflow

Go to: `https://github.com/CoinTrakrAI/FAME/actions`

Look for:
- ✅ "Login to GHCR" step should show: "Using GITHUB_TOKEN (fallback)" or "Using GHCR_PAT"
- ✅ Docker login should succeed: "Login Succeeded"
- ✅ Build should complete without "denied: installation not allowed" error
- ✅ Image should be pushed to: `ghcr.io/cointrakrai/fame-api:latest`

### 3. Verify Package Creation

If the package doesn't exist yet, check:
- Go to: `https://github.com/orgs/CoinTrakrAI/packages`
- If you see: "denied: installation not allowed to Write organization package"
- You may need: **Organization Settings → Packages → Allow members to create packages**

## 🔍 Troubleshooting

### Still Getting "denied: installation not allowed"?

1. **Check Package Creation Settings:**
   - Go to: `https://github.com/organizations/CoinTrakrAI/settings/packages`
   - Ensure: "Allow members to create packages" is enabled

2. **Verify Workflow Permissions:**
   - Workflow must have `packages: write` at top level (✅ already set)
   - Check workflow logs for actual permission errors

3. **Use PAT as Alternative:**
   - If org settings can't be changed, add `GHCR_PAT` secret
   - Create PAT with `write:packages` scope
   - Workflows will automatically use PAT if available

4. **Check Organization Membership:**
   - Ensure the GitHub user/account running the workflow is a member of `CoinTrakrAI` org
   - Organization members must have package write permissions

## ✅ Success Indicators

When everything works, you should see in workflow logs:
```
Login to GHCR
Using GITHUB_TOKEN (fallback)
WARNING! Your password will be stored unencrypted...
Login Succeeded

Build & push image
...
#28 exporting to image
#28 pushing layers
#28 pushing layers done
#28 DONE
```

And in GitHub Packages:
- Package: `ghcr.io/cointrakrai/fame-api` exists
- Latest tag is pushed
- Can pull: `docker pull ghcr.io/cointrakrai/fame-api:latest`

## 📝 Notes

- The workflow uses lowercase `cointrakrai` (not `CoinTrakrAI`) as required by Docker
- Token logging shows which authentication method is being used
- If `GHCR_PAT` secret exists, it will be used instead of `GITHUB_TOKEN`
- All workflows (`ci.yml`, `deploy-ec2.yml`, `cd.yml`) are configured identically


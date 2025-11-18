# FAME Deployment Options - EC2 Instance Sizing

## ❌ **PROBLEM: t3.micro is Too Small for Full AGI Stack**

Your current `requirements_production.txt` includes:
- transformers (needs 4GB+ RAM)
- sentence-transformers (needs 2GB+ RAM)
- chromadb (needs 2GB+ RAM)
- faiss-cpu (needs 4GB+ RAM for compile)
- PyTorch (needs 4GB+ RAM minimum)
- accelerate, scikit-learn, pyarrow, lxml (all heavy)

**Total requirement:** ~4-6 GB RAM for Docker build + runtime

**t3.micro has:** 1 GB RAM total (insufficient)

---

## ✅ **OPTION A: Upgrade to t3.large (RECOMMENDED)**

### Why t3.large?
- **8 GB RAM** - Enough for full AGI stack
- **2 vCPU** - Faster builds and better performance
- **Cost:** ~$0.0832/hour (~$60/month)
- **Full AGI capabilities** - All features enabled

### Steps:

1. **Stop EC2 Instance:**
   - AWS Console → EC2 → Instances → Select instance
   - Instance state → Stop instance

2. **Change Instance Type:**
   - Actions → Instance settings → Change instance type
   - Select: **t3.large**
   - Apply

3. **Start Instance:**
   - Instance state → Start instance
   - Wait for status check to pass

4. **Redeploy:**
   ```powershell
   .\deploy_ec2.ps1
   ```

5. **Use Full Requirements:**
   - Uses `requirements_production.txt` (already configured)
   - Full AGI capabilities enabled

---

## ⚠️ **OPTION B: Stay on t3.micro (MINIMAL BUILD)**

### Trade-offs:
- ❌ **No AGI features** (transformers, sentence-transformers, chromadb removed)
- ❌ **No vector memory** (chromadb/faiss removed)
- ❌ **No local LLM** (transformers removed)
- ✅ **Basic API works** (FastAPI, requests, yfinance, basic scraping)
- ✅ **Cost:** ~$0.0104/hour (~$7.50/month)

### Steps:

1. **Use Minimal Dockerfile:**
   ```powershell
   # On EC2, use minimal compose file
   sudo docker-compose -f docker-compose.prod.micro.yml up -d --build
   ```

2. **Or Deploy Locally:**
   ```powershell
   # Copy minimal compose file to EC2
   scp -i "C:\Users\cavek\Downloads\FAME.pem" docker-compose.prod.micro.yml ec2-user@3.135.222.143:/home/ec2-user/FAME_Desktop/
   scp -i "C:\Users\cavek\Downloads\FAME.pem" Dockerfile.minimal ec2-user@3.135.222.143:/home/ec2-user/FAME_Desktop/
   scp -i "C:\Users\cavek\Downloads\FAME.pem" requirements_production_minimal.txt ec2-user@3.135.222.143:/home/ec2-user/FAME_Desktop/
   ```

3. **Deploy:**
   ```bash
   # On EC2
   cd /home/ec2-user/FAME_Desktop
   sudo docker-compose -f docker-compose.prod.micro.yml down
   sudo docker-compose -f docker-compose.prod.micro.yml build --no-cache
   sudo docker-compose -f docker-compose.prod.micro.yml up -d
   ```

---

## 📊 **Comparison**

| Feature | t3.micro (Minimal) | t3.large (Full) |
|---------|-------------------|-----------------|
| **RAM** | 1 GB | 8 GB |
| **vCPU** | 1 | 2 |
| **Cost/month** | ~$7.50 | ~$60 |
| **AGI Features** | ❌ No | ✅ Yes |
| **Transformers** | ❌ No | ✅ Yes |
| **Vector Memory** | ❌ No | ✅ Yes |
| **Local LLM** | ❌ No | ✅ Yes |
| **Basic API** | ✅ Yes | ✅ Yes |
| **Financial Data** | ✅ Yes | ✅ Yes |
| **Web Scraping** | ✅ Yes | ✅ Yes |

---

## 🔧 **Fixes Applied**

1. ✅ **Dockerfile** - Added `curl` for healthcheck
2. ✅ **docker-compose.prod.yml** - Simplified healthcheck (uses curl)
3. ✅ **PowerShell scripts** - Fixed SSH key path quoting
4. ✅ **Dockerfile.minimal** - Created for t3.micro deployments
5. ✅ **requirements_production_minimal.txt** - Stripped down version

---

## 🚀 **Recommendation**

**Use t3.large** for production FAME AGI system. The minimal build removes core AGI capabilities that FAME relies on.

If budget is a constraint, consider:
- **t3.medium** (4 GB RAM) - May work with optimized build
- **Spot instances** - 70% cheaper for t3.large
- **Reserved instances** - 30-60% discount for 1-3 year commitments

---

**Last Updated:** 2025-01-18


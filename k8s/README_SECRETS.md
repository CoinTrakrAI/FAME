# Kubernetes Secrets Setup for FAME

## 🔐 **Creating Secrets**

### **Method 1: kubectl create (Recommended)**

```bash
# Create namespace first
kubectl create namespace fame

# Create secret with all FAME API keys
kubectl -n fame create secret generic fame-secrets \
  --from-literal=OPENAI_API_KEY="$OPENAI_API_KEY" \
  --from-literal=ELEVENLABS_API_KEY="f2e121c82fa6cd50dd7094029c335c5e3ac10d6cef698ca7a6c1770662de20b7" \
  --from-literal=ELEVENLABS_VOICE_ID="W9UYe7tosbBFWdXWaZZo" \
  --from-literal=ALPHA_VANTAGE_API_KEY="3GEY3XZMBLJGQ099" \
  --from-literal=COINGECKO_API_KEY="CG-PwNH6eV5PhUhFMhHspq3nqoz" \
  --from-literal=FINNHUB_API_KEY="d3vpeq1r01qhm1tedo10d3vpeq1r01qhm1tedo1g" \
  --from-literal=SERPAPI_KEY="$SERPAPI_KEY" \
  --from-literal=SERPAPI_BACKUP_KEY="$SERPAPI_BACKUP_KEY" \
  --from-literal=NEWSAPI_KEY="$NEWSAPI_KEY" \
  --from-literal=GNEWS_API_KEY="$GNEWS_API_KEY" \
  --from-literal=POSTGRES_PASSWORD="$(openssl rand -base64 32)"
```

### **Method 2: From .env file**

```bash
# Export variables from .env
source .env

# Create secret
kubectl -n fame create secret generic fame-secrets \
  --from-literal=OPENAI_API_KEY="$OPENAI_API_KEY" \
  --from-literal=ELEVENLABS_API_KEY="$ELEVENLABS_API_KEY" \
  --from-literal=ALPHA_VANTAGE_API_KEY="$ALPHA_VANTAGE_API_KEY" \
  --from-literal=COINGECKO_API_KEY="$COINGECKO_API_KEY" \
  --from-literal=FINNHUB_API_KEY="$FINNHUB_API_KEY" \
  --from-literal=SERPAPI_KEY="$SERPAPI_KEY" \
  --from-literal=SERPAPI_BACKUP_KEY="$SERPAPI_BACKUP_KEY" \
  --from-literal=NEWSAPI_KEY="$NEWSAPI_KEY" \
  --from-literal=GNEWS_API_KEY="$GNEWS_API_KEY" \
  --from-literal=POSTGRES_PASSWORD="$(openssl rand -base64 32)"
```

### **Method 3: Using secret.yaml.template**

```bash
# Edit k8s/secret.yaml.template with your values
# Then apply:
kubectl -n fame apply -f k8s/secret.yaml.template
```

## 🔑 **GitHub Secrets for CI/CD**

In GitHub repository settings → Secrets and variables → Actions, add:

1. **KUBE_CONFIG** (base64-encoded kubeconfig):
   ```bash
   # Get your kubeconfig and encode it
   cat ~/.kube/config | base64 -w 0
   # Paste the output into GitHub secret KUBE_CONFIG
   ```

2. **GITHUB_TOKEN** (automatically provided, but ensure it has package write permissions)

## 📋 **Required Secrets**

- `OPENAI_API_KEY` - OpenAI API key
- `ELEVENLABS_API_KEY` - ElevenLabs TTS API key
- `ELEVENLABS_VOICE_ID` - FAME voice ID (W9UYe7tosbBFWdXWaZZo)
- `ALPHA_VANTAGE_API_KEY` - Alpha Vantage API key
- `COINGECKO_API_KEY` - CoinGecko API key
- `FINNHUB_API_KEY` - Finnhub API key
- `SERPAPI_KEY` - SERPAPI primary key
- `SERPAPI_BACKUP_KEY` - SERPAPI backup key
- `NEWSAPI_KEY` - NewsAPI key
- `GNEWS_API_KEY` - GNews API key
- `POSTGRES_PASSWORD` - Database password (generate secure random)

## ✅ **Verify Secrets**

```bash
# List secrets
kubectl -n fame get secrets

# View secret (values will be base64 encoded)
kubectl -n fame get secret fame-secrets -o yaml

# Decode a specific key
kubectl -n fame get secret fame-secrets -o jsonpath='{.data.OPENAI_API_KEY}' | base64 -d
```

## 🚨 **Security Notes**

- Never commit secrets to Git
- Use secret managers (AWS Secrets Manager, GCP Secret Manager) in production
- Rotate secrets regularly
- Use least-privilege access for service accounts
- Consider using External Secrets Operator for automatic secret sync


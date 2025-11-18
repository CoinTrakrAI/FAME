# FAME Kubernetes Deployment

Production-ready Kubernetes manifests for deploying FAME on EKS (AWS) or GKE (Google Cloud).

## Quick Start

### Prerequisites

- Kubernetes cluster (EKS, GKE, or other)
- `kubectl` configured to access your cluster
- Container registry access (GHCR or Docker Hub)
- API keys stored as Kubernetes secrets

### 1. Create Namespace and Secrets

```bash
# Create namespace
kubectl apply -f k8s/deployment.yaml -n fame

# Create secrets (replace with your actual keys)
kubectl create secret generic fame-secrets \
  --from-literal=GOOGLE_AI_KEY="your_key" \
  --from-literal=SERPAPI_KEY="your_key" \
  --from-literal=ALPHA_VANTAGE_API_KEY="your_key" \
  --from-literal=FINNHUB_API_KEY="your_key" \
  -n fame

# Or from env file
kubectl create secret generic fame-secrets --from-env-file=.env -n fame
```

### 2. Deploy FAME

```bash
# Apply all manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n fame
kubectl get svc -n fame
```

### 3. Configure Ingress (Optional)

Edit `k8s/ingress.yaml` with your domain name, then:

```bash
kubectl apply -f k8s/ingress.yaml
```

## Files Overview

- **deployment.yaml**: Main deployment, service, PVC, and namespace
- **hpa.yaml**: Horizontal Pod Autoscaler for auto-scaling
- **ingress.yaml**: Ingress configuration for external access
- **secrets.yaml.example**: Example secret template (DO NOT commit real secrets!)

## AWS EKS Specific

```bash
# Deploy to EKS
kubectl apply -f k8s/deployment.yaml

# Get LoadBalancer URL
kubectl get svc fame-api-service -n fame

# View logs
kubectl logs -f deployment/fame-api -n fame
```

## Google GKE Specific

```bash
# Deploy to GKE
kubectl apply -f k8s/deployment.yaml

# Get LoadBalancer URL
kubectl get svc fame-api-service -n fame

# View logs
kubectl logs -f deployment/fame-api -n fame
```

## Monitoring

```bash
# Check pod status
kubectl get pods -n fame -w

# View logs
kubectl logs -f deployment/fame-api -n fame

# Describe pod for events
kubectl describe pod <pod-name> -n fame

# Check HPA
kubectl get hpa -n fame
```

## Scaling

HPA automatically scales based on CPU/memory usage. Manual scaling:

```bash
kubectl scale deployment fame-api --replicas=5 -n fame
```

## Troubleshooting

```bash
# Check events
kubectl get events -n fame --sort-by='.lastTimestamp'

# Describe deployment
kubectl describe deployment fame-api -n fame

# Shell into pod
kubectl exec -it <pod-name> -n fame -- /bin/bash

# View container logs
kubectl logs <pod-name> -n fame --previous
```

## Customization

- **Replicas**: Edit `spec.replicas` in `deployment.yaml`
- **Resources**: Adjust `resources.requests/limits` in `deployment.yaml`
- **Storage**: Modify PVC size in `deployment.yaml`
- **Autoscaling**: Tune HPA thresholds in `hpa.yaml`


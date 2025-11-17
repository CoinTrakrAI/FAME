# FAME Minimal Viable Production Deployment Guide

This guide walks you through deploying the containerised FAME stack locally (Docker Desktop) and on an AWS EC2 host. It assumes Phase 6+ artifacts are present, including the FastAPI gateway, health endpoints, and Prometheus-ready metrics.

---

## 1. Prerequisites

| Requirement | Local (Docker Desktop) | AWS EC2 |
|-------------|------------------------|---------|
| OS          | Windows/macOS/Linux with Docker Desktop ≥ 4.28 | Amazon Linux 2023 or Ubuntu 22.04 |
| CPU / RAM   | ≥ 4 vCPUs, 8 GB RAM recommended | t3.micro works for smoke testing |
| Software    | Docker Desktop + Compose | Docker Engine + docker compose plugin |
| Ports       | 8080 (API), optional 9090/9100 for further observability | same |

Clone the repo to the host and ensure `git` + `python` are available for running tests if desired.

---

## 2. Environment Variables

1. Copy `config/env.example` to `.env` at project root.
2. Populate the values with your real API keys or secret references. Example:

```bash
cp config/env.example .env
```

You can also inject secrets via AWS Systems Manager Parameter Store or AWS Secrets Manager: map them into environment variables before launching containers (e.g., with `aws ssm get-parameters ... --with-decryption`).

> **Security Tip:** `.env` is ignored in the Docker build and `.dockerignore` ensures it is not baked into the image. Provide values at runtime via `env_file`, `docker run --env-file`, or orchestrator secrets.

---

## 3. Local Deployment (Docker Desktop)

```bash
# build and start (development profile)
docker compose -f docker-compose.dev.yml build
docker compose -f docker-compose.dev.yml up -d

# follow logs
docker compose -f docker-compose.dev.yml logs -f fame
```

- API available at: <http://localhost:8080/docs>
- Health endpoints:
  - Liveness: `http://localhost:8080/healthz`
  - Readiness: `http://localhost:8080/readyz`
- Docker HEALTHCHECK uses `scripts/docker_healthcheck.py` to fail the container if readiness flips.

To rebuild after code changes:

```bash
docker compose -f docker-compose.dev.yml up -d --build
```

Stop and remove:

```bash
docker compose -f docker-compose.dev.yml down
```

---

## 4. AWS EC2 Deployment

1. Launch an EC2 instance (e.g., Amazon Linux 2023, t3.micro) with security group allowing inbound TCP/8080.
2. SSH into the instance and install Docker:

```bash
sudo yum update -y
sudo yum install docker -y
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user
logout  # then SSH back in to refresh group membership
```

3. Install docker-compose plugin:

```bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-linux-x86_64" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

4. Clone the repo and prepare env:

```bash
git clone https://github.com/<your-org>/FAME_Desktop.git
cd FAME_Desktop
cp config/env.example .env
# Populate secrets via vim/echo or pull from AWS SSM/Secrets Manager
# Example SSM fetch (requires IAM role/credentials):
# aws ssm get-parameter --name "/fame/OPENAI_API_KEY" --with-decryption --query 'Parameter.Value' --output text >> .env
```

5. Build & run (production profile):

```bash
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

6. Verify:

```bash
curl http://localhost:8080/healthz
curl http://localhost:8080/readyz
curl -X POST http://localhost:8080/query -H "Content-Type: application/json" -d '{"text": "hello FAME"}'
```

7. Expose externally using the instance public IP / DNS (ensure Security Group inbound 8080).

8. To stop services:

```bash
docker compose -f docker-compose.prod.yml down
```

---

## 5. Operational Notes

- **Logs**: Container logs stream to stdout/stderr for ingestion via CloudWatch Logs, ELK, etc. Enable `FAME_LOG_AGGREGATION=1` to buffer structured events.
- **Metrics**: Prometheus scraping can be enabled by exposing the telemetry ports defined in earlier phases (e.g., trading telemetry exporter).
- **Scaling**: For multi-instance setups, externalise the `.env` via AWS Systems Manager Parameter Store, integrate ALB health checks against `/readyz`, and consider ECR for image registry.
- **Updates**: Build a fresh image and redeploy (`docker compose up -d --build`). For AWS, pre-build images locally and push to ECR, or build on the instance.

---

## 6. Troubleshooting

| Symptom | Fix |
|---------|-----|
| `docker compose build` fails due to network | `sudo systemctl restart docker`; ensure outbound internet |
| Container unhealthy | `docker logs <container>` then inspect `/healthz` payload; confirm dependent API keys |
| Permission denied (Docker) | Ensure `ec2-user` is in `docker` group and re-login |
| Slow responses | Check `/healthz` warnings (CPU/memory) and telemetry exporters |

For deeper hardening (Option A), integrate reverse proxies (nginx), TLS termination, IAM roles for secrets, and multi-stage CI/CD pipelines. This MVP guide gives you a working baseline for both local and internet-accessible deployments. />


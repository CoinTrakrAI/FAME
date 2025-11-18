# syntax=docker/dockerfile:1.5

FROM python:3.11-slim AS builder

ARG DEBIAN_FRONTEND=noninteractive

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    libc6-dev \
 && rm -rf /var/lib/apt/lists/*

COPY requirements_production.txt .

# Install CPU-only PyTorch first to avoid CUDA libraries (saves ~2GB)
RUN pip install --upgrade pip \
 && pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install and build wheels in stages to save space
# Install tzdata first as it's required by pandas but may not be built as wheel
RUN pip install --no-cache-dir tzdata

# Build wheels for all requirements
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements_production.txt \
 && rm -rf ~/.cache/pip /tmp/* \
 && find /wheels -name "*.whl" -size +200M -delete 2>/dev/null || true

# Also build tzdata wheel explicitly
RUN pip wheel --no-cache-dir --wheel-dir /wheels tzdata || true

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    FAME_ENV=production

WORKDIR /app

# Install curl for healthcheck and basic system tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN adduser --disabled-password --gecos "" fame

COPY --from=builder /app/requirements_production.txt .

# Install CPU-only PyTorch first (already installed in builder but need to reinstall here)
RUN pip install --upgrade pip \
 && pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install all requirements directly from PyPI (we have network access)
# This is simpler and more reliable than using wheels
RUN pip install --no-cache-dir -r requirements_production.txt

COPY . /app

# Create logs and data directories with proper permissions (before USER switch)
# Remove any existing logs that might have wrong permissions
RUN rm -rf /app/logs /app/data 2>/dev/null || true && \
    mkdir -p /app/logs /app/data && \
    chown -R fame:fame /app && \
    chmod -R 777 /app/logs /app/data && \
    chmod -R 755 /app

COPY scripts/docker_healthcheck.py /usr/local/bin/docker_healthcheck.py
RUN chmod +x /usr/local/bin/docker_healthcheck.py

USER fame

HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=40s \
  CMD python /usr/local/bin/docker_healthcheck.py || exit 1

EXPOSE 8080

ENTRYPOINT ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8080"]


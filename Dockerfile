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
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements_production.txt \
 && rm -rf ~/.cache/pip /tmp/* \
 && find /wheels -name "*.whl" -size +200M -delete 2>/dev/null || true

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    FAME_ENV=production

WORKDIR /app

RUN adduser --disabled-password --gecos "" fame

COPY --from=builder /wheels /wheels
COPY --from=builder /app/requirements_production.txt .

# Install tzdata first (required by pandas but may not be in wheels)
RUN pip install --no-cache-dir tzdata || true

# Install from wheels, but allow PyPI fallback for missing packages
RUN pip install --no-cache-dir --prefer-binary --find-links=/wheels -r requirements_production.txt || \
    pip install --no-cache-dir --prefer-binary --find-links=/wheels --no-index -r requirements_production.txt 2>/dev/null || \
    pip install --no-cache-dir -r requirements_production.txt

RUN rm -rf /wheels

COPY . /app

RUN chown -R fame:fame /app

COPY scripts/docker_healthcheck.py /usr/local/bin/docker_healthcheck.py
RUN chmod +x /usr/local/bin/docker_healthcheck.py

USER fame

HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=40s \
  CMD python /usr/local/bin/docker_healthcheck.py || exit 1

EXPOSE 8080

ENTRYPOINT ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8080"]


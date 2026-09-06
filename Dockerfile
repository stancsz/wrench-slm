FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch with CUDA support
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cu124

# Copy project code
COPY wrench /app/wrench
COPY data /app/data
COPY models /app/models

ENV PYTHONUNBUFFERED=1
ENV LEAN_ROUTER_LOGS_DIR=/gateway_logs
ENV SIDECAR_PORT=4010

EXPOSE 4010

CMD ["python", "-u", "-m", "wrench.sidecar"]

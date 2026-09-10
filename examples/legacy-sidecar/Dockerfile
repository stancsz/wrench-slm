FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install the pinned CUDA PyTorch build for the historical native sidecar
RUN pip install --no-cache-dir numpy && \
    pip install --no-cache-dir torch==2.9.1 --index-url https://download.pytorch.org/whl/cu128

# Copy project code
COPY wrench /app/wrench
COPY data /app/data
RUN mkdir -p /app/models

ENV PYTHONUNBUFFERED=1
ENV LEAN_ROUTER_LOGS_DIR=/gateway_logs
ENV SIDECAR_PORT=4010

EXPOSE 4010

CMD ["python", "-u", "-m", "wrench.sidecar"]

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install NumPy and PyTorch with CUDA 12.8 nightly support (Blackwell sm_120 / RTX 50-series)
RUN pip install --no-cache-dir numpy && \
    pip install --no-cache-dir --pre torch --index-url https://download.pytorch.org/whl/nightly/cu128

# Copy project code
COPY wrench /app/wrench
COPY data /app/data
COPY models /app/models

ENV PYTHONUNBUFFERED=1
ENV LEAN_ROUTER_LOGS_DIR=/gateway_logs
ENV SIDECAR_PORT=4010

EXPOSE 4010

CMD ["python", "-u", "-m", "wrench.sidecar"]

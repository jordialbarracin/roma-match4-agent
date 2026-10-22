# Official AMD ROCm PyTorch Base Image (Mandated by AMD AI League)
FROM rocm/pytorch:rocm6.2_ubuntu22.04_py3.10_pytorch_2.3.0

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV AGENT_OUTPUT=/app/output

# Working directory
WORKDIR /app

# Install system dependencies (curl for healthchecks, lxml dependencies)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements with --no-deps to preserve ROCm PyTorch
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --no-deps -r /app/requirements.txt \
    && pip install --no-cache-dir \
       anyio \
       certifi \
       sniffio \
       idna \
       h11 \
       httpcore \
       starlette \
       click

# Copy application source code
COPY . /app

# Ensure output directory exists and scripts are executable
RUN mkdir -p /app/output && chmod +x /app/entrypoint.sh /app/app.py

# Healthcheck
HEALTHCHECK --interval=5s --timeout=3s --retries=5 CMD curl -f http://127.0.0.1:8000/health || exit 1

# Resident daemon entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python3", "/app/app.py", "--serve"]

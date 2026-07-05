# ---- Stage 1: Build ----
FROM python:3.12-slim AS builder

WORKDIR /app

# Install only what's needed to build, nothing extra
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ---- Stage 2: Runtime ----
FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY main.py .
COPY scrape.py .

# Create directories for output
RUN mkdir -p articles logs

# hashes.json is the state file that MUST persist between runs.
# Mount it as a volume:  -v /host/path/hashes.json:/app/hashes.json
# Logs can also be persisted:  -v /host/path/logs:/app/logs

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "main.py"]

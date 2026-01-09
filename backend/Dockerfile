# Multi-stage build for minimal final image
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /workspace

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Ensure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Add workspace to PYTHONPATH so app module can be imported
ENV PYTHONPATH=/workspace:$PYTHONPATH

# Copy application code and configuration
COPY app /workspace/app
COPY tests /workspace/tests
COPY alembic.ini /workspace/alembic.ini
COPY alembic /workspace/alembic

# Default command runs uvicorn server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

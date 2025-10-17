FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements.txt /app/
COPY web/backend/requirements-web.txt /app/web/backend/

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt && \
    pip install --no-cache-dir -r /app/web/backend/requirements-web.txt

# Copy project files
COPY . /app/

# Set Python path to include project root
ENV PYTHONPATH=/app

# Copy and set up entrypoint script
COPY web/backend/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run the application
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "web.backend.api:app", "--host", "0.0.0.0", "--port", "8000"]

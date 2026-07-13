FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application code
COPY app.py .
COPY agents/ ./agents/
COPY utils/ ./utils/

# Expose port
EXPOSE 5000

# Run with gunicorn in production, flask in development
ENV FLASK_ENV=production
CMD ["python", "app.py"]

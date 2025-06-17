FROM python:3.11-slim

# Install system dependencies and Python tools
RUN apt-get update && apt-get install -y \
    python3-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    imagemagick \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip setuptools wheel

# Create user early
RUN useradd -u 1000 -m appuser

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with verbose output to see errors
RUN pip install --no-cache-dir moviepy==1.0.3 || { echo "Error installing moviepy"; exit 1; } && \
    pip install --no-cache-dir -r requirements.txt || { echo "Error installing requirements"; exit 1; } && \
    pip install --no-cache-dir instagrapi==2.0.0 || { echo "Error installing instagrapi"; exit 1; }

# Configure ImageMagick policy
RUN if [ -f /etc/ImageMagick-6/policy.xml ]; then \
    sed -i 's/rights="none" pattern="@\*"/rights="read|write" pattern="@*"/' /etc/ImageMagick-6/policy.xml; \
    else \
    sed -i 's/rights="none" pattern="@\*"/rights="read|write" pattern="@*"/' /etc/ImageMagick/policy.xml; \
    fi

# Create necessary directories
RUN mkdir -p /tmp/uploads && \
    chown -R appuser:appuser /tmp/uploads

# Copy application code
COPY app/ ./app/
COPY config/ ./config/

# Set all permissions
RUN chown -R appuser:appuser /app

# Run the application with lower privileges
USER appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/appuser/.local/bin:$PATH"

# Run the application
CMD ["python", "app/main.py"]
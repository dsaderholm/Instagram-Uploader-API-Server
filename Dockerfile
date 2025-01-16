FROM python:3.11-slim

# Install system dependencies and Python tools
RUN apt-get update && apt-get install -y \
    ffmpeg \
    python3-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    imagemagick \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip setuptools wheel

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Configure ImageMagick policy
RUN if [ -f /etc/ImageMagick-6/policy.xml ]; then \
    sed -i 's/rights="none" pattern="@\*"/rights="read|write" pattern="@*"/' /etc/ImageMagick-6/policy.xml; \
    else \
    sed -i 's/rights="none" pattern="@\*"/rights="read|write" pattern="@*"/' /etc/ImageMagick/policy.xml; \
    fi

# Create necessary directories
RUN mkdir -p /app/config/sessions /tmp/uploads

# Copy application code
COPY app/ ./app/
COPY config/ ./config/
COPY sounds/ ./sounds/

# Set permissions
RUN chmod -R 755 /app && \
    chmod -R 777 /tmp/uploads /app/config/sessions

# Run the application with lower privileges
USER 1000:1000

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/user/.local/bin:$PATH"

# Run the application
CMD ["python", "app/main.py"]
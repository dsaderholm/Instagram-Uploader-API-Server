FROM python:3.9-slim

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

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir moviepy>=1.0.3

# Configure ImageMagick policy
RUN if [ -f /etc/ImageMagick-6/policy.xml ]; then \
    sed -i 's/rights="none" pattern="@\*"/rights="read|write" pattern="@*"/' /etc/ImageMagick-6/policy.xml; \
    else \
    sed -i 's/rights="none" pattern="@\*"/rights="read|write" pattern="@*"/' /etc/ImageMagick/policy.xml; \
    fi

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY config/ ./config/
COPY sounds/ ./sounds/

# Create necessary directories
RUN mkdir -p /app/config/sessions

# Run the application
CMD ["python", "app/main.py"]
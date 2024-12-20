FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    python3-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app/app
RUN mkdir -p /app/uploads /app/sounds /app/config

ENV PYTHONPATH=/app
EXPOSE 8048
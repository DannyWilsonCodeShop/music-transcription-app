FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for YouTube downloading
RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app.py .

# Run the application
CMD ["python", "app.py"]
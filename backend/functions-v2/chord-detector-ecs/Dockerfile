FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for audio processing and compilation
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Install Cython first (required for Madmom)
RUN pip install --no-cache-dir cython>=0.29.0 numpy>=1.24.0

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app.py .

# Run the application
CMD ["python", "app.py"]

FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for audio processing, Essentia, and compilation
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    gcc \
    g++ \
    make \
    libyaml-dev \
    libfftw3-dev \
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev \
    libswresample-dev \
    libsamplerate0-dev \
    libtag1-dev \
    libchromaprint-dev \
    python3-dev \
    python3-numpy \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Cython first (required for Essentia)
RUN pip install --no-cache-dir cython>=0.29.0 numpy>=1.24.0

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app.py .
COPY test_chord_detection.py .

# Run the application
CMD ["python", "app.py"]

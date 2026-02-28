FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for audio processing and essentia
RUN apt-get update && apt-get install -y \
    build-essential \
    libyaml-dev \
    libfftw3-dev \
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev \
    libswresample-dev \
    libsamplerate0-dev \
    libtag1-dev \
    libchromaprint-dev \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app.py .
COPY section_detection.py .

# Copy simple-pipeline directory for downbeat detection and chord detection modules
COPY simple-pipeline ./simple-pipeline

# Run the application
CMD ["python", "app.py"]

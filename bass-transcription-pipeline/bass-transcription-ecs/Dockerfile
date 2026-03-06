FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY bass-transcription-pipeline/bass-transcription-ecs/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY bass-transcription-pipeline/bass-transcription-ecs/app.py .
COPY bass-transcription-pipeline/bass-transcription-ecs/bass_note_transcription.py .
COPY bass-transcription-pipeline/bass-transcription-ecs/stem_transcription.py .
COPY bass-transcription-pipeline/bass-transcription-ecs/song_metadata_lyrics.py .
COPY bass-transcription-pipeline/bass-transcription-ecs/test_imports.py .

# Copy simple-pipeline for downbeat detection (reuse existing code)
# Note: Build context must include parent directory
# Build with: docker build -f bass-transcription-ecs/Dockerfile -t image-name .
COPY simple-pipeline ./simple-pipeline

# Run the application
CMD ["python", "app.py"]

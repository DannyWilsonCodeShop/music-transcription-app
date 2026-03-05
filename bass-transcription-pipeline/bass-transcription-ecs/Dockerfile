FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY bass_note_transcription.py .
COPY stem_transcription.py .
COPY song_metadata_lyrics.py .
COPY test_imports.py .

# Copy simple-pipeline for downbeat detection (reuse existing code)
COPY simple-pipeline ./simple-pipeline

# Run the application
CMD ["python", "app.py"]

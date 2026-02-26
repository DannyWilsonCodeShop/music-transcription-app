FROM python:3.11-slim

# Install yt-dlp, ffmpeg, and required dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    pip install --no-cache-dir yt-dlp boto3 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Verify ffmpeg is installed
RUN ffmpeg -version

# Copy application code
COPY app.py /app/app.py
WORKDIR /app

# Run the application
CMD ["python", "app.py"]

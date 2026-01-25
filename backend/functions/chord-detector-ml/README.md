# Chord Detector ML Function

This Lambda function uses machine learning to detect chords from audio files.

## Features

- Uses Basic Pitch for chord detection
- TensorFlow-based ML model
- Processes audio files from S3
- Returns chord progressions with timestamps

## Dependencies

- basic-pitch: ML model for chord detection
- TensorFlow: Deep learning framework
- librosa: Audio processing
- numpy/scipy: Numerical computing

## Docker Image

This function runs as a Docker container in AWS Lambda.

**Build Status**: The Docker image is automatically built by GitHub Actions when code changes are pushed.

## Last Updated

January 25, 2026 - Testing GitHub Actions workflow

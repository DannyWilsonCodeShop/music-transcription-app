"""
ECS Task: Chord Detector with Librosa
Runs as a Fargate task, processes audio and updates DynamoDB
Uses Librosa's chromagram-based chord detection
"""

import json
import boto3
import os
import logging
import sys
import numpy as np
from decimal import Decimal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

JOBS_TABLE = os.environ['DYNAMODB_JOBS_TABLE']

# Import Librosa
try:
    import librosa
    LIBROSA_AVAILABLE = True
    logger.info(f"Librosa version: {librosa.__version__}")
except ImportError as e:
    logger.error(f"Librosa not available: {e}")
    LIBROSA_AVAILABLE = False

# Chord templates (12 major + 12 minor chords)
CHORD_LABELS = [
    'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B',  # Major
    'Cm', 'C#m', 'Dm', 'D#m', 'Em', 'Fm', 'F#m', 'Gm', 'G#m', 'Am', 'A#m', 'Bm'  # Minor
]

def convert_to_decimal(obj):
    """Convert floats to Decimal for DynamoDB compatibility"""
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: convert_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_decimal(item) for item in obj]
    return obj

def main():
    """Main entry point for ECS task"""
    
    # Get parameters from environment (passed from Lambda)
    job_id = os.environ.get('JOB_ID')
    bucket = os.environ.get('AUDIO_BUCKET')
    key = os.environ.get('AUDIO_KEY')
    
    if not all([job_id, bucket, key]):
        logger.error(f"Missing required environment variables. JOB_ID={job_id}, AUDIO_BUCKET={bucket}, AUDIO_KEY={key}")
        sys.exit(1)
    
    logger.info(f"Processing job {job_id}: {bucket}/{key}")
    logger.info(f"Using DynamoDB table: {JOBS_TABLE}")
    
    try:
        # Update status
        update_job_status(job_id, 'DETECTING_CHORDS', 70)
        
        # Download audio from S3
        audio_path = f'/tmp/{job_id}.mp3'
        logger.info(f"Downloading from S3: {bucket}/{key}")
        s3_client.download_file(bucket, key, audio_path)
        
        # Detect chords (using mock for now)
        logger.info("Running chord detection...")
        chords_data = detect_chords(audio_path)
        
        # Convert floats to Decimal for DynamoDB
        chords_data = convert_to_decimal(chords_data)
        
        # Update job with chords
        table = dynamodb.Table(JOBS_TABLE)
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET chordsData = :chords, #status = :status, progress = :progress, updatedAt = :updated',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':chords': chords_data,
                ':status': 'CHORDS_DETECTED',
                ':progress': 85,
                ':updated': 'ecs-task'
            }
        )
        
        logger.info("Chord detection complete!")
        
        # Clean up
        if os.path.exists(audio_path):
            os.remove(audio_path)
        
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        update_job_status(job_id, 'FAILED', 0, str(e))
        sys.exit(1)

def detect_chords(audio_path):
    """
    Detect chords using Librosa's chromagram analysis
    Uses chroma features to identify chord progressions
    """
    
    if not LIBROSA_AVAILABLE:
        logger.error("Librosa not available, cannot detect chords")
        raise Exception("Librosa library not installed")
    
    try:
        logger.info(f"Loading audio file with Librosa: {audio_path}")
        
        # Load audio file
        y, sr = librosa.load(audio_path, sr=22050)
        duration = librosa.get_duration(y=y, sr=sr)
        
        logger.info(f"Audio loaded: duration={duration:.2f}s, sample_rate={sr}Hz")
        
        # Extract chroma features (pitch class profiles)
        hop_length = 512
        chromagram = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop_length)
        
        logger.info(f"Chromagram shape: {chromagram.shape}")
        
        # Define chord templates (major and minor triads)
        chord_templates = create_chord_templates()
        
        # Match chromagram to chord templates
        chord_sequence = match_chords_to_templates(chromagram, chord_templates, hop_length, sr)
        
        # Group consecutive same chords into segments
        chord_segments = group_chord_segments(chord_sequence)
        
        # Filter out very short segments (likely noise)
        chord_segments = [s for s in chord_segments if s['duration'] >= 0.5]
        
        # Detect key
        key = detect_key(chord_segments)
        
        logger.info(f"Detected {len(chord_segments)} chord segments, key: {key}, duration: {duration:.2f}s")
        
        return {
            'chords': chord_segments,
            'key': key,
            'model': 'librosa-chromagram',
            'totalChords': len(chord_segments),
            'duration': round(duration, 2)
        }
        
    except Exception as e:
        logger.error(f"Librosa chord detection failed: {str(e)}", exc_info=True)
        raise

def create_chord_templates():
    """Create chord templates for major and minor triads"""
    templates = {}
    
    # Major chord template: root, major third, perfect fifth (0, 4, 7 semitones)
    major_template = np.array([1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0])
    
    # Minor chord template: root, minor third, perfect fifth (0, 3, 7 semitones)
    minor_template = np.array([1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0])
    
    # Create templates for all 12 major chords
    for i in range(12):
        chord_name = CHORD_LABELS[i]
        templates[chord_name] = np.roll(major_template, i)
    
    # Create templates for all 12 minor chords
    for i in range(12):
        chord_name = CHORD_LABELS[i + 12]
        templates[chord_name] = np.roll(minor_template, i)
    
    return templates

def match_chords_to_templates(chromagram, templates, hop_length, sr):
    """Match each frame of chromagram to best matching chord template"""
    chord_sequence = []
    
    for frame_idx in range(chromagram.shape[1]):
        chroma_frame = chromagram[:, frame_idx]
        
        # Normalize chroma frame
        if np.sum(chroma_frame) > 0:
            chroma_frame = chroma_frame / np.sum(chroma_frame)
        
        # Find best matching chord template
        best_chord = 'N'
        best_score = 0
        
        for chord_name, template in templates.items():
            # Compute correlation between chroma frame and template
            score = np.dot(chroma_frame, template)
            
            if score > best_score:
                best_score = score
                best_chord = chord_name
        
        # Only accept chord if confidence is high enough
        if best_score < 0.3:
            best_chord = 'N'
        
        # Calculate timestamp
        time = librosa.frames_to_time(frame_idx, sr=sr, hop_length=hop_length)
        
        chord_sequence.append({
            'time': time,
            'chord': best_chord,
            'confidence': best_score
        })
    
    return chord_sequence

def group_chord_segments(chord_sequence):
    """Group consecutive same chords into segments"""
    if not chord_sequence:
        return []
    
    segments = []
    current_chord = chord_sequence[0]['chord']
    start_time = chord_sequence[0]['time']
    
    for i in range(1, len(chord_sequence)):
        chord = chord_sequence[i]['chord']
        time = chord_sequence[i]['time']
        
        if chord != current_chord:
            # Save previous segment (skip 'N' chords)
            if current_chord != 'N':
                segments.append({
                    'chord': current_chord,
                    'start': round(start_time, 2),
                    'end': round(time, 2),
                    'duration': round(time - start_time, 2)
                })
            
            current_chord = chord
            start_time = time
    
    # Add final segment
    if current_chord != 'N':
        end_time = chord_sequence[-1]['time']
        segments.append({
            'chord': current_chord,
            'start': round(start_time, 2),
            'end': round(end_time, 2),
            'duration': round(end_time - start_time, 2)
        })
    
    return segments

def detect_key(chord_segments):
    """Detect musical key based on chord frequency and duration"""
    
    # Count chord occurrences weighted by duration
    chord_weights = {}
    
    for segment in chord_segments:
        chord = segment['chord']
        if chord != 'N':
            # Remove minor suffix for root note
            root = chord.replace('m', '')
            duration = segment['duration']
            chord_weights[root] = chord_weights.get(root, 0) + duration
    
    if not chord_weights:
        return 'C'  # Default
    
    # Most common root is likely the key
    key = max(chord_weights, key=chord_weights.get)
    
    # Check if it's minor key (if minor chords dominate)
    minor_duration = sum(s['duration'] for s in chord_segments if 'm' in s['chord'])
    major_duration = sum(s['duration'] for s in chord_segments if s['chord'] != 'N' and 'm' not in s['chord'])
    
    if minor_duration > major_duration:
        key += 'm'
    
    return key

def update_job_status(job_id, status, progress, error=None):
    """Update job status in DynamoDB"""
    try:
        table = dynamodb.Table(JOBS_TABLE)
        update_expr = 'SET #status = :status, progress = :progress, updatedAt = :updated'
        expr_values = {
            ':status': status,
            ':progress': progress,
            ':updated': 'ecs-task'
        }
        
        if error:
            update_expr += ', errorMessage = :error'
            expr_values[':error'] = error
        
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues=expr_values
        )
    except Exception as e:
        logger.error(f"Failed to update job status: {str(e)}")

if __name__ == '__main__':
    main()

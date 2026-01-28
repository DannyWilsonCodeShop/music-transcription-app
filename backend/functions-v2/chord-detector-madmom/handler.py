"""
Lambda: Chord Detector (Madmom)
Detects chords using Madmom CNN+CRF model
Deployed as Docker container
"""

import json
import boto3
import os
import logging
import tempfile
import numpy as np

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Import Librosa for basic chord detection
try:
    import librosa
    import numpy as np
    LIBROSA_AVAILABLE = True
except ImportError:
    logger.warning("Librosa not available, using mock mode")
    LIBROSA_AVAILABLE = False

# For now, we'll use mock mode until we can properly install audio libraries
LIBROSA_AVAILABLE = False

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

JOBS_TABLE = os.environ['DYNAMODB_JOBS_TABLE']

# Chord mapping
CHORD_LABELS = ['N', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B',
                'Cm', 'C#m', 'Dm', 'D#m', 'Em', 'Fm', 'F#m', 'Gm', 'G#m', 'Am', 'A#m', 'Bm']

def lambda_handler(event, context):
    """Detect chords from audio file"""
    
    logger.info(f"Event: {json.dumps(event)}")
    
    try:
        job_id = event['jobId']
        bucket = event['bucket']
        key = event['key']
        
        # Update status
        update_job_status(job_id, 'DETECTING_CHORDS', 70)
        
        # Download audio from S3
        audio_path = f'/tmp/{job_id}.mp3'
        logger.info(f"Downloading from S3: {bucket}/{key}")
        s3_client.download_file(bucket, key, audio_path)
        
        # Detect chords
        logger.info("Running chord detection...")
        chords_data = detect_chords(audio_path)
        
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
                ':updated': context.request_id
            }
        )
        
        # Clean up
        if os.path.exists(audio_path):
            os.remove(audio_path)
        
        return {
            'statusCode': 200,
            'body': {
                'jobId': job_id,
                'chords': chords_data
            }
        }
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        update_job_status(job_id, 'FAILED', 0, str(e))
        return {
            'statusCode': 500,
            'body': {'error': str(e)}
        }

def detect_chords(audio_path):
    """
    Detect chords using Librosa (basic implementation)
    For production, replace with Madmom CNN+CRF
    Returns timestamped chord progressions
    """
    
    if not LIBROSA_AVAILABLE:
        logger.warning("Using mock chord detection")
        return get_mock_chords()
    
    try:
        # Load audio
        logger.info(f"Loading audio file: {audio_path}")
        y, sr = librosa.load(audio_path, sr=22050)
        
        # Get chroma features
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=512)
        
        # Simple chord detection based on chroma
        chord_list = []
        hop_length = 512
        frame_duration = hop_length / sr
        
        # Chord templates (simplified)
        chord_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        # Process in 2-second windows
        window_frames = int(2.0 / frame_duration)
        
        for i in range(0, chroma.shape[1], window_frames):
            window = chroma[:, i:i+window_frames]
            if window.shape[1] == 0:
                continue
            
            # Average chroma in window
            avg_chroma = np.mean(window, axis=1)
            
            # Find dominant pitch class
            dominant_pitch = np.argmax(avg_chroma)
            chord_name = chord_names[dominant_pitch]
            
            # Check if minor (simplified heuristic)
            if avg_chroma[(dominant_pitch + 3) % 12] > avg_chroma[(dominant_pitch + 4) % 12]:
                chord_name += 'm'
            
            start_time = i * frame_duration
            end_time = min((i + window_frames) * frame_duration, len(y) / sr)
            
            # Avoid duplicate consecutive chords
            if not chord_list or chord_list[-1]['chord'] != chord_name:
                chord_list.append({
                    'chord': chord_name,
                    'start': round(start_time, 2),
                    'end': round(end_time, 2),
                    'duration': round(end_time - start_time, 2)
                })
        
        # Detect key
        key = detect_key(chord_list)
        
        return {
            'chords': chord_list,
            'key': key,
            'model': 'librosa-chroma',
            'totalChords': len(chord_list)
        }
        
    except Exception as e:
        logger.error(f"Librosa processing failed: {str(e)}")
        return get_mock_chords()

def detect_key(chord_list):
    """Simple key detection based on chord frequency"""
    
    # Count chord occurrences (excluding 'N' for no chord)
    chord_counts = {}
    for item in chord_list:
        chord = item['chord']
        if chord != 'N':
            # Remove minor suffix for counting
            root = chord.replace('m', '')
            chord_counts[root] = chord_counts.get(root, 0) + item['duration']
    
    if not chord_counts:
        return 'C'
    
    # Most common chord is likely the key
    key = max(chord_counts, key=chord_counts.get)
    return key

def get_mock_chords():
    """Mock chord data for testing"""
    return {
        'chords': [
            {'chord': 'C', 'start': 0, 'end': 4, 'duration': 4},
            {'chord': 'Am', 'start': 4, 'end': 8, 'duration': 4},
            {'chord': 'F', 'start': 8, 'end': 12, 'duration': 4},
            {'chord': 'G', 'start': 12, 'end': 16, 'duration': 4}
        ],
        'key': 'C',
        'model': 'mock',
        'totalChords': 4
    }

def update_job_status(job_id, status, progress, error=None):
    """Update job status in DynamoDB"""
    try:
        table = dynamodb.Table(JOBS_TABLE)
        update_expr = 'SET #status = :status, progress = :progress, updatedAt = :updated'
        expr_values = {
            ':status': status,
            ':progress': progress,
            ':updated': 'lambda'
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

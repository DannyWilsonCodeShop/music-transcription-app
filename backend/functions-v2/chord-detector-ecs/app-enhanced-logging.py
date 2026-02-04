"""
ECS Task: Chord Detector with Enhanced Logging
Comprehensive logging to debug the 60% stuck issue
"""

import os
import json
import boto3
import librosa
import numpy as np
from scipy.signal import find_peaks
import time
import sys
import traceback

# AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

# Environment variables
JOBS_TABLE = os.environ.get('DYNAMODB_JOBS_TABLE', 'ChordScout-Jobs-V2-dev')
PDF_GENERATOR_FUNCTION = os.environ.get('PDF_GENERATOR_FUNCTION', 'chordscout-v2-pdf-generator-dev')

def log(message, level="INFO"):
    """Enhanced logging with timestamps and flush"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}", flush=True)
    sys.stdout.flush()

def main():
    """Main entry point for ECS task"""
    log("=" * 80)
    log("STARTING CHORD DETECTION ECS TASK")
    log("=" * 80)
    
    # Get parameters from environment
    job_id = os.environ.get('JOB_ID')
    bucket = os.environ.get('AUDIO_BUCKET') or os.environ.get('BUCKET')
    key = os.environ.get('AUDIO_KEY') or os.environ.get('KEY')
    
    log(f"Environment Variables:")
    log(f"  JOB_ID: {job_id}")
    log(f"  BUCKET: {bucket}")
    log(f"  KEY: {key}")
    log(f"  JOBS_TABLE: {JOBS_TABLE}")
    log(f"  PDF_GENERATOR_FUNCTION: {PDF_GENERATOR_FUNCTION}")
    
    if not all([job_id, bucket, key]):
        log("ERROR: Missing required environment variables", "ERROR")
        raise ValueError("Missing required environment variables: JOB_ID, BUCKET, KEY")
    
    try:
        # Update status
        log("Step 1: Updating job status to DETECTING_CHORDS (70%)")
        update_job_status(job_id, 'DETECTING_CHORDS', 70)
        log("✓ Status updated successfully")
        
        # Download audio from S3
        log(f"Step 2: Downloading audio from s3://{bucket}/{key}")
        audio_path = f"/tmp/{job_id}-audio.mp3"
        start_time = time.time()
        s3.download_file(bucket, key, audio_path)
        download_time = time.time() - start_time
        
        # Get file size
        file_size = os.path.getsize(audio_path)
        log(f"✓ Audio downloaded successfully")
        log(f"  File path: {audio_path}")
        log(f"  File size: {file_size / 1024 / 1024:.2f} MB")
        log(f"  Download time: {download_time:.2f}s")
        
        # Detect chords
        log("Step 3: Starting chord detection...")
        start_time = time.time()
        chords_data = detect_chords(audio_path, job_id)
        detection_time = time.time() - start_time
        
        log(f"✓ Chord detection complete")
        log(f"  Total chords found: {len(chords_data['chords'])}")
        log(f"  Detection time: {detection_time:.2f}s")
        log(f"  Audio duration: {chords_data.get('duration', 0):.2f}s")
        log(f"  Key detected: {chords_data.get('key', 'Unknown')}")
        
        # Update job with chord data
        log("Step 4: Updating job with chord data...")
        update_job_with_chords(job_id, chords_data)
        log("✓ Job updated with chord data")
        
        # Trigger PDF generation
        log("Step 5: Triggering PDF generation Lambda...")
        trigger_pdf_generation(job_id)
        log("✓ PDF generation triggered")
        
        log("=" * 80)
        log("CHORD DETECTION TASK COMPLETED SUCCESSFULLY")
        log("=" * 80)
        
    except Exception as e:
        log(f"FATAL ERROR in chord detection: {str(e)}", "ERROR")
        log(traceback.format_exc(), "ERROR")
        update_job_status(job_id, 'FAILED', 0, str(e))
        raise

def detect_chords(audio_path, job_id):
    """Detect chords using librosa chromagram analysis"""
    log("Loading audio file...")
    start_time = time.time()
    y, sr = librosa.load(audio_path, sr=22050)
    duration = librosa.get_duration(y=y, sr=sr)
    load_time = time.time() - start_time
    
    log(f"✓ Audio loaded successfully")
    log(f"  Duration: {duration:.2f}s")
    log(f"  Sample rate: {sr}Hz")
    log(f"  Samples: {len(y)}")
    log(f"  Load time: {load_time:.2f}s")
    
    # Compute chromagram
    log("Computing chromagram...")
    start_time = time.time()
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=512)
    chroma_time = time.time() - start_time
    log(f"✓ Chromagram computed")
    log(f"  Shape: {chroma.shape}")
    log(f"  Compute time: {chroma_time:.2f}s")
    
    # Detect chord changes
    log("Detecting chord changes...")
    start_time = time.time()
    chords = []
    
    # Simple chord detection: find peaks in chroma energy
    chroma_energy = np.sum(chroma, axis=0)
    peaks, _ = find_peaks(chroma_energy, distance=sr//512, prominence=0.5)
    log(f"  Found {len(peaks)} peaks in chroma energy")
    
    # Map chroma to chord names
    chord_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    for i, peak in enumerate(peaks):
        # Get dominant pitch class at this peak
        chroma_frame = chroma[:, peak]
        dominant_pitch = np.argmax(chroma_frame)
        chord_name = chord_names[dominant_pitch]
        
        # Calculate timing
        start_time_chord = librosa.frames_to_time(peak, sr=sr, hop_length=512)
        
        # Duration until next peak or end
        if i < len(peaks) - 1:
            next_peak = peaks[i + 1]
            end_time = librosa.frames_to_time(next_peak, sr=sr, hop_length=512)
        else:
            end_time = duration
        
        chords.append({
            'chord': chord_name,
            'start': round(start_time_chord, 2),
            'end': round(end_time, 2),
            'duration': round(end_time - start_time_chord, 2)
        })
    
    detection_time = time.time() - start_time
    
    # Estimate key
    overall_chroma = np.mean(chroma, axis=1)
    key_index = np.argmax(overall_chroma)
    key = chord_names[key_index]
    
    log(f"✓ Chord detection complete")
    log(f"  Total chords: {len(chords)}")
    log(f"  Detected key: {key}")
    log(f"  Detection time: {detection_time:.2f}s")
    
    if len(chords) > 0:
        log(f"  First chord: {chords[0]['chord']} at {chords[0]['start']}s")
        log(f"  Last chord: {chords[-1]['chord']} at {chords[-1]['start']}s")
    
    return {
        'chords': chords,
        'key': key,
        'duration': round(duration, 2),
        'totalChords': len(chords),
        'model': 'librosa-chromagram'
    }

def update_job_status(job_id, status, progress, error=None):
    """Update job status in DynamoDB"""
    log(f"Updating job status: {status} ({progress}%)")
    table = dynamodb.Table(JOBS_TABLE)
    
    update_expr = 'SET #status = :status, progress = :progress, updatedAt = :updated'
    expr_values = {
        ':status': status,
        ':progress': progress,
        ':updated': time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
    }
    expr_names = {'#status': 'status'}
    
    if error:
        update_expr += ', errorMessage = :error'
        expr_values[':error'] = error
        log(f"  Error message: {error}", "ERROR")
    
    try:
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values
        )
        log(f"✓ Job status updated in DynamoDB")
    except Exception as e:
        log(f"ERROR updating job status: {str(e)}", "ERROR")
        raise

def update_job_with_chords(job_id, chords_data):
    """Update job with chord detection results"""
    log(f"Updating job with {len(chords_data['chords'])} chords")
    table = dynamodb.Table(JOBS_TABLE)
    
    try:
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET chordsData = :chords, #status = :status, progress = :progress, updatedAt = :updated',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':chords': chords_data,
                ':status': 'CHORDS_DETECTED',
                ':progress': 80,
                ':updated': time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
            }
        )
        log(f"✓ Job updated with chord data (status: CHORDS_DETECTED, progress: 80%)")
    except Exception as e:
        log(f"ERROR updating job with chords: {str(e)}", "ERROR")
        raise

def trigger_pdf_generation(job_id):
    """Trigger PDF generation Lambda"""
    log(f"Invoking Lambda: {PDF_GENERATOR_FUNCTION}")
    log(f"  Payload: {{'jobId': '{job_id}'}}")
    
    try:
        response = lambda_client.invoke(
            FunctionName=PDF_GENERATOR_FUNCTION,
            InvocationType='Event',  # Async invocation
            Payload=json.dumps({'jobId': job_id})
        )
        log(f"✓ PDF generation Lambda invoked")
        log(f"  Status code: {response['StatusCode']}")
        log(f"  Request ID: {response['ResponseMetadata']['RequestId']}")
    except Exception as e:
        log(f"ERROR invoking PDF generation Lambda: {str(e)}", "ERROR")
        raise

if __name__ == '__main__':
    main()

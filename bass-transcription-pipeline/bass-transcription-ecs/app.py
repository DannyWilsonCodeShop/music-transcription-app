"""
Bass Transcription ECS Task
Dedicated pipeline for bass note transcription with Nashville Number System
"""

import os
import json
import boto3
import librosa
import numpy as np
import sys
import time
import traceback
from datetime import datetime

# Import bass transcription module
from bass_note_transcription import detect_bass_notes

# Demucs for stem separation
try:
    import torch
    import torchaudio
    from demucs.pretrained import get_model
    from demucs.apply import apply_model
    DEMUCS_AVAILABLE = True
except ImportError:
    DEMUCS_AVAILABLE = False
    print("WARNING: Demucs not available")

# AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

# Environment variables
JOBS_TABLE = os.environ.get('DYNAMODB_JOBS_TABLE', 'ChordScout-Jobs-V2-dev')
PDF_GENERATOR_FUNCTION = os.environ.get('PDF_GENERATOR_FUNCTION', 'bass-nns-pdf-generator-dev')

def log(message, level="INFO"):
    """Enhanced logging with timestamps"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}", flush=True)
    sys.stdout.flush()


def main():
    """Main entry point for bass transcription ECS task"""
    log("=" * 80)
    log("BASS TRANSCRIPTION PIPELINE")
    log("=" * 80)
    
    # Get parameters from environment
    job_id = os.environ.get('JOB_ID')
    bucket = os.environ.get('AUDIO_BUCKET')
    key = os.environ.get('AUDIO_KEY')
    
    log(f"Environment Variables:")
    log(f"  JOB_ID: {job_id}")
    log(f"  BUCKET: {bucket}")
    log(f"  KEY: {key}")
    log(f"  JOBS_TABLE: {JOBS_TABLE}")
    
    if not all([job_id, bucket, key]):
        log("ERROR: Missing required environment variables", "ERROR")
        raise ValueError("Missing required environment variables")
    
    try:
        # Update status
        update_job_status(job_id, 'PROCESSING', 30, "Downloading audio file...")
        
        # Download audio
        log("Step 1: Downloading audio from S3...")
        audio_path = f"/tmp/{job_id}-audio.m4a"
        s3.download_file(bucket, key, audio_path)
        file_size = os.path.getsize(audio_path)
        log(f"✓ Audio downloaded ({file_size / 1024 / 1024:.2f} MB)")
        
        # Separate stems and extract bass
        update_job_status(job_id, 'PROCESSING', 40, "Extracting bass stem...")
        log("Step 2: Extracting bass stem...")
        bass_audio, sr = extract_bass_stem(audio_path)
        log(f"✓ Bass stem extracted ({len(bass_audio) / sr:.2f}s)")
        
        # Detect tempo and beats
        update_job_status(job_id, 'PROCESSING', 50, "Detecting tempo and beats...")
        log("Step 3: Detecting tempo and beats...")
        tempo, beats = librosa.beat.beat_track(y=bass_audio, sr=sr)
        tempo_value = float(tempo) if isinstance(tempo, (int, float)) else float(tempo[0])
        time_signature = "4/4"  # Default
        log(f"✓ Tempo: {tempo_value:.1f} BPM, Time signature: {time_signature}")
        
        # Detect downbeat
        update_job_status(job_id, 'PROCESSING', 60, "Detecting downbeat...")
        log("Step 4: Detecting downbeat...")
        first_downbeat = detect_downbeat(bass_audio, sr, tempo_value, beats)
        log(f"✓ Downbeat: {first_downbeat:.3f}s")
        
        # Transcribe bass notes
        update_job_status(job_id, 'PROCESSING', 70, "Transcribing bass notes...")
        log("Step 5: Transcribing bass notes to NNS...")
        bass_data = detect_bass_notes(
            bass_audio,
            sr,
            tempo_value,
            time_signature,
            first_downbeat
        )
        log(f"✓ Transcribed {bass_data['totalNotes']} notes in {bass_data['totalMeasures']} measures")
        log(f"  Key: {bass_data['key']} {bass_data['mode']} (Relative major: {bass_data['relativeMajor']})")
        
        # Update job with bass data
        update_job_status(job_id, 'PROCESSING', 85, "Saving bass transcription...")
        log("Step 6: Updating job with bass data...")
        update_job_with_bass_data(job_id, bass_data)
        log("✓ Job updated")
        
        # Trigger PDF generation
        update_job_status(job_id, 'PROCESSING', 90, "Generating NNS chart...")
        log("Step 7: Triggering PDF generation...")
        trigger_pdf_generation(job_id)
        log("✓ PDF generation triggered")
        
        log("=" * 80)
        log("BASS TRANSCRIPTION COMPLETED SUCCESSFULLY")
        log("=" * 80)
        
    except Exception as e:
        log(f"FATAL ERROR: {str(e)}", "ERROR")
        log(traceback.format_exc(), "ERROR")
        update_job_status(job_id, 'FAILED', 0, str(e))
        raise


def extract_bass_stem(audio_path: str) -> tuple:
    """Extract bass stem using Demucs"""
    if not DEMUCS_AVAILABLE:
        log("Demucs not available, using full mix", "WARNING")
        return librosa.load(audio_path, sr=22050)
    
    try:
        log("  Loading Demucs model...")
        model = get_model('mdx_extra')
        
        log("  Loading audio...")
        wav, sr = torchaudio.load(audio_path)
        
        # Ensure stereo
        if wav.shape[0] == 1:
            wav = wav.repeat(2, 1)
        
        # Resample if needed
        if sr != model.samplerate:
            resampler = torchaudio.transforms.Resample(sr, model.samplerate)
            wav = resampler(wav)
            sr = model.samplerate
        
        log("  Separating stems...")
        with torch.no_grad():
            sources = apply_model(model, wav[None], device='cpu')[0]
        
        # Extract bass (index 1)
        bass = sources[1]
        bass_mono = torch.mean(bass, dim=0).numpy()
        
        # Resample to 22050 for librosa
        if sr != 22050:
            bass_mono = librosa.resample(bass_mono, orig_sr=sr, target_sr=22050)
            sr = 22050
        
        log("  ✓ Bass stem extracted")
        return bass_mono, sr
        
    except Exception as e:
        log(f"Stem separation failed: {e}", "ERROR")
        log("Falling back to full mix", "WARNING")
        return librosa.load(audio_path, sr=22050)


def detect_downbeat(audio: np.ndarray, sr: int, tempo: float, beats: np.ndarray) -> float:
    """Detect first downbeat"""
    try:
        # Try to use existing downbeat detection
        sys.path.insert(0, '/app/simple-pipeline/chord-detection')
        from downbeat_detection import detect_downbeats
        
        beat_times = librosa.frames_to_time(beats, sr=sr)
        downbeats, first_downbeat, info = detect_downbeats(
            None,  # We don't have the file path here
            beat_times,
            tempo,
            "4/4"
        )
        return first_downbeat
    except Exception as e:
        log(f"Downbeat detection failed: {e}", "WARNING")
        # Fallback: use first beat
        beat_times = librosa.frames_to_time(beats, sr=sr)
        return float(beat_times[0]) if len(beat_times) > 0 else 0.0


def update_job_status(job_id: str, status: str, progress: int, message: str = None):
    """Update job status in DynamoDB"""
    table = dynamodb.Table(JOBS_TABLE)
    
    update_expr = 'SET #status = :status, progress = :progress, updatedAt = :updated'
    expr_values = {
        ':status': status,
        ':progress': progress,
        ':updated': datetime.utcnow().isoformat()
    }
    expr_names = {'#status': 'status'}
    
    if message:
        update_expr += ', statusMessage = :message'
        expr_values[':message'] = message
    
    table.update_item(
        Key={'jobId': job_id},
        UpdateExpression=update_expr,
        ExpressionAttributeNames=expr_names,
        ExpressionAttributeValues=expr_values
    )


def convert_floats_to_decimal(obj):
    """Convert floats to Decimal for DynamoDB"""
    from decimal import Decimal
    
    if isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_floats_to_decimal(value) for key, value in obj.items()}
    elif isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return Decimal('0')
        return Decimal(str(obj))
    elif isinstance(obj, (np.floating, np.float32, np.float64)):
        val = float(obj)
        if np.isnan(val) or np.isinf(val):
            return Decimal('0')
        return Decimal(str(val))
    elif isinstance(obj, (np.integer, np.int32, np.int64)):
        return int(obj)
    else:
        return obj


def update_job_with_bass_data(job_id: str, bass_data: dict):
    """Update job with bass transcription data"""
    table = dynamodb.Table(JOBS_TABLE)
    
    # Convert to DynamoDB format
    bass_data_decimal = convert_floats_to_decimal(bass_data)
    
    table.update_item(
        Key={'jobId': job_id},
        UpdateExpression='SET bassData = :data, #status = :status, progress = :progress, updatedAt = :updated',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={
            ':data': bass_data_decimal,
            ':status': 'BASS_TRANSCRIBED',
            ':progress': 80,
            ':updated': datetime.utcnow().isoformat()
        }
    )


def trigger_pdf_generation(job_id: str):
    """Trigger PDF generation Lambda"""
    try:
        lambda_client.invoke(
            FunctionName=PDF_GENERATOR_FUNCTION,
            InvocationType='Event',
            Payload=json.dumps({'jobId': job_id})
        )
        log(f"✓ PDF generation Lambda invoked")
    except Exception as e:
        log(f"ERROR invoking PDF Lambda: {str(e)}", "ERROR")
        # Don't fail the whole job if PDF generation fails
        pass


if __name__ == '__main__':
    main()

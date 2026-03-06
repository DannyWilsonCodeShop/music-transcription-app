"""
Bass Transcription ECS Task - v3.0
Multi-stem transcription pipeline with song identification, lyrics, and user confirmations
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
from decimal import Decimal

# Import new modules (Task 2.1)
from bass_note_transcription import detect_bass_notes
from stem_transcription import transcribe_stems, extract_stem_audio
from song_metadata_lyrics import get_song_metadata_and_lyrics

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
AUDIO_BUCKET = os.environ.get('AUDIO_BUCKET', 'chordscout-audio-dev')

# Feature flags (Task 2.9)
ENABLE_MULTI_STEM = os.environ.get('ENABLE_MULTI_STEM', 'false').lower() == 'true'
ENABLE_LYRICS = os.environ.get('ENABLE_LYRICS', 'false').lower() == 'true'
ENABLE_SONG_ID = os.environ.get('ENABLE_SONG_ID', 'true').lower() == 'true'
DEFAULT_TRANSCRIPTION_MODE = os.environ.get('DEFAULT_TRANSCRIPTION_MODE', 'bass-only')
CONFIRMATION_TIMEOUT = int(os.environ.get('CONFIRMATION_TIMEOUT', '300'))  # 5 minutes
GENIUS_ACCESS_TOKEN = os.environ.get('GENIUS_ACCESS_TOKEN', '')


def log(message, level="INFO"):
    """Enhanced logging with timestamps"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}", flush=True)
    sys.stdout.flush()


def main():
    """Main entry point for v3.0 bass transcription ECS task - OPTIMIZED"""
    global ENABLE_MULTI_STEM, ENABLE_LYRICS, ENABLE_SONG_ID

    log("=" * 80)
    log("BASS TRANSCRIPTION PIPELINE v3.0 - OPTIMIZED")
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
    log(f"  ENABLE_MULTI_STEM: {ENABLE_MULTI_STEM}")
    log(f"  ENABLE_LYRICS: {ENABLE_LYRICS}")
    log(f"  ENABLE_SONG_ID: {ENABLE_SONG_ID}")

    if not all([job_id, bucket, key]):
        log("ERROR: Missing required environment variables", "ERROR")
        raise ValueError("Missing required environment variables")

    processing_start_time = time.time()

    try:
        # Stage 1: Download audio
        update_job_status(job_id, 'PROCESSING', 10, "Downloading audio file...")
        log("Stage 1: Downloading audio from S3...")
        audio_path = f"/tmp/{job_id}-audio.m4a"
        s3.download_file(bucket, key, audio_path)
        file_size = os.path.getsize(audio_path)
        log(f"✓ Audio downloaded ({file_size / 1024 / 1024:.2f} MB)")

        # Stage 2: Tempo and beat detection
        update_job_status(job_id, 'PROCESSING', 20, "Analyzing tempo and beats...")
        log("Stage 2: Detecting tempo and beats...")
        full_audio, sr = librosa.load(audio_path, sr=22050)
        tempo, beats = librosa.beat.beat_track(y=full_audio, sr=sr)
        tempo_value = float(tempo) if isinstance(tempo, (int, float)) else float(tempo[0])
        time_signature = "4/4"  # Default
        log(f"✓ Tempo: {tempo_value:.1f} BPM, Time signature: {time_signature}")

        # Stage 3: Downbeat detection
        update_job_status(job_id, 'PROCESSING', 30, "Detecting downbeat...")
        log("Stage 3: Detecting downbeat...")
        first_downbeat = detect_downbeat(full_audio, sr, tempo_value, beats)
        log(f"✓ Downbeat: {first_downbeat:.3f}s")

        # Stage 4: Song identification (parallel with mode selection)
        song_metadata = None
        song_id_time = 0
        if ENABLE_SONG_ID:
            update_job_status(job_id, 'PROCESSING', 35, "Identifying song...")
            log("Stage 4: Identifying song...")
            song_id_start = time.time()
            try:
                from song_metadata_lyrics import _identify_song
                song_metadata = _identify_song(audio_path, None)
                log(f"✓ Song: {song_metadata.get('artist', 'Unknown')} - {song_metadata.get('title', 'Unknown')}")
                log(f"  Source: {song_metadata.get('source', 'unknown')}")
                update_job_with_metadata(job_id, song_metadata)
            except Exception as e:
                log(f"Song identification failed: {e}", "WARNING")
                song_metadata = {'artist': '', 'title': '', 'source': 'unknown'}
            song_id_time = time.time() - song_id_start
        else:
            song_metadata = {'artist': '', 'title': '', 'source': 'disabled'}

        # Stage 5: OPTIMIZED - Ask for mode selection BEFORE stem separation
        transcription_mode = 'bass-only'
        if ENABLE_MULTI_STEM:
            update_job_status(job_id, 'PENDING_MODE_SELECTION', 40)
            log("Stage 5: Waiting for transcription mode selection...")
            transcription_mode = wait_for_mode_selection(job_id, timeout=CONFIRMATION_TIMEOUT)
            log(f"✓ Transcription mode: {transcription_mode}")
        else:
            update_job_field(job_id, 'transcriptionMode', transcription_mode)
            log(f"✓ Transcription mode: {transcription_mode} (multi-stem disabled)")

        # Stage 6: OPTIMIZED - Conditional stem separation (only if needed)
        stems_data = None
        stem_sep_time = 0
        bass_audio = None

        if transcription_mode != 'bass-only':
            # Multi-stem mode: separate stems with Demucs
            update_job_status(job_id, 'PROCESSING_STEMS', 45, "Separating audio stems...")
            log("Stage 6: Separating stems with Demucs (multi-stem mode)...")
            stem_sep_start = time.time()
            try:
                stems_sources = separate_stems(audio_path)
                upload_stems_to_s3(stems_sources, job_id, bucket, sr)
                stems_data = stems_sources
                bass_audio = extract_stem_audio(stems_data, 'bass', sr, 'mdx_extra')
                log("✓ Stems separated and uploaded to S3")
            except Exception as e:
                log(f"Stem separation failed: {e}", "ERROR")
                log("Falling back to bass extraction from full mix", "WARNING")
                bass_audio = extract_bass_with_filter(full_audio, sr)
            stem_sep_time = time.time() - stem_sep_start
        else:
            # Bass-only mode: skip stem separation, extract bass directly
            update_job_status(job_id, 'PROCESSING', 45, "Extracting bass...")
            log("Stage 6: Extracting bass from full mix (bass-only mode - FAST)...")
            stem_sep_start = time.time()
            bass_audio = extract_bass_with_filter(full_audio, sr)
            stem_sep_time = time.time() - stem_sep_start
            log(f"✓ Bass extracted in {stem_sep_time:.1f}s (skipped stem separation)")

        # Stage 7: Multi-stem transcription
        update_job_status(job_id, 'TRANSCRIBING_STEMS', 55, "Transcribing stems...")
        log("Stage 7: Transcribing stems...")
        transcription_start = time.time()

        # Always transcribe bass with 8th note quantization
        bass_data = detect_bass_notes(
            bass_audio,
            sr,
            tempo_value,
            time_signature,
            first_downbeat
        )
        log(f"✓ Bass: {bass_data['totalNotes']} notes in {bass_data['totalMeasures']} measures")
        log(f"  Key: {bass_data['key']} {bass_data['mode']} (Relative major: {bass_data['relativeMajor']})")

        # Transcribe additional stems based on mode
        stem_transcription_data = {}
        if stems_data is not None and transcription_mode != 'bass-only':
            stems_to_transcribe = []
            if transcription_mode in ['bass+piano', 'all']:
                stems_to_transcribe.append('piano')
            if transcription_mode in ['bass+guitar', 'all']:
                stems_to_transcribe.append('guitar')

            if stems_to_transcribe:
                log(f"  Transcribing additional stems: {stems_to_transcribe}")
                try:
                    stem_results = transcribe_stems(
                        stems_data,
                        sr,
                        tempo_value,
                        time_signature,
                        first_downbeat,
                        {
                            'key': bass_data['key'],
                            'mode': bass_data['mode'],
                            'relativeMajor': bass_data['relativeMajor']
                        },
                        output_mode='notes',
                        stems_to_process=stems_to_transcribe,
                        model_type='mdx_extra'
                    )

                    for stem_name, stem_result in stem_results.items():
                        if stem_result.get('available') and 'notes_data' in stem_result:
                            notes_data = stem_result['notes_data']
                            stem_transcription_data[stem_name] = {
                                'notes': notes_data['notes'],
                                'totalNotes': notes_data['totalNotes'],
                                's3Key': f"audio/{job_id}/stems/{stem_name}.wav"
                            }
                            log(f"✓ {stem_name.capitalize()}: {notes_data['totalNotes']} notes")
                except Exception as e:
                    log(f"Additional stem transcription failed: {e}", "ERROR")

        transcription_time = time.time() - transcription_start

        # Stage 8: Lyrics fetching (parallel with key detection)
        lyrics_data = None
        lyrics_time = 0
        if ENABLE_LYRICS and song_metadata and song_metadata.get('title'):
            update_job_status(job_id, 'FETCHING_LYRICS', 70, "Fetching lyrics...")
            log("Stage 8: Fetching lyrics...")
            lyrics_start = time.time()
            try:
                lyrics_result = get_song_metadata_and_lyrics(
                    audio_path,
                    tempo_value,
                    time_signature,
                    bass_data['totalMeasures'],
                    first_downbeat,
                    user_provided=song_metadata
                )

                if lyrics_result.get('lyrics_available'):
                    lyrics_data = {
                        'available': True,
                        'source': 'genius',
                        'sections': lyrics_result.get('measure_lyrics', [])
                    }
                    log(f"✓ Lyrics fetched: {lyrics_result.get('line_count', 0)} lines")
                else:
                    lyrics_data = {
                        'available': False,
                        'reason': lyrics_result.get('reason', 'Not found')
                    }
                    log(f"Lyrics not available: {lyrics_data['reason']}", "WARNING")
            except Exception as e:
                log(f"Lyrics fetch failed: {e}", "WARNING")
                lyrics_data = {'available': False, 'reason': str(e)}
            lyrics_time = time.time() - lyrics_start
        else:
            lyrics_data = {'available': False, 'reason': 'Disabled or no song metadata'}

        # Stage 9: Key detection and confirmation
        detected_key = f"{bass_data['key']} {bass_data['mode']}"
        confirmed_key = detected_key

        if ENABLE_MULTI_STEM:
            update_job_status(job_id, 'PENDING_KEY_CONFIRMATION', 75)
            log("Stage 9: Waiting for key confirmation...")
            update_job_field(job_id, 'detectedKey', detected_key)
            update_job_field(job_id, 'keyConfidence', bass_data.get('confidence', 0.8))

            confirmed_key = wait_for_key_confirmation(job_id, detected_key, timeout=CONFIRMATION_TIMEOUT)
            log(f"✓ Confirmed key: {confirmed_key}")
        else:
            update_job_field(job_id, 'detectedKey', detected_key)
            update_job_field(job_id, 'confirmedKey', confirmed_key)

        # Stage 10: Update job with all transcription data
        update_job_status(job_id, 'PROCESSING', 85, "Saving transcription data...")
        log("Stage 10: Updating job with transcription data...")

        update_data = {
            'bassData': bass_data,
            'transcriptionMode': transcription_mode,
            'detectedKey': detected_key,
            'confirmedKey': confirmed_key,
            'keyConfidence': bass_data.get('confidence', 0.8)
        }

        if song_metadata:
            update_data['songMetadata'] = song_metadata

        if lyrics_data:
            update_data['lyrics'] = lyrics_data

        if stem_transcription_data:
            update_data['stemData'] = stem_transcription_data

        # Add processing metrics
        total_time = time.time() - processing_start_time
        update_data['processingMetrics'] = {
            'songIdentificationTime': song_id_time,
            'stemSeparationTime': stem_sep_time,
            'transcriptionTime': transcription_time,
            'lyricsFetchTime': lyrics_time,
            'totalProcessingTime': total_time,
            'optimized': True,
            'stemSeparationSkipped': transcription_mode == 'bass-only'
        }

        update_job_with_all_data(job_id, update_data)
        log("✓ Job updated with all data")

        # Stage 11: Trigger PDF generation
        update_job_status(job_id, 'GENERATING_PDF', 90, "Generating NNS chart...")
        log("Stage 11: Triggering PDF generation...")
        trigger_pdf_generation(job_id)
        log("✓ PDF generation triggered")

        log("=" * 80)
        log(f"TRANSCRIPTION COMPLETED SUCCESSFULLY ({total_time:.1f}s)")
        if transcription_mode == 'bass-only':
            log(f"OPTIMIZATION: Skipped stem separation (saved ~13 minutes)")
        log("=" * 80)

    except Exception as e:
        log(f"FATAL ERROR: {str(e)}", "ERROR")
        log(traceback.format_exc(), "ERROR")
        update_job_status(job_id, 'FAILED', 0, str(e))
        raise



def separate_stems(audio_path: str):
    """Separate audio into stems using Demucs (Task 2.3)"""
    if not DEMUCS_AVAILABLE:
        raise Exception("Demucs not available")
    
    log("  Loading Demucs model...")
    model = get_model('mdx_extra')
    
    log("  Loading audio...")
    # Use librosa to load M4A files, then convert to torch tensor
    audio_np, sr_orig = librosa.load(audio_path, sr=None, mono=False)
    
    # Convert to torch tensor
    if audio_np.ndim == 1:
        # Mono - convert to stereo
        wav = torch.from_numpy(audio_np).unsqueeze(0).repeat(2, 1).float()
    else:
        # Already stereo or multi-channel
        wav = torch.from_numpy(audio_np).float()
        if wav.shape[0] == 1:
            wav = wav.repeat(2, 1)
    
    # Resample if needed
    if sr_orig != model.samplerate:
        log(f"  Resampling from {sr_orig}Hz to {model.samplerate}Hz...")
        resampler = torchaudio.transforms.Resample(sr_orig, model.samplerate)
        wav = resampler(wav)
        sr = model.samplerate
    else:
        sr = sr_orig
    
    log("  Separating stems...")
    with torch.no_grad():
        sources = apply_model(model, wav[None], device='cpu')[0]
    
    log(f"  ✓ Separated into {sources.shape[0]} stems")
    return sources


def upload_stems_to_s3(sources, job_id: str, bucket: str, sr: int):
    """Upload separated stems to S3 (Task 2.3)"""
    import soundfile as sf
    
    stem_names = ['drums', 'bass', 'other', 'vocals']
    if sources.shape[0] > 4:
        stem_names.extend(['guitar', 'piano'])
    
    for i, stem_name in enumerate(stem_names[:sources.shape[0]]):
        try:
            # Convert to mono
            if isinstance(sources, torch.Tensor):
                stem_mono = torch.mean(sources[i], dim=0).numpy()
            else:
                stem_mono = np.mean(sources[i], axis=0)
            
            # Save to temp file
            temp_path = f"/tmp/{job_id}-{stem_name}.wav"
            sf.write(temp_path, stem_mono, sr)
            
            # Upload to S3
            s3_key = f"audio/{job_id}/stems/{stem_name}.wav"
            s3.upload_file(temp_path, bucket, s3_key)
            
            # Clean up
            os.remove(temp_path)
            
            log(f"  ✓ Uploaded {stem_name}.wav to S3")
        except Exception as e:
            log(f"  Failed to upload {stem_name}: {e}", "WARNING")


def wait_for_mode_selection(job_id: str, timeout: int = 300) -> str:
    """
    Wait for user to select transcription mode (Task 2.4)
    Polls DynamoDB every 2 seconds for user selection
    Defaults to bass-only on timeout
    """
    start_time = time.time()
    poll_interval = 2
    
    while time.time() - start_time < timeout:
        job = get_job_from_dynamodb(job_id)
        if job.get('transcriptionMode'):
            return job['transcriptionMode']
        time.sleep(poll_interval)
    
    # Timeout: default to bass-only
    log(f"Mode selection timeout ({timeout}s), defaulting to bass-only", "WARNING")
    update_job_field(job_id, 'transcriptionMode', 'bass-only')
    return 'bass-only'


def wait_for_key_confirmation(job_id: str, detected_key: str, timeout: int = 300) -> str:
    """
    Wait for user to confirm or correct the detected key (Task 2.7)
    Polls DynamoDB every 2 seconds
    Defaults to detected key on timeout
    """
    start_time = time.time()
    poll_interval = 2
    
    while time.time() - start_time < timeout:
        job = get_job_from_dynamodb(job_id)
        if job.get('confirmedKey'):
            return job['confirmedKey']
        time.sleep(poll_interval)
    
    # Timeout: use detected key
    log(f"Key confirmation timeout ({timeout}s), using detected key", "WARNING")
    update_job_field(job_id, 'confirmedKey', detected_key)
    return detected_key


def extract_bass_stem(audio_path: str) -> tuple:
    """Extract bass stem using Demucs (fallback method)"""
    if not DEMUCS_AVAILABLE:
        log("Demucs not available, using full mix", "WARNING")
        return librosa.load(audio_path, sr=22050)
    
    try:
        log("  Loading Demucs model...")
        model = get_model('mdx_extra')
        
        log("  Loading audio...")
        # Use librosa to load M4A files, then convert to torch tensor
        audio_np, sr_orig = librosa.load(audio_path, sr=None, mono=False)
        
        # Convert to torch tensor
        if audio_np.ndim == 1:
            # Mono - convert to stereo
            wav = torch.from_numpy(audio_np).unsqueeze(0).repeat(2, 1).float()
        else:
            # Already stereo or multi-channel
            wav = torch.from_numpy(audio_np).float()
            if wav.shape[0] == 1:
                wav = wav.repeat(2, 1)
        
        # Resample if needed
        if sr_orig != model.samplerate:
            resampler = torchaudio.transforms.Resample(sr_orig, model.samplerate)
            wav = resampler(wav)
            sr = model.samplerate
        else:
            sr = sr_orig
        
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
def extract_bass_with_filter(audio: np.ndarray, sr: int) -> np.ndarray:
    """
    Fast bass extraction using frequency filtering (no stem separation)
    Applies low-pass filter to isolate bass frequencies (20-250 Hz)
    Much faster than Demucs stem separation (~1 second vs 13 minutes)
    """
    log("  Applying bass frequency filter (20-250 Hz)...")

    # Apply low-pass filter to isolate bass frequencies
    from scipy import signal

    # Design butterworth low-pass filter
    nyquist = sr / 2
    low_cutoff = 250 / nyquist  # 250 Hz cutoff for bass
    high_cutoff = 20 / nyquist   # 20 Hz high-pass to remove rumble

    # Band-pass filter for bass range
    sos = signal.butter(4, [high_cutoff, low_cutoff], btype='band', output='sos')
    bass_audio = signal.sosfilt(sos, audio)

    # Normalize
    if np.max(np.abs(bass_audio)) > 0:
        bass_audio = bass_audio / np.max(np.abs(bass_audio))

    log(f"  ✓ Bass extracted with filter ({len(bass_audio) / sr:.2f}s)")
    return bass_audio





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


def get_job_from_dynamodb(job_id: str) -> dict:
    """Get job record from DynamoDB"""
    table = dynamodb.Table(JOBS_TABLE)
    response = table.get_item(Key={'jobId': job_id})
    return response.get('Item', {})


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


def update_job_field(job_id: str, field_name: str, value):
    """Update a single field in DynamoDB"""
    table = dynamodb.Table(JOBS_TABLE)
    
    value_converted = convert_floats_to_decimal(value)
    
    table.update_item(
        Key={'jobId': job_id},
        UpdateExpression=f'SET {field_name} = :value, updatedAt = :updated',
        ExpressionAttributeValues={
            ':value': value_converted,
            ':updated': datetime.utcnow().isoformat()
        }
    )


def update_job_with_metadata(job_id: str, metadata: dict):
    """Update job with song metadata (Task 2.2)"""
    table = dynamodb.Table(JOBS_TABLE)
    
    metadata_decimal = convert_floats_to_decimal(metadata)
    
    table.update_item(
        Key={'jobId': job_id},
        UpdateExpression='SET songMetadata = :metadata, updatedAt = :updated',
        ExpressionAttributeValues={
            ':metadata': metadata_decimal,
            ':updated': datetime.utcnow().isoformat()
        }
    )


def update_job_with_all_data(job_id: str, data: dict):
    """Update job with all transcription data (Task 2.9)"""
    table = dynamodb.Table(JOBS_TABLE)
    
    # Convert to DynamoDB format
    data_decimal = convert_floats_to_decimal(data)
    
    # Build update expression
    update_parts = []
    expr_values = {':updated': datetime.utcnow().isoformat()}
    
    for key, value in data_decimal.items():
        update_parts.append(f'{key} = :{key}')
        expr_values[f':{key}'] = value
    
    update_expr = 'SET ' + ', '.join(update_parts) + ', updatedAt = :updated'
    
    table.update_item(
        Key={'jobId': job_id},
        UpdateExpression=update_expr,
        ExpressionAttributeValues=expr_values
    )


def convert_floats_to_decimal(obj):
    """Convert floats to Decimal for DynamoDB"""
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

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
from scipy.ndimage import median_filter
from decimal import Decimal
import time
import sys
import traceback

# Essentia for chord detection
try:
    import essentia
    import essentia.standard as es
    ESSENTIA_AVAILABLE = True
except ImportError:
    ESSENTIA_AVAILABLE = False
    print("WARNING: essentia not available, using librosa only")

# Optional: Demucs for source separation
try:
    import torch
    import torchaudio
    from demucs.pretrained import get_model
    from demucs.apply import apply_model
    DEMUCS_AVAILABLE = True
except ImportError:
    DEMUCS_AVAILABLE = False

# Optional: Whisper for lyrics extraction
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("WARNING: whisper not available, lyrics extraction disabled")

# MSAF for structural segmentation
try:
    import msaf
    MSAF_AVAILABLE = True
except ImportError:
    MSAF_AVAILABLE = False
    print("WARNING: msaf not available, using pattern-based structure detection only")

# AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

# Environment variables
JOBS_TABLE = os.environ.get('DYNAMODB_JOBS_TABLE', 'ChordScout-Jobs-V2-dev')
PDF_GENERATOR_FUNCTION = os.environ.get('PDF_GENERATOR_FUNCTION', 'chordscout-v2-pdf-generator-dev')
ENABLE_STEM_SEPARATION = os.environ.get('ENABLE_STEM_SEPARATION', 'false').lower() == 'true'
CHUNK_DURATION = int(os.environ.get('CHUNK_DURATION', '30'))  # Process in N-second chunks

def log(message, level="INFO"):
    """Enhanced logging with timestamps and flush"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}", flush=True)
    sys.stdout.flush()

def main():
    """Main entry point for ECS task"""
    
    # Check if this is a downbeat detection task
    task_type = os.environ.get('TASK_TYPE', 'CHORD_DETECTION')
    
    if task_type == 'DOWNBEAT_DETECTION':
        return run_downbeat_detection()
    
    # Otherwise, run chord detection
    log("=" * 80)
    log("STARTING CHORD DETECTION ECS TASK")
    log("=" * 80)
    
    # Get parameters from environment
    job_id = os.environ.get('JOB_ID')
    bucket = os.environ.get('AUDIO_BUCKET') or os.environ.get('BUCKET')
    key = os.environ.get('AUDIO_KEY') or os.environ.get('KEY')
    
    # Get confirmed downbeat values (if provided by user)
    confirmed_downbeat = os.environ.get('CONFIRMED_DOWNBEAT')
    confirmed_time_signature = os.environ.get('CONFIRMED_TIME_SIGNATURE')
    
    if confirmed_downbeat:
        confirmed_downbeat = float(confirmed_downbeat)
        log(f"✓ Using CONFIRMED downbeat: {confirmed_downbeat}s")
    if confirmed_time_signature:
        log(f"✓ Using CONFIRMED time signature: {confirmed_time_signature}")
    
    log(f"Environment Variables:")
    log(f"  JOB_ID: {job_id}")
    log(f"  BUCKET: {bucket}")
    log(f"  KEY: {key}")
    log(f"  JOBS_TABLE: {JOBS_TABLE}")
    log(f"  PDF_GENERATOR_FUNCTION: {PDF_GENERATOR_FUNCTION}")
    log(f"  CONFIRMED_DOWNBEAT: {confirmed_downbeat}")
    log(f"  CONFIRMED_TIME_SIGNATURE: {confirmed_time_signature}")
    
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
        chords_data = detect_chords(audio_path, job_id, confirmed_downbeat, confirmed_time_signature)
        detection_time = time.time() - start_time
        
        log(f"✓ Chord detection complete")
        log(f"  Total chords found: {len(chords_data['chords'])}")
        log(f"  Detection time: {detection_time:.2f}s")
        log(f"  Audio duration: {chords_data.get('duration', 0):.2f}s")
        log(f"  Key detected: {chords_data.get('key', 'Unknown')}")
        
        # Extract lyrics with Whisper
        log("Step 3.5: Extracting lyrics with Whisper...")
        lyrics_data = None
        if WHISPER_AVAILABLE:
            try:
                lyrics_start = time.time()
                lyrics_service = LyricsExtractionService(model_size='base')
                lyrics_data = lyrics_service.extract_lyrics(audio_path, job_id)
                lyrics_time = time.time() - lyrics_start
                
                if lyrics_data and lyrics_data.get('words'):
                    log(f"✓ Lyrics extraction complete")
                    log(f"  Words extracted: {len(lyrics_data['words'])}")
                    log(f"  Language: {lyrics_data.get('language', 'unknown')}")
                    log(f"  Extraction time: {lyrics_time:.2f}s")
                    
                    # Store lyrics data in job for alignment
                    update_job_with_lyrics(job_id, lyrics_data)
                else:
                    log("⚠️ No lyrics detected (instrumental track?)", "WARNING")
            except Exception as e:
                log(f"ERROR during lyrics extraction: {str(e)}", "ERROR")
                log(traceback.format_exc(), "ERROR")
                log("⚠️ Continuing without lyrics", "WARNING")
        else:
            log("ℹ️ Whisper not available, skipping lyrics extraction")
        
        # Perform lyrics-chord alignment if lyrics were extracted
        log("Step 3.6: Checking for lyrics data for alignment...")
        if lyrics_data and lyrics_data.get('words'):
            log("✓ Lyrics data found, performing lyrics-chord alignment...")
            try:
                alignment_start = time.time()
                lead_sheet = align_lyrics_with_chords(chords_data, lyrics_data)
                alignment_time = time.time() - alignment_start
                
                if lead_sheet:
                    chords_data['leadSheet'] = lead_sheet
                    log(f"✓ Lyrics-chord alignment complete")
                    log(f"  Sections created: {len(lead_sheet.get('sections', []))}")
                    log(f"  Alignment time: {alignment_time:.2f}s")
                else:
                    log("⚠️ Alignment returned None (possibly invalid data)", "WARNING")
            except Exception as e:
                log(f"ERROR during lyrics-chord alignment: {str(e)}", "ERROR")
                log(traceback.format_exc(), "ERROR")
                log("⚠️ Continuing without lead sheet data", "WARNING")
        else:
            log("ℹ️ No lyrics data found, skipping alignment")
        
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

class ChordDetector:
    """Chord detector with optional stem separation"""
    
    def __init__(self):
        self.demucs_model = None
        
        if ENABLE_STEM_SEPARATION and DEMUCS_AVAILABLE:
            try:
                log("Loading Demucs model for stem separation...")
                # Use lighter model for better memory efficiency
                self.demucs_model = get_model('mdx_extra')  # Lighter than htdemucs
                log("✓ Demucs model loaded successfully")
                log(f"  Model sample rate: {self.demucs_model.samplerate}Hz")
            except Exception as e:
                log(f"Failed to load Demucs model: {e}", "WARNING")
                log("Continuing without stem separation", "WARNING")
                self.demucs_model = None
        else:
            if ENABLE_STEM_SEPARATION:
                log("Stem separation enabled but Demucs not available", "WARNING")
            else:
                log("Stem separation disabled (ENABLE_STEM_SEPARATION=false)")
    
    def separate_harmonic_stem_chunked(self, audio_path: str) -> tuple:
        """
        Separate audio into stems using chunk-based processing
        Reduces peak memory usage from 8GB to ~2GB
        
        Returns:
            (audio_array, sample_rate) tuple
        """
        if not self.demucs_model:
            log("Using full mix (no stem separation)")
            return librosa.load(audio_path, sr=22050)
        
        try:
            log("🎵 Starting chunked stem separation...")
            
            # Get audio info
            info = torchaudio.info(audio_path)
            total_duration = info.num_frames / info.sample_rate
            log(f"   Audio duration: {total_duration:.1f}s")
            log(f"   Sample rate: {info.sample_rate}Hz")
            
            # Process in chunks
            chunk_size = CHUNK_DURATION * info.sample_rate
            num_chunks = int(np.ceil(info.num_frames / chunk_size))
            log(f"   Processing in {num_chunks} chunks of {CHUNK_DURATION}s each")
            
            harmonic_chunks = []
            
            for i, start_frame in enumerate(range(0, info.num_frames, chunk_size)):
                chunk_start_time = time.time()
                log(f"   Processing chunk {i+1}/{num_chunks}...")
                
                # Load only this chunk
                num_frames = min(chunk_size, info.num_frames - start_frame)
                wav, sr = torchaudio.load(
                    audio_path,
                    frame_offset=start_frame,
                    num_frames=num_frames
                )
                
                # Ensure stereo (Demucs expects stereo)
                if wav.shape[0] == 1:
                    wav = wav.repeat(2, 1)
                
                # Resample if needed
                if sr != self.demucs_model.samplerate:
                    resampler = torchaudio.transforms.Resample(sr, self.demucs_model.samplerate)
                    wav = resampler(wav)
                    sr = self.demucs_model.samplerate
                
                # Separate stems (no gradient needed for inference)
                with torch.no_grad():
                    sources = apply_model(self.demucs_model, wav[None], device='cpu')[0]
                
                # Extract harmonic content
                # sources: [drums, bass, other, vocals]
                bass = sources[1]
                other = sources[2]  # Piano, strings, synths, etc.
                harmonic = bass + other
                
                # Convert to mono
                harmonic_mono = torch.mean(harmonic, dim=0).numpy()
                harmonic_chunks.append(harmonic_mono)
                
                # Clear memory
                del wav, sources, bass, other, harmonic
                
                chunk_time = time.time() - chunk_start_time
                log(f"   ✓ Chunk {i+1}/{num_chunks} complete ({chunk_time:.1f}s)")
            
            # Concatenate all chunks
            log("   Concatenating chunks...")
            full_harmonic = np.concatenate(harmonic_chunks)
            
            # Resample to 22050 for librosa
            if sr != 22050:
                log(f"   Resampling from {sr}Hz to 22050Hz...")
                full_harmonic = librosa.resample(full_harmonic, orig_sr=sr, target_sr=22050)
                sr = 22050
            
            log(f"✓ Stem separation complete (harmonic stem extracted)")
            log(f"  Output duration: {len(full_harmonic) / sr:.1f}s")
            return full_harmonic, sr
            
        except Exception as e:
            log(f"Stem separation failed: {e}", "ERROR")
            log(traceback.format_exc(), "ERROR")
            log("Falling back to full mix", "WARNING")
            return librosa.load(audio_path, sr=22050)


class LyricsExtractionService:
    """
    Service for extracting lyrics from audio using Whisper
    Provides word-level timestamps for alignment with chords
    """
    
    def __init__(self, model_size='base'):
        """
        Initialize Whisper model
        
        Args:
            model_size: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
                       'base' is recommended for speed/accuracy balance
        """
        self.model = None
        self.model_size = model_size
        
        if not WHISPER_AVAILABLE:
            log("Whisper not available, lyrics extraction disabled", "WARNING")
            return
        
        try:
            log(f"Loading Whisper model ({model_size})...")
            self.model = whisper.load_model(model_size)
            log(f"✓ Whisper model loaded successfully")
        except Exception as e:
            log(f"Failed to load Whisper model: {e}", "ERROR")
            self.model = None
    
    def extract_lyrics(self, audio_path: str, job_id: str = None) -> dict:
        """
        Extract lyrics with word-level timestamps from audio
        
        Args:
            audio_path: Path to audio file
            job_id: Job ID for status updates (optional)
        
        Returns:
            dict with:
                - text: Full lyrics text
                - words: List of {word, start, end} dicts with timestamps
                - segments: List of phrase segments with timestamps
                - language: Detected language
                - duration: Audio duration in seconds
        """
        if not self.model:
            log("Whisper model not available", "WARNING")
            return {
                'text': '',
                'words': [],
                'segments': [],
                'language': 'unknown',
                'duration': 0
            }
        
        try:
            log(f"🎤 Extracting lyrics from: {audio_path}")
            
            # Transcribe with word-level timestamps
            if job_id:
                update_job_status(job_id, 'PROCESSING', 72, status_message="Running AI transcription on audio...")
            result = self.model.transcribe(
                audio_path,
                word_timestamps=True,
                verbose=False
            )
            
            # Extract word-level data
            if job_id:
                update_job_status(job_id, 'PROCESSING', 75, status_message="Processing transcribed lyrics...")
            words = []
            for segment in result.get('segments', []):
                for word_data in segment.get('words', []):
                    words.append({
                        'word': word_data['word'].strip(),
                        'start': word_data['start'],
                        'end': word_data['end']
                    })
            
            # Get audio duration
            try:
                audio_info = torchaudio.info(audio_path)
                duration = audio_info.num_frames / audio_info.sample_rate
            except:
                # Fallback to librosa if torchaudio fails
                y, sr = librosa.load(audio_path, sr=None)
                duration = librosa.get_duration(y=y, sr=sr)
            
            lyrics_data = {
                'text': result['text'].strip(),
                'words': words,
                'segments': result.get('segments', []),
                'language': result.get('language', 'unknown'),
                'duration': duration
            }
            
            log(f"✓ Lyrics extracted successfully")
            log(f"  Total words: {len(words)}")
            log(f"  Language: {lyrics_data['language']}")
            log(f"  Duration: {duration:.1f}s")
            
            # Check for instrumental sections (no vocals)
            if len(words) == 0:
                log("  ⚠️ No lyrics detected - may be instrumental", "WARNING")
            
            return lyrics_data
            
        except Exception as e:
            log(f"Error extracting lyrics: {e}", "ERROR")
            log(traceback.format_exc(), "ERROR")
            return {
                'text': '',
                'words': [],
                'segments': [],
                'language': 'unknown',
                'duration': 0,
                'error': str(e)
            }


# Initialize detector globally
detector = ChordDetector()

def detect_key_improved(chroma):
    """
    Improved key detection using Krumhansl-Schmuckler algorithm
    Returns: (key, mode, confidence)
    """
    # Krumhansl-Schmuckler key profiles
    major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
    
    # Average chroma over time
    chroma_mean = np.mean(chroma, axis=1)
    
    # Normalize
    if np.sum(chroma_mean) > 0:
        chroma_mean = chroma_mean / np.sum(chroma_mean)
    
    # Calculate correlation with each key
    chord_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    best_corr = -1
    best_key = 'C'
    best_mode = 'major'
    
    for i in range(12):
        # Rotate profiles to match each key
        major_rot = np.roll(major_profile, i)
        minor_rot = np.roll(minor_profile, i)
        
        # Normalize profiles
        major_rot = major_rot / np.sum(major_rot)
        minor_rot = minor_rot / np.sum(minor_rot)
        
        # Calculate correlation
        major_corr = np.corrcoef(chroma_mean, major_rot)[0, 1]
        minor_corr = np.corrcoef(chroma_mean, minor_rot)[0, 1]
        
        if major_corr > best_corr:
            best_corr = major_corr
            best_key = chord_names[i]
            best_mode = 'major'
        
        if minor_corr > best_corr:
            best_corr = minor_corr
            best_key = chord_names[i]
            best_mode = 'minor'
    
    return best_key, best_mode, best_corr

def detect_key_from_progression(chords):
    """
    ENHANCED: Detect key by analyzing ONLY repeating chord progression patterns
    PLUS: Use most common chord as a strong hint
    
    Strategy:
    1. Count chord frequency - most common chord is likely I or vi
    2. Find patterns that repeat at least 2 times
    3. Analyze repeating patterns against all possible keys
    4. Score based on common progressions (I-vi-ii-V, I-IV-V, etc.)
    5. Combine frequency analysis with progression analysis
    
    Returns: (key, mode, confidence, pattern_info)
    """
    if len(chords) < 8:  # Need at least 8 chords to detect patterns
        return 'C', 'major', 0.0, {}
    
    log("🎹 ENHANCED KEY DETECTION FROM REPEATED PROGRESSIONS")
    
    chord_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    # Extract chord roots as a sequence
    chord_sequence = []
    chord_frequency = {}  # Count how often each chord appears
    
    for chord in chords:
        chord_name = chord['chord']
        root = chord_name[0]
        if len(chord_name) > 1 and chord_name[1] in ['#', 'b']:
            root = chord_name[:2]
        
        # Determine if major or minor
        is_minor = 'm' in chord_name.lower() and 'maj' not in chord_name.lower()
        chord_sequence.append({'root': root, 'minor': is_minor})
        
        # Count frequency
        chord_frequency[root] = chord_frequency.get(root, 0) + 1
    
    log(f"  Total chords in sequence: {len(chord_sequence)}")
    
    # STEP 0: Analyze chord frequency (most common chord is likely tonic or relative)
    sorted_chords = sorted(chord_frequency.items(), key=lambda x: x[1], reverse=True)
    most_common_chord = sorted_chords[0][0] if sorted_chords else 'C'
    most_common_count = sorted_chords[0][1] if sorted_chords else 0
    
    log(f"  Most common chord: {most_common_chord} ({most_common_count} times)")
    log(f"  Top 5 chords: {sorted_chords[:5]}")
    
    # Give strong weight to most common chord being the tonic
    frequency_scores = {}
    for chord_root, count in chord_frequency.items():
        try:
            # This chord as potential tonic
            frequency_scores[chord_root] = count * 10  # Strong weight
            
            # Also consider relative major/minor (3 semitones away)
            chord_idx = chord_names.index(chord_root)
            relative_idx = (chord_idx + 3) % 12  # Minor third up = relative major
            relative_chord = chord_names[relative_idx]
            if relative_chord not in frequency_scores:
                frequency_scores[relative_chord] = 0
            frequency_scores[relative_chord] += count * 5  # Medium weight
        except ValueError:
            continue
    
    log(f"  Frequency-based key candidates:")
    for i, (key, score) in enumerate(sorted(frequency_scores.items(), key=lambda x: x[1], reverse=True)[:3], 1):
        log(f"    {i}. {key}: {score:.1f} points (frequency)")
    
    # STEP 1: Find repeating patterns (6-16 chord sequences)
    pattern_scores = {}  # key -> score
    all_patterns = {}  # Store all patterns found for structure detection
    repeating_patterns_found = 0
    
    for pattern_length in range(6, 17):  # Try patterns of 6-16 chords (1.5 to 4 measures)
        patterns_found = {}
        pattern_positions = {}  # Track where each pattern occurs
        
        for i in range(len(chord_sequence) - pattern_length + 1):
            pattern = tuple(c['root'] for c in chord_sequence[i:i+pattern_length])
            patterns_found[pattern] = patterns_found.get(pattern, 0) + 1
            
            if pattern not in pattern_positions:
                pattern_positions[pattern] = []
            pattern_positions[pattern].append(i)
        
        # STEP 2: Filter - only keep patterns that repeat at least twice
        for pattern, count in patterns_found.items():
            if count >= 2:  # Pattern must repeat at least once (appear 2+ times)
                repeating_patterns_found += 1
                
                # Store pattern info for structure detection
                all_patterns[pattern] = {
                    'count': count,
                    'length': pattern_length,
                    'positions': pattern_positions[pattern]
                }
                
                # STEP 3: Analyze this repeating pattern for each possible key
                for potential_key in chord_names:
                    key_idx = chord_names.index(potential_key)
                    
                    # Convert pattern to intervals relative to potential key
                    intervals = []
                    for root in pattern:
                        try:
                            root_idx = chord_names.index(root)
                            interval = (root_idx - key_idx) % 12
                            intervals.append(interval)
                        except ValueError:
                            continue
                    
                    # STEP 4: Score based on common progressions
                    progression_score = 0
                    
                    # I-vi-ii-V (0-9-2-7) - very common in jazz/pop
                    if tuple(intervals) == (0, 9, 2, 7) or tuple(intervals[:4]) == (0, 9, 2, 7):
                        progression_score = 10
                        log(f"  Found I-vi-ii-V in {potential_key}: {list(pattern)[:4]}")
                    # I-IV-V (0-5-7) - most common in rock/pop
                    elif tuple(intervals) == (0, 5, 7) or tuple(intervals[:3]) == (0, 5, 7):
                        progression_score = 9
                        log(f"  Found I-IV-V in {potential_key}: {list(pattern)[:3]}")
                    # I-V-vi-IV (0-7-9-5) - very common pop progression (Axis)
                    elif tuple(intervals) == (0, 7, 9, 5) or tuple(intervals[:4]) == (0, 7, 9, 5):
                        progression_score = 9
                    # ii-V-I (2-7-0) - jazz cadence
                    elif tuple(intervals) == (2, 7, 0) or tuple(intervals[:3]) == (2, 7, 0):
                        progression_score = 8
                    # I-vi-IV-V (0-9-5-7) - 50s progression
                    elif tuple(intervals) == (0, 9, 5, 7) or tuple(intervals[:4]) == (0, 9, 5, 7):
                        progression_score = 8
                    # I-IV-I-V (0-5-0-7) - common in folk/country
                    elif tuple(intervals[:4]) == (0, 5, 0, 7):
                        progression_score = 7
                    # V-I cadence (7-0) - strongest cadence
                    elif len(intervals) >= 2 and intervals[-2:] == [7, 0]:
                        progression_score = 7
                    # IV-I cadence (5-0) - plagal cadence (Amen)
                    elif len(intervals) >= 2 and intervals[-2:] == [5, 0]:
                        progression_score = 6
                    # Starts with I (0) - likely tonic
                    elif intervals[0] == 0:
                        progression_score = 4
                    # Ends with I (0) - likely tonic
                    elif intervals[-1] == 0:
                        progression_score = 5
                    
                    if progression_score > 0:
                        if potential_key not in pattern_scores:
                            pattern_scores[potential_key] = 0
                        # Weight by: progression strength × repetition count × pattern length
                        pattern_scores[potential_key] += progression_score * (count ** 1.5) * pattern_length
    
    log(f"  Repeating patterns found: {repeating_patterns_found}")
    
    # STEP 5: Combine frequency scores with pattern scores
    combined_scores = {}
    for key in set(list(frequency_scores.keys()) + list(pattern_scores.keys())):
        combined_scores[key] = frequency_scores.get(key, 0) + pattern_scores.get(key, 0)
    
    if not combined_scores:
        log("  ⚠️ No key candidates found - falling back to most common chord")
        return most_common_chord, 'major', 0.0, {}
    
    # Find best key based on combined analysis
    best_key = max(combined_scores, key=combined_scores.get)
    total_score = sum(combined_scores.values())
    confidence = combined_scores[best_key] / total_score if total_score > 0 else 0.0
    
    # Log top 3 key candidates
    sorted_keys = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
    log(f"  Top key candidates (combined):")
    for i, (key, score) in enumerate(sorted_keys[:3]):
        freq_score = frequency_scores.get(key, 0)
        prog_score = pattern_scores.get(key, 0)
        log(f"    {i+1}. {key}: {score:.1f} points (freq: {freq_score:.1f}, prog: {prog_score:.1f})")
    
    # STEP 6: Determine mode by analyzing chord qualities in the key
    major_indicators = 0
    minor_indicators = 0
    
    for i, chord_info in enumerate(chord_sequence):
        root = chord_info['root']
        is_minor = chord_info['minor']
        
        try:
            key_idx = chord_names.index(best_key)
            root_idx = chord_names.index(root)
            interval = (root_idx - key_idx) % 12
            
            # In major keys:
            # I, IV, V are major (0, 5, 7)
            # ii, iii, vi are minor (2, 4, 9)
            if interval in [0, 5, 7]:  # I, IV, V positions
                if not is_minor:
                    major_indicators += 2
                else:
                    minor_indicators += 1
            elif interval in [2, 4, 9]:  # ii, iii, vi positions
                if is_minor:
                    major_indicators += 1
                else:
                    minor_indicators += 1
            
            # In minor keys:
            # i, iv, v are minor (0, 5, 7)
            # III, VI, VII are major (3, 8, 10)
            if interval == 0:  # Tonic chord
                if is_minor:
                    minor_indicators += 3
                else:
                    major_indicators += 3
        except ValueError:
            continue
    
    mode = 'major' if major_indicators >= minor_indicators else 'minor'
    
    log(f"  ✓ Key detected: {best_key} {mode}")
    log(f"  Confidence: {confidence:.2%}")
    log(f"  Mode indicators: major={major_indicators}, minor={minor_indicators}")
    
    return best_key, mode, confidence, all_patterns

def detect_chords_essentia(audio_path, job_id):
    """
    Detect chords using Essentia's HPCP-based chord detection
    Essentia is simpler than madmom and easier to install
    """
    log("🎸 Using Essentia chord detection")
    log("Loading audio file...")
    start_time = time.time()
    
    # Load audio with essentia
    loader = es.MonoLoader(filename=audio_path, sampleRate=44100)
    audio = loader()
    duration = len(audio) / 44100.0
    load_time = time.time() - start_time
    
    log(f"✓ Audio loaded successfully")
    log(f"  Duration: {duration:.2f}s")
    log(f"  Sample rate: 44100Hz")
    log(f"  Samples: {len(audio)}")
    log(f"  Load time: {load_time:.2f}s")
    
    # Detect tempo
    log("Detecting tempo...")
    tempo_start = time.time()
    rhythm_extractor = es.RhythmExtractor2013(method="multifeature")
    bpm, beats, beats_confidence, _, beats_intervals = rhythm_extractor(audio)
    tempo_value = float(bpm)
    time_signature = "4/4"  # Essentia doesn't detect time signature directly
    tempo_time = time.time() - tempo_start
    
    log(f"✓ Tempo detected: {tempo_value:.1f} BPM")
    log(f"✓ Time signature: {time_signature} (default)")
    log(f"  Beats detected: {len(beats)}")
    log(f"  Detection time: {tempo_time:.2f}s")
    
    # Detect chords using HPCP (Harmonic Pitch Class Profile)
    log("Detecting chords with Essentia HPCP...")
    start_time = time.time()
    
    try:
        # Frame-based analysis
        frame_size = 4096
        hop_size = 2048
        
        # Windowing
        windowing = es.Windowing(type='blackmanharris62')
        # Spectrum
        spectrum = es.Spectrum()
        # Spectral peaks
        spectral_peaks = es.SpectralPeaks(orderBy='magnitude',
                                          magnitudeThreshold=0.00001,
                                          minFrequency=40,
                                          maxFrequency=5000,
                                          maxPeaks=60)
        # HPCP
        hpcp = es.HPCP()
        # Key detection
        key_detector = es.Key(profileType='temperley')
        
        # Process audio in frames
        hpcps = []
        for frame in es.FrameGenerator(audio, frameSize=frame_size, hopSize=hop_size):
            frame_windowed = windowing(frame)
            frame_spectrum = spectrum(frame_windowed)
            frequencies, magnitudes = spectral_peaks(frame_spectrum)
            frame_hpcp = hpcp(frequencies, magnitudes)
            hpcps.append(frame_hpcp)
        
        hpcps = np.array(hpcps)
        
        log(f"  Computed {len(hpcps)} HPCP frames")
        
        # Detect key from HPCP
        # Key algorithm returns: key, scale, strength, first_to_second_relative_strength
        key_result = key_detector(np.mean(hpcps, axis=0))
        key = key_result[0]
        scale = key_result[1]
        strength = key_result[2]
        
        log(f"  Key detected: {key} {scale} (strength: {strength:.2f})")
        
        # Simple chord detection: analyze HPCP at beat positions
        beat_chords = []
        frames_per_second = 44100 / hop_size
        
        for i, beat_time in enumerate(beats):
            frame_idx = int(beat_time * frames_per_second)
            if frame_idx >= len(hpcps):
                continue
            
            # Average HPCP around this beat
            start_frame = max(0, frame_idx - 2)
            end_frame = min(len(hpcps), frame_idx + 3)
            beat_hpcp = np.mean(hpcps[start_frame:end_frame], axis=0)
            
            # Find dominant pitch class
            dominant_pc = np.argmax(beat_hpcp)
            
            # Map to chord name (simplified - just root note for now)
            chord_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            chord_root = chord_names[dominant_pc]
            
            # Determine major/minor by checking third
            minor_third_idx = (dominant_pc + 3) % 12
            major_third_idx = (dominant_pc + 4) % 12
            
            if beat_hpcp[minor_third_idx] > beat_hpcp[major_third_idx] * 1.2:
                chord_name = chord_root + 'm'
            else:
                chord_name = chord_root
            
            beat_chords.append({
                'chord': chord_name,
                'time': float(beat_time),
                'confidence': float(beat_hpcp[dominant_pc])
            })
        
        log(f"  Detected {len(beat_chords)} beat-level chords")
        
        # Consolidate consecutive identical chords
        log("  Consolidating consecutive identical chords...")
        chords = []
        if len(beat_chords) > 0:
            current = beat_chords[0].copy()
            current['start'] = current['time']
            
            for i in range(1, len(beat_chords)):
                if beat_chords[i]['chord'] == current['chord']:
                    # Extend current chord
                    pass
                else:
                    # Save current and start new
                    current['end'] = beat_chords[i]['time']
                    current['duration'] = current['end'] - current['start']
                    if current['duration'] >= 0.5:  # Min 0.5s
                        chords.append(current)
                    current = beat_chords[i].copy()
                    current['start'] = current['time']
            
            # Add last chord
            current['end'] = duration
            current['duration'] = duration - current['start']
            if current['duration'] >= 0.5:
                chords.append(current)
        
        # Clean up chord data
        for chord in chords:
            chord['start'] = round(chord['start'], 2)
            chord['end'] = round(chord['end'], 2)
            chord['duration'] = round(chord['duration'], 2)
            chord['confidence'] = round(chord['confidence'], 2)
            del chord['time']
        
        detection_time = time.time() - start_time
        log(f"✓ Chord detection complete")
        log(f"  Final chord count: {len(chords)}")
        if len(chords) > 0:
            log(f"  Average chord duration: {np.mean([c['duration'] for c in chords]):.2f}s")
            major_count = sum(1 for c in chords if 'm' not in c['chord'])
            minor_count = sum(1 for c in chords if 'm' in c['chord'])
            log(f"  Chord quality: {major_count} major, {minor_count} minor")
            
            log("  First 20 chords detected:")
            for i, chord in enumerate(chords[:20]):
                log(f"    {i+1}. {chord['chord']:6s} at {chord['start']:6.1f}s (duration: {chord['duration']:.1f}s)")
        
        log(f"  Detection time: {detection_time:.2f}s")
        
    except Exception as e:
        log(f"ERROR in essentia chord detection: {str(e)}", "ERROR")
        log(traceback.format_exc(), "ERROR")
        log("Falling back to librosa chord detection", "WARNING")
        return detect_chords_librosa(audio_path, job_id)
    
    # Detect key from progression
    log("Detecting key from progression...")
    key_start = time.time()
    key_prog, mode_prog, confidence_prog, pattern_info = detect_key_from_progression(chords)
    
    # Use essentia key if progression confidence is low
    if confidence_prog < 0.2:
        # Convert essentia key format
        key_final = key
        mode_final = 'major' if scale == 'major' else 'minor'
        confidence_final = strength
        log(f"  Using Essentia key detection (low progression confidence)")
    else:
        key_final = key_prog
        mode_final = mode_prog
        confidence_final = confidence_prog
        log(f"  Using progression-based key detection")
    
    key_time = time.time() - key_start
    
    log(f"✓ Key detection complete")
    log(f"  Detected key: {key_final} {mode_final}")
    log(f"  Confidence: {confidence_final:.2f}")
    log(f"  Essentia: {key} {scale} ({strength:.2f})")
    log(f"  Progression: {key_prog} {mode_prog} ({confidence_prog:.2f})")
    log(f"  Detection time: {key_time:.2f}s")
    
    # Detect song structure with MSAF (audio-based segmentation)
    log("Detecting song structure...")
    structure_start = time.time()
    
    # Try MSAF first for audio-based segmentation
    msaf_segments = detect_structure_msaf(audio_path)
    
    # Also get pattern-based structure for comparison/fallback
    pattern_structure = detect_song_structure(chords, pattern_info, tempo_value)
    
    # Use MSAF if available and reasonable, otherwise fall back to pattern-based
    if msaf_segments and len(msaf_segments) >= 3 and len(msaf_segments) <= 20:
        song_structure = msaf_segments
        log(f"✓ Using MSAF audio-based segmentation: {len(song_structure)} segments")
        log(f"  Algorithm: {song_structure[0].get('algorithm', 'unknown')}")
    else:
        song_structure = pattern_structure
        if msaf_segments:
            log(f"⚠️ MSAF returned {len(msaf_segments)} segments (outside 3-20 range), using pattern-based")
        else:
            log(f"✓ Using pattern-based structure detection: {len(song_structure)} sections")
    
    structure_time = time.time() - structure_start
    
    for section in song_structure:
        if 'measureStart' in section:
            log(f"  {section['label']}: measures {section['measureStart']}-{section['measureEnd']} ({section.get('patternCount', 0)} repetitions)")
        else:
            log(f"  {section['label']}: {section['start']:.1f}s - {section['end']:.1f}s ({section['duration']:.1f}s)")
    log(f"  Detection time: {structure_time:.2f}s")
    
    # Pattern analysis logging
    log("=" * 80)
    log("📊 DETAILED PATTERN ANALYSIS")
    log("=" * 80)
    
    if pattern_info:
        sorted_patterns = sorted(
            pattern_info.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )
        repeating_patterns = [(p, info) for p, info in sorted_patterns if info['count'] >= 2]
        
        log(f"Total patterns found: {len(pattern_info)}")
        log(f"Repeating patterns (2+ occurrences): {len(repeating_patterns)}")
        log("")
        
        for i, (pattern, info) in enumerate(repeating_patterns[:10], 1):
            log(f"Pattern {i}:")
            log(f"  Progression: {' → '.join(list(pattern))}")
            log(f"  Length: {info['length']} chords")
            log(f"  Occurrences: {info['count']} times")
            log("")
    else:
        log("No patterns detected")
    
    log("=" * 80)
    
    return {
        'chords': chords,
        'key': key_final,
        'mode': mode_final,
        'keyConfidence': round(confidence_final, 2),
        'tempo': round(tempo_value, 1),
        'timeSignature': time_signature,
        'duration': round(duration, 2),
        'totalChords': len(chords),
        'songStructure': song_structure,
        'patternAnalysis': format_pattern_analysis(pattern_info, key_final),
        'model': 'essentia-hpcp'
    }

def detect_chords(audio_path, job_id, confirmed_downbeat=None, confirmed_time_signature=None):
    """
    Main chord detection function - ALWAYS uses enhanced librosa with 84 templates
    (Essentia detection disabled in favor of enhanced librosa system)
    """
    # FORCE enhanced librosa detection (84 templates)
    # Even if essentia is available, we want to use the new enhanced system
    log("Using ENHANCED librosa chord detection (84 templates)")
    return detect_chords_librosa(audio_path, job_id, confirmed_downbeat, confirmed_time_signature)

def detect_chords_librosa(audio_path, job_id, confirmed_downbeat=None, confirmed_time_signature=None):
    """Detect chords using librosa chromagram analysis with optional stem separation"""
    log("Loading audio file...")
    start_time = time.time()
    
    # Use stem separation if enabled, otherwise load full mix
    if ENABLE_STEM_SEPARATION and detector.demucs_model:
        log("Using stem separation for improved chord detection...")
        y, sr = detector.separate_harmonic_stem_chunked(audio_path)
    else:
        y, sr = librosa.load(audio_path, sr=22050)
    
    duration = librosa.get_duration(y=y, sr=sr)
    load_time = time.time() - start_time
    
    log(f"✓ Audio loaded successfully")
    log(f"  Duration: {duration:.2f}s")
    log(f"  Sample rate: {sr}Hz")
    log(f"  Samples: {len(y)}")
    log(f"  Load time: {load_time:.2f}s")
    
    # Detect tempo and time signature using beat tracking
    log("Detecting tempo and time signature...")
    tempo_start = time.time()
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    tempo_time = time.time() - tempo_start
    # Extract tempo value (librosa returns array, take first element)
    tempo_value = float(tempo) if isinstance(tempo, (int, float)) else float(tempo[0]) if hasattr(tempo, '__len__') else float(tempo)
    
    # Use confirmed time signature if provided, otherwise detect
    if confirmed_time_signature:
        time_signature = confirmed_time_signature
        log(f"✓ Using CONFIRMED time signature: {time_signature}")
    else:
        time_signature = detect_time_signature(y, sr, beats)
        log(f"✓ Time signature detected: {time_signature}")
    
    log(f"✓ Tempo detected: {tempo_value:.1f} BPM")
    log(f"  Beats detected: {len(beats)}")
    log(f"  Detection time: {tempo_time:.2f}s")
    
    # Detect downbeat if not confirmed
    if confirmed_downbeat is None:
        log("Detecting downbeat automatically...")
        try:
            sys.path.insert(0, '/app/simple-pipeline/chord-detection')
            from downbeat_detection import detect_downbeats
            
            beat_times = librosa.frames_to_time(beats, sr=sr)
            downbeats, first_downbeat, downbeat_info = detect_downbeats(
                audio_path, 
                beat_times, 
                tempo_value, 
                time_signature if confirmed_time_signature else time_signature
            )
            
            confirmed_downbeat = first_downbeat
            log(f"✓ Downbeat detected automatically: {confirmed_downbeat:.3f}s")
            log(f"  Confidence: {downbeat_info.get('confidence', 0):.2f}")
            log(f"  Method: {downbeat_info.get('method', 'unknown')}")
        except Exception as e:
            log(f"⚠ Downbeat detection failed, using first beat: {str(e)}", "WARNING")
            confirmed_downbeat = None
    
    # Use confirmed downbeat if provided
    if confirmed_downbeat is not None:
        log(f"✓ Using CONFIRMED downbeat: {confirmed_downbeat}s")
        # Adjust beat times to align with confirmed downbeat
        beat_times = librosa.frames_to_time(beats, sr=sr)
        
        # Find the beat closest to the confirmed downbeat
        closest_beat_idx = np.argmin(np.abs(beat_times - confirmed_downbeat))
        
        # Calculate beats per measure from time signature
        beats_per_measure = int(time_signature.split('/')[0])
        
        # Determine which beat in the measure the closest beat represents
        # and adjust to make confirmed_downbeat the first beat of a measure
        beat_offset = closest_beat_idx % beats_per_measure
        
        # Shift all beat indices so confirmed downbeat aligns with measure start
        if beat_offset != 0:
            # We need to shift beats so the confirmed downbeat is at position 0 in measure
            beats = beats[beat_offset:]
            log(f"  Adjusted beat alignment: removed {beat_offset} beats to align with downbeat")
        
        log(f"  Beats after alignment: {len(beats)}")
    else:
        log("  Using auto-detected downbeat (first beat)")
    
    # Compute chromagram with better parameters for chord detection
    log("Computing chromagram...")
    start_time = time.time()
    
    # Use CQT chromagram with higher resolution and smoothing
    chroma = librosa.feature.chroma_cqt(
        y=y, 
        sr=sr, 
        hop_length=2048,  # Larger hop = less temporal resolution but more stable
        n_chroma=12,
        bins_per_octave=36  # Higher resolution
    )
    
    # Apply median filtering to smooth out noise
    chroma = median_filter(chroma, size=(1, 5))  # Smooth along time axis
    
    chroma_time = time.time() - start_time
    log(f"✓ Chromagram computed")
    log(f"  Shape: {chroma.shape}")
    log(f"  Compute time: {chroma_time:.2f}s")
    
    # IMPROVED CHORD DETECTION WITH ENHANCED TEMPLATES
    log("Detecting chord changes (beat-synchronized with enhanced templates)...")
    start_time = time.time()
    chords = []
    
    # IMPROVED: Create half-beat analysis points for better temporal resolution
    # This captures chord changes that happen between beats
    beat_times = librosa.frames_to_time(beats, sr=sr)
    
    # Generate half-beat positions
    half_beat_times = []
    for i in range(len(beat_times) - 1):
        half_beat_times.append(beat_times[i])
        # Add midpoint between this beat and next
        half_beat_times.append((beat_times[i] + beat_times[i + 1]) / 2)
    half_beat_times.append(beat_times[-1])  # Add last beat
    
    # Convert to frames
    analysis_frames = librosa.time_to_frames(
        np.array(half_beat_times),
        sr=sr,
        hop_length=2048
    )
    
    log(f"  Analyzing at {len(analysis_frames)} positions (half-beat resolution)")
    log(f"  Original beats: {len(beats)}, Analysis points: {len(analysis_frames)}")
    
    # ENHANCED: Create comprehensive chord templates (84 total)
    chord_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    def create_enhanced_chord_templates():
        """Create 84 chord templates covering major, minor, 7th, maj7, m7, sus4, dim"""
        templates = {}
        
        for root_idx in range(12):
            root = chord_names[root_idx]
            
            # Major (1, 3, 5)
            major = np.zeros(12)
            major[[0, 4, 7]] = [1.0, 0.8, 0.9]
            templates[root] = np.roll(major, root_idx)
            
            # Minor (1, b3, 5)
            minor = np.zeros(12)
            minor[[0, 3, 7]] = [1.0, 0.8, 0.9]
            templates[root + 'm'] = np.roll(minor, root_idx)
            
            # Dominant 7th (1, 3, 5, b7)
            dom7 = np.zeros(12)
            dom7[[0, 4, 7, 10]] = [1.0, 0.7, 0.8, 0.6]
            templates[root + '7'] = np.roll(dom7, root_idx)
            
            # Major 7th (1, 3, 5, 7)
            maj7 = np.zeros(12)
            maj7[[0, 4, 7, 11]] = [1.0, 0.7, 0.8, 0.6]
            templates[root + 'maj7'] = np.roll(maj7, root_idx)
            
            # Minor 7th (1, b3, 5, b7)
            min7 = np.zeros(12)
            min7[[0, 3, 7, 10]] = [1.0, 0.7, 0.8, 0.6]
            templates[root + 'm7'] = np.roll(min7, root_idx)
            
            # Sus4 (1, 4, 5)
            sus4 = np.zeros(12)
            sus4[[0, 5, 7]] = [1.0, 0.7, 0.9]
            templates[root + 'sus4'] = np.roll(sus4, root_idx)
            
            # Diminished (1, b3, b5)
            dim = np.zeros(12)
            dim[[0, 3, 6]] = [1.0, 0.8, 0.8]
            templates[root + 'dim'] = np.roll(dim, root_idx)
        
        return templates
    
    templates = create_enhanced_chord_templates()
    log(f"  Created {len(templates)} enhanced chord templates (major, minor, 7th, maj7, m7, sus4, dim)")
    
    # Analyze chords at each half-beat position
    beat_chords = []
    for i, analysis_frame in enumerate(analysis_frames):
        if analysis_frame >= chroma.shape[1]:
            continue
        
        # Get chroma vector at this position (average nearby frames for stability)
        start_frame = max(0, analysis_frame - 2)
        end_frame = min(chroma.shape[1], analysis_frame + 3)
        chroma_beat = np.mean(chroma[:, start_frame:end_frame], axis=1)
        
        # Normalize
        if np.sum(chroma_beat) > 0:
            chroma_beat = chroma_beat / np.sum(chroma_beat)
        
        # Find best matching chord from all 84 templates
        best_score = -1
        best_chord = 'C'
        
        for chord_name, template in templates.items():
            # Normalize template
            if np.sum(template) > 0:
                template_norm = template / np.sum(template)
            else:
                continue
            
            # Calculate correlation
            score = np.dot(chroma_beat, template_norm)
            
            if score > best_score:
                best_score = score
                best_chord = chord_name
        
        analysis_time = half_beat_times[i] if i < len(half_beat_times) else duration
        
        beat_chords.append({
            'chord': best_chord,
            'time': analysis_time,
            'confidence': best_score,
            'position_index': i
        })
    
    log(f"  Detected {len(beat_chords)} chords at half-beat positions")
    
    # CONSOLIDATE: Merge consecutive identical chords
    log("  Consolidating consecutive identical chords...")
    
    if len(beat_chords) > 0:
        current_chord = beat_chords[0]['chord']
        current_start = beat_chords[0]['time']
        current_confidence = [beat_chords[0]['confidence']]
        
        for i in range(1, len(beat_chords)):
            if beat_chords[i]['chord'] == current_chord:
                # Same chord, accumulate confidence
                current_confidence.append(beat_chords[i]['confidence'])
            else:
                # Chord changed, save previous chord
                avg_confidence = np.mean(current_confidence)
                
                # Only keep chords with reasonable confidence (lowered for enhanced templates)
                if avg_confidence > 0.08:  # Lower threshold for 84-template system
                    chords.append({
                        'chord': current_chord,
                        'start': round(current_start, 2),
                        'end': round(beat_chords[i]['time'], 2),
                        'duration': round(beat_chords[i]['time'] - current_start, 2),
                        'confidence': round(avg_confidence, 2)
                    })
                
                # Start new chord
                current_chord = beat_chords[i]['chord']
                current_start = beat_chords[i]['time']
                current_confidence = [beat_chords[i]['confidence']]
        
        # Add last chord
        if len(current_confidence) > 0:
            avg_confidence = np.mean(current_confidence)
            if avg_confidence > 0.08:  # Lower threshold for 84-template system
                chords.append({
                    'chord': current_chord,
                    'start': round(current_start, 2),
                    'end': round(duration, 2),
                    'duration': round(duration - current_start, 2),
                    'confidence': round(avg_confidence, 2)
                })
    
    # FILTER: Remove very short chords (likely noise)
    log("  Filtering out very short chords...")
    min_duration = 0.5  # Minimum 0.5 seconds (lowered from 1.0 for better resolution)
    chords = [c for c in chords if c['duration'] >= min_duration]
    
    detection_time = time.time() - start_time
    log(f"✓ Chord detection complete")
    log(f"  Final chord count: {len(chords)} (after consolidation and filtering)")
    log(f"  Average chord duration: {np.mean([c['duration'] for c in chords]):.2f}s")
    log(f"  Detection time: {detection_time:.2f}s")
    
    # Estimate key using improved Krumhansl-Schmuckler algorithm
    log("Detecting key...")
    key_start = time.time()
    key_chromagram, mode_chromagram, confidence_chromagram = detect_key_improved(chroma)
    
    # Also analyze chord progression for better key detection
    key_progression, mode_progression, confidence_progression, pattern_info = detect_key_from_progression(chords)
    
    # Use progression-based detection if confidence is higher
    if confidence_progression > confidence_chromagram:
        key = key_progression
        mode = mode_progression
        confidence = confidence_progression
        log(f"  Using progression-based key detection (higher confidence)")
    else:
        key = key_chromagram
        mode = mode_chromagram
        confidence = confidence_chromagram
        log(f"  Using chromagram-based key detection")
    
    key_time = time.time() - key_start
    
    log(f"✓ Key detection complete")
    log(f"  Detected key: {key} {mode}")
    log(f"  Confidence: {confidence:.2f}")
    log(f"  Chromagram: {key_chromagram} {mode_chromagram} ({confidence_chromagram:.2f})")
    log(f"  Progression: {key_progression} {mode_progression} ({confidence_progression:.2f})")
    log(f"  Detection time: {key_time:.2f}s")
    
    # Detect song structure with MSAF (audio-based segmentation)
    log("Detecting song structure...")
    structure_start = time.time()
    
    # Try MSAF first for audio-based segmentation
    msaf_segments = detect_structure_msaf(audio_path)
    
    # Also get pattern-based structure for comparison/fallback
    pattern_structure = detect_song_structure(chords, pattern_info, tempo_value)
    
    # Use MSAF if available and reasonable, otherwise fall back to pattern-based
    if msaf_segments and len(msaf_segments) >= 3 and len(msaf_segments) <= 20:
        song_structure = msaf_segments
        log(f"✓ Using MSAF audio-based segmentation: {len(song_structure)} segments")
        log(f"  Algorithm: {song_structure[0].get('algorithm', 'unknown')}")
    else:
        song_structure = pattern_structure
        if msaf_segments:
            log(f"⚠️ MSAF returned {len(msaf_segments)} segments (outside 3-20 range), using pattern-based")
        else:
            log(f"✓ Using pattern-based structure detection: {len(song_structure)} sections")
    
    structure_time = time.time() - structure_start
    
    for section in song_structure:
        if 'measureStart' in section:
            log(f"  {section['label']}: measures {section['measureStart']}-{section['measureEnd']} ({section.get('patternCount', 0)} repetitions)")
        else:
            log(f"  {section['label']}: {section['start']:.1f}s - {section['end']:.1f}s ({section['duration']:.1f}s)")
    log(f"  Detection time: {structure_time:.2f}s")
    
    # DETAILED PATTERN ANALYSIS FOR DEBUGGING
    log("=" * 80)
    log("📊 DETAILED PATTERN ANALYSIS")
    log("=" * 80)
    
    if pattern_info:
        # Sort patterns by count (most repeated first)
        sorted_patterns = sorted(
            pattern_info.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )
        
        # Filter to only repeating patterns (2+ occurrences)
        repeating_patterns = [(p, info) for p, info in sorted_patterns if info['count'] >= 2]
        
        log(f"Total patterns found: {len(pattern_info)}")
        log(f"Repeating patterns (2+ occurrences): {len(repeating_patterns)}")
        log("")
        
        for i, (pattern, info) in enumerate(repeating_patterns[:10], 1):  # Show top 10
            log(f"Pattern {i}:")
            log(f"  Progression: {' → '.join(list(pattern))}")
            log(f"  Length: {info['length']} chords")
            log(f"  Occurrences: {info['count']} times")
            log(f"  Positions: {info['positions']}")
            
            # Show timing for each occurrence
            for j, pos in enumerate(info['positions'][:5], 1):  # Show first 5 occurrences
                if pos < len(chords):
                    start_time = chords[pos].get('start', 0) or chords[pos].get('time', 0)
                    log(f"    Occurrence {j}: starts at {start_time:.1f}s (chord index {pos})")
            
            if len(info['positions']) > 5:
                log(f"    ... and {len(info['positions']) - 5} more occurrences")
            log("")
    else:
        log("No patterns detected")
    
    log("=" * 80)
    
    if len(chords) > 0:
        log(f"First chord: {chords[0]['chord']} at {chords[0]['start']}s")
        log(f"Last chord: {chords[-1]['chord']} at {chords[-1]['start']}s")
    
    return {
        'chords': chords,
        'key': key,
        'mode': mode,
        'keyConfidence': round(confidence, 2),
        'tempo': round(tempo_value, 1),
        'timeSignature': time_signature,
        'duration': round(duration, 2),
        'totalChords': len(chords),
        'songStructure': song_structure,
        'patternAnalysis': format_pattern_analysis(pattern_info, key),  # Pass detected key
        'model': 'librosa-enhanced-84-templates'  # 84 chord templates (major, minor, 7th, maj7, m7, sus4, dim)
    }

def format_pattern_analysis(pattern_info, key='C'):
    """
    Format pattern analysis for storage in DynamoDB
    Converts chord names to Nashville numbers based on detected key
    Returns a list of pattern summaries
    """
    if not pattern_info:
        return []
    
    # Sort patterns by count (most repeated first)
    sorted_patterns = sorted(
        pattern_info.items(),
        key=lambda x: x[1]['count'],
        reverse=True
    )
    
    # Filter to only repeating patterns (2+ occurrences)
    repeating_patterns = [(p, info) for p, info in sorted_patterns if info['count'] >= 2]
    
    result = []
    for i, (pattern, info) in enumerate(repeating_patterns[:10], 1):  # Top 10 patterns
        # Convert chord names to Nashville numbers
        nashville_progression = []
        for chord_name in pattern:
            nashville = convert_chord_to_nashville(chord_name, key)
            nashville_progression.append(nashville)
        
        result.append({
            'patternNumber': i,
            'progression': list(pattern),  # Original chord names
            'nashvilleProgression': nashville_progression,  # Nashville numbers
            'length': info['length'],
            'occurrences': info['count'],
            'positions': info['positions'][:10]  # Limit to first 10 positions
        })
    
    return result

def detect_bass_notes_from_stem(audio_path, chords, demucs_model=None):
    """
    Detect bass notes from Demucs bass stem
    
    Strategy:
    1. Use Demucs to separate bass stem
    2. For each chord timing, analyze bass frequencies
    3. Detect the fundamental frequency (lowest note)
    4. Map to note name
    5. Return bass note for each chord
    
    Args:
        audio_path: Path to audio file
        chords: List of detected chords with timing
        demucs_model: Optional Demucs model for stem separation
    
    Returns:
        List of bass notes corresponding to each chord
        
    Note: This is a placeholder for future enhancement.
    Currently returns None for all chords (no bass detection).
    When implemented, will use Demucs bass stem + pitch detection.
    """
    # TODO: Implement bass note detection
    # For now, return None for all chords (use chord root as bass)
    log("  Bass note detection not yet implemented, using chord roots")
    return [None] * len(chords)

def convert_chord_to_nashville(chord_name, key='C', bass_note=None):
    """
    Convert a chord name to Nashville Number System notation
    Returns simple numbers (1-7) with modifiers for accidentals and quality
    
    ENHANCED: Supports bass notes for slash chords
    
    Examples:
    - C in key of C = "1"
    - Dm in key of C = "2m"
    - F in key of C = "4"
    - G in key of C = "5"
    - Am in key of C = "6m"
    - C/G in key of C = "1/5" (C chord with G bass)
    - F/C in key of C = "4/1" (F chord with C bass)
    
    Args:
        chord_name: The chord symbol (e.g., "C", "Dm", "F")
        key: The key of the song (e.g., "C", "F major")
        bass_note: Optional bass note if different from chord root (e.g., "G" for C/G)
    """
    if not chord_name or chord_name == 'N':
        return '1'
    
    chord_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    # Check if chord already has slash notation (e.g., "C/G")
    if '/' in chord_name:
        parts = chord_name.split('/')
        chord_name = parts[0]
        bass_note = parts[1] if len(parts) > 1 else None
    
    # Extract root note
    root = chord_name[0]
    if len(chord_name) > 1 and chord_name[1] in ['#', 'b']:
        root = chord_name[:2]
        # Convert flats to sharps
        if chord_name[1] == 'b':
            flat_to_sharp = {'Db': 'C#', 'Eb': 'D#', 'Gb': 'F#', 'Ab': 'G#', 'Bb': 'A#'}
            root = flat_to_sharp.get(root, root)
    
    # Extract key root
    key_root = key.split(' ')[0] if ' ' in key else key
    if len(key_root) > 1 and key_root[1] == 'b':
        flat_to_sharp = {'Db': 'C#', 'Eb': 'D#', 'Gb': 'F#', 'Ab': 'G#', 'Bb': 'A#'}
        key_root = flat_to_sharp.get(key_root, key_root)
    
    try:
        key_idx = chord_names.index(key_root)
        root_idx = chord_names.index(root)
    except ValueError:
        return '1'
    
    # Calculate interval (scale degree)
    interval = (root_idx - key_idx + 12) % 12
    
    # Determine if chord is minor
    is_minor = 'm' in chord_name.lower() and 'maj' not in chord_name.lower()
    
    # Map interval to scale degree (1-7)
    interval_to_degree = {
        0: '1',      # Tonic
        1: 'b2',     # Flat 2
        2: '2',      # 2
        3: 'b3',     # Flat 3
        4: '3',      # 3
        5: '4',      # 4
        6: 'b5',     # Flat 5 (diminished 5th)
        7: '5',      # 5
        8: 'b6',     # Flat 6
        9: '6',      # 6
        10: 'b7',    # Flat 7
        11: '7'      # 7
    }
    
    degree = interval_to_degree.get(interval, '1')
    
    # Add quality modifier
    if is_minor:
        degree = degree + 'm'
    
    # Handle bass note (slash chord)
    if bass_note and bass_note != root:
        # Normalize bass note
        bass_root = bass_note[0]
        if len(bass_note) > 1 and bass_note[1] in ['#', 'b']:
            bass_root = bass_note[:2]
            if bass_note[1] == 'b':
                flat_to_sharp = {'Db': 'C#', 'Eb': 'D#', 'Gb': 'F#', 'Ab': 'G#', 'Bb': 'A#'}
                bass_root = flat_to_sharp.get(bass_root, bass_root)
        
        try:
            bass_idx = chord_names.index(bass_root)
            bass_interval = (bass_idx - key_idx + 12) % 12
            bass_degree = interval_to_degree.get(bass_interval, '1')
            
            # Return slash notation: chord/bass
            return f"{degree}/{bass_degree}"
        except ValueError:
            pass
    
    return degree

def detect_time_signature(y, sr, beats):
    """
    Detect time signature by analyzing beat patterns
    Returns: time signature string (e.g., "4/4", "3/4", "6/8")
    """
    if len(beats) < 8:
        return "4/4"  # Default if not enough beats
    
    # Calculate inter-beat intervals
    beat_times = librosa.frames_to_time(beats, sr=sr)
    intervals = np.diff(beat_times)
    
    # Most common time signatures
    # For now, default to 4/4 (most common in popular music)
    # Could be enhanced with more sophisticated analysis
    return "4/4"

def detect_structure_msaf(audio_path):
    """
    Use MSAF for structural segmentation with multiple algorithm fallbacks
    Detects segment boundaries and identifies repeated sections
    
    Tries multiple algorithms in order of accuracy:
    1. sf (Spectral Clustering) - Best for pop/rock
    2. foote (Foote Novelty) - Fast and reliable
    3. cnmf (CNN) - Deep learning based
    
    Returns: list of segments with boundaries and labels (A, B, A, C, etc.)
    """
    if not MSAF_AVAILABLE:
        log("MSAF not available, skipping audio-based segmentation", "WARNING")
        return []
    
    log("🎵 Detecting structure with MSAF...")
    start_time = time.time()
    
    # Try multiple algorithms in order of preference
    algorithms = [
        ('sf', 'scluster', 'mfcc'),      # Spectral clustering - best for pop/rock
        ('foote', 'fmc2d', 'mfcc'),      # Foote novelty - fast and reliable
        ('olda', 'scluster', 'cqt'),     # Online learning - good for varied music
        ('cnmf', 'cnmf', 'mfcc'),        # CNN - deep learning (slowest)
    ]
    
    for boundaries_id, labels_id, feature in algorithms:
        try:
            log(f"  Trying algorithm: {boundaries_id} with {feature} features...")
            
            boundaries, labels = msaf.process(
                audio_path,
                boundaries_id=boundaries_id,
                labels_id=labels_id,
                feature=feature
            )
            
            # Check if we got reasonable results
            num_segments = len(boundaries) - 1
            
            if num_segments < 2:
                log(f"  ⚠️ Only {num_segments} segment(s) detected, trying next algorithm...", "WARNING")
                continue
            
            if num_segments > 50:
                log(f"  ⚠️ Too many segments ({num_segments}), trying next algorithm...", "WARNING")
                continue
            
            # Success!
            log(f"  ✓ {boundaries_id} detected {num_segments} segments")
            log(f"  Boundaries: {[round(b, 1) for b in boundaries[:10]]}{'...' if len(boundaries) > 10 else ''}")
            log(f"  Labels: {labels[:10]}{'...' if len(labels) > 10 else ''}")
            
            # Convert to our format
            segments = []
            for i in range(len(boundaries) - 1):
                segment = {
                    'start': float(boundaries[i]),
                    'end': float(boundaries[i + 1]),
                    'label': str(labels[i]),
                    'duration': float(boundaries[i + 1] - boundaries[i]),
                    'algorithm': boundaries_id  # Track which algorithm was used
                }
                segments.append(segment)
                log(f"  Segment {i+1}: {segment['label']} ({segment['start']:.1f}s - {segment['end']:.1f}s, {segment['duration']:.1f}s)")
            
            detection_time = time.time() - start_time
            log(f"✓ MSAF segmentation complete using {boundaries_id} ({detection_time:.2f}s)")
            
            # Count repetitions of each label
            label_counts = {}
            for seg in segments:
                label_counts[seg['label']] = label_counts.get(seg['label'], 0) + 1
            
            log(f"  Label distribution: {label_counts}")
            
            return segments
            
        except Exception as e:
            log(f"  Algorithm {boundaries_id} failed: {str(e)}", "WARNING")
            continue
    
    # All algorithms failed
    log("All MSAF algorithms failed, falling back to pattern-based structure detection", "WARNING")
    return []

def detect_song_structure(chords, pattern_info, tempo):
    """
    ENHANCED: Intelligent song structure detection
    
    Strategy:
    1. Find ALL repeating chord progression patterns (3-8 chords)
    2. Only keep patterns that repeat at least 2 times
    3. Group consecutive repetitions into sections
    4. Label based on repetition count and position
    5. Filter out non-repeating sections (spoken words, intros, outros)
    
    Returns: list of sections with labels, measure ranges, and chord patterns
    """
    if not pattern_info or len(chords) == 0:
        return []
    
    log("🎵 ENHANCED SONG STRUCTURE DETECTION")
    log(f"  Total chords to analyze: {len(chords)}")
    log(f"  Patterns found: {len(pattern_info)}")
    
    # Calculate measures per chord (approximate)
    seconds_per_beat = 60 / tempo
    seconds_per_measure = seconds_per_beat * 4  # Assuming 4/4 time
    
    # STEP 1: Filter patterns - only keep those that repeat at least 2 times
    repeating_patterns = {
        pattern: info for pattern, info in pattern_info.items()
        if info['count'] >= 2  # Must repeat at least once (appear 2+ times)
    }
    
    log(f"  Repeating patterns (2+ occurrences): {len(repeating_patterns)}")
    
    if not repeating_patterns:
        log("  ⚠️ No repeating patterns found - song may be through-composed")
        return []
    
    # STEP 2: Sort by repetition count and length (most important patterns first)
    sorted_patterns = sorted(
        repeating_patterns.items(),
        key=lambda x: (x[1]['count'], x[1]['length']),
        reverse=True
    )
    
    # Log top patterns
    for i, (pattern, info) in enumerate(sorted_patterns[:5]):
        log(f"  Pattern {i+1}: {list(pattern)[:4]}... (length={info['length']}, count={info['count']})")
    
    sections = []
    used_positions = set()
    
    # STEP 3: Process each repeating pattern to create sections
    for pattern, info in sorted_patterns:
        positions = info['positions']
        pattern_length = info['length']
        
        # Group consecutive occurrences of this pattern
        groups = []
        current_group = []
        
        for pos in positions:
            # Skip if this position overlaps with already used positions
            if any(pos <= used_pos < pos + pattern_length for used_pos in used_positions):
                continue
            
            # Check if this position is consecutive with the current group
            if not current_group or pos == current_group[-1] + pattern_length:
                current_group.append(pos)
            else:
                # Start a new group
                if current_group:
                    groups.append(current_group)
                current_group = [pos]
        
        # Add the last group
        if current_group:
            groups.append(current_group)
        
        # STEP 4: Create sections from groups (only if they repeat)
        for group in groups:
            if len(group) >= 1:  # At least 1 occurrence
                start_chord_idx = group[0]
                end_chord_idx = min(group[-1] + pattern_length - 1, len(chords) - 1)
                
                # Mark positions as used
                for pos in range(group[0], min(group[-1] + pattern_length, len(chords))):
                    used_positions.add(pos)
                
                # Calculate time ranges
                start_time = chords[start_chord_idx].get('start', 0) or chords[start_chord_idx].get('time', 0)
                end_chord = chords[end_chord_idx]
                end_time = end_chord.get('end', start_time + 10) or end_chord.get('time', start_time) + 10
                
                measure_start = int(start_time / seconds_per_measure) + 1
                measure_end = int(end_time / seconds_per_measure) + 1
                
                sections.append({
                    'label': 'Section',  # Will be relabeled later
                    'measureStart': measure_start,
                    'measureEnd': measure_end,
                    'patternCount': len(group),
                    'totalOccurrences': info['count'],  # Total times this pattern appears in song
                    'pattern': list(pattern),
                    'startTime': round(start_time, 2),
                    'endTime': round(end_time, 2),
                    'chordIndices': (start_chord_idx, end_chord_idx)
                })
    
    # Sort sections by start time
    sections.sort(key=lambda x: x['startTime'])
    
    log(f"  Sections created: {len(sections)}")
    
    # STEP 5: Intelligent labeling based on repetition patterns
    if sections:
        # Find the most repeated pattern (likely chorus)
        max_occurrences = max(s['totalOccurrences'] for s in sections)
        
        verse_count = 0
        chorus_assigned = False
        bridge_assigned = False
        
        for i, section in enumerate(sections):
            # CHORUS: Most repeated pattern in the song
            if section['totalOccurrences'] == max_occurrences and not chorus_assigned:
                section['label'] = 'Chorus'
                chorus_assigned = True
                log(f"  ✓ Chorus identified: measures {section['measureStart']}-{section['measureEnd']} ({section['totalOccurrences']} occurrences)")
            
            # VERSE: Repeated sections that aren't chorus
            elif section['totalOccurrences'] >= 2 and section['label'] == 'Section':
                verse_count += 1
                section['label'] = 'Verse'
                log(f"  ✓ Verse identified: measures {section['measureStart']}-{section['measureEnd']} ({section['totalOccurrences']} occurrences)")
            
            # BRIDGE: Later section with different pattern (appears in second half of song)
            elif not bridge_assigned and i > len(sections) / 2 and section['totalOccurrences'] >= 2:
                section['label'] = 'Bridge'
                bridge_assigned = True
                log(f"  ✓ Bridge identified: measures {section['measureStart']}-{section['measureEnd']}")
            
            # INTRO/OUTRO: Single occurrence sections at beginning or end
            elif section['totalOccurrences'] < 2:
                if i == 0:
                    section['label'] = 'Intro'
                elif i == len(sections) - 1:
                    section['label'] = 'Outro'
                else:
                    # Skip non-repeating middle sections (likely spoken words or transitions)
                    section['label'] = 'Transition'
    
    # STEP 6: Filter out transitions and non-essential sections
    # Only keep: Verse, Chorus, Bridge, Intro (if first), Outro (if last)
    essential_sections = [
        s for s in sections 
        if s['label'] in ['Verse', 'Chorus', 'Bridge'] or 
        (s['label'] == 'Intro' and sections.index(s) == 0) or
        (s['label'] == 'Outro' and sections.index(s) == len(sections) - 1)
    ]
    
    log(f"  Essential sections (filtered): {len(essential_sections)}")
    log(f"  Structure: {' → '.join([s['label'] for s in essential_sections])}")
    
    return essential_sections

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

def get_job_from_dynamodb(job_id):
    """Get job data from DynamoDB"""
    log(f"Fetching job data for job_id: {job_id}")
    table = dynamodb.Table(JOBS_TABLE)
    
    try:
        response = table.get_item(Key={'jobId': job_id})
        
        if 'Item' not in response:
            log(f"Job not found: {job_id}", "WARNING")
            return None
        
        job_data = response['Item']
        log(f"✓ Job data retrieved successfully")
        
        # Log what data is available
        has_lyrics = 'lyricsData' in job_data and job_data['lyricsData']
        has_chords = 'chordsData' in job_data and job_data['chordsData']
        log(f"  Has lyrics data: {has_lyrics}")
        log(f"  Has chords data: {has_chords}")
        
        return job_data
    except Exception as e:
        log(f"ERROR fetching job data: {str(e)}", "ERROR")
        raise

def convert_floats_to_decimal(obj):
    """Recursively convert all float values to Decimal for DynamoDB"""
    if isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_floats_to_decimal(value) for key, value in obj.items()}
    elif isinstance(obj, float):
        # Convert float to Decimal, handling special cases
        if np.isnan(obj) or np.isinf(obj):
            return Decimal('0')
        return Decimal(str(obj))
    elif isinstance(obj, (np.floating, np.float32, np.float64)):
        # Handle numpy float types
        val = float(obj)
        if np.isnan(val) or np.isinf(val):
            return Decimal('0')
        return Decimal(str(val))
    elif isinstance(obj, (np.integer, np.int32, np.int64)):
        # Handle numpy int types
        return int(obj)
    else:
        return obj

def update_job_with_lyrics(job_id, lyrics_data):
    """Update job with lyrics extraction results"""
    log(f"Updating job with lyrics data ({len(lyrics_data.get('words', []))} words)")
    
    table = dynamodb.Table(JOBS_TABLE)
    
    try:
        # Convert all floats to Decimal for DynamoDB compatibility
        log("Converting lyrics data to DynamoDB format...")
        lyrics_data_decimal = convert_floats_to_decimal(lyrics_data)
        log(f"✓ Converted lyrics data to DynamoDB format")
        
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET lyricsData = :lyrics, updatedAt = :updated',
            ExpressionAttributeValues={
                ':lyrics': lyrics_data_decimal,
                ':updated': time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
            }
        )
        log(f"✓ Job updated with lyrics data")
    except Exception as e:
        log(f"ERROR updating job with lyrics: {str(e)}", "ERROR")
        raise


def update_job_with_chords(job_id, chords_data):
    """Update job with chord detection results"""
    log(f"Updating job with {len(chords_data['chords'])} chords")
    
    # Check if leadSheet data is present
    has_lead_sheet = 'leadSheet' in chords_data
    if has_lead_sheet:
        lead_sheet = chords_data['leadSheet']
        num_sections = len(lead_sheet.get('sections', []))
        total_lines = sum(len(section.get('lines', [])) for section in lead_sheet.get('sections', []))
        log(f"✓ Lead sheet data found: {num_sections} sections, {total_lines} lines")
    else:
        log("ℹ️ No lead sheet data (lyrics not available)")
    
    table = dynamodb.Table(JOBS_TABLE)
    
    try:
        # Convert all floats to Decimal for DynamoDB compatibility
        # This handles nested structures including leadSheet automatically
        log("Converting float values to Decimal for DynamoDB...")
        chords_data_decimal = convert_floats_to_decimal(chords_data)
        log(f"✓ Converted {len(chords_data['chords'])} chords to DynamoDB format")
        
        if has_lead_sheet:
            log("✓ Lead sheet data converted to DynamoDB format (nested structures handled)")
        
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET chordsData = :chords, #status = :status, progress = :progress, updatedAt = :updated',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':chords': chords_data_decimal,
                ':status': 'CHORDS_DETECTED',
                ':progress': 80,
                ':updated': time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
            }
        )
        log(f"✓ Job updated with chord data (status: CHORDS_DETECTED, progress: 80%)")
        
        if has_lead_sheet:
            log(f"✓ Lead sheet data saved to DynamoDB ({num_sections} sections, {total_lines} lines)")
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

def run_downbeat_detection():
    """Run downbeat detection task"""
    log("=" * 80)
    log("STARTING DOWNBEAT DETECTION ECS TASK")
    log("=" * 80)
    
    # Get parameters from environment
    job_id = os.environ.get('JOB_ID')
    audio_bucket = os.environ.get('AUDIO_BUCKET')
    audio_key = os.environ.get('AUDIO_KEY')
    jobs_table_name = os.environ.get('JOBS_TABLE', JOBS_TABLE)
    
    log(f"Environment Variables:")
    log(f"  JOB_ID: {job_id}")
    log(f"  AUDIO_BUCKET: {audio_bucket}")
    log(f"  AUDIO_KEY: {audio_key}")
    log(f"  JOBS_TABLE: {jobs_table_name}")
    
    if not all([job_id, audio_bucket, audio_key]):
        log("ERROR: Missing required environment variables", "ERROR")
        sys.exit(1)
    
    jobs_table = dynamodb.Table(jobs_table_name)
    
    try:
        # Download audio file
        audio_path = f'/tmp/{job_id}-audio.m4a'
        log(f"Downloading audio from s3://{audio_bucket}/{audio_key}...")
        s3.download_file(audio_bucket, audio_key, audio_path)
        log("✓ Audio downloaded successfully")
        
        # Import detection modules
        sys.path.insert(0, '/app/simple-pipeline/chord-detection')
        from chord_detection_v2 import detect_tempo_and_beats
        from downbeat_detection import detect_downbeats
        
        # Detect tempo and beats first
        log("Detecting tempo and beats...")
        tempo, beats, time_signature = detect_tempo_and_beats(audio_path)
        log(f"✓ Detected {len(beats)} beats at {tempo:.1f} BPM, time signature: {time_signature}")
        
        # Detect downbeat
        log("Detecting downbeat...")
        downbeats, first_downbeat, info = detect_downbeats(audio_path, beats, tempo, time_signature)
        
        result = {
            'tempo': tempo,
            'time_signature': time_signature,
            'first_downbeat': first_downbeat,
            'confidence': info.get('confidence', 0.8),
            'beat_times': beats.tolist(),
            'downbeats': downbeats.tolist(),
            'method_info': info
        }
        
        log(f"✓ Downbeat detection complete:")
        log(f"  Tempo: {result['tempo']} BPM")
        log(f"  Time Signature: {result['time_signature']}")
        log(f"  Detected Downbeat: {result['first_downbeat']}s")
        log(f"  Confidence: {result['confidence']:.2f}")
        log(f"  Total Beats: {len(result['beat_times'])}")
        log(f"  Total Measures: {len(result['downbeats'])}")
        
        # Update DynamoDB with results
        log("Updating DynamoDB...")
        jobs_table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='''
                SET downbeatData = :data,
                    downbeatStatus = :status,
                    updatedAt = :now
            ''',
            ExpressionAttributeValues={
                ':data': {
                    'tempo': Decimal(str(result['tempo'])),
                    'timeSignature': result['time_signature'],
                    'detectedDownbeat': Decimal(str(result['first_downbeat'])),
                    'confidence': Decimal(str(result['confidence'])),
                    'beatTimes': [Decimal(str(t)) for t in result['beat_times']],
                    'downbeats': [Decimal(str(t)) for t in result['downbeats']],
                    'totalBeats': len(result['beat_times']),
                    'totalMeasures': len(result['downbeats']),
                    'methodInfo': result.get('method_info', {}),
                },
                ':status': 'COMPLETED',
                ':now': datetime.utcnow().isoformat(),
            }
        )
        
        log("✓ Downbeat detection completed successfully!")
        
        # Clean up
        if os.path.exists(audio_path):
            os.remove(audio_path)
        
        sys.exit(0)
        
    except Exception as e:
        log(f"ERROR: Downbeat detection failed: {str(e)}", "ERROR")
        import traceback
        log(traceback.format_exc(), "ERROR")
        
        # Update DynamoDB with error
        try:
            jobs_table.update_item(
                Key={'jobId': job_id},
                UpdateExpression='''
                    SET downbeatStatus = :status,
                        errorMessage = :error,
                        updatedAt = :now
                ''',
                ExpressionAttributeValues={
                    ':status': 'FAILED',
                    ':error': str(e),
                    ':now': datetime.utcnow().isoformat(),
                }
            )
        except Exception as update_error:
            log(f"ERROR: Failed to update DynamoDB: {str(update_error)}", "ERROR")
        
        sys.exit(1)

# ============================================================================
# LYRICS-CHORD ALIGNMENT FUNCTIONS
# ============================================================================

def find_word_at_timestamp(words, timestamp, tolerance=0.1, max_tolerance=0.5):
    """
    Find the word being sung at a given timestamp with adaptive tolerance

    Args:
        words: List of word dicts with 'start' and 'end' times
        timestamp: Time in seconds to find word for
        tolerance: Initial time tolerance in seconds (default 0.1s)
        max_tolerance: Maximum tolerance to try (default 0.5s)

    Returns:
        Word index (int) or None if no word found
    """
    # Try with initial tolerance
    for i, word in enumerate(words):
        if word['start'] - tolerance <= timestamp <= word['end'] + tolerance:
            return i

    # Check if timestamp is just before a word (anticipation)
    for i, word in enumerate(words):
        if word['start'] - 0.2 <= timestamp < word['start']:
            return i

    # If no match found, try with progressively larger tolerances up to max_tolerance
    current_tolerance = tolerance
    while current_tolerance < max_tolerance:
        # Double the tolerance, but don't exceed max_tolerance
        current_tolerance = min(current_tolerance * 2, max_tolerance)
        log(f"  No word found at {timestamp:.2f}s with previous tolerance, trying {current_tolerance:.2f}s", "WARNING")

        # Try again with increased tolerance
        for i, word in enumerate(words):
            if word['start'] - current_tolerance <= timestamp <= word['end'] + current_tolerance:
                log(f"  Found word at index {i} ('{word.get('word', 'N/A')}') with adaptive tolerance {current_tolerance:.2f}s", "INFO")
                return i

    # Log misalignment if still no match after trying all tolerances
    log(f"  Timestamp mismatch: No word found at {timestamp:.2f}s even with max tolerance {max_tolerance:.2f}s", "WARNING")

    return None  # Instrumental section



def calculate_measure_number(timestamp, tempo, time_signature, first_downbeat=0.0):
    """
    Convert timestamp to measure number
    
    Args:
        timestamp: Time in seconds
        tempo: BPM
        time_signature: String like '4/4'
        first_downbeat: Time of first downbeat in seconds
    
    Returns:
        Measure number (1-indexed)
    """
    beats_per_measure = int(time_signature.split('/')[0])
    beat_duration = 60.0 / tempo
    measure_duration = beat_duration * beats_per_measure
    
    # Calculate measures from first downbeat
    time_from_downbeat = timestamp - first_downbeat
    if time_from_downbeat < 0:
        return 1
    
    measure_number = int(time_from_downbeat / measure_duration) + 1
    return measure_number

def get_words_in_segment(words, start_time, end_time):
    """
    Filter words by time range
    
    Args:
        words: List of word dicts
        start_time: Segment start time
        end_time: Segment end time
    
    Returns:
        List of words within time range
    """
    return [w for w in words if start_time <= w['start'] <= end_time]

def get_chords_in_segment(chords, start_time, end_time):
    """
    Filter chords by time range
    
    Args:
        chords: List of chord dicts
        start_time: Segment start time
        end_time: Segment end time
    
    Returns:
        List of chords within time range
    """
    return [c for c in chords if start_time <= c['start'] <= end_time]

def get_lines_in_range(lines, start_time, end_time):
    """
    Filter lines by time range
    
    Args:
        lines: List of line dicts
        start_time: Range start time
        end_time: Range end time
    
    Returns:
        List of lines within time range
    """
    result = []
    for line in lines:
        # Check if line overlaps with range
        if line.get('start') is not None and line.get('end') is not None:
            if line['start'] <= end_time and line['end'] >= start_time:
                result.append(line)
    return result

def get_chords_in_range(chords, start_time, end_time):
    """
    Filter chords by time range (alias for get_chords_in_segment)
    """
    return get_chords_in_segment(chords, start_time, end_time)

def ends_with_punctuation(text):
    """
    Check if text ends with punctuation
    
    Args:
        text: String to check
    
    Returns:
        Boolean
    """
    if not text:
        return False
    return text.strip()[-1] in '.!?,;:'

def get_song_duration(chords_data):
    """
    Get total song duration from chords data
    
    Args:
        chords_data: Dict with duration or chords list
    
    Returns:
        Duration in seconds
    """
    if 'duration' in chords_data:
        return chords_data['duration']
    elif 'chords' in chords_data and len(chords_data['chords']) > 0:
        return chords_data['chords'][-1]['end']
    return 0.0

# ============================================================================
# CHORD-TO-WORD ALIGNMENT
# ============================================================================

def align_chords_to_words(chords, words):
    """
    Align each chord change to the word being sung at that moment
    
    Strategy:
    1. For each chord, find the word that overlaps with chord start time
    2. If chord starts within 0.2s before word, snap to word start
    3. If chord is mid-word, associate with that word
    4. If no word found (instrumental), mark as instrumental
    
    Args:
        chords: List of chord dicts with 'start', 'chord', 'measure', 'beat'
        words: List of word dicts with 'word', 'start', 'end'
    
    Returns:
        List of aligned chord dicts with wordIndex and positionType
    """
    aligned_chords = []
    
    for chord in chords:
        chord_time = chord['start']
        
        # Find word at this timestamp
        word_index = find_word_at_timestamp(words, chord_time)
        
        if word_index is not None:
            word = words[word_index]
            
            # Check if chord is close to word start (within 0.2s before)
            time_before_word = word['start'] - chord_time
            if 0 <= time_before_word <= 0.2:
                # Snap to word start for cleaner alignment
                position_type = 'word_start'
            elif word['start'] <= chord_time <= word['end']:
                # Chord change during word
                position_type = 'mid_word'
            else:
                position_type = 'between_words'
            
            aligned_chords.append({
                **chord,
                'wordIndex': word_index,
                'word': word['word'],
                'positionType': position_type
            })
        else:
            # No word found - instrumental section
            aligned_chords.append({
                **chord,
                'wordIndex': None,
                'word': None,
                'positionType': 'instrumental'
            })
    
    return aligned_chords

def handle_multiple_chords_per_word(word, chords_for_word):
    """
    When multiple chords occur during a single word,
    space them evenly across the word length
    
    Args:
        word: Word dict with 'word', 'charPosition'
        chords_for_word: List of chord dicts for this word
    
    Returns:
        List of chords with updated charPosition
    """
    word_length = len(word['word'])
    num_chords = len(chords_for_word)
    
    if num_chords <= 1:
        return chords_for_word
    
    for i, chord in enumerate(chords_for_word):
        # Distribute chords across word
        offset = (word_length / num_chords) * i
        chord['charPosition'] = word['charPosition'] + int(offset)
    
    return chords_for_word

def ensure_chord_spacing(chords, min_spacing=3):
    """
    Ensure chords don't overlap by enforcing minimum spacing
    Abbreviate chord names if needed
    
    Args:
        chords: List of chord dicts with 'charPosition', 'chord'
        min_spacing: Minimum characters between chords
    
    Returns:
        List of chords with adjusted spacing and abbreviated names
    """
    if len(chords) <= 1:
        return chords
    
    for i in range(1, len(chords)):
        prev_chord = chords[i-1]
        curr_chord = chords[i]
        
        # Calculate space between chords
        space = curr_chord['charPosition'] - (prev_chord['charPosition'] + len(prev_chord['chord']))
        
        if space < min_spacing:
            # Abbreviate chord names if needed
            if len(prev_chord['chord']) > 4:
                prev_chord['chord'] = abbreviate_chord(prev_chord['chord'])
            if len(curr_chord['chord']) > 4:
                curr_chord['chord'] = abbreviate_chord(curr_chord['chord'])
    
    return chords

def abbreviate_chord(chord_name):
    """
    Shorten chord names for better spacing
    Examples: Cmaj7 -> CM7, Dm7b5 -> Dm7♭5
    
    Args:
        chord_name: Full chord name string
    
    Returns:
        Abbreviated chord name
    """
    chord_name = chord_name.replace('maj', 'M')
    chord_name = chord_name.replace('min', 'm')
    chord_name = chord_name.replace('dim', '°')
    chord_name = chord_name.replace('aug', '+')
    chord_name = chord_name.replace('b5', '♭5')
    chord_name = chord_name.replace('#5', '♯5')
    chord_name = chord_name.replace('b9', '♭9')
    chord_name = chord_name.replace('#9', '♯9')
    return chord_name

# ============================================================================
# PHRASE/LINE GROUPING
# ============================================================================

def group_into_lines(aligned_chords, words, segments, tempo, time_signature, first_downbeat=0.0):
    """
    Group words and chords into readable lines
    
    Strategy:
    1. Use Whisper segments as initial phrase boundaries
    2. Ensure each line is 2-4 measures (adjustable)
    3. Break at natural boundaries (punctuation, silence)
    4. Keep lines roughly equal length for readability
    
    Args:
        aligned_chords: List of chords with word associations
        words: List of all words with timestamps
        segments: Whisper's phrase-level segments
        tempo: BPM
        time_signature: String like '4/4'
        first_downbeat: Time of first downbeat in seconds
    
    Returns:
        List of line objects with lyrics and chords
    """
    lines = []
    beats_per_measure = int(time_signature.split('/')[0])
    beat_duration = 60.0 / tempo
    measure_duration = beat_duration * beats_per_measure
    
    # Target: 2-4 measures per line
    target_line_duration = measure_duration * 3  # 3 measures average
    min_line_duration = measure_duration * 2
    max_line_duration = measure_duration * 4
    
    current_line = {
        'words': [],
        'chords': [],
        'start': None,
        'end': None
    }
    
    for segment in segments:
        segment_words = get_words_in_segment(words, segment['start'], segment['end'])
        segment_chords = get_chords_in_segment(aligned_chords, segment['start'], segment['end'])
        
        # Check if adding this segment would exceed max line duration
        if current_line['start'] is not None:
            potential_duration = segment['end'] - current_line['start']
            
            if potential_duration > max_line_duration:
                # Finish current line and start new one
                lines.append(finalize_line(current_line, tempo, time_signature, first_downbeat))
                current_line = {
                    'words': segment_words,
                    'chords': segment_chords,
                    'start': segment['start'],
                    'end': segment['end']
                }
            else:
                # Add to current line
                current_line['words'].extend(segment_words)
                current_line['chords'].extend(segment_chords)
                current_line['end'] = segment['end']
        else:
            # First segment
            current_line = {
                'words': segment_words,
                'chords': segment_chords,
                'start': segment['start'],
                'end': segment['end']
            }
        
        # Check if current line meets minimum duration
        if current_line['start'] is not None:
            duration = current_line['end'] - current_line['start']
            
            # If line is long enough and segment ends with punctuation, break
            if duration >= min_line_duration and ends_with_punctuation(segment['text']):
                lines.append(finalize_line(current_line, tempo, time_signature, first_downbeat))
                current_line = {'words': [], 'chords': [], 'start': None, 'end': None}
    
    # Add final line
    if current_line['words']:
        lines.append(finalize_line(current_line, tempo, time_signature, first_downbeat))
    
    return lines

def finalize_line(line_data, tempo, time_signature, first_downbeat=0.0):
    """
    Convert line data to final format with measure numbers
    
    Args:
        line_data: Dict with 'words', 'chords', 'start', 'end'
        tempo: BPM
        time_signature: String like '4/4'
        first_downbeat: Time of first downbeat in seconds
    
    Returns:
        Finalized line dict with measure numbers, lyrics string, and chord positions
    """
    # Calculate measure numbers
    measure_start = calculate_measure_number(line_data['start'], tempo, time_signature, first_downbeat)
    measure_end = calculate_measure_number(line_data['end'], tempo, time_signature, first_downbeat)
    
    # Build lyrics string
    lyrics_text = ' '.join(word['word'] for word in line_data['words'])
    
    # Calculate character positions for each word
    char_pos = 0
    for word in line_data['words']:
        word['charPosition'] = char_pos
        char_pos += len(word['word']) + 1  # +1 for space
    
    # Map chords to character positions
    for chord in line_data['chords']:
        if chord.get('wordIndex') is not None:
            # Find the word in our line's word list
            word_found = False
            for i, word in enumerate(line_data['words']):
                # Match by timestamp since wordIndex is global
                if abs(word['start'] - chord.get('timestamp', chord['start'])) < 0.1:
                    chord['charPosition'] = word['charPosition']
                    word_found = True
                    break
            
            if not word_found:
                # Fallback: use first word position
                chord['charPosition'] = 0
        else:
            # Instrumental chord
            chord['charPosition'] = 0
    
    return {
        'measureStart': measure_start,
        'measureEnd': measure_end,
        'lyrics': lyrics_text,
        'words': line_data['words'],
        'chords': line_data['chords'],
        'isInstrumental': len(line_data['words']) == 0,
        'start': line_data['start'],
        'end': line_data['end']
    }


def align_lyrics_with_chords(chords_data, lyrics_data):
    """
    Main function to align lyrics with chords and create lead sheet structure
    
    This orchestrates all alignment steps:
    1. Align chords to words based on timestamps
    2. Group words/chords into readable lines (2-4 measures)
    3. Detect and label song sections (Verse, Chorus, etc.)
    4. Return structured AlignedLeadSheet data
    
    Args:
        chords_data: Dict containing:
            - chords: List of chord objects with timestamps
            - key: Detected key (e.g., 'C major')
            - tempo: BPM
            - timeSignature: String like '4/4'
            - songStructure: List of detected sections
            - duration: Song duration in seconds
            - firstDownbeat: Time of first downbeat (optional)
        
        lyrics_data: Dict containing:
            - text: Full lyrics text
            - words: List of word objects with timestamps
            - segments: Phrase-level segments from Whisper
            - language: Detected language
            - confidence: Transcription confidence
    
    Returns:
        AlignedLeadSheet dict with structure:
        {
            'metadata': {key, tempo, timeSignature, duration},
            'sections': [
                {
                    'label': 'Verse 1',
                    'measureStart': 1,
                    'measureEnd': 8,
                    'lines': [...]
                }
            ]
        }
        
        Returns None if alignment cannot be performed (missing data)
    """
    log("=" * 60)
    log("Starting lyrics-chord alignment...")
    log("=" * 60)
    
    # Validate inputs
    if not lyrics_data or not lyrics_data.get('words'):
        log("⚠️  No lyrics data available - skipping alignment", "WARNING")
        return None
    
    if not chords_data or not chords_data.get('chords'):
        log("❌ No chord data available - cannot perform alignment", "ERROR")
        return None
    
    if not chords_data.get('songStructure'):
        log("⚠️  No song structure data - will create default sections", "WARNING")
        # Create a default single section
        chords_data['songStructure'] = [{
            'label': 'Song',
            'start': 0.0,
            'end': chords_data.get('duration', 300.0),
            'measureStart': 1,
            'measureEnd': 100
        }]
    
    try:
        # Extract required data
        chords = chords_data['chords']
        words = lyrics_data['words']
        segments = lyrics_data.get('segments', [])
        tempo = chords_data.get('tempo', 120.0)
        time_signature = chords_data.get('timeSignature', '4/4')
        first_downbeat = chords_data.get('firstDownbeat', 0.0)
        
        log(f"📊 Input data:")
        log(f"   - Chords: {len(chords)}")
        log(f"   - Words: {len(words)}")
        log(f"   - Segments: {len(segments)}")
        log(f"   - Tempo: {tempo} BPM")
        log(f"   - Time Signature: {time_signature}")
        log(f"   - First Downbeat: {first_downbeat:.2f}s")
        
        # Step 1: Align chords to words
        log("\n🎯 Step 1: Aligning chords to words...")
        aligned_chords = align_chords_to_words(chords, words)
        
        # Count alignment types
        word_start_count = sum(1 for c in aligned_chords if c.get('positionType') == 'word_start')
        mid_word_count = sum(1 for c in aligned_chords if c.get('positionType') == 'mid_word')
        instrumental_count = sum(1 for c in aligned_chords if c.get('positionType') == 'instrumental')
        
        log(f"   ✓ Aligned {len(aligned_chords)} chords:")
        log(f"     - At word start: {word_start_count}")
        log(f"     - Mid-word: {mid_word_count}")
        log(f"     - Instrumental: {instrumental_count}")
        
        # Step 2: Group into lines
        log("\n📝 Step 2: Grouping into lines...")
        lines = group_into_lines(
            aligned_chords,
            words,
            segments,
            tempo,
            time_signature,
            first_downbeat
        )
        
        # Count line types
        lyric_lines = sum(1 for l in lines if not l.get('isInstrumental', False))
        instrumental_lines = sum(1 for l in lines if l.get('isInstrumental', False))
        
        log(f"   ✓ Created {len(lines)} lines:")
        log(f"     - With lyrics: {lyric_lines}")
        log(f"     - Instrumental: {instrumental_lines}")
        
        # Step 3: Detect and label sections
        log("\n🏷️  Step 3: Detecting and labeling sections...")
        
        # Import section detection function
        from section_detection import detect_and_label_sections
        
        sections = detect_and_label_sections(
            chords_data['songStructure'],
            lines,
            chords
        )
        
        log(f"   ✓ Identified {len(sections)} sections:")
        for section in sections:
            line_count = len(section.get('lines', []))
            log(f"     - {section['label']}: {line_count} lines (M{section['measureStart']}-{section['measureEnd']})")
        
        # Step 4: Create final lead sheet structure
        log("\n📄 Step 4: Creating lead sheet structure...")
        lead_sheet = {
            'metadata': {
                'key': chords_data.get('key', 'Unknown'),
                'tempo': tempo,
                'timeSignature': time_signature,
                'duration': chords_data.get('duration', 0.0),
                'language': lyrics_data.get('language', 'en'),
                'confidence': lyrics_data.get('confidence', 1.0)
            },
            'sections': sections
        }
        
        # Calculate statistics
        total_lines = sum(len(s.get('lines', [])) for s in sections)
        total_chords = sum(len(l.get('chords', [])) for l in lines)
        
        log(f"   ✓ Lead sheet created:")
        log(f"     - Sections: {len(sections)}")
        log(f"     - Total lines: {total_lines}")
        log(f"     - Total chords: {total_chords}")
        
        log("\n" + "=" * 60)
        log("✅ Lyrics-chord alignment complete!")
        log("=" * 60)
        
        return lead_sheet
        
    except Exception as e:
        log(f"❌ Error during lyrics-chord alignment: {str(e)}", "ERROR")
        log(f"   Exception type: {type(e).__name__}", "ERROR")
        import traceback
        log(f"   Traceback: {traceback.format_exc()}", "ERROR")
        return None


if __name__ == '__main__':
    main()

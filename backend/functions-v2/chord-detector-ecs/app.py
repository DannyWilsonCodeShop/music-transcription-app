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
    
    Strategy:
    1. Find patterns that repeat at least 2 times (ignore single occurrences)
    2. Analyze only these repeating patterns against all possible keys
    3. Score based on common progressions (I-vi-ii-V, I-IV-V, etc.)
    4. Use the context of repeated progressions to determine key
    
    Returns: (key, mode, confidence, pattern_info)
    """
    if len(chords) < 8:  # Need at least 8 chords to detect patterns
        return 'C', 'major', 0.0, {}
    
    log("🎹 ENHANCED KEY DETECTION FROM REPEATED PROGRESSIONS")
    
    chord_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    # Extract chord roots as a sequence
    chord_sequence = []
    for chord in chords:
        chord_name = chord['chord']
        root = chord_name[0]
        if len(chord_name) > 1 and chord_name[1] in ['#', 'b']:
            root = chord_name[:2]
        
        # Determine if major or minor
        is_minor = 'm' in chord_name.lower() and 'maj' not in chord_name.lower()
        chord_sequence.append({'root': root, 'minor': is_minor})
    
    log(f"  Total chords in sequence: {len(chord_sequence)}")
    
    # STEP 1: Find repeating patterns (3-8 chord sequences)
    # Only patterns that repeat at least 2 times
    pattern_scores = {}  # key -> score
    all_patterns = {}  # Store all patterns found for structure detection
    repeating_patterns_found = 0
    
    # IMPROVED: Look for patterns of at least 2 measures
    # In 4/4 time with half-beat analysis: 4 beats/measure * 2 positions/beat = 8 positions/measure
    # So 2 measures = 16 chord positions minimum
    # But after consolidation, we might have 4-8 unique chords per 2 measures
    # Start at 6 chords (1.5 measures) to catch meaningful progressions
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
                        # Heavily weight repetition count (repeated patterns are most important)
                        pattern_scores[potential_key] += progression_score * (count ** 1.5) * pattern_length
    
    log(f"  Repeating patterns found: {repeating_patterns_found}")
    
    if not pattern_scores:
        log("  ⚠️ No repeating patterns found - falling back to C major")
        return 'C', 'major', 0.0, {}
    
    # STEP 5: Find best key based on repeated pattern analysis
    best_key = max(pattern_scores, key=pattern_scores.get)
    total_score = sum(pattern_scores.values())
    confidence = pattern_scores[best_key] / total_score if total_score > 0 else 0.0
    
    # Log top 3 key candidates
    sorted_keys = sorted(pattern_scores.items(), key=lambda x: x[1], reverse=True)
    log(f"  Top key candidates:")
    for i, (key, score) in enumerate(sorted_keys[:3]):
        log(f"    {i+1}. {key}: {score:.1f} points")
    
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
    
    # Detect song structure
    log("Detecting song structure...")
    structure_start = time.time()
    song_structure = detect_song_structure(chords, pattern_info, tempo_value)
    structure_time = time.time() - structure_start
    log(f"✓ Song structure detected: {len(song_structure)} sections")
    for section in song_structure:
        log(f"  {section['label']}: measures {section['measureStart']}-{section['measureEnd']} ({section['patternCount']} repetitions)")
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

def detect_chords(audio_path, job_id):
    """
    Main chord detection function - uses essentia if available, falls back to librosa
    """
    if ESSENTIA_AVAILABLE:
        log("Using Essentia for chord detection")
        return detect_chords_essentia(audio_path, job_id)
    else:
        log("Essentia not available, using librosa chord detection")
        return detect_chords_librosa(audio_path, job_id)

def detect_chords_librosa(audio_path, job_id):
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
    
    # Detect time signature by analyzing beat patterns
    time_signature = detect_time_signature(y, sr, beats)
    
    log(f"✓ Tempo detected: {tempo_value:.1f} BPM")
    log(f"✓ Time signature detected: {time_signature}")
    log(f"  Beats detected: {len(beats)}")
    log(f"  Detection time: {tempo_time:.2f}s")
    
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
    
    # IMPROVED CHORD DETECTION
    log("Detecting chord changes (beat-synchronized)...")
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
    
    # Chord templates for major and minor chords
    chord_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    # Major chord template: root, major third, perfect fifth (0, 4, 7 semitones)
    major_template = np.array([1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0])
    # Minor chord template: root, minor third, perfect fifth (0, 3, 7 semitones)
    minor_template = np.array([1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0])
    
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
        
        # Find best matching chord (try all 12 roots × 2 qualities)
        best_score = -1
        best_chord = 'C'
        best_quality = 'major'
        
        for root_idx, root in enumerate(chord_names):
            # Try major
            major_rotated = np.roll(major_template, root_idx)
            major_score = np.dot(chroma_beat, major_rotated)
            
            if major_score > best_score:
                best_score = major_score
                best_chord = root
                best_quality = 'major'
            
            # Try minor
            minor_rotated = np.roll(minor_template, root_idx)
            minor_score = np.dot(chroma_beat, minor_rotated)
            
            if minor_score > best_score:
                best_score = minor_score
                best_chord = root + 'm'
                best_quality = 'minor'
        
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
                
                # Only keep chords with reasonable confidence
                if avg_confidence > 0.3:  # Threshold for confidence
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
            if avg_confidence > 0.3:
                chords.append({
                    'chord': current_chord,
                    'start': round(current_start, 2),
                    'end': round(duration, 2),
                    'duration': round(duration - current_start, 2),
                    'confidence': round(avg_confidence, 2)
                })
    
    # FILTER: Remove very short chords (likely noise)
    log("  Filtering out very short chords...")
    min_duration = 1.0  # Minimum 1 second
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
    
    # Detect song structure using the same pattern analysis
    log("Detecting song structure...")
    structure_start = time.time()
    song_structure = detect_song_structure(chords, pattern_info, tempo_value)
    structure_time = time.time() - structure_start
    log(f"✓ Song structure detected: {len(song_structure)} sections")
    for section in song_structure:
        log(f"  {section['label']}: measures {section['measureStart']}-{section['measureEnd']} ({section['patternCount']} repetitions)")
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
        'model': 'librosa-chromagram-enhanced'
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

def convert_chord_to_nashville(chord_name, key='C'):
    """Convert a chord name to Roman numeral notation based on key"""
    if not chord_name or chord_name == 'N':
        return 'I'
    
    chord_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
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
        return 'I'
    
    # Calculate interval (scale degree)
    interval = (root_idx - key_idx + 12) % 12
    
    # Determine if chord is minor
    is_minor = 'm' in chord_name.lower() and 'maj' not in chord_name.lower()
    
    # Map to Roman numeral based on scale degree
    # In major key: I, ii, iii, IV, V, vi, vii°
    roman_numerals_major = {
        0: 'I',      # Tonic (major)
        1: 'bII',    # Flat 2 (major)
        2: 'II',     # 2 (major)
        3: 'bIII',   # Flat 3 (major)
        4: 'III',    # 3 (major)
        5: 'IV',     # 4 (major)
        6: 'bV',     # Flat 5 (diminished)
        7: 'V',      # 5 (major)
        8: 'bVI',    # Flat 6 (major)
        9: 'VI',     # 6 (major)
        10: 'bVII',  # Flat 7 (major)
        11: 'VII'    # 7 (major)
    }
    
    roman_numerals_minor = {
        0: 'i',      # Tonic (minor)
        1: 'bii',    # Flat 2 (minor)
        2: 'ii',     # 2 (minor)
        3: 'biii',   # Flat 3 (minor)
        4: 'iii',    # 3 (minor)
        5: 'iv',     # 4 (minor)
        6: 'bv',     # Flat 5 (diminished)
        7: 'v',      # 5 (minor)
        8: 'bvi',    # Flat 6 (minor)
        9: 'vi',     # 6 (minor)
        10: 'bvii',  # Flat 7 (minor)
        11: 'vii'    # 7 (minor)
    }
    
    # Select appropriate Roman numeral based on chord quality
    if is_minor:
        return roman_numerals_minor.get(interval, 'i')
    else:
        return roman_numerals_major.get(interval, 'I')

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

def update_job_with_chords(job_id, chords_data):
    """Update job with chord detection results"""
    log(f"Updating job with {len(chords_data['chords'])} chords")
    table = dynamodb.Table(JOBS_TABLE)
    
    try:
        # Convert all floats to Decimal for DynamoDB compatibility
        log("Converting float values to Decimal for DynamoDB...")
        chords_data_decimal = convert_floats_to_decimal(chords_data)
        log(f"✓ Converted {len(chords_data['chords'])} chords to DynamoDB format")
        
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

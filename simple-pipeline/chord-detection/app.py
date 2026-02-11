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
from urllib.parse import unquote_plus

try:
    import essentia
    import essentia.standard as es
    ESSENTIA_AVAILABLE = True
except ImportError:
    ESSENTIA_AVAILABLE = False
    print("WARNING: essentia not available, using librosa only")

# Demucs disabled for simple pipeline
DEMUCS_AVAILABLE = False

# MSAF disabled for simple pipeline  
MSAF_AVAILABLE = False

# AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Environment variables
JOBS_TABLE = os.environ.get('JOBS_TABLE', 'MusicTranscription-Jobs-test')
ENABLE_STEM_SEPARATION = False  # Disabled for simple pipeline
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
    
    # URL-decode the key (S3 events have URL-encoded keys)
    if key:
        key = unquote_plus(key)
    
    log(f"Environment Variables:")
    log(f"  JOB_ID: {job_id}")
    log(f"  BUCKET: {bucket}")
    log(f"  KEY: {key}")
    log(f"  KEY: {key}")
    log(f"  JOBS_TABLE: {JOBS_TABLE}")
    
    if not all([job_id, bucket, key]):
        log("ERROR: Missing required environment variables", "ERROR")
        raise ValueError("Missing required environment variables: JOB_ID, BUCKET, KEY")
    
    try:
        # Update status
        log("Step 1: Updating job status to PROCESSING (10%)")
        update_job_status(job_id, 'PROCESSING', 10)
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
        
        # Mark as complete
        log("Step 5: Marking job as complete...")
        update_job_status(job_id, 'COMPLETED', 100)
        log("✓ Job marked as complete")
        
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

def detect_key_improved(chroma, bass_chroma=None):
    """
    Improved key detection using Krumhansl-Schmuckler algorithm
    BASS-WEIGHTED: Emphasizes bass notes for more accurate key detection
    
    Args:
        chroma: Full spectrum chromagram
        bass_chroma: Bass-only chromagram (optional, for weighting)
    
    Returns: (key, mode, confidence)
    """
    # Krumhansl-Schmuckler key profiles
    major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
    
    # Average chroma over time
    chroma_mean = np.mean(chroma, axis=1)
    
    # BASS-WEIGHTED: If bass chroma provided, weight it heavily
    if bass_chroma is not None:
        bass_mean = np.mean(bass_chroma, axis=1)
        # Bass gets 3x weight for key detection (even more important than chord detection)
        chroma_mean = (chroma_mean + 3.0 * bass_mean) / 4.0
    
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

def detect_chords(audio_path, job_id):
    """
    Main chord detection function - ALWAYS uses enhanced librosa with 84 templates
    (Essentia detection disabled in favor of enhanced librosa system)
    """
    # FORCE enhanced librosa detection (84 templates)
    # Even if essentia is available, we want to use the new enhanced system
    log("Using ENHANCED librosa chord detection (84 templates)")
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
    log("=" * 60)
    log("AUDIO ANALYSIS CONFIGURATION")
    log("=" * 60)
    log(f"  Stem separation: DISABLED (using full mix)")
    log(f"  Drum removal: ENABLED (HPSS)")
    log(f"  Bass weighting: ENABLED (C2-C4 range)")
    log(f"  Analysis method: Chromagram + Pattern matching")
    log("=" * 60)
    start_time = time.time()
    
    # HARMONIC/PERCUSSIVE SEPARATION: Remove drums before analysis
    log("Separating harmonic content from percussion...")
    y_harmonic, y_percussive = librosa.effects.hpss(y, margin=3.0)
    harmonic_energy = np.sum(np.abs(y_harmonic))
    percussive_energy = np.sum(np.abs(y_percussive))
    total_energy = harmonic_energy + percussive_energy
    log(f"  Harmonic energy: {harmonic_energy:.0f} ({harmonic_energy/total_energy*100:.1f}%)")
    log(f"  Percussive energy: {percussive_energy:.0f} ({percussive_energy/total_energy*100:.1f}%)")
    log(f"  Using harmonic component for chord/key detection")
    
    # Use CQT chromagram with higher resolution and smoothing (harmonic only)
    chroma = librosa.feature.chroma_cqt(
        y=y_harmonic,  # Use harmonic component only (no drums)
        sr=sr, 
        hop_length=2048,  # Larger hop = less temporal resolution but more stable
        n_chroma=12,
        bins_per_octave=36  # Higher resolution
    )
    
    # Apply median filtering to smooth out noise
    chroma = median_filter(chroma, size=(1, 5))  # Smooth along time axis
    
    # BASS-WEIGHTED: Compute bass chromagram (low frequencies only, harmonic only)
    log("Computing bass chromagram for improved key/chord detection...")
    bass_chroma = librosa.feature.chroma_cqt(
        y=y_harmonic,  # Use harmonic component only (no kick drum)
        sr=sr,
        hop_length=2048,
        n_chroma=12,
        bins_per_octave=36,
        fmin=librosa.note_to_hz('C2'),  # Start at C2 (65.4 Hz) - bass range
        n_octaves=2  # Cover C2 to C4 (2 octaves)
    )
    
    # Apply median filtering to bass chroma
    bass_chroma = median_filter(bass_chroma, size=(1, 5))
    
    chroma_time = time.time() - start_time
    log(f"✓ Chromagram computed (drums excluded)")
    log(f"  Full spectrum shape: {chroma.shape}")
    log(f"  Bass spectrum shape: {bass_chroma.shape}")
    log(f"  Compute time: {chroma_time:.2f}s")
    
    # IMPROVED CHORD DETECTION WITH ENHANCED TEMPLATES
    log("Detecting chord changes (downbeat-synchronized with enhanced templates)...")
    start_time = time.time()
    chords = []
    
    # DOWNBEAT-ONLY ANALYSIS: Only analyze first beat of each measure
    # This reduces noise from passing tones and non-chord tones
    beat_times = librosa.frames_to_time(beats, sr=sr)
    
    # Detect time signature to determine beats per measure
    # Most common: 4/4 (4 beats), 3/4 (3 beats), 6/8 (2 beats)
    if time_signature == '4/4':
        beats_per_measure = 4
    elif time_signature == '3/4':
        beats_per_measure = 3
    elif time_signature == '6/8':
        beats_per_measure = 2
    else:
        beats_per_measure = 4  # Default to 4/4
    
    # Extract only downbeats (first beat of each measure)
    downbeat_times = []
    for i in range(0, len(beat_times), beats_per_measure):
        downbeat_times.append(beat_times[i])
    
    log(f"  Time signature: {time_signature} ({beats_per_measure} beats per measure)")
    log(f"  Total beats: {len(beat_times)}")
    log(f"  Downbeats (first beat of each measure): {len(downbeat_times)}")
    log(f"  Sampling strategy: DOWNBEAT-ONLY (reduces noise from passing tones)")
    
    # Convert to frames
    analysis_frames = librosa.time_to_frames(
        np.array(downbeat_times),
        sr=sr,
        hop_length=2048
    )
    
    log(f"  Analyzing at {len(analysis_frames)} downbeat positions")
    
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
        
        # Get bass chroma at this position
        bass_chroma_beat = np.mean(bass_chroma[:, start_frame:end_frame], axis=1)
        
        # BASS-WEIGHTED: Combine full spectrum with bass emphasis
        # Bass gets 2x weight for more accurate root detection
        weighted_chroma = (chroma_beat + 2.0 * bass_chroma_beat) / 3.0
        
        # Normalize
        if np.sum(weighted_chroma) > 0:
            weighted_chroma = weighted_chroma / np.sum(weighted_chroma)
        
        # Find best matching chord from all 84 templates
        best_score = -1
        best_chord = 'C'
        
        for chord_name, template in templates.items():
            # Normalize template
            if np.sum(template) > 0:
                template_norm = template / np.sum(template)
            else:
                continue
            
            # Calculate correlation using bass-weighted chroma
            score = np.dot(weighted_chroma, template_norm)
            
            if score > best_score:
                best_score = score
                best_chord = chord_name
        
        analysis_time = downbeat_times[i] if i < len(downbeat_times) else duration
        
        beat_chords.append({
            'chord': best_chord,
            'time': analysis_time,
            'confidence': best_score,
            'position_index': i
        })
    
    log(f"  Detected {len(beat_chords)} chords at downbeat positions")
    
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
    
    # FREQUENCY-BASED KEY DETECTION: Find most common chord
    log("Detecting key from chord frequency...")
    log("=" * 60)
    log("KEY DETECTION: FREQUENCY-BASED APPROACH")
    log("=" * 60)
    key_start = time.time()
    
    # Count chord occurrences (root notes only, ignore quality)
    from collections import Counter
    
    # Extract root notes from chords
    chord_roots = []
    for chord in chords:
        chord_name = chord['chord']
        # Extract root (first 1-2 characters)
        root = chord_name[0]
        if len(chord_name) > 1 and chord_name[1] in ['#', 'b']:
            root = chord_name[:2]
        chord_roots.append(root)
    
    # Count frequency
    root_counts = Counter(chord_roots)
    
    log("Chord Root Frequency:")
    for root, count in root_counts.most_common(10):
        percentage = (count / len(chord_roots)) * 100
        log(f"  {root}: {count} times ({percentage:.1f}%)")
    
    # Most common chord is the key
    if root_counts:
        most_common_root = root_counts.most_common(1)[0][0]
        most_common_count = root_counts.most_common(1)[0][1]
        confidence = most_common_count / len(chord_roots)
        
        # Determine if minor or major by checking chord quality
        # Count major vs minor versions of the most common chord
        major_count = sum(1 for c in chords if c['chord'].startswith(most_common_root) and 'm' not in c['chord'].lower())
        minor_count = sum(1 for c in chords if c['chord'].startswith(most_common_root) and 'm' in c['chord'].lower() and 'maj' not in c['chord'].lower())
        
        if minor_count > major_count:
            mode = 'minor'
            key = most_common_root
            
            # Calculate relative major
            note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            # Normalize to sharp
            if 'b' in most_common_root:
                flat_to_sharp = {'Db': 'C#', 'Eb': 'D#', 'Gb': 'F#', 'Ab': 'G#', 'Bb': 'A#'}
                most_common_root = flat_to_sharp.get(most_common_root, most_common_root)
            
            try:
                minor_idx = note_names.index(most_common_root)
                # Relative major is 3 semitones up (minor 3rd)
                relative_major_idx = (minor_idx + 3) % 12
                relative_major = note_names[relative_major_idx]
                
                log("")
                log(f"✓ KEY DETECTED: {key} {mode}")
                log(f"  Relative Major: {relative_major}")
                log(f"  Display Format: {key} Minor / {relative_major} Major")
                log(f"  Nashville Numbers: Calculated from {relative_major} Major")
                log(f"  Confidence: {confidence:.3f} ({most_common_count}/{len(chord_roots)} chords)")
                log(f"  Chord quality: {major_count} major, {minor_count} minor")
                
                # Store both for Nashville number calculation
                key_for_display = f"{key} Minor / {relative_major} Major"
                key_for_nashville = relative_major  # Use relative major for NNS
            except (ValueError, IndexError):
                relative_major = most_common_root
                key_for_display = f"{key} {mode}"
                key_for_nashville = key
        else:
            mode = 'major'
            key = most_common_root
            key_for_display = f"{key} Major"
            key_for_nashville = key
            
            log("")
            log(f"✓ KEY DETECTED: {key} {mode}")
            log(f"  Confidence: {confidence:.3f} ({most_common_count}/{len(chord_roots)} chords)")
            log(f"  Chord quality: {major_count} major, {minor_count} minor")
    else:
        key = 'C'
        mode = 'major'
        confidence = 0.0
        key_for_display = 'C Major'
        key_for_nashville = 'C'
        log("⚠️ No chords detected, defaulting to C Major")
    
    log("=" * 60)
    key_time = time.time() - key_start
    
    log(f"✓ Key detection complete in {key_time:.2f}s")
    
    # Get pattern info for structure detection (don't use key from this)
    log("Analyzing chord patterns for structure detection...")
    _, _, _, pattern_info = detect_key_from_progression(chords)
    
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
        'key': key_for_display,  # Display format (e.g., "A Minor / C Major")
        'mode': mode,
        'keyConfidence': round(confidence, 2),
        'tempo': round(tempo_value, 1),
        'timeSignature': time_signature,
        'duration': round(duration, 2),
        'totalChords': len(chords),
        'songStructure': song_structure,
        'patternAnalysis': format_pattern_analysis(pattern_info, key_for_display, key_for_nashville),  # Use relative major for NNS
        'model': 'librosa-enhanced-84-templates-downbeat-frequency-key'  # Updated model identifier
    }

def format_pattern_analysis(pattern_info, key='C', key_for_nashville=None):
    """
    Format pattern analysis for storage in DynamoDB
    Converts chord names to Nashville numbers based on detected key
    Returns a list of pattern summaries
    
    Args:
        pattern_info: Pattern information dictionary
        key: Display key (e.g., "A Minor / C Major")
        key_for_nashville: Key to use for Nashville calculation (e.g., "C" for relative major)
    """
    if not pattern_info:
        return []
    
    # Use key_for_nashville if provided, otherwise use key
    nns_key = key_for_nashville if key_for_nashville else key
    
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
            nashville = convert_chord_to_nashville(chord_name, nns_key)
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
                ':status': 'PROCESSING',
                ':progress': 90,
                ':updated': time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
            }
        )
        log(f"✓ Job updated with chord data (status: PROCESSING, progress: 90%)")
    except Exception as e:
        log(f"ERROR updating job with chords: {str(e)}", "ERROR")
        raise

if __name__ == '__main__':
    main()

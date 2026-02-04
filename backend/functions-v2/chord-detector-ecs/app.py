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
from decimal import Decimal
import time
import sys
import traceback

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
    Detect key by analyzing repeating chord progression patterns
    Looks for common progressions like I-vi-ii-V, I-IV-V, ii-V-I, etc.
    Returns: (key, mode, confidence, pattern_info)
    """
    if len(chords) < 8:  # Need at least 8 chords to detect patterns
        return 'C', 'major', 0.0, {}
    
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
    
    # Find repeating patterns (3-6 chord sequences)
    pattern_scores = {}  # key -> {pattern: count}
    all_patterns = {}  # Store all patterns found for structure detection
    
    for pattern_length in range(3, 7):  # Try patterns of 3-6 chords
        patterns_found = {}
        pattern_positions = {}  # Track where each pattern occurs
        
        for i in range(len(chord_sequence) - pattern_length + 1):
            pattern = tuple(c['root'] for c in chord_sequence[i:i+pattern_length])
            patterns_found[pattern] = patterns_found.get(pattern, 0) + 1
            
            if pattern not in pattern_positions:
                pattern_positions[pattern] = []
            pattern_positions[pattern].append(i)
        
        # Find patterns that repeat at least twice
        for pattern, count in patterns_found.items():
            if count >= 2:  # Pattern repeats at least once
                # Store pattern info for structure detection
                all_patterns[pattern] = {
                    'count': count,
                    'length': pattern_length,
                    'positions': pattern_positions[pattern]
                }
                
                # Analyze this pattern for each possible key
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
                    
                    # Check if this matches common progressions
                    progression_score = 0
                    
                    # I-vi-ii-V (0-9-2-7) - very common in jazz/pop
                    if tuple(intervals) == (0, 9, 2, 7) or tuple(intervals[:4]) == (0, 9, 2, 7):
                        progression_score = 10
                    # I-IV-V (0-5-7) - most common in rock/pop
                    elif tuple(intervals) == (0, 5, 7) or tuple(intervals[:3]) == (0, 5, 7):
                        progression_score = 9
                    # I-V-vi-IV (0-7-9-5) - very common pop progression
                    elif tuple(intervals) == (0, 7, 9, 5) or tuple(intervals[:4]) == (0, 7, 9, 5):
                        progression_score = 9
                    # ii-V-I (2-7-0) - jazz cadence
                    elif tuple(intervals) == (2, 7, 0) or tuple(intervals[:3]) == (2, 7, 0):
                        progression_score = 8
                    # I-vi-IV-V (0-9-5-7) - 50s progression
                    elif tuple(intervals) == (0, 9, 5, 7) or tuple(intervals[:4]) == (0, 9, 5, 7):
                        progression_score = 8
                    # V-I cadence (7-0) - strongest cadence
                    elif len(intervals) >= 2 and intervals[-2:] == [7, 0]:
                        progression_score = 7
                    # IV-I cadence (5-0) - plagal cadence
                    elif len(intervals) >= 2 and intervals[-2:] == [5, 0]:
                        progression_score = 6
                    # Starts with I (0) - likely tonic
                    elif intervals[0] == 0:
                        progression_score = 3
                    # Ends with I (0) - likely tonic
                    elif intervals[-1] == 0:
                        progression_score = 4
                    
                    if progression_score > 0:
                        if potential_key not in pattern_scores:
                            pattern_scores[potential_key] = 0
                        # Weight by: progression strength × repetition count × pattern length
                        pattern_scores[potential_key] += progression_score * count * pattern_length
    
    if not pattern_scores:
        return 'C', 'major', 0.0, {}
    
    # Find best key based on pattern analysis
    best_key = max(pattern_scores, key=pattern_scores.get)
    total_score = sum(pattern_scores.values())
    confidence = pattern_scores[best_key] / total_score if total_score > 0 else 0.0
    
    # Determine mode by analyzing chord qualities in the key
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
    
    log(f"  Pattern analysis: Found {len(pattern_scores)} potential keys")
    log(f"  Best key: {best_key} (score: {pattern_scores[best_key]}, confidence: {confidence:.2f})")
    log(f"  Mode indicators: major={major_indicators}, minor={minor_indicators}")
    
    return best_key, mode, confidence, all_patterns

def detect_chords(audio_path, job_id):
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
    
    if len(chords) > 0:
        log(f"  First chord: {chords[0]['chord']} at {chords[0]['start']}s")
        log(f"  Last chord: {chords[-1]['chord']} at {chords[-1]['start']}s")
    
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
        'model': 'librosa-chromagram-enhanced'
    }

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
    Detect song structure (verse, chorus, bridge) using repeating chord patterns
    Groups consecutive repetitions of the same pattern into sections
    Returns: list of sections with labels and measure ranges
    """
    if not pattern_info or len(chords) == 0:
        return []
    
    # Sort patterns by count (most repeated first) and length
    sorted_patterns = sorted(
        pattern_info.items(),
        key=lambda x: (x[1]['count'], x[1]['length']),
        reverse=True
    )
    
    if not sorted_patterns:
        return []
    
    # Calculate measures per chord (approximate)
    seconds_per_beat = 60 / tempo
    seconds_per_measure = seconds_per_beat * 4  # Assuming 4/4 time
    
    sections = []
    section_labels = ['Verse', 'Chorus', 'Bridge', 'Pre-Chorus', 'Outro', 'Intro']
    label_index = 0
    used_positions = set()
    
    # Process each pattern
    for pattern, info in sorted_patterns[:6]:  # Limit to top 6 patterns
        positions = info['positions']
        pattern_length = info['length']
        
        # Group consecutive occurrences of this pattern
        groups = []
        current_group = []
        
        for i, pos in enumerate(positions):
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
        
        # Create sections from groups
        for group in groups:
            if len(group) >= 1:  # At least 1 occurrence
                start_chord_idx = group[0]
                end_chord_idx = group[-1] + pattern_length - 1
                
                # Mark positions as used
                for pos in range(group[0], group[-1] + pattern_length):
                    used_positions.add(pos)
                
                # Calculate measure numbers (approximate)
                start_time = chords[start_chord_idx].get('start', 0) or chords[start_chord_idx].get('time', 0)
                end_time = chords[min(end_chord_idx, len(chords)-1)].get('end', start_time + 10) or chords[min(end_chord_idx, len(chords)-1)].get('time', start_time) + 10
                
                measure_start = int(start_time / seconds_per_measure) + 1
                measure_end = int(end_time / seconds_per_measure) + 1
                
                # Assign label
                if label_index < len(section_labels):
                    label = section_labels[label_index]
                    label_index += 1
                else:
                    label = f"Section {label_index - len(section_labels) + 1}"
                
                sections.append({
                    'label': label,
                    'measureStart': measure_start,
                    'measureEnd': measure_end,
                    'patternCount': len(group),
                    'pattern': list(pattern),
                    'startTime': round(start_time, 2),
                    'endTime': round(end_time, 2)
                })
    
    # Sort sections by start time
    sections.sort(key=lambda x: x['startTime'])
    
    # Relabel based on typical song structure
    # First section is usually Intro or Verse
    # Most repeated pattern is usually Chorus
    if sections:
        # Find the section with most repetitions
        max_repetitions = max(s['patternCount'] for s in sections)
        
        for i, section in enumerate(sections):
            if section['patternCount'] == max_repetitions and section['label'] not in ['Chorus']:
                # This is likely the chorus (most repeated)
                section['label'] = 'Chorus'
            elif i == 0 and section['patternCount'] == 1:
                # First section with single occurrence might be intro
                section['label'] = 'Intro'
            elif section['label'] == 'Chorus':
                # Keep chorus label
                pass
            elif 'Verse' not in [s['label'] for s in sections[:i]]:
                # First non-chorus section is verse
                section['label'] = 'Verse'
            elif 'Bridge' not in [s['label'] for s in sections[:i]] and i > len(sections) / 2:
                # Later section might be bridge
                section['label'] = 'Bridge'
    
    return sections

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

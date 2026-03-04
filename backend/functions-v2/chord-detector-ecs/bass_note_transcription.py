"""
Bass Note Transcription System
Transcribes monophonic bass notes and converts to Nashville Number System
"""

import numpy as np
import librosa
from typing import List, Dict, Tuple
import logging

# Try to import Basic Pitch
try:
    from basic_pitch.inference import predict
    from basic_pitch import ICASSP_2022_MODEL_PATH
    BASIC_PITCH_AVAILABLE = True
except ImportError:
    BASIC_PITCH_AVAILABLE = False
    print("WARNING: basic-pitch not available, using librosa pitch detection")

log = logging.getLogger(__name__)


def detect_bass_notes(bass_audio: np.ndarray, sr: int, tempo: float, 
                     time_signature: str, first_downbeat: float = 0.0) -> Dict:
    """
    Transcribe bass notes (monophonic) and convert to Nashville numbers
    
    Args:
        bass_audio: Bass stem audio (numpy array)
        sr: Sample rate
        tempo: BPM
        time_signature: e.g., "4/4"
        first_downbeat: Time of first downbeat in seconds
    
    Returns:
        Dictionary with notes, key, relative major, and measures
    """
    log.info("=" * 80)
    log.info("BASS NOTE TRANSCRIPTION")
    log.info("=" * 80)
    
    duration = len(bass_audio) / sr
    log.info(f"Bass audio duration: {duration:.2f}s")
    log.info(f"Tempo: {tempo:.1f} BPM")
    log.info(f"Time signature: {time_signature}")
    log.info(f"First downbeat: {first_downbeat:.3f}s")
    
    # Step 1: Transcribe bass notes
    log.info("\nStep 1: Transcribing bass notes...")
    notes = transcribe_bass_notes(bass_audio, sr, tempo)
    log.info(f"✓ Transcribed {len(notes)} note events")
    
    if len(notes) == 0:
        log.warning("No notes detected in bass stem")
        return create_empty_result()
    
    # Step 2: Filter to monophonic (keep strongest note at each time)
    log.info("\nStep 2: Filtering to monophonic...")
    notes = filter_to_monophonic(notes)
    log.info(f"✓ Filtered to {len(notes)} monophonic notes")
    
    # Step 3: Quantize to 16th note grid
    log.info("\nStep 3: Quantizing to 16th note grid...")
    notes = quantize_notes(notes, tempo, time_signature, first_downbeat)
    log.info(f"✓ Quantized {len(notes)} notes")
    
    # Step 4: Detect key from note progression
    log.info("\nStep 4: Detecting key from bass progression...")
    key_info = detect_key_from_notes(notes)
    log.info(f"✓ Detected key: {key_info['key']} {key_info['mode']}")
    log.info(f"  Relative major: {key_info['relativeMajor']}")
    log.info(f"  Confidence: {key_info['confidence']:.2%}")
    
    # Step 5: Convert notes to Nashville numbers
    log.info("\nStep 5: Converting to Nashville numbers...")
    notes = convert_to_nashville(notes, key_info)
    log.info(f"✓ Converted {len(notes)} notes to NNS")
    
    # Step 6: Group by measures
    log.info("\nStep 6: Grouping notes by measure...")
    measures = group_by_measures(notes, tempo, time_signature, first_downbeat, duration)
    log.info(f"✓ Created {len(measures)} measures")
    
    # Log first few measures
    log.info("\nFirst 4 measures:")
    for measure in measures[:4]:
        nns_str = ' '.join(measure['nns'])
        notes_str = ' '.join(measure['noteNames'])
        log.info(f"  Measure {measure['measure']}: {nns_str} ({notes_str})")
    
    log.info("=" * 80)
    
    return {
        'notes': notes,
        'key': key_info['key'],
        'mode': key_info['mode'],
        'relativeMajor': key_info['relativeMajor'],
        'confidence': key_info['confidence'],
        'measures': measures,
        'tempo': tempo,
        'timeSignature': time_signature,
        'duration': duration,
        'totalNotes': len(notes),
        'totalMeasures': len(measures)
    }


def transcribe_bass_notes(audio: np.ndarray, sr: int, tempo: float = 120.0) -> List[Dict]:
    """
    Transcribe bass notes using Basic Pitch or librosa
    
    Returns:
        List of note events with pitch, start, end, velocity
    """
    if BASIC_PITCH_AVAILABLE:
        return transcribe_with_basic_pitch(audio, sr, tempo)
    else:
        return transcribe_with_librosa(audio, sr)


def transcribe_with_basic_pitch(audio: np.ndarray, sr: int, tempo: float = 120.0) -> List[Dict]:
    """Transcribe using Basic Pitch (preferred method)"""
    log.info("  Using Basic Pitch for transcription...")
    
    # Basic Pitch expects audio at 22050 Hz
    if sr != 22050:
        audio = librosa.resample(audio, orig_sr=sr, target_sr=22050)
        sr = 22050
    
    # Calculate minimum note length from tempo (60% of 8th note)
    eighth_note_ms = int((60.0 / tempo / 2) * 1000) if tempo else 125
    
    # Run Basic Pitch with frequency constraints for bass range
    model_output, midi_data, note_events = predict(
        audio,
        sr,
        ICASSP_2022_MODEL_PATH,
        minimum_note_length=eighth_note_ms * 0.6,
        minimum_frequency=40.0,   # E1 — low bass limit
        maximum_frequency=300.0,  # D4 — high bass limit
        onset_threshold=0.5,
        frame_threshold=0.3,
    )
    
    # Convert to our format
    notes = []
    for note in note_events:
        notes.append({
            'pitch': int(note['pitch_midi']),
            'start': float(note['start_time']),
            'end': float(note['end_time']),
            'velocity': float(note.get('amplitude', 0.8)),
            'note_name': librosa.midi_to_note(int(note['pitch_midi']))
        })
    
    log.info(f"  Basic Pitch detected {len(notes)} notes")
    return notes


def transcribe_with_librosa(audio: np.ndarray, sr: int) -> List[Dict]:
    """Transcribe using librosa pitch detection (fallback)"""
    log.info("  Using librosa for pitch detection...")
    
    # Use pyin for pitch detection (better for monophonic sources)
    f0, voiced_flag, voiced_probs = librosa.pyin(
        audio,
        fmin=librosa.note_to_hz('E1'),  # Bass range: E1 to E4
        fmax=librosa.note_to_hz('E4'),
        sr=sr,
        frame_length=2048,
        hop_length=512
    )
    
    # Convert frame times
    times = librosa.frames_to_time(np.arange(len(f0)), sr=sr, hop_length=512)
    
    # Convert to note events
    notes = []
    current_note = None
    
    for i, (time, freq, voiced, prob) in enumerate(zip(times, f0, voiced_flag, voiced_probs)):
        if not voiced or np.isnan(freq) or prob < 0.5:
            # End current note if exists
            if current_note is not None:
                current_note['end'] = time
                notes.append(current_note)
                current_note = None
            continue
        
        # Convert frequency to MIDI note
        midi_note = librosa.hz_to_midi(freq)
        midi_note_rounded = int(np.round(midi_note))
        
        # Start new note or continue current
        if current_note is None:
            current_note = {
                'pitch': midi_note_rounded,
                'start': time,
                'end': time,
                'velocity': prob,
                'note_name': librosa.midi_to_note(midi_note_rounded)
            }
        elif abs(midi_note_rounded - current_note['pitch']) > 0.5:
            # Pitch changed, end current note and start new one
            current_note['end'] = time
            notes.append(current_note)
            current_note = {
                'pitch': midi_note_rounded,
                'start': time,
                'end': time,
                'velocity': prob,
                'note_name': librosa.midi_to_note(midi_note_rounded)
            }
        else:
            # Continue current note
            current_note['end'] = time
    
    # Add last note
    if current_note is not None:
        notes.append(current_note)
    
    log.info(f"  Librosa detected {len(notes)} notes")
    return notes


def filter_to_monophonic(notes: List[Dict]) -> List[Dict]:
    """
    Filter overlapping notes to keep only the strongest (monophonic)
    Bass should be monophonic, but transcription might detect harmonics
    """
    if len(notes) == 0:
        return notes
    
    # Sort by start time
    notes = sorted(notes, key=lambda n: n['start'])
    
    filtered = []
    for note in notes:
        # Check if this note overlaps with the last filtered note
        if filtered and note['start'] < filtered[-1]['end']:
            # Overlapping - keep the one with higher velocity
            if note['velocity'] > filtered[-1]['velocity']:
                filtered[-1] = note
        else:
            filtered.append(note)
    
    return filtered


def quantize_notes(notes: List[Dict], tempo: float, time_signature: str, 
                   first_downbeat: float) -> List[Dict]:
    """
    Quantize note start times to 8th note grid
    """
    beats_per_measure = int(time_signature.split('/')[0])
    beat_duration = 60.0 / tempo
    eighth_duration = beat_duration / 2
    
    quantized = []
    for note in notes:
        # Calculate time from first downbeat
        time_from_downbeat = note['start'] - first_downbeat
        
        # Quantize to nearest 8th note
        eighth_index = round(time_from_downbeat / eighth_duration)
        quantized_time = first_downbeat + (eighth_index * eighth_duration)
        
        # Calculate measure and beat
        beats_from_downbeat = eighth_index / 2
        measure = int(beats_from_downbeat / beats_per_measure) + 1
        beat_in_measure = (beats_from_downbeat % beats_per_measure) + 1
        subdivision = (eighth_index % 2) + 1  # 1=downbeat, 2=upbeat ("and")
        
        quantized.append({
            **note,
            'quantized_start': quantized_time,
            'measure': measure,
            'beat': beat_in_measure,
            'subdivision': subdivision,
            'eighth_index': eighth_index,
            'quantization_resolution': '8th'
        })
    
    return quantized


def detect_key_from_notes(notes: List[Dict]) -> Dict:
    """
    Detect key from bass note progression
    Uses note frequency analysis and common bass patterns
    """
    if len(notes) == 0:
        return {
            'key': 'C',
            'mode': 'major',
            'relativeMajor': 'C',
            'confidence': 0.0
        }
    
    # Count note occurrences (weighted by duration)
    note_weights = {}
    for note in notes:
        pitch_class = note['pitch'] % 12
        duration = note['end'] - note['start']
        note_weights[pitch_class] = note_weights.get(pitch_class, 0) + duration
    
    # Normalize
    total_weight = sum(note_weights.values())
    note_profile = np.zeros(12)
    for pc, weight in note_weights.items():
        note_profile[pc] = weight / total_weight
    
    # Krumhansl-Schmuckler key profiles
    major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
    
    # Normalize profiles
    major_profile = major_profile / np.sum(major_profile)
    minor_profile = minor_profile / np.sum(minor_profile)
    
    # Test all keys
    note_names = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']
    best_corr = -1
    best_key = 'C'
    best_mode = 'major'
    
    for i in range(12):
        # Rotate profiles
        major_rot = np.roll(major_profile, i)
        minor_rot = np.roll(minor_profile, i)
        
        # Calculate correlation
        major_corr = np.corrcoef(note_profile, major_rot)[0, 1]
        minor_corr = np.corrcoef(note_profile, minor_rot)[0, 1]
        
        if major_corr > best_corr:
            best_corr = major_corr
            best_key = note_names[i]
            best_mode = 'major'
        
        if minor_corr > best_corr:
            best_corr = minor_corr
            best_key = note_names[i]
            best_mode = 'minor'
    
    # Calculate relative major if minor key
    if best_mode == 'minor':
        key_index = note_names.index(best_key)
        relative_major_index = (key_index + 3) % 12  # Minor third up
        relative_major = note_names[relative_major_index]
    else:
        relative_major = best_key
    
    return {
        'key': best_key,
        'mode': best_mode,
        'relativeMajor': relative_major,
        'confidence': best_corr
    }


def convert_to_nashville(notes: List[Dict], key_info: Dict) -> List[Dict]:
    """
    Convert notes to Nashville Number System based on key
    Uses relative major for NNS calculation
    """
    note_names = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']
    
    # Use relative major for NNS calculation
    key_root = key_info['relativeMajor']
    key_index = note_names.index(key_root)
    
    for note in notes:
        pitch_class = note['pitch'] % 12
        
        # Calculate interval from key root
        interval = (pitch_class - key_index) % 12
        
        # Map to scale degree
        interval_to_degree = {
            0: '1',   # Root
            1: 'b2',  # Flat 2
            2: '2',   # 2
            3: 'b3',  # Flat 3 (minor 3rd)
            4: '3',   # Major 3rd
            5: '4',   # 4
            6: 'b5',  # Flat 5 (diminished 5th)
            7: '5',   # 5
            8: 'b6',  # Flat 6
            9: '6',   # 6
            10: 'b7', # Flat 7
            11: '7'   # Major 7
        }
        
        nns = interval_to_degree.get(interval, '1')
        note['nns'] = nns
    
    return notes


def group_by_measures(notes: List[Dict], tempo: float, time_signature: str,
                     first_downbeat: float, duration: float) -> List[Dict]:
    """
    Group notes by measure
    """
    beats_per_measure = int(time_signature.split('/')[0])
    beat_duration = 60.0 / tempo
    measure_duration = beat_duration * beats_per_measure
    
    # Calculate total measures
    total_measures = int((duration - first_downbeat) / measure_duration) + 1
    
    measures = []
    for measure_num in range(1, total_measures + 1):
        measure_start = first_downbeat + ((measure_num - 1) * measure_duration)
        measure_end = measure_start + measure_duration
        
        # Get notes in this measure
        measure_notes = [n for n in notes if measure_start <= n['quantized_start'] < measure_end]
        
        if len(measure_notes) == 0:
            continue
        
        measures.append({
            'measure': measure_num,
            'start': measure_start,
            'end': measure_end,
            'notes': measure_notes,
            'nns': [n['nns'] for n in measure_notes],
            'noteNames': [n['note_name'] for n in measure_notes],
            'pitches': [n['pitch'] for n in measure_notes]
        })
    
    return measures


def create_empty_result() -> Dict:
    """Create empty result when no notes detected"""
    return {
        'notes': [],
        'key': 'C',
        'mode': 'major',
        'relativeMajor': 'C',
        'confidence': 0.0,
        'measures': [],
        'tempo': 0,
        'timeSignature': '4/4',
        'duration': 0,
        'totalNotes': 0,
        'totalMeasures': 0
    }

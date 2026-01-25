"""
Chord detection utilities using Basic Pitch MIDI output
"""
import numpy as np
from collections import defaultdict
from typing import List, Dict, Tuple

# Chord templates (pitch classes)
CHORD_TEMPLATES = {
    'major': [0, 4, 7],
    'minor': [0, 3, 7],
    'dim': [0, 3, 6],
    'aug': [0, 4, 8],
    'sus2': [0, 2, 7],
    'sus4': [0, 5, 7],
    '7': [0, 4, 7, 10],
    'maj7': [0, 4, 7, 11],
    'min7': [0, 3, 7, 10],
    'dim7': [0, 3, 6, 9],
    'm7b5': [0, 3, 6, 10],  # half-diminished
    '6': [0, 4, 7, 9],
    'min6': [0, 3, 7, 9],
    '9': [0, 4, 7, 10, 14],
    'add9': [0, 4, 7, 14],
}

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def midi_to_pitch_class(midi_note: int) -> int:
    """Convert MIDI note to pitch class (0-11)"""
    return midi_note % 12

def detect_key(pitch_classes: List[int]) -> Tuple[str, str]:
    """
    Detect the key of the song using Krumhansl-Schmuckler algorithm
    Returns (key_name, mode) e.g., ('C', 'major')
    """
    # Major and minor key profiles (Krumhansl-Kessler)
    major_profile = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
    minor_profile = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
    
    # Count pitch class occurrences
    pc_counts = [0] * 12
    for pc in pitch_classes:
        pc_counts[pc] += 1
    
    # Normalize
    total = sum(pc_counts)
    if total == 0:
        return 'C', 'major'
    
    pc_distribution = [count / total for count in pc_counts]
    
    # Calculate correlation for all keys
    best_correlation = -1
    best_key = 0
    best_mode = 'major'
    
    for key in range(12):
        # Test major
        rotated_profile = major_profile[key:] + major_profile[:key]
        correlation = np.corrcoef(pc_distribution, rotated_profile)[0, 1]
        if correlation > best_correlation:
            best_correlation = correlation
            best_key = key
            best_mode = 'major'
        
        # Test minor
        rotated_profile = minor_profile[key:] + minor_profile[:key]
        correlation = np.corrcoef(pc_distribution, rotated_profile)[0, 1]
        if correlation > best_correlation:
            best_correlation = correlation
            best_key = key
            best_mode = 'minor'
    
    return NOTE_NAMES[best_key], best_mode

def match_chord(pitch_classes: List[int]) -> Tuple[str, float]:
    """
    Match a set of pitch classes to the best chord
    Returns (chord_name, confidence)
    """
    if not pitch_classes:
        return 'N', 0.0
    
    pitch_classes = sorted(set(pitch_classes))
    
    # Try all possible roots
    best_match = ('N', 0.0)
    
    for root in range(12):
        # Normalize to root
        normalized = [(pc - root) % 12 for pc in pitch_classes]
        normalized = sorted(set(normalized))
        
        # Try each chord type
        for chord_type, template in CHORD_TEMPLATES.items():
            # Calculate match score
            matches = sum(1 for pc in normalized if pc in template)
            extras = len(normalized) - matches
            missing = len(template) - matches
            
            # Confidence calculation
            if len(template) == 0:
                continue
            
            confidence = matches / len(template)
            confidence -= (extras * 0.1)  # Penalize extra notes
            confidence -= (missing * 0.2)  # Penalize missing notes
            confidence = max(0, min(1, confidence))
            
            if confidence > best_match[1]:
                chord_name = f"{NOTE_NAMES[root]}{chord_type if chord_type != 'major' else ''}"
                best_match = (chord_name, confidence)
    
    return best_match

def extract_chords_from_midi(midi_data, segment_duration: float = 2.0) -> List[Dict]:
    """
    Extract chord progression from MIDI data
    
    Args:
        midi_data: pretty_midi.PrettyMIDI object
        segment_duration: Duration of each segment in seconds
    
    Returns:
        List of chord dictionaries with timestamp, name, and confidence
    """
    if not midi_data.instruments:
        return []
    
    # Get total duration
    total_duration = midi_data.get_end_time()
    
    # Collect all pitch classes over time
    all_pitch_classes = []
    for instrument in midi_data.instruments:
        if not instrument.is_drum:
            for note in instrument.notes:
                all_pitch_classes.append(midi_to_pitch_class(note.pitch))
    
    # Detect key
    key_name, mode = detect_key(all_pitch_classes)
    
    # Segment the song and detect chords
    chords = []
    num_segments = int(np.ceil(total_duration / segment_duration))
    
    for i in range(num_segments):
        start_time = i * segment_duration
        end_time = min((i + 1) * segment_duration, total_duration)
        
        # Collect notes in this segment
        segment_pitches = []
        for instrument in midi_data.instruments:
            if not instrument.is_drum:
                for note in instrument.notes:
                    if start_time <= note.start < end_time:
                        segment_pitches.append(midi_to_pitch_class(note.pitch))
        
        # Match chord
        if segment_pitches:
            chord_name, confidence = match_chord(segment_pitches)
            
            # Only add if confidence is reasonable or if it's different from previous
            if confidence > 0.3 or (chords and chord_name != chords[-1]['name']):
                chords.append({
                    'timestamp': round(start_time, 2),
                    'name': chord_name,
                    'confidence': round(confidence, 2),
                    'duration': round(end_time - start_time, 2)
                })
    
    # Merge consecutive identical chords
    merged_chords = []
    for chord in chords:
        if merged_chords and merged_chords[-1]['name'] == chord['name']:
            merged_chords[-1]['duration'] += chord['duration']
        else:
            merged_chords.append(chord)
    
    return {
        'key': key_name,
        'mode': mode,
        'chords': merged_chords
    }

def format_chord_progression(chords_data: Dict) -> str:
    """
    Format chord progression as a readable string
    """
    key_info = f"Key: {chords_data['key']} {chords_data['mode']}\n\n"
    
    chord_lines = []
    for chord in chords_data['chords']:
        time_str = f"{int(chord['timestamp'] // 60):02d}:{int(chord['timestamp'] % 60):02d}"
        chord_lines.append(
            f"{time_str} - {chord['name']:<8} "
            f"(confidence: {chord['confidence']:.0%}, duration: {chord['duration']:.1f}s)"
        )
    
    return key_info + "\n".join(chord_lines)

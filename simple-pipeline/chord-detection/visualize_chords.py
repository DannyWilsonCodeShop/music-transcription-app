#!/usr/bin/env python3
"""
Quick chord visualization - show chords aligned to beats/measures
"""

import json
import sys
from typing import List, Dict

def load_results(json_path: str) -> Dict:
    """Load chord detection results from JSON"""
    with open(json_path, 'r') as f:
        return json.load(f)

def format_time(seconds: float) -> str:
    """Format seconds as MM:SS.ms"""
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes:02d}:{secs:05.2f}"

def create_measure_grid(results: Dict, measures_per_line: int = 4) -> str:
    """
    Create a measure-by-measure grid showing chords
    
    Args:
        results: Chord detection results
        measures_per_line: How many measures to show per line
    
    Returns:
        Formatted string with chord grid
    """
    tempo = results['tempo']
    time_sig = results.get('time_signature', '4/4')
    beats_per_measure = int(time_sig.split('/')[0])
    chords = results['chords']
    duration = results['duration']
    
    # Calculate measure duration
    beat_duration = 60.0 / tempo  # seconds per beat
    measure_duration = beat_duration * beats_per_measure
    
    # Calculate total measures
    total_measures = int(duration / measure_duration) + 1
    
    output = []
    output.append("=" * 80)
    output.append(f"CHORD PROGRESSION - MEASURE VIEW")
    output.append("=" * 80)
    output.append(f"Tempo: {tempo:.1f} BPM | Time Signature: {time_sig}")
    output.append(f"Beat duration: {beat_duration:.3f}s | Measure duration: {measure_duration:.3f}s")
    output.append(f"Total measures: {total_measures}")
    output.append("=" * 80)
    output.append("")
    
    # Build measure grid
    chord_idx = 0
    for measure_start in range(0, total_measures, measures_per_line):
        measure_end = min(measure_start + measures_per_line, total_measures)
        
        # Header with measure numbers
        header = "Measure: "
        for m in range(measure_start, measure_end):
            header += f"{m+1:>12} "
        output.append(header)
        
        # Time markers
        times = "Time:    "
        for m in range(measure_start, measure_end):
            time_s = m * measure_duration
            times += f"{format_time(time_s):>12} "
        output.append(times)
        
        # Chord line
        chord_line = "Chords:  "
        for m in range(measure_start, measure_end):
            measure_time_start = m * measure_duration
            measure_time_end = (m + 1) * measure_duration
            
            # Find chords in this measure
            measure_chords = []
            while chord_idx < len(chords):
                chord = chords[chord_idx]
                chord_start = chord['start']
                chord_end = chord['end']
                
                # Check if chord overlaps with this measure
                if chord_end <= measure_time_start:
                    # Chord is before this measure
                    chord_idx += 1
                    continue
                elif chord_start >= measure_time_end:
                    # Chord is after this measure
                    break
                else:
                    # Chord overlaps with this measure
                    measure_chords.append(chord['name'])
                    if chord_end <= measure_time_end:
                        chord_idx += 1
                    else:
                        break
            
            # Format chord display
            if len(measure_chords) == 0:
                chord_display = "-"
            elif len(measure_chords) == 1:
                chord_display = measure_chords[0]
            else:
                # Multiple chords in measure - show first and count
                chord_display = f"{measure_chords[0]}+{len(measure_chords)-1}"
            
            chord_line += f"{chord_display:>12} "
        
        output.append(chord_line)
        output.append("")
        
        # Reset chord index for next line
        chord_idx = 0
    
    return "\n".join(output)

def create_beat_grid(results: Dict, beats_per_line: int = 16) -> str:
    """
    Create a beat-by-beat grid showing chords
    
    Args:
        results: Chord detection results
        beats_per_line: How many beats to show per line
    
    Returns:
        Formatted string with chord grid
    """
    tempo = results['tempo']
    chords = results['chords']
    duration = results['duration']
    
    beat_duration = 60.0 / tempo
    total_beats = int(duration / beat_duration) + 1
    
    output = []
    output.append("=" * 80)
    output.append(f"CHORD PROGRESSION - BEAT VIEW")
    output.append("=" * 80)
    output.append(f"Tempo: {tempo:.1f} BPM | Beat duration: {beat_duration:.3f}s")
    output.append(f"Total beats: {total_beats}")
    output.append("=" * 80)
    output.append("")
    
    # Build beat grid
    chord_idx = 0
    for beat_start in range(0, total_beats, beats_per_line):
        beat_end = min(beat_start + beats_per_line, total_beats)
        
        # Header with beat numbers
        header = "Beat:   "
        for b in range(beat_start, beat_end):
            header += f"{b+1:>6}"
        output.append(header)
        
        # Chord line
        chord_line = "Chord:  "
        for b in range(beat_start, beat_end):
            beat_time_start = b * beat_duration
            beat_time_end = (b + 1) * beat_duration
            
            # Find chord at this beat
            current_chord = "-"
            for chord in chords:
                if chord['start'] <= beat_time_start < chord['end']:
                    current_chord = chord['name'][:5]  # Truncate to 5 chars
                    break
            
            chord_line += f"{current_chord:>6}"
        
        output.append(chord_line)
        output.append("")
    
    return "\n".join(output)

def create_detailed_list(results: Dict, max_chords: int = 100) -> str:
    """
    Create detailed list of first N chords with timing
    
    Args:
        results: Chord detection results
        max_chords: Maximum number of chords to show
    
    Returns:
        Formatted string with chord list
    """
    tempo = results['tempo']
    chords = results['chords']
    beat_duration = 60.0 / tempo
    
    output = []
    output.append("=" * 80)
    output.append(f"DETAILED CHORD LIST (first {max_chords} chords)")
    output.append("=" * 80)
    output.append(f"{'#':>4} {'Chord':>10} {'Start':>12} {'End':>12} {'Duration':>10} {'Beat':>8} {'Conf':>6}")
    output.append("-" * 80)
    
    for i, chord in enumerate(chords[:max_chords], 1):
        start_beat = chord['start'] / beat_duration
        duration_beats = chord['duration'] / beat_duration
        
        output.append(
            f"{i:>4} {chord['name']:>10} "
            f"{format_time(chord['start']):>12} "
            f"{format_time(chord['end']):>12} "
            f"{chord['duration']:>9.2f}s "
            f"{start_beat:>7.1f} "
            f"{chord['confidence']:>6.3f}"
        )
    
    if len(chords) > max_chords:
        output.append(f"\n... and {len(chords) - max_chords} more chords")
    
    return "\n".join(output)

def main():
    if len(sys.argv) < 2:
        print("Usage: python visualize_chords.py <results.json>")
        print("Example: python visualize_chords.py /tmp/thats_what_i_like_results.json")
        sys.exit(1)
    
    json_path = sys.argv[1]
    
    print(f"Loading results from: {json_path}")
    results = load_results(json_path)
    
    print(f"\nSong: {results.get('audio_file', 'Unknown')}")
    print(f"Duration: {results['duration']:.1f}s")
    print(f"Tempo: {results['tempo']:.1f} BPM")
    print(f"Key: {results['key']} {results['scale']}")
    print(f"Total chords: {len(results['chords'])}")
    print("")
    
    # Show detailed list of first 50 chords
    print(create_detailed_list(results, max_chords=50))
    print("\n")
    
    # Show beat grid for first 64 beats
    print(create_beat_grid(results, beats_per_line=16))
    print("\n")
    
    # Show measure grid for first 32 measures
    print(create_measure_grid(results, measures_per_line=4))

if __name__ == "__main__":
    main()

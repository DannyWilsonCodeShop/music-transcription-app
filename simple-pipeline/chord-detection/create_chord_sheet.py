#!/usr/bin/env python3
"""
Create a measure-based chord sheet from detection results
Shows chords organized by measures, not individual beats
"""

import json
import sys
from typing import List, Dict, Tuple

def load_results(json_path: str) -> Dict:
    """Load chord detection results from JSON"""
    with open(json_path, 'r') as f:
        return json.load(f)

def format_time(seconds: float) -> str:
    """Format seconds as MM:SS"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"

def get_chords_in_measure(
    chords: List[Dict],
    measure_start: float,
    measure_end: float
) -> List[Tuple[str, float, float]]:
    """
    Get all chords that occur within a measure
    
    Returns:
        List of (chord_name, start_in_measure, duration) tuples
    """
    measure_chords = []
    
    for chord in chords:
        chord_start = chord['start']
        chord_end = chord['end']
        
        # Skip chords that end before this measure
        if chord_end <= measure_start:
            continue
        
        # Stop when we reach chords that start after this measure
        if chord_start >= measure_end:
            break
        
        # Calculate overlap with measure
        overlap_start = max(chord_start, measure_start)
        overlap_end = min(chord_end, measure_end)
        overlap_duration = overlap_end - overlap_start
        
        # Position within measure (0.0 to 1.0)
        position_in_measure = (overlap_start - measure_start) / (measure_end - measure_start)
        
        measure_chords.append((
            chord['name'],
            position_in_measure,
            overlap_duration
        ))
    
    return measure_chords

def create_ascii_chord_sheet(results: Dict, measures_per_line: int = 4) -> str:
    """
    Create ASCII art chord sheet organized by measures
    
    Args:
        results: Chord detection results
        measures_per_line: How many measures per line (default 4)
    
    Returns:
        Formatted string with chord sheet
    """
    tempo = results['tempo']
    time_sig = results.get('time_signature', '4/4')
    beats_per_measure = int(time_sig.split('/')[0])
    chords = results['chords']
    duration = results['duration']
    key = results['key']
    scale = results['scale']
    
    # Calculate measure duration
    beat_duration = 60.0 / tempo  # seconds per beat
    measure_duration = beat_duration * beats_per_measure
    
    # Calculate total measures
    total_measures = int(duration / measure_duration) + 1
    
    output = []
    output.append("=" * 100)
    output.append(f"CHORD SHEET - {key} {scale}")
    output.append("=" * 100)
    output.append(f"Tempo: {tempo:.0f} BPM | Time Signature: {time_sig} | Total Measures: {total_measures}")
    output.append("=" * 100)
    output.append("")
    
    # Build measure-by-measure sheet
    for line_start in range(0, total_measures, measures_per_line):
        line_end = min(line_start + measures_per_line, total_measures)
        
        # Measure numbers
        measure_line = ""
        for m in range(line_start, line_end):
            measure_line += f"| {m+1:^22} "
        measure_line += "|"
        output.append(measure_line)
        
        # Time markers
        time_line = ""
        for m in range(line_start, line_end):
            time_s = m * measure_duration
            time_line += f"| {format_time(time_s):^22} "
        time_line += "|"
        output.append(time_line)
        
        # Separator
        separator = ""
        for m in range(line_start, line_end):
            separator += "|" + "-" * 23 + " "
        separator += "|"
        output.append(separator)
        
        # Chord line
        chord_line = ""
        for m in range(line_start, line_end):
            measure_time_start = m * measure_duration
            measure_time_end = (m + 1) * measure_duration
            
            # Get chords in this measure
            measure_chords = get_chords_in_measure(
                chords,
                measure_time_start,
                measure_time_end
            )
            
            # Format chord display
            if len(measure_chords) == 0:
                chord_display = "-"
            elif len(measure_chords) == 1:
                # Single chord for whole measure
                chord_display = measure_chords[0][0]
            elif len(measure_chords) == 2:
                # Two chords - show both
                chord_display = f"{measure_chords[0][0]} {measure_chords[1][0]}"
            elif len(measure_chords) == 3:
                # Three chords - show all
                chord_display = f"{measure_chords[0][0]} {measure_chords[1][0]} {measure_chords[2][0]}"
            elif len(measure_chords) == 4:
                # Four chords - one per beat
                chord_display = f"{measure_chords[0][0]} {measure_chords[1][0]} {measure_chords[2][0]} {measure_chords[3][0]}"
            else:
                # Many chords - show first few and count
                first_three = " ".join([c[0] for c in measure_chords[:3]])
                chord_display = f"{first_three} +{len(measure_chords)-3}"
            
            chord_line += f"| {chord_display:^22} "
        
        chord_line += "|"
        output.append(chord_line)
        
        # Blank line between systems
        output.append("")
    
    return "\n".join(output)

def create_compact_chord_sheet(results: Dict, measures_per_line: int = 8) -> str:
    """
    Create compact chord sheet with one chord per measure (most prominent)
    
    Args:
        results: Chord detection results
        measures_per_line: How many measures per line (default 8)
    
    Returns:
        Formatted string with compact chord sheet
    """
    tempo = results['tempo']
    time_sig = results.get('time_signature', '4/4')
    beats_per_measure = int(time_sig.split('/')[0])
    chords = results['chords']
    duration = results['duration']
    key = results['key']
    scale = results['scale']
    
    # Calculate measure duration
    beat_duration = 60.0 / tempo
    measure_duration = beat_duration * beats_per_measure
    
    # Calculate total measures
    total_measures = int(duration / measure_duration) + 1
    
    output = []
    output.append("=" * 100)
    output.append(f"COMPACT CHORD SHEET - {key} {scale}")
    output.append("=" * 100)
    output.append(f"Tempo: {tempo:.0f} BPM | Time: {time_sig} | Showing primary chord per measure")
    output.append("=" * 100)
    output.append("")
    
    # Build compact sheet
    for line_start in range(0, total_measures, measures_per_line):
        line_end = min(line_start + measures_per_line, total_measures)
        
        # Measure numbers
        measure_line = ""
        for m in range(line_start, line_end):
            measure_line += f"{m+1:>4} "
        output.append("M:  " + measure_line)
        
        # Chord line
        chord_line = ""
        for m in range(line_start, line_end):
            measure_time_start = m * measure_duration
            measure_time_end = (m + 1) * measure_duration
            
            # Get chords in this measure
            measure_chords = get_chords_in_measure(
                chords,
                measure_time_start,
                measure_time_end
            )
            
            # Find longest chord (most prominent)
            if len(measure_chords) == 0:
                primary_chord = "-"
            else:
                # Sort by duration, take longest
                longest = max(measure_chords, key=lambda x: x[2])
                primary_chord = longest[0]
            
            chord_line += f"{primary_chord:>4} "
        
        output.append("C:  " + chord_line)
        output.append("")
    
    return "\n".join(output)

def create_detailed_measure_list(results: Dict, max_measures: int = 32) -> str:
    """
    Create detailed list of measures with all chords
    
    Args:
        results: Chord detection results
        max_measures: Maximum measures to show
    
    Returns:
        Formatted string with detailed measure list
    """
    tempo = results['tempo']
    time_sig = results.get('time_signature', '4/4')
    beats_per_measure = int(time_sig.split('/')[0])
    chords = results['chords']
    duration = results['duration']
    
    beat_duration = 60.0 / tempo
    measure_duration = beat_duration * beats_per_measure
    total_measures = int(duration / measure_duration) + 1
    
    output = []
    output.append("=" * 100)
    output.append(f"DETAILED MEASURE LIST (first {max_measures} measures)")
    output.append("=" * 100)
    output.append(f"{'Measure':>8} {'Time':>8} {'Chords in Measure'}")
    output.append("-" * 100)
    
    for m in range(min(max_measures, total_measures)):
        measure_time_start = m * measure_duration
        measure_time_end = (m + 1) * measure_duration
        
        # Get chords in this measure
        measure_chords = get_chords_in_measure(
            chords,
            measure_time_start,
            measure_time_end
        )
        
        # Format chord list
        if len(measure_chords) == 0:
            chord_list = "-"
        else:
            chord_list = ", ".join([f"{c[0]}" for c in measure_chords])
        
        output.append(f"{m+1:>8} {format_time(measure_time_start):>8} {chord_list}")
    
    if total_measures > max_measures:
        output.append(f"\n... and {total_measures - max_measures} more measures")
    
    return "\n".join(output)

def main():
    if len(sys.argv) < 2:
        print("Usage: python create_chord_sheet.py <results.json>")
        print("Example: python create_chord_sheet.py /tmp/thats_what_i_like_results.json")
        sys.exit(1)
    
    json_path = sys.argv[1]
    
    print(f"Loading results from: {json_path}\n")
    results = load_results(json_path)
    
    # Show compact sheet
    print(create_compact_chord_sheet(results, measures_per_line=8))
    print("\n")
    
    # Show detailed sheet
    print(create_ascii_chord_sheet(results, measures_per_line=4))
    print("\n")
    
    # Show detailed measure list
    print(create_detailed_measure_list(results, max_measures=32))

if __name__ == "__main__":
    main()

"""
Section detection and labeling for lyrics-chord alignment
"""

def create_chord_fingerprint(chords):
    """
    Generate pattern signature for chord progression
    
    Args:
        chords: List of chord objects with 'chord' and 'measure' fields
    
    Returns:
        Tuple representing the chord pattern (chord roots and relative positions)
    """
    if not chords:
        return tuple()
    
    # Use chord names and their position within a 4-measure cycle
    # This helps identify repeated patterns regardless of absolute measure numbers
    fingerprint = []
    for chord in chords:
        chord_name = chord.get('chord', '')
        measure = chord.get('measure', 0)
        # Normalize to 4-measure cycle for pattern matching
        relative_measure = measure % 4
        fingerprint.append((chord_name, relative_measure))
    
    return tuple(fingerprint)


def is_verse_like(chords, lines):
    """
    Heuristic for verse detection
    
    Verses typically have:
    - More lyrics (wordy)
    - Simpler chord progressions
    - Narrative content
    
    Args:
        chords: List of chord objects for this section
        lines: List of line objects for this section
    
    Returns:
        Boolean indicating if section is verse-like
    """
    if not lines:
        return False
    
    # Calculate average words per line
    total_words = sum(len(line.get('words', [])) for line in lines)
    avg_words_per_line = total_words / max(len(lines), 1)
    
    # Verses tend to be wordy (more than 8 words per line on average)
    return avg_words_per_line > 8


def is_chorus_like(chords, lines):
    """
    Heuristic for chorus detection
    
    Choruses typically have:
    - Repetitive lyrics
    - Stronger/more memorable chord progressions
    - Hook phrases
    
    Args:
        chords: List of chord objects for this section
        lines: List of line objects for this section
    
    Returns:
        Boolean indicating if section is chorus-like
    """
    if not lines:
        return False
    
    # Check for repeated phrases within the section
    lyrics_texts = [line.get('lyrics', '') for line in lines]
    unique_texts = set(lyrics_texts)
    
    # If there's repetition within the section, it's likely a chorus
    has_repetition = len(lyrics_texts) != len(unique_texts)
    
    # Choruses also tend to have fewer words per line (more punchy)
    total_words = sum(len(line.get('words', [])) for line in lines)
    avg_words_per_line = total_words / max(len(lines), 1)
    is_concise = avg_words_per_line < 8
    
    return has_repetition or is_concise


def is_bridge_like(chords, lines):
    """
    Heuristic for bridge detection
    
    Bridges typically have:
    - Different chord progressions from verse/chorus
    - Appear later in the song
    - Often only once
    
    Args:
        chords: List of chord objects for this section
        lines: List of line objects for this section
    
    Returns:
        Boolean indicating if section is bridge-like
    """
    # This is a simplified heuristic
    # In practice, bridge detection requires comparing against
    # verse and chorus patterns, which is done in detect_and_label_sections
    
    # For now, return False - the main function will handle bridge detection
    # by checking if a section doesn't match verse or chorus patterns
    return False


def format_instrumental_section(chords, measures_per_line=4):
    """
    Format instrumental section as chord grid
    
    Args:
        chords: List of chord objects for instrumental section
        measures_per_line: Number of measures to display per line (default: 4)
    
    Returns:
        List of line objects formatted for instrumental display
    
    Example output:
        [Instrumental]
        M17: Am7  | Dm7  | G7   | Cmaj7 |
        M21: Fmaj7| Bm7♭5| E7   | Am7   |
    """
    if not chords:
        return []
    
    lines = []
    
    # Group chords by measure
    chords_by_measure = {}
    for chord in chords:
        measure = chord.get('measure', 1)
        if measure not in chords_by_measure:
            chords_by_measure[measure] = []
        chords_by_measure[measure].append(chord)
    
    # Get sorted measure numbers
    measures = sorted(chords_by_measure.keys())
    
    # Group into lines of N measures each
    for i in range(0, len(measures), measures_per_line):
        line_measures = measures[i:i + measures_per_line]
        
        if not line_measures:
            continue
        
        measure_start = line_measures[0]
        measure_end = line_measures[-1]
        
        # Build chord grid string
        chord_parts = []
        for measure in line_measures:
            measure_chords = chords_by_measure[measure]
            # Take the first chord in each measure for grid display
            chord_name = measure_chords[0].get('chord', '?')
            # Pad to 6 characters for alignment
            chord_parts.append(f"{chord_name:6s}")
        
        chord_grid = ' | '.join(chord_parts) + ' |'
        lyrics_text = f"M{measure_start}: {chord_grid}"
        
        lines.append({
            'measureStart': measure_start,
            'measureEnd': measure_end,
            'lyrics': lyrics_text,
            'words': [],
            'chords': [c for m in line_measures for c in chords_by_measure[m]],
            'isInstrumental': True,
            'start': chords[0].get('start', 0.0),
            'end': chords[-1].get('end', 0.0)
        })
    
    return lines


def get_lines_in_range(lines, start_time, end_time):
    """
    Get lines that fall within a time range
    
    Args:
        lines: List of line objects with 'start' and 'end' timestamps
        start_time: Start of time range (seconds)
        end_time: End of time range (seconds)
    
    Returns:
        List of lines within the time range
    """
    result = []
    for line in lines:
        line_start = line.get('start', 0.0)
        line_end = line.get('end', 0.0)
        
        # Check if line overlaps with the time range
        if line_start <= end_time and line_end >= start_time:
            result.append(line)
    
    return result


def get_chords_in_range(chords, start_time, end_time):
    """
    Get chords that fall within a time range
    
    Args:
        chords: List of chord objects with 'start' timestamps
        start_time: Start of time range (seconds)
        end_time: End of time range (seconds)
    
    Returns:
        List of chords within the time range
    """
    return [c for c in chords if start_time <= c.get('start', 0.0) <= end_time]


def get_song_duration(chords):
    """
    Get total song duration from chord data
    
    Args:
        chords: List of chord objects
    
    Returns:
        Duration in seconds
    """
    if not chords:
        return 0.0
    
    # Find the latest chord end time
    max_end = max(c.get('end', c.get('start', 0.0)) for c in chords)
    return max_end


def detect_and_label_sections(song_structure, lines, chords):
    """
    Identify song sections and assign appropriate labels
    
    Strategy:
    1. Use existing song_structure from chord detection
    2. Correlate with lyric line boundaries
    3. Detect repeated sections (same chords + similar lyrics)
    4. Assign standard labels (Verse 1, Chorus, Bridge, etc.)
    5. Handle instrumental sections (Intro, Solo, Outro)
    
    Args:
        song_structure: List of detected sections from chord analysis
        lines: Grouped lyric lines
        chords: Chord progression
    
    Returns:
        List of sections with labels and line groupings
    """
    import logging
    logger = logging.getLogger()
    
    sections = []
    verse_count = 0
    chorus_count = 0
    bridge_count = 0
    
    # Track repeated sections for numbering
    section_fingerprints = {}  # chord pattern -> section type
    
    song_duration = get_song_duration(chords)
    
    for struct_section in song_structure:
        section_start = struct_section.get('start', 0.0)
        section_end = struct_section.get('end', 0.0)
        
        # Get lines that fall within this section
        section_lines = get_lines_in_range(lines, section_start, section_end)
        
        # Get chord progression for this section
        section_chords = get_chords_in_range(chords, section_start, section_end)
        
        # Create fingerprint (chord progression pattern)
        fingerprint = create_chord_fingerprint(section_chords)
        
        # Determine section type
        has_lyrics = any(
            not line.get('isInstrumental', False) 
            for line in section_lines 
            if line.get('start', 0.0) >= section_start and line.get('end', 0.0) <= section_end
        )
        
        # Check if section has no lines after filtering
        if not section_lines or len(section_lines) == 0:
            logger.warning(f"Empty section detected at {section_start:.2f}s-{section_end:.2f}s (measures {struct_section.get('measureStart', '?')}-{struct_section.get('measureEnd', '?')})")
            
            # Create placeholder instrumental section
            if section_chords:
                section_lines = format_instrumental_section(section_chords)
                logger.info(f"  Created placeholder instrumental section with {len(section_lines)} lines")
            else:
                # No chords either - create minimal placeholder
                logger.warning(f"  No chords found for empty section, creating minimal placeholder")
                section_lines = [{
                    'measureStart': struct_section.get('measureStart', 1),
                    'measureEnd': struct_section.get('measureEnd', 1),
                    'lyrics': '[No data]',
                    'words': [],
                    'chords': [],
                    'isInstrumental': True,
                    'start': section_start,
                    'end': section_end
                }]
            
            has_lyrics = False
        
        if not has_lyrics:
            # Instrumental section
            if section_start < 5.0:
                label = 'Intro'
            elif section_end > song_duration - 10.0:
                label = 'Outro'
            else:
                label = 'Instrumental'
            
            # Format instrumental section with chord grid (if not already done)
            if section_chords and not any(line.get('isInstrumental', False) for line in section_lines):
                section_lines = format_instrumental_section(section_chords)
        else:
            # Section with lyrics - use existing label or detect
            base_label = struct_section.get('label', 'Section')
            
            # Check if this is a repeated section
            if fingerprint in section_fingerprints:
                # Repeated section - increment counter
                section_type = section_fingerprints[fingerprint]
                if section_type == 'Verse':
                    verse_count += 1
                    label = f'Verse {verse_count}'
                elif section_type == 'Chorus':
                    chorus_count += 1
                    # First chorus is just "Chorus", subsequent ones are numbered
                    label = 'Chorus' if chorus_count == 1 else f'Chorus {chorus_count}'
                else:
                    label = section_type
            else:
                # New section - classify
                if base_label == 'Verse' or is_verse_like(section_chords, section_lines):
                    verse_count += 1
                    label = f'Verse {verse_count}'
                    section_fingerprints[fingerprint] = 'Verse'
                elif base_label == 'Chorus' or is_chorus_like(section_chords, section_lines):
                    chorus_count += 1
                    label = 'Chorus'
                    section_fingerprints[fingerprint] = 'Chorus'
                elif base_label == 'Bridge' or is_bridge_like(section_chords, section_lines):
                    bridge_count += 1
                    label = 'Bridge'
                    section_fingerprints[fingerprint] = 'Bridge'
                else:
                    # Unknown section type - use base label or default
                    label = base_label if base_label != 'Section' else f'Section {len(sections) + 1}'
        
        sections.append({
            'label': label,
            'measureStart': struct_section.get('measureStart', 1),
            'measureEnd': struct_section.get('measureEnd', 1),
            'lines': section_lines,
            'start': section_start,
            'end': section_end
        })
    
    return sections

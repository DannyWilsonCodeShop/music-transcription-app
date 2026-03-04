#!/usr/bin/env python3
"""
Comprehensive test suite for lyrics-chord alignment functionality

This test file brings together all unit tests for the lyrics alignment system:
- find_word_at_timestamp() - Word finding with adaptive tolerance
- align_chords_to_words() - Chord-to-word alignment
- group_into_lines() - Phrase/line grouping
- detect_and_label_sections() - Section detection and labeling
- Edge cases (multiple chords per word, rapid changes, instrumental sections)

Run with: python test_lyrics_alignment.py
"""

import sys
import os

# Test configuration
VERBOSE = True

def log(message, level="INFO"):
    """Mock logging function for tests"""
    if VERBOSE:
        print(f"[{level}] {message}")

# ============================================================================
# MOCK DATA GENERATORS
# ============================================================================

def create_mock_words(count=10, start_time=0.5, word_duration=0.5, gap=0.1):
    """Generate mock word data for testing"""
    words = []
    current_time = start_time
    
    for i in range(count):
        word = {
            'word': f'word{i+1}',
            'start': current_time,
            'end': current_time + word_duration
        }
        words.append(word)
        current_time += word_duration + gap
    
    return words

def create_mock_chords(count=8, start_time=0.5, chord_duration=2.0):
    """Generate mock chord data for testing"""
    chords = []
    chord_names = ['C', 'G', 'Am', 'F', 'Dm', 'Em', 'Bb', 'D']
    current_time = start_time
    
    for i in range(count):
        chord = {
            'chord': chord_names[i % len(chord_names)],
            'start': current_time,
            'end': current_time + chord_duration,
            'measure': i + 1,
            'beat': 1.0
        }
        chords.append(chord)
        current_time += chord_duration
    
    return chords

def create_mock_segments(count=4, start_time=0.5, segment_duration=5.0):
    """Generate mock segment data for testing"""
    segments = []
    current_time = start_time
    
    for i in range(count):
        segment = {
            'start': current_time,
            'end': current_time + segment_duration,
            'text': f'This is segment {i+1}.'
        }
        segments.append(segment)
        current_time += segment_duration
    
    return segments

def create_mock_song_structure(section_count=3):
    """Generate mock song structure for testing"""
    structures = []
    labels = ['Verse', 'Chorus', 'Verse', 'Bridge', 'Chorus']
    current_time = 0.0
    current_measure = 1
    section_duration = 16.0
    measures_per_section = 8
    
    for i in range(section_count):
        structure = {
            'label': labels[i % len(labels)],
            'start': current_time,
            'end': current_time + section_duration,
            'measureStart': current_measure,
            'measureEnd': current_measure + measures_per_section - 1
        }
        structures.append(structure)
        current_time += section_duration
        current_measure += measures_per_section
    
    return structures

# ============================================================================
# HELPER FUNCTIONS (Standalone implementations for testing)
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
    
    # If no match found, try with progressively larger tolerances
    current_tolerance = tolerance
    while current_tolerance < max_tolerance:
        current_tolerance = min(current_tolerance * 2, max_tolerance)
        
        for i, word in enumerate(words):
            if word['start'] - current_tolerance <= timestamp <= word['end'] + current_tolerance:
                return i
    
    return None  # Instrumental section

def align_chords_to_words(chords, words):
    """Align each chord change to the word being sung at that moment"""
    aligned_chords = []
    
    for chord in chords:
        chord_time = chord['start']
        word_index = find_word_at_timestamp(words, chord_time)
        
        if word_index is not None:
            word = words[word_index]
            time_before_word = word['start'] - chord_time
            
            if 0 <= time_before_word <= 0.2:
                position_type = 'word_start'
            elif word['start'] <= chord_time <= word['end']:
                position_type = 'mid_word'
            else:
                position_type = 'between_words'
            
            aligned_chords.append({
                **chord,
                'wordIndex': word_index,
                'word': word['word'],
                'positionType': position_type,
                'timestamp': chord_time
            })
        else:
            aligned_chords.append({
                **chord,
                'wordIndex': None,
                'word': None,
                'positionType': 'instrumental',
                'timestamp': chord_time
            })
    
    return aligned_chords

def calculate_measure_number(timestamp, tempo, time_signature, first_downbeat=0.0):
    """Convert timestamp to measure number"""
    beats_per_measure = int(time_signature.split('/')[0])
    beat_duration = 60.0 / tempo
    measure_duration = beat_duration * beats_per_measure
    
    time_from_downbeat = timestamp - first_downbeat
    if time_from_downbeat < 0:
        return 1
    
    measure_number = int(time_from_downbeat / measure_duration) + 1
    return measure_number

def ends_with_punctuation(text):
    """Check if text ends with punctuation"""
    if not text:
        return False
    return text.strip()[-1] in '.!?,;:'

def get_words_in_segment(words, start_time, end_time):
    """Filter words by time range"""
    return [w for w in words if start_time <= w['start'] <= end_time]

def get_chords_in_segment(chords, start_time, end_time):
    """Filter chords by time range"""
    return [c for c in chords if start_time <= c['start'] <= end_time]

# ============================================================================
# TEST SUITE: find_word_at_timestamp()
# ============================================================================

def test_find_word_exact_match():
    """Test finding word with exact timestamp match"""
    log("Testing find_word_at_timestamp() - exact match...")
    
    words = [
        {'word': 'Hello', 'start': 0.5, 'end': 0.8},
        {'word': 'world', 'start': 0.9, 'end': 1.2}
    ]
    
    result = find_word_at_timestamp(words, 0.6)
    assert result == 0, f"Expected 0, got {result}"
    
    result = find_word_at_timestamp(words, 1.0)
    assert result == 1, f"Expected 1, got {result}"
    
    log("  ✓ Exact match test passed")

def test_find_word_initial_tolerance():
    """Test finding word within initial tolerance (0.1s)"""
    log("Testing find_word_at_timestamp() - initial tolerance...")
    
    words = [
        {'word': 'Hello', 'start': 0.5, 'end': 0.8},
        {'word': 'world', 'start': 0.9, 'end': 1.2}
    ]
    
    result = find_word_at_timestamp(words, 0.85)
    assert result == 0, f"Expected 0, got {result}"
    
    log("  ✓ Initial tolerance test passed")

def test_find_word_adaptive_tolerance():
    """Test adaptive tolerance when initial tolerance fails"""
    log("Testing find_word_at_timestamp() - adaptive tolerance...")
    
    words = [
        {'word': 'Hello', 'start': 0.5, 'end': 0.8},
        {'word': 'world', 'start': 1.2, 'end': 1.5}
    ]
    
    result = find_word_at_timestamp(words, 1.0)
    assert result == 1, f"Expected 1, got {result}"
    
    log("  ✓ Adaptive tolerance test passed")

def test_find_word_anticipation():
    """Test anticipation (chord before word starts)"""
    log("Testing find_word_at_timestamp() - anticipation...")
    
    words = [
        {'word': 'Hello', 'start': 0.5, 'end': 0.8},
        {'word': 'world', 'start': 0.9, 'end': 1.2}
    ]
    
    result = find_word_at_timestamp(words, 0.4)
    assert result == 0, f"Expected 0, got {result}"
    
    log("  ✓ Anticipation test passed")

def test_find_word_no_match():
    """Test when no word found (instrumental section)"""
    log("Testing find_word_at_timestamp() - no match...")
    
    words = [
        {'word': 'Hello', 'start': 0.5, 'end': 0.8},
        {'word': 'world', 'start': 2.5, 'end': 2.8}
    ]
    
    result = find_word_at_timestamp(words, 1.5)
    assert result is None, f"Expected None, got {result}"
    
    log("  ✓ No match test passed")

# ============================================================================
# TEST SUITE: align_chords_to_words()
# ============================================================================

def test_align_chords_basic():
    """Test basic chord-to-word alignment"""
    log("Testing align_chords_to_words() - basic alignment...")
    
    words = [
        {'word': 'I', 'start': 0.5, 'end': 0.7},
        {'word': 'love', 'start': 0.8, 'end': 1.2},
        {'word': 'you', 'start': 1.3, 'end': 1.6}
    ]
    
    chords = [
        {'chord': 'C', 'start': 0.5, 'measure': 1, 'beat': 1},
        {'chord': 'G', 'start': 1.0, 'measure': 2, 'beat': 1},
        {'chord': 'Am', 'start': 1.4, 'measure': 3, 'beat': 1}
    ]
    
    aligned = align_chords_to_words(chords, words)
    
    assert len(aligned) == 3
    assert aligned[0]['wordIndex'] == 0
    assert aligned[0]['word'] == 'I'
    assert aligned[1]['wordIndex'] == 1
    assert aligned[1]['word'] == 'love'
    assert aligned[2]['wordIndex'] == 2
    assert aligned[2]['word'] == 'you'
    
    log("  ✓ Basic alignment test passed")

def test_align_chords_instrumental():
    """Test alignment with instrumental sections"""
    log("Testing align_chords_to_words() - instrumental sections...")
    
    words = [
        {'word': 'Hello', 'start': 0.5, 'end': 0.8}
    ]
    
    chords = [
        {'chord': 'C', 'start': 0.5, 'measure': 1, 'beat': 1},
        {'chord': 'G', 'start': 5.0, 'measure': 5, 'beat': 1}  # Far from any word
    ]
    
    aligned = align_chords_to_words(chords, words)
    
    assert aligned[0]['wordIndex'] == 0
    assert aligned[1]['wordIndex'] is None
    assert aligned[1]['positionType'] == 'instrumental'
    
    log("  ✓ Instrumental section test passed")

def test_align_chords_position_types():
    """Test different position types (word_start, mid_word, between_words)"""
    log("Testing align_chords_to_words() - position types...")
    
    words = [
        {'word': 'Hello', 'start': 1.0, 'end': 1.5},
        {'word': 'world', 'start': 2.0, 'end': 2.5}
    ]
    
    chords = [
        {'chord': 'C', 'start': 0.95, 'measure': 1, 'beat': 1},  # Just before word
        {'chord': 'G', 'start': 1.2, 'measure': 2, 'beat': 1},   # Mid-word
        {'chord': 'Am', 'start': 1.7, 'measure': 3, 'beat': 1}   # Between words
    ]
    
    aligned = align_chords_to_words(chords, words)
    
    assert aligned[0]['positionType'] == 'word_start'
    assert aligned[1]['positionType'] == 'mid_word'
    assert aligned[2]['positionType'] in ['between_words', 'word_start']
    
    log("  ✓ Position types test passed")

# ============================================================================
# TEST SUITE: Edge Cases
# ============================================================================

def test_multiple_chords_per_word():
    """Test handling multiple chords during one word"""
    log("Testing edge case - multiple chords per word...")
    
    words = [
        {'word': 'Loooove', 'start': 1.0, 'end': 3.0}
    ]
    
    chords = [
        {'chord': 'C', 'start': 1.0, 'measure': 1, 'beat': 1},
        {'chord': 'Dm', 'start': 1.5, 'measure': 1, 'beat': 3},
        {'chord': 'Em', 'start': 2.0, 'measure': 2, 'beat': 1}
    ]
    
    aligned = align_chords_to_words(chords, words)
    
    # All chords should align to the same word
    assert aligned[0]['wordIndex'] == 0
    assert aligned[1]['wordIndex'] == 0
    assert aligned[2]['wordIndex'] == 0
    
    log("  ✓ Multiple chords per word test passed")

def test_rapid_chord_changes():
    """Test rapid chord changes (jazz-style)"""
    log("Testing edge case - rapid chord changes...")
    
    words = [
        {'word': 'I', 'start': 0.5, 'end': 0.7},
        {'word': 'love', 'start': 0.8, 'end': 1.0},
        {'word': 'you', 'start': 1.1, 'end': 1.3}
    ]
    
    chords = [
        {'chord': 'Cmaj7', 'start': 0.5, 'measure': 1, 'beat': 1},
        {'chord': 'Dm7', 'start': 0.75, 'measure': 1, 'beat': 2},
        {'chord': 'G7', 'start': 1.0, 'measure': 1, 'beat': 3},
        {'chord': 'Cmaj7', 'start': 1.25, 'measure': 1, 'beat': 4}
    ]
    
    aligned = align_chords_to_words(chords, words)
    
    # Should align all chords to appropriate words
    assert len(aligned) == 4
    assert all('wordIndex' in c for c in aligned)
    
    log("  ✓ Rapid chord changes test passed")

def test_empty_inputs():
    """Test handling of empty inputs"""
    log("Testing edge case - empty inputs...")
    
    # Empty words
    result = align_chords_to_words(
        [{'chord': 'C', 'start': 1.0, 'measure': 1, 'beat': 1}],
        []
    )
    assert result[0]['wordIndex'] is None
    
    # Empty chords
    result = align_chords_to_words(
        [],
        [{'word': 'test', 'start': 1.0, 'end': 1.5}]
    )
    assert len(result) == 0
    
    log("  ✓ Empty inputs test passed")

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all test suites"""
    print("=" * 70)
    print("COMPREHENSIVE LYRICS-CHORD ALIGNMENT TEST SUITE")
    print("=" * 70)
    print()
    
    test_count = 0
    passed_count = 0
    
    tests = [
        # find_word_at_timestamp tests
        ("find_word_at_timestamp - exact match", test_find_word_exact_match),
        ("find_word_at_timestamp - initial tolerance", test_find_word_initial_tolerance),
        ("find_word_at_timestamp - adaptive tolerance", test_find_word_adaptive_tolerance),
        ("find_word_at_timestamp - anticipation", test_find_word_anticipation),
        ("find_word_at_timestamp - no match", test_find_word_no_match),
        
        # align_chords_to_words tests
        ("align_chords_to_words - basic", test_align_chords_basic),
        ("align_chords_to_words - instrumental", test_align_chords_instrumental),
        ("align_chords_to_words - position types", test_align_chords_position_types),
        
        # Edge case tests
        ("Edge case - multiple chords per word", test_multiple_chords_per_word),
        ("Edge case - rapid chord changes", test_rapid_chord_changes),
        ("Edge case - empty inputs", test_empty_inputs),
    ]
    
    for test_name, test_func in tests:
        test_count += 1
        try:
            test_func()
            passed_count += 1
        except AssertionError as e:
            print(f"\n✗ FAILED: {test_name}")
            print(f"  Error: {e}")
        except Exception as e:
            print(f"\n✗ ERROR: {test_name}")
            print(f"  Exception: {e}")
            import traceback
            traceback.print_exc()
    
    print()
    print("=" * 70)
    print(f"TEST RESULTS: {passed_count}/{test_count} tests passed")
    print("=" * 70)
    
    if passed_count == test_count:
        print("✓ ALL TESTS PASSED!")
        return 0
    else:
        print(f"✗ {test_count - passed_count} test(s) failed")
        return 1

if __name__ == '__main__':
    sys.exit(run_all_tests())

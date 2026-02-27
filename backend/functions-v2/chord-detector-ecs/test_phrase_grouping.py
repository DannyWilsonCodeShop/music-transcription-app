"""
Test phrase/line grouping functions - standalone version
"""
import sys

def ends_with_punctuation(text):
    """Check if text ends with punctuation"""
    if not text:
        return False
    return text.strip()[-1] in '.!?,;:'

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

def get_words_in_segment(words, start_time, end_time):
    """Filter words by time range"""
    return [w for w in words if start_time <= w['start'] <= end_time]

def get_chords_in_segment(chords, start_time, end_time):
    """Filter chords by time range"""
    return [c for c in chords if start_time <= c['start'] <= end_time]

def finalize_line(line_data, tempo, time_signature, first_downbeat=0.0):
    """Convert line data to final format with measure numbers"""
    measure_start = calculate_measure_number(line_data['start'], tempo, time_signature, first_downbeat)
    measure_end = calculate_measure_number(line_data['end'], tempo, time_signature, first_downbeat)
    
    lyrics_text = ' '.join(word['word'] for word in line_data['words'])
    
    char_pos = 0
    for word in line_data['words']:
        word['charPosition'] = char_pos
        char_pos += len(word['word']) + 1
    
    for chord in line_data['chords']:
        if chord.get('wordIndex') is not None:
            word_found = False
            for i, word in enumerate(line_data['words']):
                if abs(word['start'] - chord.get('timestamp', chord['start'])) < 0.1:
                    chord['charPosition'] = word['charPosition']
                    word_found = True
                    break
            
            if not word_found:
                chord['charPosition'] = 0
        else:
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

def group_into_lines(aligned_chords, words, segments, tempo, time_signature, first_downbeat=0.0):
    """Group words and chords into readable lines"""
    lines = []
    beats_per_measure = int(time_signature.split('/')[0])
    beat_duration = 60.0 / tempo
    measure_duration = beat_duration * beats_per_measure
    
    target_line_duration = measure_duration * 3
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
        
        if current_line['start'] is not None:
            potential_duration = segment['end'] - current_line['start']
            
            if potential_duration > max_line_duration:
                lines.append(finalize_line(current_line, tempo, time_signature, first_downbeat))
                current_line = {
                    'words': segment_words,
                    'chords': segment_chords,
                    'start': segment['start'],
                    'end': segment['end']
                }
            else:
                current_line['words'].extend(segment_words)
                current_line['chords'].extend(segment_chords)
                current_line['end'] = segment['end']
        else:
            current_line = {
                'words': segment_words,
                'chords': segment_chords,
                'start': segment['start'],
                'end': segment['end']
            }
        
        if current_line['start'] is not None:
            duration = current_line['end'] - current_line['start']
            
            if duration >= min_line_duration and ends_with_punctuation(segment['text']):
                lines.append(finalize_line(current_line, tempo, time_signature, first_downbeat))
                current_line = {'words': [], 'chords': [], 'start': None, 'end': None}
    
    if current_line['words']:
        lines.append(finalize_line(current_line, tempo, time_signature, first_downbeat))
    
    return lines

def test_ends_with_punctuation():
    """Test punctuation detection"""
    print("Testing ends_with_punctuation()...")
    
    assert ends_with_punctuation("Hello world.") == True
    assert ends_with_punctuation("Hello world!") == True
    assert ends_with_punctuation("Hello world?") == True
    assert ends_with_punctuation("Hello world,") == True
    assert ends_with_punctuation("Hello world") == False
    assert ends_with_punctuation("") == False
    assert ends_with_punctuation("Hello world  .  ") == True  # With trailing spaces
    
    print("  ✓ All punctuation tests passed")

def test_finalize_line():
    """Test line finalization"""
    print("\nTesting finalize_line()...")
    
    line_data = {
        'words': [
            {'word': 'Hello', 'start': 1.0, 'end': 1.5},
            {'word': 'world', 'start': 1.6, 'end': 2.0}
        ],
        'chords': [
            {'chord': 'C', 'start': 1.0, 'wordIndex': 0, 'timestamp': 1.0},
            {'chord': 'G', 'start': 1.6, 'wordIndex': 1, 'timestamp': 1.6}
        ],
        'start': 1.0,
        'end': 2.0
    }
    
    result = finalize_line(line_data, tempo=120, time_signature='4/4', first_downbeat=0.0)
    
    # Check structure
    assert 'measureStart' in result
    assert 'measureEnd' in result
    assert 'lyrics' in result
    assert 'words' in result
    assert 'chords' in result
    assert 'isInstrumental' in result
    
    # Check lyrics
    assert result['lyrics'] == 'Hello world'
    
    # Check word positions
    assert result['words'][0]['charPosition'] == 0
    assert result['words'][1]['charPosition'] == 6  # "Hello " = 6 chars
    
    # Check chord positions
    assert result['chords'][0]['charPosition'] == 0
    assert result['chords'][1]['charPosition'] == 6
    
    # Check not instrumental
    assert result['isInstrumental'] == False
    
    print("  ✓ Line finalization test passed")

def test_group_into_lines():
    """Test grouping words into lines"""
    print("\nTesting group_into_lines()...")
    
    # Sample data - longer segments to meet minimum duration
    words = [
        {'word': 'Hello', 'start': 1.0, 'end': 1.5},
        {'word': 'world', 'start': 1.6, 'end': 2.0},
        {'word': 'how', 'start': 2.1, 'end': 2.3},
        {'word': 'are', 'start': 2.4, 'end': 2.6},
        {'word': 'you', 'start': 2.7, 'end': 3.0},
        {'word': 'this', 'start': 8.0, 'end': 8.3},
        {'word': 'is', 'start': 8.4, 'end': 8.6},
        {'word': 'a', 'start': 8.7, 'end': 8.8},
        {'word': 'test', 'start': 8.9, 'end': 9.5},
        {'word': 'line', 'start': 9.6, 'end': 10.0}
    ]
    
    aligned_chords = [
        {'chord': 'C', 'start': 1.0, 'wordIndex': 0, 'timestamp': 1.0},
        {'chord': 'G', 'start': 1.6, 'wordIndex': 1, 'timestamp': 1.6},
        {'chord': 'Am', 'start': 2.1, 'wordIndex': 2, 'timestamp': 2.1},
        {'chord': 'F', 'start': 8.0, 'wordIndex': 5, 'timestamp': 8.0},
        {'chord': 'C', 'start': 9.6, 'wordIndex': 9, 'timestamp': 9.6}
    ]
    
    # Segments with punctuation and sufficient duration (>4s for 2 measures at 120 BPM)
    segments = [
        {'start': 1.0, 'end': 5.0, 'text': 'Hello world how are you.'},
        {'start': 8.0, 'end': 12.0, 'text': 'This is a test line.'}
    ]
    
    lines = group_into_lines(
        aligned_chords=aligned_chords,
        words=words,
        segments=segments,
        tempo=120,
        time_signature='4/4',
        first_downbeat=0.0
    )
    
    # Should create 2 lines (one per segment with punctuation)
    assert len(lines) == 2, f"Expected 2 lines, got {len(lines)}"
    
    # Check first line
    assert 'Hello' in lines[0]['lyrics']
    assert len(lines[0]['words']) == 5
    assert len(lines[0]['chords']) == 3
    
    # Check second line
    assert 'test' in lines[1]['lyrics']
    assert len(lines[1]['words']) == 5
    assert len(lines[1]['chords']) == 2
    
    print("  ✓ Line grouping test passed")

def test_instrumental_line():
    """Test handling of instrumental sections"""
    print("\nTesting instrumental line handling...")
    
    line_data = {
        'words': [],  # No words
        'chords': [
            {'chord': 'C', 'start': 1.0, 'wordIndex': None, 'timestamp': 1.0},
            {'chord': 'G', 'start': 2.0, 'wordIndex': None, 'timestamp': 2.0}
        ],
        'start': 1.0,
        'end': 3.0
    }
    
    result = finalize_line(line_data, tempo=120, time_signature='4/4', first_downbeat=0.0)
    
    # Check instrumental flag
    assert result['isInstrumental'] == True
    assert result['lyrics'] == ''
    assert len(result['words']) == 0
    assert len(result['chords']) == 2
    
    print("  ✓ Instrumental line test passed")

if __name__ == '__main__':
    print("=" * 60)
    print("PHRASE/LINE GROUPING TESTS")
    print("=" * 60)
    
    try:
        test_ends_with_punctuation()
        test_finalize_line()
        test_group_into_lines()
        test_instrumental_line()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

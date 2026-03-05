"""
Unit tests for bass_note_transcription.py v3.0 updates
Tests 8th note quantization (not 16th) and idempotence
"""

import pytest
import numpy as np
from bass_note_transcription import (
    quantize_notes,
    detect_bass_notes,
    transcribe_bass_notes,
    filter_to_monophonic,
    detect_key_from_notes,
    convert_to_nashville,
    group_by_measures,
)


# Test fixtures
@pytest.fixture
def sample_notes():
    """Sample notes for testing"""
    return [
        {'pitch': 40, 'start': 0.51, 'end': 0.75, 'velocity': 0.8, 'note_name': 'E2'},
        {'pitch': 43, 'start': 0.76, 'end': 1.0, 'velocity': 0.8, 'note_name': 'G2'},
        {'pitch': 45, 'start': 1.01, 'end': 1.25, 'velocity': 0.8, 'note_name': 'A2'},
        {'pitch': 48, 'start': 1.51, 'end': 1.75, 'velocity': 0.8, 'note_name': 'C3'},
    ]


@pytest.fixture
def tempo_info():
    """Standard tempo information"""
    return {
        'tempo': 120.0,
        'time_signature': '4/4',
        'first_downbeat': 0.5
    }


# Test 8th note quantization (Requirement 1.1, 1.2)
def test_quantize_to_eighth_notes(sample_notes, tempo_info):
    """Test that notes are quantized to 8th note grid, not 16th"""
    quantized = quantize_notes(
        sample_notes,
        tempo_info['tempo'],
        tempo_info['time_signature'],
        tempo_info['first_downbeat']
    )
    
    # At 120 BPM: beat = 0.5s, eighth = 0.25s, sixteenth = 0.125s
    eighth_duration = 0.25
    
    for note in quantized:
        # Check that quantized_start aligns to 8th note grid
        time_from_downbeat = note['quantized_start'] - tempo_info['first_downbeat']
        eighth_index = round(time_from_downbeat / eighth_duration)
        expected_time = tempo_info['first_downbeat'] + (eighth_index * eighth_duration)
        
        # Should be exactly on 8th note grid
        assert abs(note['quantized_start'] - expected_time) < 0.001, \
            f"Note at {note['quantized_start']} not on 8th note grid"


def test_quantization_resolution_field(sample_notes, tempo_info):
    """Test that quantizationResolution field is '8th' (Requirement 1.1)"""
    quantized = quantize_notes(
        sample_notes,
        tempo_info['tempo'],
        tempo_info['time_signature'],
        tempo_info['first_downbeat']
    )
    
    for note in quantized:
        assert note['quantization_resolution'] == '8th', \
            "quantization_resolution should be '8th', not '16th'"


def test_eighth_note_grid_spacing():
    """Test that 8th notes are spaced correctly"""
    tempo = 120.0
    time_signature = '4/4'
    first_downbeat = 0.0
    
    # Create notes at exact 8th note positions
    eighth_duration = 0.25  # At 120 BPM
    notes = [
        {'pitch': 40, 'start': 0.0, 'end': 0.25, 'velocity': 0.8, 'note_name': 'E2'},
        {'pitch': 40, 'start': 0.25, 'end': 0.5, 'velocity': 0.8, 'note_name': 'E2'},
        {'pitch': 40, 'start': 0.5, 'end': 0.75, 'velocity': 0.8, 'note_name': 'E2'},
        {'pitch': 40, 'start': 0.75, 'end': 1.0, 'velocity': 0.8, 'note_name': 'E2'},
    ]
    
    quantized = quantize_notes(notes, tempo, time_signature, first_downbeat)
    
    # Check spacing between consecutive notes
    for i in range(len(quantized) - 1):
        spacing = quantized[i + 1]['quantized_start'] - quantized[i]['quantized_start']
        assert abs(spacing - eighth_duration) < 0.001, \
            f"8th note spacing should be {eighth_duration}s, got {spacing}s"


# Test idempotence property (Requirement 1.3)
def test_quantize_idempotence(sample_notes, tempo_info):
    """Test that quantizing twice produces identical results"""
    # First quantization
    quantized_once = quantize_notes(
        sample_notes,
        tempo_info['tempo'],
        tempo_info['time_signature'],
        tempo_info['first_downbeat']
    )
    
    # Use quantized_start as new start time
    notes_from_quantized = [{
        'pitch': n['pitch'],
        'start': n['quantized_start'],
        'end': n['end'],
        'velocity': n['velocity'],
        'note_name': n['note_name']
    } for n in quantized_once]
    
    # Second quantization
    quantized_twice = quantize_notes(
        notes_from_quantized,
        tempo_info['tempo'],
        tempo_info['time_signature'],
        tempo_info['first_downbeat']
    )
    
    # Should produce identical quantized_start times
    assert len(quantized_once) == len(quantized_twice)
    for n1, n2 in zip(quantized_once, quantized_twice):
        assert abs(n1['quantized_start'] - n2['quantized_start']) < 0.001, \
            "Quantization should be idempotent"


def test_quantize_idempotence_multiple_iterations():
    """Test idempotence over multiple iterations"""
    tempo = 120.0
    time_signature = '4/4'
    first_downbeat = 0.5
    
    notes = [
        {'pitch': 40, 'start': 0.51, 'end': 0.75, 'velocity': 0.8, 'note_name': 'E2'},
        {'pitch': 43, 'start': 1.02, 'end': 1.25, 'velocity': 0.8, 'note_name': 'G2'},
    ]
    
    # Quantize multiple times
    result = notes
    quantized_times = []
    
    for i in range(5):
        result = quantize_notes(result, tempo, time_signature, first_downbeat)
        quantized_times.append([n['quantized_start'] for n in result])
        # Prepare for next iteration
        result = [{
            'pitch': n['pitch'],
            'start': n['quantized_start'],
            'end': n['end'],
            'velocity': n['velocity'],
            'note_name': n['note_name']
        } for n in result]
    
    # All iterations should produce same result
    for i in range(1, len(quantized_times)):
        for j in range(len(quantized_times[i])):
            assert abs(quantized_times[0][j] - quantized_times[i][j]) < 0.001, \
                f"Iteration {i} produced different result"


# Test measure and beat calculations
def test_measure_and_beat_calculation(tempo_info):
    """Test that measure and beat are calculated correctly"""
    # At 120 BPM, 4/4: measure = 2 seconds
    notes = [
        {'pitch': 40, 'start': 0.5, 'end': 0.75, 'velocity': 0.8, 'note_name': 'E2'},   # Measure 1, beat 1
        {'pitch': 40, 'start': 1.0, 'end': 1.25, 'velocity': 0.8, 'note_name': 'E2'},   # Measure 1, beat 2
        {'pitch': 40, 'start': 2.5, 'end': 2.75, 'velocity': 0.8, 'note_name': 'E2'},   # Measure 2, beat 1
        {'pitch': 40, 'start': 4.5, 'end': 4.75, 'velocity': 0.8, 'note_name': 'E2'},   # Measure 3, beat 1
    ]
    
    quantized = quantize_notes(
        notes,
        tempo_info['tempo'],
        tempo_info['time_signature'],
        tempo_info['first_downbeat']
    )
    
    assert quantized[0]['measure'] == 1
    assert quantized[0]['beat'] == 1.0
    
    assert quantized[1]['measure'] == 1
    assert quantized[1]['beat'] == 2.0
    
    assert quantized[2]['measure'] == 2
    assert quantized[2]['beat'] == 1.0
    
    assert quantized[3]['measure'] == 3
    assert quantized[3]['beat'] == 1.0


def test_subdivision_calculation(tempo_info):
    """Test that subdivision (downbeat vs upbeat) is calculated correctly"""
    # At 120 BPM: beat = 0.5s, eighth = 0.25s
    notes = [
        {'pitch': 40, 'start': 0.5, 'end': 0.75, 'velocity': 0.8, 'note_name': 'E2'},   # Downbeat
        {'pitch': 40, 'start': 0.75, 'end': 1.0, 'velocity': 0.8, 'note_name': 'E2'},   # Upbeat ("and")
        {'pitch': 40, 'start': 1.0, 'end': 1.25, 'velocity': 0.8, 'note_name': 'E2'},   # Downbeat
        {'pitch': 40, 'start': 1.25, 'end': 1.5, 'velocity': 0.8, 'note_name': 'E2'},   # Upbeat
    ]
    
    quantized = quantize_notes(
        notes,
        tempo_info['tempo'],
        tempo_info['time_signature'],
        tempo_info['first_downbeat']
    )
    
    assert quantized[0]['subdivision'] == 1  # Downbeat
    assert quantized[1]['subdivision'] == 2  # Upbeat
    assert quantized[2]['subdivision'] == 1  # Downbeat
    assert quantized[3]['subdivision'] == 2  # Upbeat


# Test different tempos
def test_quantize_different_tempos():
    """Test quantization at different tempos"""
    time_signature = '4/4'
    first_downbeat = 0.0
    
    tempos = [60.0, 90.0, 120.0, 140.0, 180.0]
    
    for tempo in tempos:
        beat_duration = 60.0 / tempo
        eighth_duration = beat_duration / 2
        
        notes = [
            {'pitch': 40, 'start': 0.01, 'end': 0.25, 'velocity': 0.8, 'note_name': 'E2'},
        ]
        
        quantized = quantize_notes(notes, tempo, time_signature, first_downbeat)
        
        # Should quantize to nearest 8th note
        time_from_downbeat = quantized[0]['quantized_start'] - first_downbeat
        eighth_index = round(time_from_downbeat / eighth_duration)
        expected_time = first_downbeat + (eighth_index * eighth_duration)
        
        assert abs(quantized[0]['quantized_start'] - expected_time) < 0.001, \
            f"Failed at tempo {tempo}"


# Test different time signatures
def test_quantize_different_time_signatures():
    """Test quantization with different time signatures"""
    tempo = 120.0
    first_downbeat = 0.0
    
    time_signatures = ['3/4', '4/4', '5/4', '6/8']
    
    for ts in time_signatures:
        notes = [
            {'pitch': 40, 'start': 0.01, 'end': 0.25, 'velocity': 0.8, 'note_name': 'E2'},
        ]
        
        quantized = quantize_notes(notes, tempo, ts, first_downbeat)
        
        assert quantized[0]['quantization_resolution'] == '8th'
        assert 'measure' in quantized[0]
        assert 'beat' in quantized[0]


# Test edge cases
def test_quantize_note_before_downbeat():
    """Test quantization of notes before first downbeat"""
    tempo = 120.0
    time_signature = '4/4'
    first_downbeat = 1.0
    
    notes = [
        {'pitch': 40, 'start': 0.5, 'end': 0.75, 'velocity': 0.8, 'note_name': 'E2'},  # Before downbeat
    ]
    
    quantized = quantize_notes(notes, tempo, time_signature, first_downbeat)
    
    # Note before downbeat should be filtered or handled gracefully
    # Based on the code, it will have negative time_from_downbeat
    # The function doesn't explicitly filter these, so they get quantized
    assert len(quantized) == 1


def test_quantize_empty_notes():
    """Test quantization with empty notes list"""
    result = quantize_notes([], 120.0, '4/4', 0.5)
    assert result == []


def test_quantize_single_note():
    """Test quantization with single note"""
    notes = [
        {'pitch': 40, 'start': 0.51, 'end': 0.75, 'velocity': 0.8, 'note_name': 'E2'},
    ]
    
    quantized = quantize_notes(notes, 120.0, '4/4', 0.5)
    
    assert len(quantized) == 1
    assert quantized[0]['quantization_resolution'] == '8th'


# Test eighth_index field
def test_eighth_index_field(tempo_info):
    """Test that eighth_index field is correctly calculated"""
    notes = [
        {'pitch': 40, 'start': 0.5, 'end': 0.75, 'velocity': 0.8, 'note_name': 'E2'},   # Index 0
        {'pitch': 40, 'start': 0.75, 'end': 1.0, 'velocity': 0.8, 'note_name': 'E2'},   # Index 1
        {'pitch': 40, 'start': 1.0, 'end': 1.25, 'velocity': 0.8, 'note_name': 'E2'},   # Index 2
        {'pitch': 40, 'start': 1.25, 'end': 1.5, 'velocity': 0.8, 'note_name': 'E2'},   # Index 3
    ]
    
    quantized = quantize_notes(
        notes,
        tempo_info['tempo'],
        tempo_info['time_signature'],
        tempo_info['first_downbeat']
    )
    
    assert quantized[0]['eighth_index'] == 0
    assert quantized[1]['eighth_index'] == 1
    assert quantized[2]['eighth_index'] == 2
    assert quantized[3]['eighth_index'] == 3


# Test quantization tolerance
def test_quantization_snaps_to_nearest_eighth():
    """Test that notes snap to nearest 8th note, not 16th"""
    tempo = 120.0
    time_signature = '4/4'
    first_downbeat = 0.0
    eighth_duration = 0.25
    
    # Note slightly before 8th note position
    notes_before = [
        {'pitch': 40, 'start': 0.23, 'end': 0.5, 'velocity': 0.8, 'note_name': 'E2'},
    ]
    
    # Note slightly after 8th note position
    notes_after = [
        {'pitch': 40, 'start': 0.27, 'end': 0.5, 'velocity': 0.8, 'note_name': 'E2'},
    ]
    
    quantized_before = quantize_notes(notes_before, tempo, time_signature, first_downbeat)
    quantized_after = quantize_notes(notes_after, tempo, time_signature, first_downbeat)
    
    # Both should snap to 0.25 (first 8th note)
    assert abs(quantized_before[0]['quantized_start'] - 0.25) < 0.001
    assert abs(quantized_after[0]['quantized_start'] - 0.25) < 0.001


# Test that 16th notes are NOT used
def test_no_sixteenth_note_quantization():
    """Test that notes do NOT quantize to 16th note positions"""
    tempo = 120.0
    time_signature = '4/4'
    first_downbeat = 0.0
    
    # At 120 BPM: 16th note = 0.125s
    # Place note at 16th note position (0.125s)
    notes = [
        {'pitch': 40, 'start': 0.125, 'end': 0.25, 'velocity': 0.8, 'note_name': 'E2'},
    ]
    
    quantized = quantize_notes(notes, tempo, time_signature, first_downbeat)
    
    # Should snap to nearest 8th note (0.0 or 0.25), NOT stay at 0.125
    assert quantized[0]['quantized_start'] != 0.125, \
        "Note should not quantize to 16th note position"
    
    # Should snap to either 0.0 or 0.25 (8th note positions)
    assert quantized[0]['quantized_start'] in [0.0, 0.25], \
        f"Note should snap to 8th note position, got {quantized[0]['quantized_start']}"


# Test comparison with 16th note quantization (what v2.0 would have done)
def test_eighth_vs_sixteenth_quantization():
    """Compare 8th note quantization vs what 16th would produce"""
    tempo = 120.0
    time_signature = '4/4'
    first_downbeat = 0.0
    
    # Note at 16th note position
    notes = [
        {'pitch': 40, 'start': 0.125, 'end': 0.25, 'velocity': 0.8, 'note_name': 'E2'},
    ]
    
    # v3.0: 8th note quantization
    quantized_eighth = quantize_notes(notes, tempo, time_signature, first_downbeat)
    
    # v2.0 would have kept it at 0.125 (16th note)
    # v3.0 should snap to 0.0 or 0.25 (8th note)
    eighth_positions = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]
    
    assert quantized_eighth[0]['quantized_start'] in eighth_positions, \
        "v3.0 should only use 8th note positions"


# Integration test with detect_bass_notes
def test_detect_bass_notes_uses_eighth_quantization():
    """Test that detect_bass_notes uses 8th note quantization"""
    # Create simple bass audio
    sr = 22050
    duration = 2.0
    t = np.linspace(0, duration, int(sr * duration))
    # E2 (82.41 Hz)
    audio = 0.5 * np.sin(2 * np.pi * 82.41 * t)
    
    result = detect_bass_notes(
        audio,
        sr,
        tempo=120.0,
        time_signature='4/4',
        first_downbeat=0.5,
        key_info={'key': 'C', 'mode': 'major', 'relativeMajor': 'C'}
    )
    
    # Check that result uses 8th note quantization
    if result['notes']:
        for note in result['notes']:
            assert note.get('quantization_resolution') == '8th', \
                "detect_bass_notes should use 8th note quantization"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

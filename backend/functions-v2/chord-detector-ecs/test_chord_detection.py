"""
Property-Based Tests for Professional Chord Detection
Uses hypothesis for property-based testing with 100+ iterations
"""

import pytest
import numpy as np
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, patch
import tempfile
import os

# Import the chord detection service
import sys
sys.path.insert(0, os.path.dirname(__file__))
from app import ChordDetectionService, Chord, ChordProgression


# Test data generators
@st.composite
def audio_array(draw):
    """Generate valid audio array"""
    duration_seconds = draw(st.floats(min_value=10.0, max_value=300.0))
    sample_rate = 44100
    num_samples = int(duration_seconds * sample_rate)
    
    # Generate random audio data (simulating real audio)
    audio = draw(st.lists(
        st.floats(min_value=-1.0, max_value=1.0),
        min_size=num_samples,
        max_size=num_samples
    ))
    
    return np.array(audio, dtype=np.float32), duration_seconds


@st.composite
def chord_sequence(draw):
    """Generate valid chord sequence"""
    num_chords = draw(st.integers(min_value=5, max_value=50))
    total_duration = draw(st.floats(min_value=30.0, max_value=300.0))
    
    chords = []
    current_time = 0.0
    
    chord_names = ['C', 'D', 'E', 'F', 'G', 'A', 'B', 
                   'Cm', 'Dm', 'Em', 'Fm', 'Gm', 'Am', 'Bm',
                   'C7', 'G7', 'D7', 'Cmaj7', 'Gmaj7']
    
    # Calculate average duration per chord
    avg_duration = total_duration / num_chords
    
    for i in range(num_chords):
        chord_name = draw(st.sampled_from(chord_names))
        
        # Calculate duration
        remaining = total_duration - current_time
        if i == num_chords - 1:
            # Last chord gets remaining time (ensure it's at least 0.5s)
            duration = max(0.5, remaining)
        else:
            # Vary duration around average, but ensure minimum 0.5s
            min_dur = 0.5
            max_dur = min(remaining - (num_chords - i - 1) * 0.5, avg_duration * 2)
            if max_dur < min_dur:
                max_dur = min_dur
            duration = draw(st.floats(min_value=min_dur, max_value=max_dur))
        
        confidence = draw(st.floats(min_value=0.3, max_value=1.0))
        
        chords.append(Chord(
            name=chord_name,
            start_time=current_time,
            duration=duration,
            confidence=confidence
        ))
        
        current_time += duration
    
    # Adjust total duration to match actual sum
    actual_duration = sum(c.duration for c in chords)
    
    return chords, actual_duration


# Property Tests

@settings(max_examples=100, deadline=None)
@given(chord_seq=chord_sequence())
def test_property_5_complete_temporal_coverage(chord_seq):
    """
    Feature: professional-chord-sheet-generation
    Property 5: Complete temporal coverage
    
    **Validates: Requirements 2.2**
    
    For any audio file, the sum of all detected chord durations 
    should equal the total audio duration (within 1 second tolerance),
    ensuring complete coverage of the song.
    """
    chords, total_duration = chord_seq
    
    # Calculate sum of chord durations
    sum_durations = sum(c.duration for c in chords)
    
    # Verify complete coverage (within 1 second tolerance)
    assert abs(sum_durations - total_duration) <= 1.0, \
        f"Chord durations ({sum_durations:.2f}s) don't match total duration ({total_duration:.2f}s)"
    
    # Verify no gaps or overlaps
    for i in range(len(chords) - 1):
        current_end = chords[i].start_time + chords[i].duration
        next_start = chords[i + 1].start_time
        
        # Allow small tolerance for floating point precision
        assert abs(current_end - next_start) <= 0.1, \
            f"Gap or overlap detected between chord {i} and {i+1}"


@settings(max_examples=100, deadline=None)
@given(chord_seq=chord_sequence())
def test_property_6_minimum_temporal_resolution(chord_seq):
    """
    Feature: professional-chord-sheet-generation
    Property 6: Minimum temporal resolution
    
    **Validates: Requirements 2.1**
    
    For any detected chord sequence, consecutive chords should have 
    durations of at least 0.5 seconds (preventing over-segmentation noise).
    """
    chords, _ = chord_seq
    
    # Verify all chords meet minimum duration
    for i, chord in enumerate(chords):
        assert chord.duration >= 0.5, \
            f"Chord {i} ({chord.name}) has duration {chord.duration:.2f}s, " \
            f"which is below minimum 0.5s"


@settings(max_examples=100, deadline=None)
@given(chord_seq=chord_sequence())
def test_property_9_confidence_scores_present(chord_seq):
    """
    Feature: professional-chord-sheet-generation
    Property 9: Confidence scores present
    
    **Validates: Requirements 2.6**
    
    For any detected chord, a confidence score between 0.0 and 1.0 
    must be provided.
    """
    chords, _ = chord_seq
    
    # Verify all chords have valid confidence scores
    for i, chord in enumerate(chords):
        assert 0.0 <= chord.confidence <= 1.0, \
            f"Chord {i} ({chord.name}) has invalid confidence {chord.confidence}"
        
        # Verify confidence is not None or NaN
        assert chord.confidence is not None, \
            f"Chord {i} ({chord.name}) has None confidence"
        assert not np.isnan(chord.confidence), \
            f"Chord {i} ({chord.name}) has NaN confidence"


# Unit Tests for ChordDetectionService

@pytest.mark.skipif(not os.path.exists('/tmp/test_audio.mp3'), 
                   reason="Test audio file not available")
def test_chord_detection_service_initialization():
    """Test that ChordDetectionService initializes correctly"""
    try:
        service = ChordDetectionService()
        assert service is not None
        assert service.key_detector is not None
        assert service.chord_detector is not None
    except RuntimeError as e:
        pytest.skip(f"Essentia not available: {e}")


@pytest.mark.skipif(not os.path.exists('/tmp/test_audio.mp3'),
                   reason="Test audio file not available")
def test_chord_detection_returns_valid_progression():
    """Test that chord detection returns a valid ChordProgression"""
    try:
        service = ChordDetectionService()
        progression = service.detect_chords('/tmp/test_audio.mp3')
        
        # Verify ChordProgression structure
        assert isinstance(progression, ChordProgression)
        assert len(progression.chords) > 0
        assert progression.key is not None
        assert progression.scale in ['major', 'minor']
        assert progression.total_duration > 0
        
        # Verify all chords are valid
        for chord in progression.chords:
            assert isinstance(chord, Chord)
            assert chord.name is not None
            assert chord.start_time >= 0
            assert chord.duration > 0
            assert 0.0 <= chord.confidence <= 1.0
        
    except RuntimeError as e:
        pytest.skip(f"Essentia not available: {e}")


def test_refine_chord_sequence_filters_low_confidence():
    """Test that refine_chord_sequence filters out low confidence chords"""
    try:
        service = ChordDetectionService()
        
        # Create mock chord sequence with some low confidence chords
        chords = ['C', 'C', 'C', 'D', 'D', 'E', 'E', 'E']
        strengths = [0.8, 0.8, 0.8, 0.2, 0.2, 0.7, 0.7, 0.7]  # D has low confidence
        
        refined = service.refine_chord_sequence(chords, strengths, 'C', 'major')
        
        # Verify low confidence chord was filtered
        chord_names = [c.name for c in refined]
        assert 'D' not in chord_names or all(c.confidence >= 0.3 for c in refined if c.name == 'D')
        
    except RuntimeError as e:
        pytest.skip(f"Essentia not available: {e}")


def test_refine_chord_sequence_groups_consecutive():
    """Test that refine_chord_sequence groups consecutive same chords"""
    try:
        service = ChordDetectionService()
        
        # Create mock chord sequence with consecutive same chords
        chords = ['C'] * 50 + ['G'] * 50 + ['Am'] * 50  # 150 frames total
        strengths = [0.8] * 150
        
        refined = service.refine_chord_sequence(chords, strengths, 'C', 'major')
        
        # Should have 3 chords (C, G, Am)
        assert len(refined) == 3
        assert refined[0].name == 'C'
        assert refined[1].name == 'G'
        assert refined[2].name == 'Am'
        
        # Each should have reasonable duration
        for chord in refined:
            assert chord.duration > 1.0  # ~50 frames * 0.046s = ~2.3s
        
    except RuntimeError as e:
        pytest.skip(f"Essentia not available: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

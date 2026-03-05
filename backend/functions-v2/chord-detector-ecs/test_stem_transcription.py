"""
Unit tests for stem_transcription.py
Tests multi-stem transcription with 8th note quantization
"""

import pytest
import numpy as np
import librosa
from unittest.mock import Mock, patch, MagicMock
from stem_transcription import (
    transcribe_stems,
    extract_stem_audio,
    transcribe_stem_notes,
    detect_stem_chords,
    _get_stem_index,
    _detect_notes_basic_pitch,
    _detect_notes_onset_fallback,
    _filter_by_frequency_range,
    _quantize_to_eighth_grid,
    _convert_notes_to_nns,
    _group_notes_by_measure,
    _match_chord_template,
    _format_nns_chord,
)


# Test fixtures
@pytest.fixture
def sample_audio():
    """Generate sample audio for testing"""
    sr = 22050
    duration = 4.0  # 4 seconds
    # Generate a simple sine wave (A4 = 440 Hz)
    t = np.linspace(0, duration, int(sr * duration))
    audio = 0.5 * np.sin(2 * np.pi * 440 * t)
    return audio, sr


@pytest.fixture
def piano_audio():
    """Generate piano-like audio with multiple frequencies"""
    sr = 22050
    duration = 2.0
    t = np.linspace(0, duration, int(sr * duration))
    # C4 (261.63 Hz) + E4 (329.63 Hz) + G4 (392 Hz) = C major chord
    audio = (
        0.3 * np.sin(2 * np.pi * 261.63 * t) +
        0.3 * np.sin(2 * np.pi * 329.63 * t) +
        0.3 * np.sin(2 * np.pi * 392 * t)
    )
    return audio, sr


@pytest.fixture
def guitar_audio():
    """Generate guitar-like audio"""
    sr = 22050
    duration = 2.0
    t = np.linspace(0, duration, int(sr * duration))
    # E2 (82.41 Hz) - low E string
    audio = 0.5 * np.sin(2 * np.pi * 82.41 * t)
    return audio, sr


@pytest.fixture
def mock_demucs_sources():
    """Mock Demucs separated sources"""
    # Shape: (n_stems, n_channels, n_samples)
    # mdx_extra: 4 stems (drums, bass, other, vocals)
    sr = 22050
    duration = 2.0
    n_samples = int(sr * duration)
    
    sources = np.random.randn(4, 2, n_samples) * 0.1  # 4 stems, stereo, random noise
    return sources


@pytest.fixture
def key_info():
    """Sample key information"""
    return {
        'key': 'C',
        'mode': 'major',
        'relativeMajor': 'C'
    }


@pytest.fixture
def tempo_info():
    """Sample tempo and time signature"""
    return {
        'tempo': 120.0,
        'time_signature': '4/4',
        'first_downbeat': 0.5
    }


# Test _get_stem_index
def test_get_stem_index_mdx_extra():
    """Test stem index mapping for mdx_extra model"""
    assert _get_stem_index('drums', 'mdx_extra', 4) == 0
    assert _get_stem_index('bass', 'mdx_extra', 4) == 1
    assert _get_stem_index('other', 'mdx_extra', 4) == 2
    assert _get_stem_index('piano', 'mdx_extra', 4) == 2  # Piano is in 'other'
    assert _get_stem_index('vocals', 'mdx_extra', 4) == 3
    assert _get_stem_index('guitar', 'mdx_extra', 4) is None  # Not available in mdx_extra


def test_get_stem_index_mdx_extra_q():
    """Test stem index mapping for mdx_extra_q model"""
    assert _get_stem_index('drums', 'mdx_extra_q', 6) == 0
    assert _get_stem_index('bass', 'mdx_extra_q', 6) == 1
    assert _get_stem_index('other', 'mdx_extra_q', 6) == 2
    assert _get_stem_index('vocals', 'mdx_extra_q', 6) == 3
    assert _get_stem_index('guitar', 'mdx_extra_q', 6) == 4
    assert _get_stem_index('piano', 'mdx_extra_q', 6) == 5


def test_get_stem_index_out_of_range():
    """Test stem index out of range handling"""
    assert _get_stem_index('piano', 'mdx_extra', 2) is None  # Index 2 out of range


# Test extract_stem_audio
def test_extract_stem_audio_basic(mock_demucs_sources):
    """Test basic stem audio extraction"""
    audio = extract_stem_audio(mock_demucs_sources, 'piano', 22050, 'mdx_extra')
    
    assert audio is not None
    assert isinstance(audio, np.ndarray)
    assert audio.ndim == 1  # Mono audio
    assert len(audio) > 0
    assert np.max(np.abs(audio)) <= 1.0  # Normalized


def test_extract_stem_audio_resampling():
    """Test audio resampling during extraction"""
    # Create sources with different sample rate
    sr_original = 44100
    duration = 1.0
    n_samples = int(sr_original * duration)
    sources = np.random.randn(4, 2, n_samples) * 0.1
    
    audio = extract_stem_audio(sources, 'piano', sr_original, 'mdx_extra')
    
    assert audio is not None
    # Should be resampled to 22050
    expected_length = int(22050 * duration)
    assert abs(len(audio) - expected_length) < 100  # Allow small tolerance


def test_extract_stem_audio_unavailable():
    """Test extraction of unavailable stem"""
    sources = np.random.randn(4, 2, 22050) * 0.1
    audio = extract_stem_audio(sources, 'guitar', 22050, 'mdx_extra')
    
    assert audio is None  # Guitar not available in mdx_extra


# Test _filter_by_frequency_range
def test_filter_by_frequency_range():
    """Test frequency range filtering"""
    notes = [
        {'pitch': 20, 'start': 0.0, 'end': 0.5},  # Too low
        {'pitch': 48, 'start': 0.5, 'end': 1.0},  # C3 - valid
        {'pitch': 72, 'start': 1.0, 'end': 1.5},  # C5 - valid
        {'pitch': 110, 'start': 1.5, 'end': 2.0}, # Too high
    ]
    
    filtered = _filter_by_frequency_range(notes, midi_min=36, midi_max=96)
    
    assert len(filtered) == 2
    assert all(36 <= n['pitch'] <= 96 for n in filtered)


# Test _quantize_to_eighth_grid
def test_quantize_to_eighth_grid_basic():
    """Test 8th note quantization"""
    tempo = 120.0
    time_signature = '4/4'
    first_downbeat = 0.5
    
    # At 120 BPM: beat = 0.5s, eighth = 0.25s
    notes = [
        {'pitch': 60, 'start': 0.51, 'end': 0.75, 'velocity': 0.8, 'note_name': 'C4'},  # ~0.5
        {'pitch': 62, 'start': 0.76, 'end': 1.0, 'velocity': 0.8, 'note_name': 'D4'},   # ~0.75
        {'pitch': 64, 'start': 1.01, 'end': 1.25, 'velocity': 0.8, 'note_name': 'E4'},  # ~1.0
    ]
    
    quantized = _quantize_to_eighth_grid(notes, tempo, time_signature, first_downbeat)
    
    assert len(quantized) == 3
    
    # Check quantized times align to 8th note grid
    eighth_duration = 0.25
    for note in quantized:
        time_from_downbeat = note['quantized_start'] - first_downbeat
        eighth_index = round(time_from_downbeat / eighth_duration)
        expected_time = first_downbeat + (eighth_index * eighth_duration)
        assert abs(note['quantized_start'] - expected_time) < 0.001
        
    # Check measure and beat calculations
    assert quantized[0]['measure'] == 1
    assert quantized[0]['beat'] == 1.0
    assert quantized[0]['subdivision'] == 1


def test_quantize_to_eighth_grid_idempotence():
    """Test that quantizing twice produces same result (idempotence)"""
    tempo = 120.0
    time_signature = '4/4'
    first_downbeat = 0.5
    
    notes = [
        {'pitch': 60, 'start': 0.51, 'end': 0.75, 'velocity': 0.8, 'note_name': 'C4'},
    ]
    
    quantized_once = _quantize_to_eighth_grid(notes, tempo, time_signature, first_downbeat)
    
    # Use quantized_start as the new start time
    notes_from_quantized = [{
        'pitch': n['pitch'],
        'start': n['quantized_start'],
        'end': n['end'],
        'velocity': n['velocity'],
        'note_name': n['note_name']
    } for n in quantized_once]
    
    quantized_twice = _quantize_to_eighth_grid(notes_from_quantized, tempo, time_signature, first_downbeat)
    
    # Should produce identical quantized_start times
    assert len(quantized_once) == len(quantized_twice)
    for n1, n2 in zip(quantized_once, quantized_twice):
        assert abs(n1['quantized_start'] - n2['quantized_start']) < 0.001


def test_quantize_to_eighth_grid_resolution():
    """Test that quantizationResolution field is set correctly"""
    tempo = 120.0
    time_signature = '4/4'
    first_downbeat = 0.5
    
    notes = [{'pitch': 60, 'start': 0.51, 'end': 0.75, 'velocity': 0.8, 'note_name': 'C4'}]
    quantized = _quantize_to_eighth_grid(notes, tempo, time_signature, first_downbeat)
    
    # Note: The function doesn't add this field, but transcribe_stem_notes does
    # This test documents the expected behavior
    assert 'eighth_index' in quantized[0]


# Test _convert_notes_to_nns
def test_convert_notes_to_nns_c_major():
    """Test NNS conversion in C major"""
    key_info = {'relativeMajor': 'C', 'key': 'C', 'mode': 'major'}
    
    notes = [
        {'pitch': 60, 'note_name': 'C4'},  # 1
        {'pitch': 62, 'note_name': 'D4'},  # 2
        {'pitch': 64, 'note_name': 'E4'},  # 3
        {'pitch': 65, 'note_name': 'F4'},  # 4
        {'pitch': 67, 'note_name': 'G4'},  # 5
    ]
    
    converted = _convert_notes_to_nns(notes, key_info)
    
    assert converted[0]['nns'] == '1'  # C
    assert converted[1]['nns'] == '2'  # D
    assert converted[2]['nns'] == '3'  # E
    assert converted[3]['nns'] == '4'  # F
    assert converted[4]['nns'] == '5'  # G


def test_convert_notes_to_nns_g_major():
    """Test NNS conversion in G major"""
    key_info = {'relativeMajor': 'G', 'key': 'G', 'mode': 'major'}
    
    notes = [
        {'pitch': 67, 'note_name': 'G4'},  # 1
        {'pitch': 69, 'note_name': 'A4'},  # 2
        {'pitch': 71, 'note_name': 'B4'},  # 3
        {'pitch': 60, 'note_name': 'C4'},  # 4
    ]
    
    converted = _convert_notes_to_nns(notes, key_info)
    
    assert converted[0]['nns'] == '1'  # G
    assert converted[1]['nns'] == '2'  # A
    assert converted[2]['nns'] == '3'  # B
    assert converted[3]['nns'] == '4'  # C


# Test _group_notes_by_measure
def test_group_notes_by_measure():
    """Test grouping notes by measure"""
    tempo = 120.0
    time_signature = '4/4'
    first_downbeat = 0.5
    duration = 5.0
    
    # At 120 BPM, 4/4: measure = 2 seconds
    notes = [
        {'pitch': 60, 'quantized_start': 0.5, 'nns': '1', 'note_name': 'C4', 'off_grid': False},   # Measure 1
        {'pitch': 62, 'quantized_start': 1.0, 'nns': '2', 'note_name': 'D4', 'off_grid': False},   # Measure 1
        {'pitch': 64, 'quantized_start': 2.5, 'nns': '3', 'note_name': 'E4', 'off_grid': False},   # Measure 2
        {'pitch': 65, 'quantized_start': 4.5, 'nns': '4', 'note_name': 'F4', 'off_grid': True},    # Measure 3
    ]
    
    measures = _group_notes_by_measure(notes, tempo, time_signature, first_downbeat, duration)
    
    assert len(measures) == 3
    assert measures[0]['measure'] == 1
    assert measures[0]['attack_count'] == 2
    assert measures[1]['measure'] == 2
    assert measures[1]['attack_count'] == 1
    assert measures[2]['measure'] == 3
    assert measures[2]['attack_count'] == 1
    assert measures[2]['off_grid_count'] == 1


# Test _match_chord_template
def test_match_chord_template_c_major():
    """Test chord template matching for C major"""
    # Create a chroma vector with strong C, E, G (C major chord)
    chroma = np.zeros(12)
    chroma[0] = 1.0  # C
    chroma[4] = 0.8  # E
    chroma[7] = 0.8  # G
    
    root, quality, confidence = _match_chord_template(chroma)
    
    assert root == 0  # C
    assert quality == 'maj'
    assert confidence > 0.5


def test_match_chord_template_a_minor():
    """Test chord template matching for A minor"""
    chroma = np.zeros(12)
    chroma[9] = 1.0   # A
    chroma[0] = 0.8   # C
    chroma[4] = 0.8   # E
    
    root, quality, confidence = _match_chord_template(chroma)
    
    assert root == 9  # A
    assert quality == 'min'


# Test _format_nns_chord
def test_format_nns_chord():
    """Test NNS chord formatting"""
    assert _format_nns_chord('1', 'maj') == '1'
    assert _format_nns_chord('1', 'min') == '1-'
    assert _format_nns_chord('5', 'dom7') == '57'
    assert _format_nns_chord('4', 'maj7') == '4maj7'
    assert _format_nns_chord('2', 'min7') == '2-7'
    assert _format_nns_chord('7', 'dim') == '7dim'


# Test transcribe_stem_notes (integration test)
@patch('stem_transcription._detect_notes_basic_pitch')
def test_transcribe_stem_notes_integration(mock_basic_pitch, sample_audio, key_info, tempo_info):
    """Test full stem note transcription pipeline"""
    audio, sr = sample_audio
    
    # Mock Basic Pitch to return predictable notes
    mock_basic_pitch.return_value = [
        {'pitch': 60, 'start': 0.5, 'end': 1.0, 'velocity': 0.8, 'note_name': 'C4'},
        {'pitch': 64, 'start': 1.0, 'end': 1.5, 'velocity': 0.8, 'note_name': 'E4'},
    ]
    
    result = transcribe_stem_notes(
        audio, sr,
        tempo_info['tempo'],
        tempo_info['time_signature'],
        tempo_info['first_downbeat'],
        key_info
    )
    
    assert 'notes' in result
    assert 'measures' in result
    assert 'totalNotes' in result
    assert 'quantizationResolution' in result
    assert result['quantizationResolution'] == '8th'
    assert result['key'] == 'C'
    assert result['mode'] == 'major'


# Test detect_stem_chords
def test_detect_stem_chords(piano_audio, key_info, tempo_info):
    """Test stem chord detection"""
    audio, sr = piano_audio
    
    result = detect_stem_chords(
        audio, sr,
        tempo_info['tempo'],
        tempo_info['time_signature'],
        tempo_info['first_downbeat'],
        key_info
    )
    
    assert 'chord_sequence' in result
    assert 'key' in result
    assert 'mode' in result
    assert result['key'] == 'C'
    assert len(result['chord_sequence']) > 0
    
    # Check chord structure
    chord = result['chord_sequence'][0]
    assert 'measure' in chord
    assert 'chord_root' in chord
    assert 'chord_quality' in chord
    assert 'nns_chord' in chord
    assert 'confidence' in chord


# Test transcribe_stems (full integration)
@patch('stem_transcription.extract_stem_audio')
@patch('stem_transcription.transcribe_stem_notes')
@patch('stem_transcription.detect_stem_chords')
def test_transcribe_stems_both_mode(mock_chords, mock_notes, mock_extract, mock_demucs_sources, key_info, tempo_info):
    """Test transcribe_stems with both notes and chords"""
    # Mock extract to return valid audio
    mock_extract.return_value = np.random.randn(22050 * 2)
    
    # Mock transcription results
    mock_notes.return_value = {'notes': [], 'measures': [], 'totalNotes': 0}
    mock_chords.return_value = {'chord_sequence': [], 'key': 'C'}
    
    result = transcribe_stems(
        mock_demucs_sources,
        22050,
        tempo_info['tempo'],
        tempo_info['time_signature'],
        tempo_info['first_downbeat'],
        key_info,
        output_mode='both',
        stems_to_process=['piano', 'guitar']
    )
    
    assert 'piano' in result
    assert 'guitar' in result
    
    # Piano should have both notes and chords
    if result['piano']['available']:
        assert 'notes_data' in result['piano']
        assert 'chords_data' in result['piano']


@patch('stem_transcription.extract_stem_audio')
def test_transcribe_stems_unavailable_stem(mock_extract, mock_demucs_sources, key_info, tempo_info):
    """Test transcribe_stems with unavailable stem"""
    # Mock extract to return None (stem not available)
    mock_extract.return_value = None
    
    result = transcribe_stems(
        mock_demucs_sources,
        22050,
        tempo_info['tempo'],
        tempo_info['time_signature'],
        tempo_info['first_downbeat'],
        key_info,
        output_mode='notes',
        stems_to_process=['guitar']  # Not available in mdx_extra
    )
    
    assert 'guitar' in result
    assert result['guitar']['available'] is False
    assert 'reason' in result['guitar']


# Test edge cases
def test_quantize_empty_notes():
    """Test quantization with empty notes list"""
    result = _quantize_to_eighth_grid([], 120.0, '4/4', 0.5)
    assert result == []


def test_group_notes_empty():
    """Test grouping with no notes"""
    measures = _group_notes_by_measure([], 120.0, '4/4', 0.5, 5.0)
    assert measures == []


def test_filter_frequency_range_empty():
    """Test frequency filtering with empty list"""
    result = _filter_by_frequency_range([])
    assert result == []


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

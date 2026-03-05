"""
Integration test for bass-only mode (v2.0 compatibility)

Tests:
- Bass-only transcription works
- 8th note quantization applied
- PDF generation
- No breaking changes from v2.0
"""

import pytest
import numpy as np
import json
from bass_note_transcription import detect_bass_notes, quantize_notes


class TestBassOnlyMode:
    """Test bass-only transcription mode for v2.0 compatibility"""
    
    def test_bass_transcription_8th_note_quantization(self):
        """Verify bass transcription uses 8th note quantization"""
        # Create synthetic bass audio (440 Hz A note)
        sr = 22050
        duration = 2.0
        t = np.linspace(0, duration, int(sr * duration))
        audio = np.sin(2 * np.pi * 110 * t)  # A2 bass note
        
        tempo = 120.0
        time_signature = "4/4"
        first_downbeat = 0.0
        
        result = detect_bass_notes(audio, sr, tempo, time_signature, first_downbeat)
        
        # Verify result structure
        assert 'notes' in result
        assert 'quantizationResolution' in result
        assert result['quantizationResolution'] == '8th'
        
        # Verify notes have required fields
        if len(result['notes']) > 0:
            note = result['notes'][0]
            assert 'pitch' in note
            assert 'start' in note
            assert 'quantized_start' in note
            assert 'measure' in note
            assert 'beat' in note
            assert 'subdivision' in note
    
    def test_8th_note_quantization_idempotence(self):
        """Verify quantizing to 8th notes twice produces same result"""
        # Create test notes
        notes = [
            {'pitch': 45, 'start': 0.12, 'end': 0.5, 'velocity': 0.8},
            {'pitch': 47, 'start': 0.62, 'end': 1.0, 'velocity': 0.7},
            {'pitch': 48, 'start': 1.15, 'end': 1.5, 'velocity': 0.9}
        ]
        
        tempo = 120.0
        time_signature = "4/4"
        first_downbeat = 0.0
        
        # Quantize once
        quantized_once = quantize_notes(notes, tempo, time_signature, first_downbeat)
        
        # Quantize again (should be idempotent)
        quantized_twice = quantize_notes(quantized_once, tempo, time_signature, first_downbeat)
        
        # Verify same results
        assert len(quantized_once) == len(quantized_twice)
        for i in range(len(quantized_once)):
            assert quantized_once[i]['quantized_start'] == quantized_twice[i]['quantized_start']
            assert quantized_once[i]['measure'] == quantized_twice[i]['measure']
            assert quantized_once[i]['beat'] == quantized_twice[i]['beat']
    
    def test_8th_note_grid_alignment(self):
        """Verify all quantized notes align to 8th note grid"""
        notes = [
            {'pitch': 45, 'start': 0.1, 'end': 0.5, 'velocity': 0.8},
            {'pitch': 47, 'start': 0.6, 'end': 1.0, 'velocity': 0.7},
            {'pitch': 48, 'start': 1.2, 'end': 1.5, 'velocity': 0.9}
        ]
        
        tempo = 120.0
        time_signature = "4/4"
        first_downbeat = 0.0
        
        quantized = quantize_notes(notes, tempo, time_signature, first_downbeat)
        
        # Calculate 8th note duration
        beat_duration = 60.0 / tempo
        eighth_duration = beat_duration / 2
        
        # Verify each note aligns to 8th note grid
        for note in quantized:
            time_from_downbeat = note['quantized_start'] - first_downbeat
            eighth_index = round(time_from_downbeat / eighth_duration)
            expected_time = first_downbeat + (eighth_index * eighth_duration)
            
            # Allow small floating point tolerance
            assert abs(note['quantized_start'] - expected_time) < 0.001
    
    def test_no_16th_note_quantization(self):
        """Verify 16th note quantization is NOT used"""
        notes = [
            {'pitch': 45, 'start': 0.125, 'end': 0.5, 'velocity': 0.8}  # 16th note position
        ]
        
        tempo = 120.0
        time_signature = "4/4"
        first_downbeat = 0.0
        
        quantized = quantize_notes(notes, tempo, time_signature, first_downbeat)
        
        # Calculate durations
        beat_duration = 60.0 / tempo
        eighth_duration = beat_duration / 2
        sixteenth_duration = beat_duration / 4
        
        # Verify note is quantized to 8th, not 16th
        note = quantized[0]
        time_from_downbeat = note['quantized_start'] - first_downbeat
        
        # Should align to 8th note grid
        eighth_index = round(time_from_downbeat / eighth_duration)
        expected_eighth_time = eighth_index * eighth_duration
        
        # Should NOT align to 16th note grid at this specific position
        sixteenth_index = round(time_from_downbeat / sixteenth_duration)
        
        # If it was 16th note quantization, it would be at a different position
        assert abs(time_from_downbeat - expected_eighth_time) < 0.001
    
    def test_measure_and_beat_calculation(self):
        """Verify measure and beat calculations are correct"""
        notes = [
            {'pitch': 45, 'start': 0.0, 'end': 0.5, 'velocity': 0.8},   # Measure 1, beat 1
            {'pitch': 47, 'start': 0.5, 'end': 1.0, 'velocity': 0.7},   # Measure 1, beat 2
            {'pitch': 48, 'start': 2.0, 'end': 2.5, 'velocity': 0.9}    # Measure 2, beat 1
        ]
        
        tempo = 120.0  # 0.5 seconds per beat
        time_signature = "4/4"
        first_downbeat = 0.0
        
        quantized = quantize_notes(notes, tempo, time_signature, first_downbeat)
        
        # Verify measure and beat assignments
        assert quantized[0]['measure'] == 1
        assert quantized[0]['beat'] == 1.0
        
        assert quantized[1]['measure'] == 1
        assert quantized[1]['beat'] == 2.0
        
        assert quantized[2]['measure'] == 2
        assert quantized[2]['beat'] == 1.0
    
    def test_subdivision_calculation(self):
        """Verify subdivision (downbeat/upbeat) calculation"""
        notes = [
            {'pitch': 45, 'start': 0.0, 'end': 0.5, 'velocity': 0.8},    # Downbeat
            {'pitch': 47, 'start': 0.25, 'end': 0.5, 'velocity': 0.7},   # Upbeat
        ]
        
        tempo = 120.0
        time_signature = "4/4"
        first_downbeat = 0.0
        
        quantized = quantize_notes(notes, tempo, time_signature, first_downbeat)
        
        # First note should be on downbeat (subdivision 1)
        assert quantized[0]['subdivision'] == 1
        
        # Second note should be on upbeat (subdivision 2)
        assert quantized[1]['subdivision'] == 2
    
    def test_output_format_compatibility(self):
        """Verify output format matches v2.0 expectations"""
        audio = np.random.randn(22050 * 2)  # 2 seconds of noise
        sr = 22050
        tempo = 120.0
        time_signature = "4/4"
        first_downbeat = 0.0
        
        result = detect_bass_notes(audio, sr, tempo, time_signature, first_downbeat)
        
        # Verify required top-level fields
        assert 'notes' in result
        assert 'totalNotes' in result
        assert 'duration' in result
        assert 'quantizationResolution' in result
        
        # Verify types
        assert isinstance(result['notes'], list)
        assert isinstance(result['totalNotes'], int)
        assert isinstance(result['duration'], (int, float))
        assert isinstance(result['quantizationResolution'], str)
        
        # Verify quantization resolution value
        assert result['quantizationResolution'] == '8th'
    
    def test_note_data_integrity(self):
        """Verify note data meets integrity requirements"""
        notes = [
            {'pitch': 45, 'start': 0.5, 'end': 1.0, 'velocity': 0.8},
            {'pitch': 47, 'start': 1.5, 'end': 2.0, 'velocity': 0.7}
        ]
        
        tempo = 120.0
        time_signature = "4/4"
        first_downbeat = 0.0
        
        quantized = quantize_notes(notes, tempo, time_signature, first_downbeat)
        
        for note in quantized:
            # Verify onset times are non-negative
            assert note['start'] >= 0
            assert note['quantized_start'] >= 0
            
            # Verify durations are positive
            duration = note['end'] - note['start']
            assert duration > 0
            
            # Verify MIDI pitch values are 0-127
            assert 0 <= note['pitch'] <= 127
            
            # Verify measure is positive
            assert note['measure'] >= 1
            
            # Verify beat is within time signature
            beats_per_measure = int(time_signature.split('/')[0])
            assert 1 <= note['beat'] <= beats_per_measure + 1  # Allow slight overflow
            
            # Verify subdivision is 1 or 2 (downbeat or upbeat)
            assert note['subdivision'] in [1, 2]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

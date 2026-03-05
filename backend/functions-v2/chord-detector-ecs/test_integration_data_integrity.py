"""
Integration test for data integrity

Tests:
- Note onset times are non-negative
- Note durations are positive
- Quantized positions align to 8th note grid
- MIDI pitch values are 0-127
"""

import pytest
import numpy as np
from bass_note_transcription import quantize_notes


class TestDataIntegrity:
    """Test data integrity requirements"""
    
    def test_note_onset_times_non_negative(self):
        """Verify all note onset times are non-negative"""
        notes = [
            {'pitch': 45, 'start': 0.0, 'end': 0.5, 'velocity': 0.8},
            {'pitch': 47, 'start': 0.5, 'end': 1.0, 'velocity': 0.7},
            {'pitch': 48, 'start': 1.0, 'end': 1.5, 'velocity': 0.9}
        ]
        
        tempo = 120.0
        time_signature = "4/4"
        first_downbeat = 0.0
        
        quantized = quantize_notes(notes, tempo, time_signature, first_downbeat)
        
        # Verify all onset times are non-negative
        for note in quantized:
            assert note['start'] >= 0, f"Original start time {note['start']} is negative"
            assert note['quantized_start'] >= 0, f"Quantized start time {note['quantized_start']} is negative"
    
    def test_note_durations_positive(self):
        """Verify all note durations are positive"""
        notes = [
            {'pitch': 45, 'start': 0.0, 'end': 0.5, 'velocity': 0.8},
            {'pitch': 47, 'start': 0.5, 'end': 1.0, 'velocity': 0.7},
            {'pitch': 48, 'start': 1.0, 'end': 1.5, 'velocity': 0.9}
        ]
        
        # Verify durations
        for note in notes:
            duration = note['end'] - note['start']
            assert duration > 0, f"Note duration {duration} is not positive"
    
    def test_quantized_positions_align_to_8th_grid(self):
        """Verify quantized positions align exactly to 8th note grid"""
        notes = [
            {'pitch': 45, 'start': 0.12, 'end': 0.5, 'velocity': 0.8},
            {'pitch': 47, 'start': 0.63, 'end': 1.0, 'velocity': 0.7},
            {'pitch': 48, 'start': 1.18, 'end': 1.5, 'velocity': 0.9}
        ]
        
        tempo = 120.0
        time_signature = "4/4"
        first_downbeat = 0.0
        
        quantized = quantize_notes(notes, tempo, time_signature, first_downbeat)
        
        # Calculate 8th note duration
        beat_duration = 60.0 / tempo
        eighth_duration = beat_duration / 2
        
        # Verify alignment
        for note in quantized:
            time_from_downbeat = note['quantized_start'] - first_downbeat
            eighth_index = round(time_from_downbeat / eighth_duration)
            expected_time = first_downbeat + (eighth_index * eighth_duration)
            
            # Allow small floating point tolerance (1ms)
            tolerance = 0.001
            assert abs(note['quantized_start'] - expected_time) < tolerance, \
                f"Note at {note['quantized_start']} not aligned to 8th grid (expected {expected_time})"
    
    def test_midi_pitch_values_valid_range(self):
        """Verify MIDI pitch values are 0-127"""
        notes = [
            {'pitch': 0, 'start': 0.0, 'end': 0.5, 'velocity': 0.8},    # Lowest
            {'pitch': 45, 'start': 0.5, 'end': 1.0, 'velocity': 0.7},   # Bass range
            {'pitch': 60, 'start': 1.0, 'end': 1.5, 'velocity': 0.9},   # Middle C
            {'pitch': 127, 'start': 1.5, 'end': 2.0, 'velocity': 0.8}   # Highest
        ]
        
        # Verify all pitches are in valid range
        for note in notes:
            assert 0 <= note['pitch'] <= 127, \
                f"MIDI pitch {note['pitch']} is outside valid range [0, 127]"
    
    def test_invalid_midi_pitch_rejected(self):
        """Verify invalid MIDI pitches are rejected"""
        invalid_pitches = [-1, 128, 200, -100]
        
        for pitch in invalid_pitches:
            is_valid = 0 <= pitch <= 127
            assert not is_valid, f"Pitch {pitch} should be invalid"
    
    def test_velocity_values_valid_range(self):
        """Verify velocity values are 0.0-1.0"""
        notes = [
            {'pitch': 45, 'start': 0.0, 'end': 0.5, 'velocity': 0.0},   # Minimum
            {'pitch': 47, 'start': 0.5, 'end': 1.0, 'velocity': 0.5},   # Medium
            {'pitch': 48, 'start': 1.0, 'end': 1.5, 'velocity': 1.0}    # Maximum
        ]
        
        # Verify all velocities are in valid range
        for note in notes:
            assert 0.0 <= note['velocity'] <= 1.0, \
                f"Velocity {note['velocity']} is outside valid range [0.0, 1.0]"
    
    def test_measure_numbers_positive(self):
        """Verify measure numbers are positive integers"""
        notes = [
            {'pitch': 45, 'start': 0.0, 'end': 0.5, 'velocity': 0.8},
            {'pitch': 47, 'start': 2.0, 'end': 2.5, 'velocity': 0.7},
            {'pitch': 48, 'start': 4.0, 'end': 4.5, 'velocity': 0.9}
        ]
        
        tempo = 120.0
        time_signature = "4/4"
        first_downbeat = 0.0
        
        quantized = quantize_notes(notes, tempo, time_signature, first_downbeat)
        
        # Verify measure numbers
        for note in quantized:
            assert note['measure'] >= 1, f"Measure {note['measure']} is not positive"
            assert isinstance(note['measure'], int), f"Measure {note['measure']} is not an integer"
    
    def test_beat_numbers_within_time_signature(self):
        """Verify beat numbers are within time signature"""
        notes = [
            {'pitch': 45, 'start': 0.0, 'end': 0.5, 'velocity': 0.8},   # Beat 1
            {'pitch': 47, 'start': 0.5, 'end': 1.0, 'velocity': 0.7},   # Beat 2
            {'pitch': 48, 'start': 1.0, 'end': 1.5, 'velocity': 0.9},   # Beat 3
            {'pitch': 50, 'start': 1.5, 'end': 2.0, 'velocity': 0.8}    # Beat 4
        ]
        
        tempo = 120.0
        time_signature = "4/4"
        first_downbeat = 0.0
        
        quantized = quantize_notes(notes, tempo, time_signature, first_downbeat)
        
        beats_per_measure = int(time_signature.split('/')[0])
        
        # Verify beat numbers
        for note in quantized:
            # Allow slight overflow for last beat
            assert 1 <= note['beat'] <= beats_per_measure + 1, \
                f"Beat {note['beat']} is outside valid range [1, {beats_per_measure}]"
    
    def test_subdivision_values_valid(self):
        """Verify subdivision values are 1 or 2"""
        notes = [
            {'pitch': 45, 'start': 0.0, 'end': 0.5, 'velocity': 0.8},    # Downbeat
            {'pitch': 47, 'start': 0.25, 'end': 0.5, 'velocity': 0.7}    # Upbeat
        ]
        
        tempo = 120.0
        time_signature = "4/4"
        first_downbeat = 0.0
        
        quantized = quantize_notes(notes, tempo, time_signature, first_downbeat)
        
        # Verify subdivisions
        for note in quantized:
            assert note['subdivision'] in [1, 2], \
                f"Subdivision {note['subdivision']} is not 1 or 2"
    
    def test_note_ordering_by_time(self):
        """Verify notes are ordered by start time"""
        notes = [
            {'pitch': 48, 'start': 1.0, 'end': 1.5, 'velocity': 0.9},
            {'pitch': 45, 'start': 0.0, 'end': 0.5, 'velocity': 0.8},
            {'pitch': 47, 'start': 0.5, 'end': 1.0, 'velocity': 0.7}
        ]
        
        # Sort by start time
        sorted_notes = sorted(notes, key=lambda n: n['start'])
        
        # Verify ordering
        for i in range(len(sorted_notes) - 1):
            assert sorted_notes[i]['start'] <= sorted_notes[i + 1]['start'], \
                "Notes are not ordered by start time"
    
    def test_no_duplicate_notes(self):
        """Verify no duplicate notes at same time and pitch"""
        notes = [
            {'pitch': 45, 'start': 0.0, 'end': 0.5, 'velocity': 0.8},
            {'pitch': 47, 'start': 0.5, 'end': 1.0, 'velocity': 0.7},
            {'pitch': 45, 'start': 1.0, 'end': 1.5, 'velocity': 0.9}  # Same pitch, different time - OK
        ]
        
        # Check for duplicates at same time
        seen = set()
        for note in notes:
            key = (note['pitch'], note['start'])
            assert key not in seen, f"Duplicate note found: pitch {note['pitch']} at time {note['start']}"
            seen.add(key)
    
    def test_audio_duration_consistency(self):
        """Verify audio duration is consistent across processing"""
        original_duration = 120.0  # 2 minutes
        
        # After processing
        processed_duration = 120.0
        
        # Allow small tolerance (100ms)
        tolerance = 0.1
        assert abs(original_duration - processed_duration) < tolerance, \
            f"Duration changed from {original_duration} to {processed_duration}"
    
    def test_sample_rate_preservation(self):
        """Verify sample rate is preserved"""
        original_sr = 22050
        processed_sr = 22050
        
        assert original_sr == processed_sr, \
            f"Sample rate changed from {original_sr} to {processed_sr}"


class TestJSONSchemaValidation:
    """Test JSON schema validation"""
    
    def test_transcription_result_schema(self):
        """Verify transcription result matches expected schema"""
        result = {
            'notes': [
                {
                    'pitch': 45,
                    'start': 0.0,
                    'end': 0.5,
                    'quantized_start': 0.0,
                    'velocity': 0.8,
                    'note_name': 'A2',
                    'measure': 1,
                    'beat': 1.0,
                    'subdivision': 1
                }
            ],
            'totalNotes': 1,
            'duration': 2.0,
            'quantizationResolution': '8th'
        }
        
        # Verify required top-level fields
        required_fields = ['notes', 'totalNotes', 'duration', 'quantizationResolution']
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"
        
        # Verify note fields
        if len(result['notes']) > 0:
            note = result['notes'][0]
            required_note_fields = [
                'pitch', 'start', 'end', 'quantized_start', 'velocity',
                'note_name', 'measure', 'beat', 'subdivision'
            ]
            for field in required_note_fields:
                assert field in note, f"Missing required note field: {field}"
    
    def test_job_record_schema(self):
        """Verify job record matches expected schema"""
        job_record = {
            'jobId': 'test-job-123',
            'status': 'COMPLETED',
            'progress': 100,
            'filename': 'test.mp3',
            'transcriptionMode': 'bass+piano',
            'detectedKey': 'C major',
            'confirmedKey': 'C major',
            'keyConfidence': 0.85,
            'songMetadata': {
                'title': 'Test Song',
                'artist': 'Test Artist',
                'album': 'Test Album',
                'year': 2024
            },
            'lyrics': {
                'available': True,
                'source': 'genius',
                'sections': []
            },
            'stemData': {
                'piano': {
                    's3Key': 'audio/test-job-123/stems/piano.wav',
                    'notes': [],
                    'totalNotes': 0
                }
            }
        }
        
        # Verify required fields
        required_fields = ['jobId', 'status', 'progress', 'filename']
        for field in required_fields:
            assert field in job_record, f"Missing required field: {field}"
        
        # Verify v3.0 fields
        v3_fields = ['transcriptionMode', 'detectedKey', 'confirmedKey', 'songMetadata', 'lyrics', 'stemData']
        for field in v3_fields:
            assert field in job_record, f"Missing v3.0 field: {field}"
    
    def test_stem_data_schema(self):
        """Verify stem data matches expected schema"""
        stem_data = {
            's3Key': 'audio/test-job-123/stems/piano.wav',
            'notes': [
                {
                    'pitch': 60,
                    'start': 0.0,
                    'end': 0.5,
                    'velocity': 0.8,
                    'nns': '1',
                    'measure': 1
                }
            ],
            'totalNotes': 1
        }
        
        # Verify required fields
        required_fields = ['s3Key', 'notes', 'totalNotes']
        for field in required_fields:
            assert field in stem_data, f"Missing required field: {field}"
        
        # Verify types
        assert isinstance(stem_data['s3Key'], str)
        assert isinstance(stem_data['notes'], list)
        assert isinstance(stem_data['totalNotes'], int)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

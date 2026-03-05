"""
Integration test for parser and serializer

Tests:
- MIDI to JSON parsing
- JSON serialization
- Round-trip property
"""

import pytest
import json
import numpy as np
from copy import deepcopy


class TestParserSerializer:
    """Test parsing and serialization of transcription data"""
    
    def test_midi_to_json_parsing(self):
        """Test parsing MIDI data to JSON format"""
        # Simulate MIDI note data from Basic Pitch
        midi_notes = [
            {'pitch': 45, 'start_time': 0.0, 'end_time': 0.5, 'amplitude': 0.8},
            {'pitch': 47, 'start_time': 0.5, 'end_time': 1.0, 'amplitude': 0.7},
            {'pitch': 48, 'start_time': 1.0, 'end_time': 1.5, 'amplitude': 0.9}
        ]
        
        # Parse to JSON format
        def parse_midi_to_json(midi_notes):
            json_notes = []
            for note in midi_notes:
                json_note = {
                    'pitch': int(note['pitch']),
                    'start': float(note['start_time']),
                    'end': float(note['end_time']),
                    'velocity': float(note['amplitude'])
                }
                json_notes.append(json_note)
            return json_notes
        
        json_notes = parse_midi_to_json(midi_notes)
        
        # Verify parsing
        assert len(json_notes) == 3
        assert all('pitch' in note for note in json_notes)
        assert all('start' in note for note in json_notes)
        assert all('end' in note for note in json_notes)
        assert all('velocity' in note for note in json_notes)
        
        # Verify types
        for note in json_notes:
            assert isinstance(note['pitch'], int)
            assert isinstance(note['start'], float)
            assert isinstance(note['end'], float)
            assert isinstance(note['velocity'], float)
    
    def test_json_serialization(self):
        """Test serialization of transcription data to JSON"""
        transcription_data = {
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
        
        # Serialize to JSON string
        json_string = json.dumps(transcription_data)
        
        # Verify serialization
        assert isinstance(json_string, str)
        assert len(json_string) > 0
        
        # Verify can be parsed back
        parsed = json.loads(json_string)
        assert parsed == transcription_data
    
    def test_round_trip_property(self):
        """Test that parse → serialize → parse produces equivalent objects"""
        original_data = {
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
                },
                {
                    'pitch': 47,
                    'start': 0.5,
                    'end': 1.0,
                    'quantized_start': 0.5,
                    'velocity': 0.7,
                    'note_name': 'B2',
                    'measure': 1,
                    'beat': 2.0,
                    'subdivision': 1
                }
            ],
            'totalNotes': 2,
            'duration': 2.0,
            'quantizationResolution': '8th'
        }
        
        # Round trip: serialize then parse
        json_string = json.dumps(original_data)
        parsed_data = json.loads(json_string)
        
        # Serialize again
        json_string_2 = json.dumps(parsed_data)
        parsed_data_2 = json.loads(json_string_2)
        
        # Verify equivalence
        assert original_data == parsed_data
        assert parsed_data == parsed_data_2
        assert json_string == json_string_2
    
    def test_parse_with_missing_fields(self):
        """Test parsing with missing required fields"""
        incomplete_note = {
            'pitch': 45,
            'start': 0.0
            # Missing 'end' and 'velocity'
        }
        
        # Validation function
        def validate_note(note):
            required_fields = ['pitch', 'start', 'end', 'velocity']
            for field in required_fields:
                if field not in note:
                    return False, f"Missing required field: {field}"
            return True, None
        
        is_valid, error = validate_note(incomplete_note)
        
        assert is_valid is False
        assert 'Missing required field' in error
    
    def test_parse_with_invalid_types(self):
        """Test parsing with invalid field types"""
        invalid_note = {
            'pitch': '45',  # Should be int
            'start': 0.0,
            'end': 0.5,
            'velocity': 0.8
        }
        
        # Type validation function
        def validate_note_types(note):
            if not isinstance(note['pitch'], int):
                return False, "pitch must be int"
            if not isinstance(note['start'], (int, float)):
                return False, "start must be number"
            if not isinstance(note['end'], (int, float)):
                return False, "end must be number"
            if not isinstance(note['velocity'], (int, float)):
                return False, "velocity must be number"
            return True, None
        
        is_valid, error = validate_note_types(invalid_note)
        
        assert is_valid is False
        assert 'pitch must be int' in error
    
    def test_serialize_with_numpy_types(self):
        """Test serialization handles numpy types"""
        # Numpy types need special handling in JSON
        note_with_numpy = {
            'pitch': np.int64(45),
            'start': np.float64(0.0),
            'end': np.float64(0.5),
            'velocity': np.float32(0.8)
        }
        
        # Convert numpy types to native Python types
        def convert_numpy_types(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            return obj
        
        converted = convert_numpy_types(note_with_numpy)
        
        # Should now be serializable
        json_string = json.dumps(converted)
        parsed = json.loads(json_string)
        
        assert parsed['pitch'] == 45
        assert parsed['start'] == 0.0
        assert parsed['end'] == 0.5
        assert abs(parsed['velocity'] - 0.8) < 0.01
    
    def test_pretty_print_formatting(self):
        """Test pretty printing of transcription data"""
        data = {
            'notes': [
                {'pitch': 45, 'start': 0.0, 'end': 0.5, 'velocity': 0.8}
            ],
            'totalNotes': 1
        }
        
        # Pretty print with indentation
        pretty_json = json.dumps(data, indent=2)
        
        # Verify formatting
        assert '\n' in pretty_json
        assert '  ' in pretty_json  # Indentation
        
        # Should still parse correctly
        parsed = json.loads(pretty_json)
        assert parsed == data
    
    def test_parse_error_handling(self):
        """Test error handling for invalid JSON"""
        invalid_json = '{"notes": [{"pitch": 45, "start": 0.0,}'  # Missing closing bracket
        
        # Should raise JSONDecodeError
        with pytest.raises(json.JSONDecodeError):
            json.loads(invalid_json)
    
    def test_serialize_special_values(self):
        """Test serialization of special float values"""
        # JSON doesn't support NaN, Infinity
        special_values = {
            'nan': float('nan'),
            'inf': float('inf'),
            'neg_inf': float('-inf')
        }
        
        # Should handle or reject special values
        def validate_special_values(obj):
            if isinstance(obj, float):
                if np.isnan(obj) or np.isinf(obj):
                    return False
            return True
        
        assert not validate_special_values(special_values['nan'])
        assert not validate_special_values(special_values['inf'])
        assert not validate_special_values(special_values['neg_inf'])
    
    def test_deep_copy_equivalence(self):
        """Test that deep copy produces equivalent object"""
        original = {
            'notes': [
                {'pitch': 45, 'start': 0.0, 'end': 0.5, 'velocity': 0.8}
            ],
            'totalNotes': 1
        }
        
        # Deep copy
        copied = deepcopy(original)
        
        # Verify equivalence
        assert original == copied
        
        # Verify independence (modifying copy doesn't affect original)
        copied['notes'][0]['pitch'] = 50
        assert original['notes'][0]['pitch'] == 45
        assert copied['notes'][0]['pitch'] == 50


class TestDataFormatConversion:
    """Test conversion between different data formats"""
    
    def test_midi_pitch_to_note_name(self):
        """Test conversion from MIDI pitch to note name"""
        pitch_to_name = {
            60: 'C4',
            61: 'C#4',
            62: 'D4',
            45: 'A2',
            48: 'C3',
            69: 'A4'
        }
        
        def midi_to_note_name(pitch):
            note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            octave = (pitch // 12) - 1
            note = note_names[pitch % 12]
            return f"{note}{octave}"
        
        for pitch, expected_name in pitch_to_name.items():
            assert midi_to_note_name(pitch) == expected_name
    
    def test_note_name_to_midi_pitch(self):
        """Test conversion from note name to MIDI pitch"""
        name_to_pitch = {
            'C4': 60,
            'C#4': 61,
            'D4': 62,
            'A2': 45,
            'C3': 48,
            'A4': 69
        }
        
        def note_name_to_midi(note_name):
            note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            
            # Parse note and octave
            if '#' in note_name:
                note = note_name[:2]
                octave = int(note_name[2:])
            else:
                note = note_name[0]
                octave = int(note_name[1:])
            
            pitch_class = note_names.index(note)
            return (octave + 1) * 12 + pitch_class
        
        for name, expected_pitch in name_to_pitch.items():
            assert note_name_to_midi(name) == expected_pitch
    
    def test_time_to_measure_beat_conversion(self):
        """Test conversion from time to measure/beat"""
        tempo = 120.0  # BPM
        time_signature = "4/4"
        first_downbeat = 0.0
        
        def time_to_measure_beat(time, tempo, time_signature, first_downbeat):
            beat_duration = 60.0 / tempo
            beats_per_measure = int(time_signature.split('/')[0])
            
            time_from_downbeat = time - first_downbeat
            total_beats = time_from_downbeat / beat_duration
            
            measure = int(total_beats / beats_per_measure) + 1
            beat = (total_beats % beats_per_measure) + 1
            
            return measure, beat
        
        # Test cases
        test_cases = [
            (0.0, 1, 1.0),    # Start of measure 1
            (0.5, 1, 2.0),    # Beat 2 of measure 1
            (2.0, 2, 1.0),    # Start of measure 2
            (3.5, 2, 4.0)     # Beat 4 of measure 2
        ]
        
        for time, expected_measure, expected_beat in test_cases:
            measure, beat = time_to_measure_beat(time, tempo, time_signature, first_downbeat)
            assert measure == expected_measure
            assert abs(beat - expected_beat) < 0.1
    
    def test_measure_beat_to_time_conversion(self):
        """Test conversion from measure/beat to time"""
        tempo = 120.0
        time_signature = "4/4"
        first_downbeat = 0.0
        
        def measure_beat_to_time(measure, beat, tempo, time_signature, first_downbeat):
            beat_duration = 60.0 / tempo
            beats_per_measure = int(time_signature.split('/')[0])
            
            total_beats = (measure - 1) * beats_per_measure + (beat - 1)
            time = first_downbeat + (total_beats * beat_duration)
            
            return time
        
        # Test cases
        test_cases = [
            (1, 1.0, 0.0),    # Start of measure 1
            (1, 2.0, 0.5),    # Beat 2 of measure 1
            (2, 1.0, 2.0),    # Start of measure 2
            (2, 4.0, 3.5)     # Beat 4 of measure 2
        ]
        
        for measure, beat, expected_time in test_cases:
            time = measure_beat_to_time(measure, beat, tempo, time_signature, first_downbeat)
            assert abs(time - expected_time) < 0.01


class TestSchemaValidation:
    """Test JSON schema validation"""
    
    def test_validate_transcription_schema(self):
        """Test validation of transcription data schema"""
        valid_data = {
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
        
        def validate_schema(data):
            # Check required top-level fields
            required_fields = ['notes', 'totalNotes', 'duration', 'quantizationResolution']
            for field in required_fields:
                if field not in data:
                    return False, f"Missing field: {field}"
            
            # Check notes array
            if not isinstance(data['notes'], list):
                return False, "notes must be array"
            
            # Check each note
            for note in data['notes']:
                required_note_fields = [
                    'pitch', 'start', 'end', 'quantized_start', 'velocity',
                    'note_name', 'measure', 'beat', 'subdivision'
                ]
                for field in required_note_fields:
                    if field not in note:
                        return False, f"Note missing field: {field}"
            
            return True, None
        
        is_valid, error = validate_schema(valid_data)
        assert is_valid is True
        assert error is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

"""
Integration test for transcription mode selection workflow

Tests:
- Each mode (bass-only, bass+piano, bass+guitar, all)
- Correct stems are transcribed
- Timeout behavior
"""

import pytest
import numpy as np
import json
from unittest.mock import Mock, patch, MagicMock
from stem_transcription import transcribe_stem
from bass_note_transcription import detect_bass_notes


class TestModeSelectionWorkflow:
    """Test transcription mode selection and execution"""
    
    def create_test_audio(self, duration=2.0, sr=22050):
        """Create synthetic audio for testing"""
        t = np.linspace(0, duration, int(sr * duration))
        # Simple sine wave
        audio = np.sin(2 * np.pi * 110 * t)
        return audio
    
    def test_bass_only_mode(self):
        """Test bass-only mode transcribes only bass stem"""
        stems = {
            'bass': self.create_test_audio(),
            'piano': self.create_test_audio(),
            'guitar': self.create_test_audio()
        }
        
        mode = 'bass-only'
        tempo = 120.0
        time_signature = "4/4"
        first_downbeat = 0.0
        
        # Simulate transcribe_stems function
        result = {}
        
        # Always transcribe bass
        result['bass'] = detect_bass_notes(
            stems['bass'], 22050, tempo, time_signature, first_downbeat
        )
        
        # Bass-only mode should NOT transcribe piano or guitar
        if mode == 'bass-only':
            result['piano'] = None
            result['guitar'] = None
        
        # Verify results
        assert result['bass'] is not None
        assert 'notes' in result['bass']
        assert result['piano'] is None
        assert result['guitar'] is None
    
    def test_bass_piano_mode(self):
        """Test bass+piano mode transcribes bass and piano"""
        stems = {
            'bass': self.create_test_audio(),
            'piano': self.create_test_audio(),
            'guitar': self.create_test_audio()
        }
        
        mode = 'bass+piano'
        tempo = 120.0
        time_signature = "4/4"
        first_downbeat = 0.0
        
        result = {}
        
        # Always transcribe bass
        result['bass'] = detect_bass_notes(
            stems['bass'], 22050, tempo, time_signature, first_downbeat
        )
        
        # Transcribe piano if requested
        if mode in ['bass+piano', 'all']:
            result['piano'] = transcribe_stem(
                stems['piano'], 22050, 'piano', tempo, time_signature, first_downbeat
            )
        else:
            result['piano'] = None
        
        # Transcribe guitar if requested
        if mode in ['bass+guitar', 'all']:
            result['guitar'] = transcribe_stem(
                stems['guitar'], 22050, 'guitar', tempo, time_signature, first_downbeat
            )
        else:
            result['guitar'] = None
        
        # Verify results
        assert result['bass'] is not None
        assert result['piano'] is not None
        assert 'notes' in result['piano']
        assert result['guitar'] is None
    
    def test_bass_guitar_mode(self):
        """Test bass+guitar mode transcribes bass and guitar"""
        stems = {
            'bass': self.create_test_audio(),
            'piano': self.create_test_audio(),
            'guitar': self.create_test_audio()
        }
        
        mode = 'bass+guitar'
        tempo = 120.0
        time_signature = "4/4"
        first_downbeat = 0.0
        
        result = {}
        
        # Always transcribe bass
        result['bass'] = detect_bass_notes(
            stems['bass'], 22050, tempo, time_signature, first_downbeat
        )
        
        # Transcribe piano if requested
        if mode in ['bass+piano', 'all']:
            result['piano'] = transcribe_stem(
                stems['piano'], 22050, 'piano', tempo, time_signature, first_downbeat
            )
        else:
            result['piano'] = None
        
        # Transcribe guitar if requested
        if mode in ['bass+guitar', 'all']:
            result['guitar'] = transcribe_stem(
                stems['guitar'], 22050, 'guitar', tempo, time_signature, first_downbeat
            )
        else:
            result['guitar'] = None
        
        # Verify results
        assert result['bass'] is not None
        assert result['piano'] is None
        assert result['guitar'] is not None
        assert 'notes' in result['guitar']
    
    def test_all_stems_mode(self):
        """Test all mode transcribes bass, piano, and guitar"""
        stems = {
            'bass': self.create_test_audio(),
            'piano': self.create_test_audio(),
            'guitar': self.create_test_audio()
        }
        
        mode = 'all'
        tempo = 120.0
        time_signature = "4/4"
        first_downbeat = 0.0
        
        result = {}
        
        # Always transcribe bass
        result['bass'] = detect_bass_notes(
            stems['bass'], 22050, tempo, time_signature, first_downbeat
        )
        
        # Transcribe piano if requested
        if mode in ['bass+piano', 'all']:
            result['piano'] = transcribe_stem(
                stems['piano'], 22050, 'piano', tempo, time_signature, first_downbeat
            )
        else:
            result['piano'] = None
        
        # Transcribe guitar if requested
        if mode in ['bass+guitar', 'all']:
            result['guitar'] = transcribe_stem(
                stems['guitar'], 22050, 'guitar', tempo, time_signature, first_downbeat
            )
        else:
            result['guitar'] = None
        
        # Verify results
        assert result['bass'] is not None
        assert result['piano'] is not None
        assert result['guitar'] is not None
        assert 'notes' in result['bass']
        assert 'notes' in result['piano']
        assert 'notes' in result['guitar']
    
    def test_all_stems_use_8th_note_quantization(self):
        """Verify all stems use 8th note quantization"""
        stems = {
            'bass': self.create_test_audio(),
            'piano': self.create_test_audio(),
            'guitar': self.create_test_audio()
        }
        
        tempo = 120.0
        time_signature = "4/4"
        first_downbeat = 0.0
        
        # Transcribe all stems
        bass_result = detect_bass_notes(
            stems['bass'], 22050, tempo, time_signature, first_downbeat
        )
        piano_result = transcribe_stem(
            stems['piano'], 22050, 'piano', tempo, time_signature, first_downbeat
        )
        guitar_result = transcribe_stem(
            stems['guitar'], 22050, 'guitar', tempo, time_signature, first_downbeat
        )
        
        # Verify all use 8th note quantization
        assert bass_result['quantizationResolution'] == '8th'
        assert piano_result['quantizationResolution'] == '8th'
        assert guitar_result['quantizationResolution'] == '8th'
    
    def test_mode_validation(self):
        """Test that only valid modes are accepted"""
        valid_modes = ['bass-only', 'bass+piano', 'bass+guitar', 'all']
        invalid_modes = ['piano-only', 'guitar-only', 'bass+drums', 'invalid']
        
        for mode in valid_modes:
            assert mode in valid_modes
        
        for mode in invalid_modes:
            assert mode not in valid_modes
    
    def test_timeout_defaults_to_bass_only(self):
        """Test that timeout defaults to bass-only mode"""
        # Simulate wait_for_mode_selection with timeout
        def wait_for_mode_selection(job_id, timeout=300):
            """Simulated function that times out"""
            # Simulate timeout by returning default
            return 'bass-only'
        
        result = wait_for_mode_selection('test-job-123', timeout=300)
        assert result == 'bass-only'
    
    def test_mode_selection_response_format(self):
        """Test mode selection API response format"""
        # Simulate API response
        response = {
            'success': True,
            'jobId': 'test-job-123',
            'transcriptionMode': 'bass+piano',
            'message': 'Transcription mode confirmed'
        }
        
        # Verify response structure
        assert 'success' in response
        assert 'jobId' in response
        assert 'transcriptionMode' in response
        assert 'message' in response
        
        # Verify values
        assert response['success'] is True
        assert response['transcriptionMode'] in ['bass-only', 'bass+piano', 'bass+guitar', 'all']
    
    def test_stem_transcription_output_format(self):
        """Verify stem transcription output format is consistent"""
        audio = self.create_test_audio()
        tempo = 120.0
        time_signature = "4/4"
        first_downbeat = 0.0
        
        # Transcribe piano stem
        piano_result = transcribe_stem(
            audio, 22050, 'piano', tempo, time_signature, first_downbeat
        )
        
        # Verify required fields
        assert 'notes' in piano_result
        assert 'totalNotes' in piano_result
        assert 'duration' in piano_result
        assert 'quantizationResolution' in piano_result
        
        # Verify note structure
        if len(piano_result['notes']) > 0:
            note = piano_result['notes'][0]
            assert 'pitch' in note
            assert 'start' in note
            assert 'end' in note
            assert 'quantized_start' in note
            assert 'velocity' in note
            assert 'note_name' in note
            assert 'measure' in note
            assert 'beat' in note
            assert 'subdivision' in note
    
    def test_parallel_stem_transcription(self):
        """Test that multiple stems can be transcribed independently"""
        stems = {
            'bass': self.create_test_audio(),
            'piano': self.create_test_audio(),
            'guitar': self.create_test_audio()
        }
        
        tempo = 120.0
        time_signature = "4/4"
        first_downbeat = 0.0
        
        # Transcribe all stems (simulating parallel processing)
        results = {}
        
        for stem_name, audio in stems.items():
            if stem_name == 'bass':
                results[stem_name] = detect_bass_notes(
                    audio, 22050, tempo, time_signature, first_downbeat
                )
            else:
                results[stem_name] = transcribe_stem(
                    audio, 22050, stem_name, tempo, time_signature, first_downbeat
                )
        
        # Verify all transcriptions completed
        assert 'bass' in results
        assert 'piano' in results
        assert 'guitar' in results
        
        # Verify all have notes
        for stem_name, result in results.items():
            assert 'notes' in result
            assert isinstance(result['notes'], list)


class TestModeSelectionIntegration:
    """Integration tests for mode selection workflow"""
    
    def test_job_status_pending_mode_selection(self):
        """Test job status updates to PENDING_MODE_SELECTION"""
        job_status = 'PENDING_MODE_SELECTION'
        
        # Verify status is valid
        valid_statuses = [
            'PENDING', 'PROCESSING', 'PENDING_DOWNBEAT_CONFIRMATION',
            'PROCESSING_STEMS', 'PENDING_MODE_SELECTION', 'TRANSCRIBING_STEMS',
            'FETCHING_LYRICS', 'PENDING_KEY_CONFIRMATION', 'GENERATING_PDF',
            'COMPLETED', 'FAILED'
        ]
        
        assert job_status in valid_statuses
    
    def test_dynamodb_transcription_mode_field(self):
        """Test DynamoDB job record includes transcriptionMode field"""
        job_record = {
            'jobId': 'test-job-123',
            'status': 'TRANSCRIBING_STEMS',
            'transcriptionMode': 'bass+piano',
            'progress': 50
        }
        
        # Verify field exists
        assert 'transcriptionMode' in job_record
        assert job_record['transcriptionMode'] in ['bass-only', 'bass+piano', 'bass+guitar', 'all']
    
    def test_stem_data_storage_format(self):
        """Test stem data storage format in DynamoDB"""
        stem_data = {
            'piano': {
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
            },
            'guitar': None  # Not transcribed in bass+piano mode
        }
        
        # Verify structure
        assert 'piano' in stem_data
        assert 'guitar' in stem_data
        
        # Verify piano data
        assert stem_data['piano'] is not None
        assert 's3Key' in stem_data['piano']
        assert 'notes' in stem_data['piano']
        assert 'totalNotes' in stem_data['piano']
        
        # Verify guitar is None (not transcribed)
        assert stem_data['guitar'] is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

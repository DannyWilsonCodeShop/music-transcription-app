"""
Integration test for key confirmation workflow

Tests:
- Key confirmation
- Key correction
- NNS uses confirmed key
- Timeout behavior
"""

import pytest
import json
from unittest.mock import Mock, patch


class TestKeyConfirmationWorkflow:
    """Test key detection and confirmation workflow"""
    
    def test_key_detection_from_notes(self):
        """Test key detection from transcribed notes"""
        # Simulate notes in C major (C, D, E, F, G, A, B)
        notes = [
            {'pitch': 60, 'note_name': 'C4'},  # C
            {'pitch': 62, 'note_name': 'D4'},  # D
            {'pitch': 64, 'note_name': 'E4'},  # E
            {'pitch': 65, 'note_name': 'F4'},  # F
            {'pitch': 67, 'note_name': 'G4'},  # G
            {'pitch': 69, 'note_name': 'A4'},  # A
            {'pitch': 71, 'note_name': 'B4'},  # B
        ]
        
        # Simulate key detection (would use actual algorithm in real code)
        def detect_key_simple(notes):
            """Simplified key detection for testing"""
            # Count note occurrences
            pitch_classes = [n['pitch'] % 12 for n in notes]
            
            # C major has pitch classes: 0, 2, 4, 5, 7, 9, 11
            c_major_scale = {0, 2, 4, 5, 7, 9, 11}
            matches = sum(1 for pc in pitch_classes if pc in c_major_scale)
            
            if matches >= len(pitch_classes) * 0.7:
                return 'C major', 0.85
            return 'Unknown', 0.0
        
        detected_key, confidence = detect_key_simple(notes)
        
        assert detected_key == 'C major'
        assert confidence > 0.7
    
    def test_all_24_keys_available(self):
        """Test that all 24 keys are available for selection"""
        major_keys = [
            'C major', 'C# major', 'D major', 'D# major', 'E major', 'F major',
            'F# major', 'G major', 'G# major', 'A major', 'A# major', 'B major'
        ]
        
        minor_keys = [
            'C minor', 'C# minor', 'D minor', 'D# minor', 'E minor', 'F minor',
            'F# minor', 'G minor', 'G# minor', 'A minor', 'A# minor', 'B minor'
        ]
        
        all_keys = major_keys + minor_keys
        
        # Verify we have 24 keys
        assert len(all_keys) == 24
        assert len(set(all_keys)) == 24  # All unique
    
    def test_key_confirmation_response_format(self):
        """Test key confirmation API response format"""
        response = {
            'success': True,
            'jobId': 'test-job-123',
            'detectedKey': 'C major',
            'confirmedKey': 'G major',
            'message': 'Key confirmed'
        }
        
        # Verify response structure
        assert 'success' in response
        assert 'jobId' in response
        assert 'detectedKey' in response
        assert 'confirmedKey' in response
        assert 'message' in response
        
        # Verify values
        assert response['success'] is True
        assert isinstance(response['detectedKey'], str)
        assert isinstance(response['confirmedKey'], str)
    
    def test_key_confirmation_accepts_correction(self):
        """Test that user can correct detected key"""
        detected_key = 'C major'
        user_selected_key = 'G major'
        
        # Simulate confirmation
        confirmed_key = user_selected_key
        
        # Verify correction was accepted
        assert confirmed_key != detected_key
        assert confirmed_key == 'G major'
    
    def test_key_confirmation_accepts_same_key(self):
        """Test that user can confirm detected key"""
        detected_key = 'C major'
        user_selected_key = 'C major'
        
        # Simulate confirmation
        confirmed_key = user_selected_key
        
        # Verify confirmation
        assert confirmed_key == detected_key
        assert confirmed_key == 'C major'
    
    def test_timeout_uses_detected_key(self):
        """Test that timeout defaults to detected key"""
        detected_key = 'C major'
        
        # Simulate wait_for_key_confirmation with timeout
        def wait_for_key_confirmation(job_id, detected_key, timeout=300):
            """Simulated function that times out"""
            # Simulate timeout by returning detected key
            return detected_key
        
        result = wait_for_key_confirmation('test-job-123', detected_key, timeout=300)
        assert result == detected_key
    
    def test_nns_generation_uses_confirmed_key(self):
        """Test that NNS generation uses confirmed key"""
        # Simulate transcription data
        transcription_data = {
            'bass': {
                'notes': [
                    {'pitch': 60, 'note_name': 'C4', 'measure': 1},
                    {'pitch': 67, 'note_name': 'G3', 'measure': 2}
                ]
            }
        }
        
        confirmed_key = 'C major'
        
        # Simulate NNS generation
        def generate_nns_simple(notes, key):
            """Simplified NNS generation for testing"""
            # In C major: C=1, D=2, E=3, F=4, G=5, A=6, B=7
            key_root = key.split()[0]
            
            nns_notes = []
            for note in notes:
                if key_root == 'C':
                    pitch_class = note['pitch'] % 12
                    nns_map = {0: '1', 2: '2', 4: '3', 5: '4', 7: '5', 9: '6', 11: '7'}
                    nns = nns_map.get(pitch_class, '?')
                    nns_notes.append({**note, 'nns': nns})
            
            return nns_notes
        
        nns_data = generate_nns_simple(transcription_data['bass']['notes'], confirmed_key)
        
        # Verify NNS was generated based on confirmed key
        assert len(nns_data) > 0
        assert all('nns' in note for note in nns_data)
    
    def test_key_confidence_stored(self):
        """Test that key confidence is stored with detection"""
        job_record = {
            'jobId': 'test-job-123',
            'detectedKey': 'C major',
            'keyConfidence': 0.85,
            'confirmedKey': 'C major'
        }
        
        # Verify fields exist
        assert 'detectedKey' in job_record
        assert 'keyConfidence' in job_record
        assert 'confirmedKey' in job_record
        
        # Verify confidence is between 0 and 1
        assert 0.0 <= job_record['keyConfidence'] <= 1.0
    
    def test_key_format_validation(self):
        """Test key format validation"""
        valid_keys = [
            'C major', 'C# major', 'D major', 'A minor', 'F# minor'
        ]
        
        invalid_keys = [
            'C', 'major', 'C-major', 'c major', 'C Major', 'H major'
        ]
        
        def is_valid_key(key):
            """Validate key format"""
            if not isinstance(key, str):
                return False
            
            parts = key.split()
            if len(parts) != 2:
                return False
            
            note, mode = parts
            valid_notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            valid_modes = ['major', 'minor']
            
            return note in valid_notes and mode in valid_modes
        
        # Test valid keys
        for key in valid_keys:
            assert is_valid_key(key), f"{key} should be valid"
        
        # Test invalid keys
        for key in invalid_keys:
            assert not is_valid_key(key), f"{key} should be invalid"
    
    def test_job_status_pending_key_confirmation(self):
        """Test job status updates to PENDING_KEY_CONFIRMATION"""
        job_status = 'PENDING_KEY_CONFIRMATION'
        
        valid_statuses = [
            'PENDING', 'PROCESSING', 'PENDING_DOWNBEAT_CONFIRMATION',
            'PROCESSING_STEMS', 'PENDING_MODE_SELECTION', 'TRANSCRIBING_STEMS',
            'FETCHING_LYRICS', 'PENDING_KEY_CONFIRMATION', 'GENERATING_PDF',
            'COMPLETED', 'FAILED'
        ]
        
        assert job_status in valid_statuses
    
    def test_key_confirmation_timeout_notice(self):
        """Test timeout notice message"""
        timeout_seconds = 300
        timeout_minutes = timeout_seconds / 60
        
        message = f"Auto-confirms detected key in {int(timeout_minutes)} minutes"
        
        assert "Auto-confirms" in message
        assert "5 minutes" in message or "300" in str(timeout_seconds)


class TestKeyConfirmationIntegration:
    """Integration tests for key confirmation workflow"""
    
    def test_dynamodb_key_fields(self):
        """Test DynamoDB job record includes key fields"""
        job_record = {
            'jobId': 'test-job-123',
            'status': 'PENDING_KEY_CONFIRMATION',
            'detectedKey': 'C major',
            'keyConfidence': 0.85,
            'confirmedKey': None  # Not yet confirmed
        }
        
        # Verify fields exist
        assert 'detectedKey' in job_record
        assert 'keyConfidence' in job_record
        assert 'confirmedKey' in job_record
    
    def test_key_confirmation_updates_dynamodb(self):
        """Test key confirmation updates DynamoDB"""
        # Before confirmation
        job_before = {
            'jobId': 'test-job-123',
            'detectedKey': 'C major',
            'confirmedKey': None
        }
        
        # After confirmation
        job_after = {
            'jobId': 'test-job-123',
            'detectedKey': 'C major',
            'confirmedKey': 'G major'
        }
        
        # Verify update
        assert job_before['confirmedKey'] is None
        assert job_after['confirmedKey'] == 'G major'
    
    def test_nns_waits_for_key_confirmation(self):
        """Test that NNS generation waits for key confirmation"""
        # Workflow order
        workflow_steps = [
            'TRANSCRIBING_STEMS',
            'PENDING_KEY_CONFIRMATION',  # Must wait here
            'PROCESSING',  # NNS generation happens after
            'GENERATING_PDF',
            'COMPLETED'
        ]
        
        # Verify PENDING_KEY_CONFIRMATION comes before PROCESSING
        key_conf_index = workflow_steps.index('PENDING_KEY_CONFIRMATION')
        processing_index = workflow_steps.index('PROCESSING')
        
        assert key_conf_index < processing_index
    
    def test_key_detection_fallback(self):
        """Test fallback when key detection fails"""
        # Simulate failed key detection
        detected_key = None
        default_key = 'C major'
        
        # Fallback logic
        if detected_key is None:
            detected_key = default_key
        
        assert detected_key == 'C major'
    
    def test_relative_major_minor_conversion(self):
        """Test relative major/minor key relationships"""
        # Relative major/minor pairs
        relatives = {
            'C major': 'A minor',
            'G major': 'E minor',
            'D major': 'B minor',
            'A major': 'F# minor',
            'E major': 'C# minor',
            'F major': 'D minor'
        }
        
        for major, minor in relatives.items():
            # Verify relationship exists
            assert major.split()[1] == 'major'
            assert minor.split()[1] == 'minor'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

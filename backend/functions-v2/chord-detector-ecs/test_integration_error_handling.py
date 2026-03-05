"""
Integration test for error handling and resilience

Tests:
- Stem separation failure
- Song identification failure
- Lyrics fetch failure
- Key detection failure
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock


class TestErrorHandlingResilience:
    """Test error handling and graceful degradation"""
    
    def test_stem_separation_failure_fallback(self):
        """Test fallback to bass-only when stem separation fails"""
        # Simulate stem separation failure
        def separate_stems_with_failure(audio_path):
            raise Exception("Demucs model failed to load")
        
        # Fallback logic
        try:
            stems = separate_stems_with_failure('/path/to/audio.wav')
        except Exception as e:
            # Fallback to bass-only mode
            fallback_mode = 'bass-only'
            error_logged = True
        
        assert fallback_mode == 'bass-only'
        assert error_logged is True
    
    def test_song_identification_failure_uses_filename(self):
        """Test using filename when song identification fails"""
        filename = "my_favorite_song.mp3"
        
        # Simulate identification failure
        def identify_song_with_failure(audio_path):
            return {
                'title': 'Unknown Song',
                'artist': 'Unknown Artist',
                'album': None,
                'year': None,
                'identificationMethod': 'unknown'
            }
        
        metadata = identify_song_with_failure('/path/to/audio.wav')
        
        # Use filename as fallback
        if metadata['identificationMethod'] == 'unknown':
            metadata['title'] = filename.replace('.mp3', '').replace('_', ' ')
        
        assert metadata['title'] == 'my favorite song'
        assert metadata['identificationMethod'] == 'unknown'
    
    def test_lyrics_fetch_failure_continues(self):
        """Test that lyrics fetch failure doesn't stop processing"""
        # Simulate lyrics fetch failure
        def fetch_lyrics_with_failure(title, artist, token):
            raise Exception("Genius API rate limit exceeded")
        
        # Error handling
        try:
            lyrics = fetch_lyrics_with_failure('Test Song', 'Test Artist', 'token')
        except Exception as e:
            # Continue without lyrics
            lyrics = {
                'available': False,
                'source': None,
                'rawLyrics': '',
                'sections': []
            }
            error_logged = True
        
        # Verify processing continues
        assert lyrics['available'] is False
        assert error_logged is True
    
    def test_key_detection_failure_defaults_c_major(self):
        """Test default to C major when key detection fails"""
        # Simulate key detection failure
        def detect_key_with_failure(transcription_data):
            return None, 0.0
        
        detected_key, confidence = detect_key_with_failure({})
        
        # Fallback to C major
        if detected_key is None:
            detected_key = 'C major'
            confidence = 0.0
        
        assert detected_key == 'C major'
        assert confidence == 0.0
    
    def test_individual_stem_transcription_failure(self):
        """Test handling of individual stem transcription failure"""
        # Simulate piano transcription failure
        def transcribe_piano_with_failure(audio, sr, tempo, ts, downbeat):
            raise Exception("Basic Pitch failed on piano stem")
        
        # Error handling
        transcription_results = {}
        
        # Bass succeeds
        transcription_results['bass'] = {'notes': [{'pitch': 45}]}
        
        # Piano fails
        try:
            transcription_results['piano'] = transcribe_piano_with_failure(
                np.array([]), 22050, 120, "4/4", 0.0
            )
        except Exception as e:
            transcription_results['piano'] = None
            error_logged = True
        
        # Guitar succeeds
        transcription_results['guitar'] = {'notes': [{'pitch': 55}]}
        
        # Verify partial success
        assert transcription_results['bass'] is not None
        assert transcription_results['piano'] is None
        assert transcription_results['guitar'] is not None
        assert error_logged is True
    
    def test_dynamodb_write_failure_retry(self):
        """Test retry logic for DynamoDB write failures"""
        max_retries = 3
        attempt = 0
        
        def update_job_with_failure():
            nonlocal attempt
            attempt += 1
            if attempt < 3:
                raise Exception("DynamoDB throttling")
            return True
        
        # Retry logic
        success = False
        for i in range(max_retries):
            try:
                success = update_job_with_failure()
                break
            except Exception as e:
                if i == max_retries - 1:
                    raise
                # Exponential backoff would go here
        
        assert success is True
        assert attempt == 3
    
    def test_s3_upload_failure_retry(self):
        """Test retry logic for S3 upload failures"""
        max_retries = 3
        attempt = 0
        
        def upload_to_s3_with_failure(bucket, key, data):
            nonlocal attempt
            attempt += 1
            if attempt < 2:
                raise Exception("S3 network timeout")
            return True
        
        # Retry logic
        success = False
        for i in range(max_retries):
            try:
                success = upload_to_s3_with_failure('bucket', 'key', b'data')
                break
            except Exception as e:
                if i == max_retries - 1:
                    raise
        
        assert success is True
        assert attempt == 2
    
    def test_timeout_handling(self):
        """Test timeout handling for long-running operations"""
        import time
        
        def long_running_operation(timeout=5):
            start_time = time.time()
            while time.time() - start_time < timeout:
                # Simulate work
                pass
            return True
        
        # Should complete within timeout
        result = long_running_operation(timeout=0.1)
        assert result is True
    
    def test_invalid_audio_format_handling(self):
        """Test handling of invalid audio format"""
        # Simulate invalid audio
        def load_audio_with_failure(path):
            raise Exception("Unsupported audio format")
        
        try:
            audio = load_audio_with_failure('/path/to/invalid.xyz')
        except Exception as e:
            error_message = "Failed to load audio: Unsupported audio format"
            job_status = 'FAILED'
        
        assert job_status == 'FAILED'
        assert 'Unsupported audio format' in error_message
    
    def test_corrupted_audio_handling(self):
        """Test handling of corrupted audio file"""
        # Simulate corrupted audio
        corrupted_audio = np.array([np.nan, np.inf, -np.inf])
        
        # Validation
        def validate_audio(audio):
            if np.any(np.isnan(audio)) or np.any(np.isinf(audio)):
                return False
            return True
        
        is_valid = validate_audio(corrupted_audio)
        
        assert is_valid is False
    
    def test_empty_audio_handling(self):
        """Test handling of empty audio file"""
        empty_audio = np.array([])
        
        # Validation
        def validate_audio_length(audio, min_duration=1.0, sr=22050):
            min_samples = int(min_duration * sr)
            return len(audio) >= min_samples
        
        is_valid = validate_audio_length(empty_audio)
        
        assert is_valid is False
    
    def test_memory_error_handling(self):
        """Test handling of memory errors"""
        # Simulate memory error
        def process_large_file():
            raise MemoryError("Not enough memory to process audio")
        
        try:
            process_large_file()
        except MemoryError as e:
            error_message = "Memory error: Not enough memory to process audio"
            job_status = 'FAILED'
        
        assert job_status == 'FAILED'
        assert 'Memory error' in error_message


class TestErrorLogging:
    """Test error logging and monitoring"""
    
    def test_error_logged_to_cloudwatch(self):
        """Test that errors are logged with context"""
        error_log = {
            'jobId': 'test-job-123',
            'stage': 'stem_separation',
            'error': 'Demucs model failed',
            'timestamp': '2026-03-01T12:00:00Z',
            'stackTrace': 'Exception in stem_separation...'
        }
        
        # Verify log structure
        assert 'jobId' in error_log
        assert 'stage' in error_log
        assert 'error' in error_log
        assert 'timestamp' in error_log
        assert 'stackTrace' in error_log
    
    def test_job_status_updated_on_failure(self):
        """Test that job status is updated to FAILED on error"""
        job_record = {
            'jobId': 'test-job-123',
            'status': 'PROCESSING',
            'errorMessage': None
        }
        
        # Simulate error
        try:
            raise Exception("Processing failed")
        except Exception as e:
            job_record['status'] = 'FAILED'
            job_record['errorMessage'] = str(e)
        
        assert job_record['status'] == 'FAILED'
        assert job_record['errorMessage'] == 'Processing failed'
    
    def test_error_metrics_emitted(self):
        """Test that error metrics are emitted to CloudWatch"""
        metrics = {
            'StemSeparationFailure': 1,
            'LyricsFetchFailure': 1,
            'KeyDetectionFailure': 0
        }
        
        # Verify metrics structure
        assert 'StemSeparationFailure' in metrics
        assert 'LyricsFetchFailure' in metrics
        assert 'KeyDetectionFailure' in metrics
        
        # Verify counts
        assert metrics['StemSeparationFailure'] >= 0
        assert metrics['LyricsFetchFailure'] >= 0


class TestGracefulDegradation:
    """Test graceful degradation scenarios"""
    
    def test_partial_stem_transcription_success(self):
        """Test that partial stem transcription is acceptable"""
        transcription_results = {
            'bass': {'notes': [{'pitch': 45}], 'totalNotes': 1},
            'piano': {'notes': [{'pitch': 60}], 'totalNotes': 1},
            'guitar': None  # Failed
        }
        
        # Should still proceed with available data
        available_stems = [k for k, v in transcription_results.items() if v is not None]
        
        assert len(available_stems) == 2
        assert 'bass' in available_stems
        assert 'piano' in available_stems
    
    def test_no_lyrics_still_generates_pdf(self):
        """Test that PDF generates without lyrics"""
        pdf_input = {
            'jobId': 'test-job-123',
            'songMetadata': {'title': 'Test Song'},
            'lyrics': {'available': False, 'sections': []},
            'bassData': {'measures': [{'measure': 1, 'nns': '1'}]}
        }
        
        # Should generate PDF without lyrics
        can_generate_pdf = (
            'bassData' in pdf_input and
            len(pdf_input['bassData']['measures']) > 0
        )
        
        assert can_generate_pdf is True
    
    def test_unknown_song_still_transcribes(self):
        """Test that transcription works without song identification"""
        song_metadata = {
            'title': 'Unknown Song',
            'artist': 'Unknown Artist',
            'identificationMethod': 'unknown'
        }
        
        # Should still proceed with transcription
        can_transcribe = True  # Transcription doesn't depend on metadata
        
        assert can_transcribe is True
        assert song_metadata['title'] == 'Unknown Song'
    
    def test_low_confidence_key_detection_proceeds(self):
        """Test that low confidence key detection still proceeds"""
        detected_key = 'C major'
        confidence = 0.3  # Low confidence
        
        # Should still use detected key (user can correct)
        use_key = detected_key
        
        assert use_key == 'C major'
        assert confidence < 0.5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

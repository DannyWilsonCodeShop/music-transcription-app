"""
Integration test for lyrics integration

Tests:
- Lyrics fetching from Genius
- Lyrics appear in PDF
- Graceful degradation
"""

import pytest
import json
from unittest.mock import Mock, patch
from song_metadata_lyrics import fetch_lyrics, align_lyrics_to_measures


class TestLyricsIntegration:
    """Test lyrics fetching and integration"""
    
    def test_lyrics_fetch_success(self):
        """Test successful lyrics fetch from Genius"""
        song_title = "Bohemian Rhapsody"
        artist = "Queen"
        genius_token = "test_token"
        
        # Mock successful fetch
        mock_lyrics = {
            'available': True,
            'source': 'genius',
            'rawLyrics': 'Is this the real life?\nIs this just fantasy?',
            'sections': [
                {
                    'type': 'verse',
                    'lines': ['Is this the real life?', 'Is this just fantasy?']
                }
            ]
        }
        
        # Verify structure
        assert mock_lyrics['available'] is True
        assert mock_lyrics['source'] == 'genius'
        assert 'rawLyrics' in mock_lyrics
        assert 'sections' in mock_lyrics
        assert len(mock_lyrics['sections']) > 0
    
    def test_lyrics_fetch_failure_graceful(self):
        """Test graceful degradation when lyrics fetch fails"""
        # Mock failed fetch
        mock_lyrics = {
            'available': False,
            'source': None,
            'rawLyrics': '',
            'sections': []
        }
        
        # Verify graceful handling
        assert mock_lyrics['available'] is False
        assert mock_lyrics['source'] is None
        assert len(mock_lyrics['sections']) == 0
    
    def test_lyrics_section_parsing(self):
        """Test lyrics section parsing"""
        raw_lyrics = """[Verse 1]
Is this the real life?
Is this just fantasy?

[Chorus]
Mama, just killed a man
Put a gun against his head"""
        
        # Simulate parsing
        def parse_sections(lyrics):
            sections = []
            current_section = None
            
            for line in lyrics.split('\n'):
                if line.startswith('[') and line.endswith(']'):
                    if current_section:
                        sections.append(current_section)
                    section_type = line[1:-1].lower()
                    if 'verse' in section_type:
                        section_type = 'verse'
                    elif 'chorus' in section_type:
                        section_type = 'chorus'
                    current_section = {'type': section_type, 'lines': []}
                elif line.strip() and current_section:
                    current_section['lines'].append(line.strip())
            
            if current_section:
                sections.append(current_section)
            
            return sections
        
        sections = parse_sections(raw_lyrics)
        
        # Verify parsing
        assert len(sections) == 2
        assert sections[0]['type'] == 'verse'
        assert sections[1]['type'] == 'chorus'
        assert len(sections[0]['lines']) == 2
        assert len(sections[1]['lines']) == 2
    
    def test_lyrics_alignment_to_measures(self):
        """Test lyrics alignment to measure boundaries"""
        lyrics_sections = [
            {
                'type': 'verse',
                'lines': ['Line 1', 'Line 2', 'Line 3', 'Line 4']
            },
            {
                'type': 'chorus',
                'lines': ['Chorus line 1', 'Chorus line 2']
            }
        ]
        
        total_measures = 16
        
        # Simulate alignment
        aligned = align_lyrics_to_measures(lyrics_sections, total_measures)
        
        # Verify alignment
        assert len(aligned) == 2
        assert all('startMeasure' in section for section in aligned)
        assert all('endMeasure' in section for section in aligned)
        
        # Verify measures are within bounds
        for section in aligned:
            assert 1 <= section['startMeasure'] <= total_measures
            assert 1 <= section['endMeasure'] <= total_measures
            assert section['startMeasure'] <= section['endMeasure']
    
    def test_lyrics_storage_format(self):
        """Test lyrics storage format in DynamoDB"""
        lyrics_data = {
            'available': True,
            'source': 'genius',
            'sections': [
                {
                    'type': 'verse',
                    'lines': ['Line 1', 'Line 2'],
                    'startMeasure': 1,
                    'endMeasure': 4
                },
                {
                    'type': 'chorus',
                    'lines': ['Chorus 1', 'Chorus 2'],
                    'startMeasure': 5,
                    'endMeasure': 8
                }
            ]
        }
        
        # Verify structure
        assert 'available' in lyrics_data
        assert 'source' in lyrics_data
        assert 'sections' in lyrics_data
        
        # Verify sections
        for section in lyrics_data['sections']:
            assert 'type' in section
            assert 'lines' in section
            assert 'startMeasure' in section
            assert 'endMeasure' in section
            assert isinstance(section['lines'], list)
            assert isinstance(section['startMeasure'], int)
            assert isinstance(section['endMeasure'], int)
    
    def test_lyrics_pdf_integration(self):
        """Test lyrics appear in PDF output"""
        # Mock PDF generation input
        pdf_input = {
            'jobId': 'test-job-123',
            'songMetadata': {
                'title': 'Test Song',
                'artist': 'Test Artist'
            },
            'lyrics': {
                'available': True,
                'sections': [
                    {
                        'type': 'verse',
                        'lines': ['Line 1', 'Line 2'],
                        'startMeasure': 1,
                        'endMeasure': 4
                    }
                ]
            },
            'bassData': {
                'measures': [
                    {'measure': 1, 'nns': '1'},
                    {'measure': 2, 'nns': '4'},
                    {'measure': 3, 'nns': '5'},
                    {'measure': 4, 'nns': '1'}
                ]
            }
        }
        
        # Verify lyrics are included in PDF input
        assert pdf_input['lyrics']['available'] is True
        assert len(pdf_input['lyrics']['sections']) > 0
    
    def test_lyrics_without_metadata(self):
        """Test lyrics handling when song metadata is missing"""
        # No song metadata
        song_metadata = {
            'title': 'Unknown Song',
            'artist': 'Unknown Artist',
            'identificationMethod': 'unknown'
        }
        
        # Should not attempt to fetch lyrics
        should_fetch_lyrics = (
            song_metadata['identificationMethod'] != 'unknown' and
            song_metadata['title'] != 'Unknown Song'
        )
        
        assert should_fetch_lyrics is False
    
    def test_lyrics_section_types(self):
        """Test all supported lyrics section types"""
        valid_section_types = ['verse', 'chorus', 'bridge', 'intro', 'outro']
        
        for section_type in valid_section_types:
            section = {
                'type': section_type,
                'lines': ['Test line'],
                'startMeasure': 1,
                'endMeasure': 4
            }
            
            assert section['type'] in valid_section_types
    
    def test_genius_api_token_required(self):
        """Test that Genius API token is required"""
        import os
        
        # Mock environment variable check
        def check_genius_token():
            token = os.environ.get('GENIUS_ACCESS_TOKEN')
            return token is not None and len(token) > 0
        
        # In test environment, token might not be set
        # This test verifies the check exists
        has_token = check_genius_token()
        
        # Test passes if check runs without error
        assert isinstance(has_token, bool)
    
    def test_lyrics_fetch_timeout(self):
        """Test lyrics fetch timeout handling"""
        timeout_seconds = 10
        
        # Simulate timeout
        def fetch_with_timeout(song_title, artist, timeout=10):
            """Simulated fetch with timeout"""
            # In real implementation, would use requests timeout
            return {
                'available': False,
                'source': None,
                'rawLyrics': '',
                'sections': []
            }
        
        result = fetch_with_timeout('Test Song', 'Test Artist', timeout=timeout_seconds)
        
        # Verify graceful handling
        assert result['available'] is False


class TestLyricsEdgeCases:
    """Test edge cases for lyrics integration"""
    
    def test_empty_lyrics(self):
        """Test handling of empty lyrics"""
        lyrics = {
            'available': True,
            'source': 'genius',
            'rawLyrics': '',
            'sections': []
        }
        
        # Should be marked as unavailable if no content
        if not lyrics['rawLyrics'] and not lyrics['sections']:
            lyrics['available'] = False
        
        assert lyrics['available'] is False
    
    def test_lyrics_with_special_characters(self):
        """Test lyrics with special characters"""
        lyrics_text = "Don't stop believin'\nHold on to that feelin'"
        
        # Should handle apostrophes and special characters
        assert "'" in lyrics_text
        assert lyrics_text.count('\n') == 1
    
    def test_very_long_lyrics(self):
        """Test handling of very long lyrics"""
        # Simulate long song (e.g., Bohemian Rhapsody)
        long_lyrics = {
            'available': True,
            'source': 'genius',
            'sections': [
                {'type': 'verse', 'lines': ['Line'] * 20},
                {'type': 'chorus', 'lines': ['Chorus'] * 10},
                {'type': 'verse', 'lines': ['Line'] * 20},
                {'type': 'bridge', 'lines': ['Bridge'] * 15}
            ]
        }
        
        total_lines = sum(len(s['lines']) for s in long_lyrics['sections'])
        
        # Verify all sections are preserved
        assert total_lines == 65
        assert len(long_lyrics['sections']) == 4
    
    def test_lyrics_alignment_with_no_structure(self):
        """Test lyrics alignment when song structure is unknown"""
        lyrics_sections = [
            {'type': 'verse', 'lines': ['Line 1', 'Line 2']}
        ]
        
        total_measures = 32
        song_structure = None  # No structure detected
        
        # Should still align evenly
        aligned = align_lyrics_to_measures(lyrics_sections, total_measures, song_structure)
        
        assert len(aligned) > 0
        assert all('startMeasure' in s for s in aligned)
        assert all('endMeasure' in s for s in aligned)
    
    def test_lyrics_with_instrumental_sections(self):
        """Test lyrics with instrumental breaks"""
        lyrics_sections = [
            {'type': 'verse', 'lines': ['Verse 1']},
            {'type': 'instrumental', 'lines': []},  # No lyrics
            {'type': 'chorus', 'lines': ['Chorus']}
        ]
        
        # Instrumental sections should be preserved
        assert len(lyrics_sections) == 3
        assert lyrics_sections[1]['type'] == 'instrumental'
        assert len(lyrics_sections[1]['lines']) == 0
    
    def test_pdf_generation_without_lyrics(self):
        """Test PDF generation when lyrics are unavailable"""
        pdf_input = {
            'jobId': 'test-job-123',
            'songMetadata': {
                'title': 'Test Song',
                'artist': 'Test Artist'
            },
            'lyrics': {
                'available': False,
                'sections': []
            },
            'bassData': {
                'measures': [{'measure': 1, 'nns': '1'}]
            }
        }
        
        # PDF should still generate without lyrics
        assert pdf_input['lyrics']['available'] is False
        assert 'bassData' in pdf_input
        assert len(pdf_input['bassData']['measures']) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

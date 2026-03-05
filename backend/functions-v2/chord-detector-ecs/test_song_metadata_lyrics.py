"""
Unit tests for song_metadata_lyrics.py
Tests song identification, lyrics fetching, and alignment
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from song_metadata_lyrics import (
    get_song_metadata_and_lyrics,
    _identify_song,
    _read_embedded_metadata,
    _parse_filename,
    _fetch_lyrics_from_genius,
    _search_genius,
    _match_score,
    _scrape_genius_lyrics,
    _align_lyrics_to_measures,
    _parse_lyric_sections,
    format_measure_lyrics_for_output,
)


# Test fixtures
@pytest.fixture
def sample_audio_file():
    """Create a temporary audio file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.m4a', delete=False) as f:
        # Write minimal valid audio data (not actually used in tests)
        f.write(b'fake audio data')
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def sample_lyrics():
    """Sample lyrics with sections"""
    return [
        "[Verse 1]",
        "This is the first line",
        "This is the second line",
        "[Chorus]",
        "This is the chorus",
        "Singing loud and clear",
        "[Verse 2]",
        "Another verse here",
        "With more lyrics",
    ]


@pytest.fixture
def mock_genius_response():
    """Mock Genius API search response"""
    return {
        'response': {
            'hits': [
                {
                    'result': {
                        'title': 'Test Song',
                        'url': 'https://genius.com/test-song',
                        'primary_artist': {
                            'name': 'Test Artist'
                        }
                    }
                }
            ]
        }
    }


@pytest.fixture
def mock_genius_lyrics_html():
    """Mock Genius lyrics page HTML"""
    return '''
    <html>
        <body>
            <div data-lyrics-container="true">
                [Verse 1]<br>
                First line of lyrics<br>
                Second line of lyrics<br>
            </div>
            <div data-lyrics-container="true">
                [Chorus]<br>
                Chorus line one<br>
                Chorus line two<br>
            </div>
        </body>
    </html>
    '''


# Test _parse_filename
def test_parse_filename_with_dash():
    """Test filename parsing with artist - title format"""
    result = _parse_filename('/path/to/Artist Name - Song Title.m4a')
    
    assert result['artist'] == 'Artist Name'
    assert result['title'] == 'Song Title'


def test_parse_filename_with_underscore():
    """Test filename parsing with artist_title format"""
    result = _parse_filename('/path/to/Artist_Name_Song_Title.m4a')
    
    assert result['artist'] == 'Artist_Name'
    assert result['title'] == 'Song_Title'


def test_parse_filename_with_track_number():
    """Test filename parsing with leading track number"""
    result = _parse_filename('/path/to/01 Song Title.m4a')
    
    assert result['title'] == 'Song Title'


def test_parse_filename_simple():
    """Test filename parsing with just title"""
    result = _parse_filename('/path/to/Song Title.m4a')
    
    assert result['title'] == 'Song Title'


# Test _read_embedded_metadata
@patch('song_metadata_lyrics.MutagenFile')
def test_read_embedded_metadata_success(mock_mutagen):
    """Test reading embedded metadata successfully"""
    # Mock mutagen file object
    mock_file = MagicMock()
    mock_file.get.side_effect = lambda tag: {
        'artist': ['Test Artist'],
        'title': ['Test Song'],
        'album': ['Test Album'],
        'date': ['2024']
    }.get(tag)
    
    mock_mutagen.return_value = mock_file
    
    result = _read_embedded_metadata('/path/to/audio.m4a')
    
    assert result['artist'] == 'Test Artist'
    assert result['title'] == 'Test Song'
    assert result['album'] == 'Test Album'
    assert result['year'] == '2024'


@patch('song_metadata_lyrics.MutagenFile')
def test_read_embedded_metadata_no_tags(mock_mutagen):
    """Test reading metadata when no tags present"""
    mock_file = MagicMock()
    mock_file.get.return_value = None
    mock_mutagen.return_value = mock_file
    
    result = _read_embedded_metadata('/path/to/audio.m4a')
    
    assert result['artist'] == ''
    assert result['title'] == ''


@patch('song_metadata_lyrics.MutagenFile')
def test_read_embedded_metadata_error(mock_mutagen):
    """Test error handling when reading metadata fails"""
    mock_mutagen.side_effect = Exception("File not found")
    
    result = _read_embedded_metadata('/path/to/nonexistent.m4a')
    
    assert result == {}


# Test _identify_song
def test_identify_song_user_provided():
    """Test song identification with user-provided metadata"""
    user_provided = {
        'artist': 'User Artist',
        'title': 'User Song'
    }
    
    result = _identify_song('/path/to/audio.m4a', user_provided)
    
    assert result['artist'] == 'User Artist'
    assert result['title'] == 'User Song'
    assert result['source'] == 'user_provided'
    assert result['confidence'] == 'high'


@patch('song_metadata_lyrics._read_embedded_metadata')
def test_identify_song_embedded_tags(mock_read_metadata):
    """Test song identification from embedded tags"""
    mock_read_metadata.return_value = {
        'artist': 'Embedded Artist',
        'title': 'Embedded Song',
        'album': 'Album Name'
    }
    
    result = _identify_song('/path/to/audio.m4a')
    
    assert result['artist'] == 'Embedded Artist'
    assert result['title'] == 'Embedded Song'
    assert result['source'] == 'embedded_tags'
    assert result['confidence'] == 'high'


@patch('song_metadata_lyrics._read_embedded_metadata')
def test_identify_song_from_filename(mock_read_metadata):
    """Test song identification from filename when no embedded tags"""
    mock_read_metadata.return_value = {}
    
    result = _identify_song('/path/to/Artist - Song.m4a')
    
    assert result['artist'] == 'Artist'
    assert result['title'] == 'Song'
    assert result['source'] == 'filename'
    assert result['confidence'] == 'low'


@patch('song_metadata_lyrics._read_embedded_metadata')
def test_identify_song_unknown(mock_read_metadata):
    """Test song identification when all methods fail"""
    mock_read_metadata.return_value = {}
    
    result = _identify_song('/path/to/unknown.m4a')
    
    assert result['source'] == 'unknown'
    assert result['confidence'] == 'none'


# Test _match_score
def test_match_score_exact_match():
    """Test match score with exact title match"""
    score = _match_score('Artist', 'Song Title', 'Artist', 'Song Title')
    
    assert score > 0.9  # Should be very high


def test_match_score_partial_match():
    """Test match score with partial match"""
    score = _match_score('Artist', 'Song Title', 'Artist', 'Song Title (Remix)')
    
    assert 0.5 < score < 0.9  # Should be moderate


def test_match_score_no_match():
    """Test match score with no match"""
    score = _match_score('Artist A', 'Song A', 'Artist B', 'Song B')
    
    assert score < 0.5  # Should be low


def test_match_score_case_insensitive():
    """Test that match score is case insensitive"""
    score1 = _match_score('Artist', 'Song', 'artist', 'song')
    score2 = _match_score('Artist', 'Song', 'ARTIST', 'SONG')
    
    assert abs(score1 - score2) < 0.01  # Should be nearly identical


def test_match_score_punctuation_ignored():
    """Test that punctuation is ignored in matching"""
    score = _match_score('Artist', "Don't Stop", 'Artist', 'Dont Stop')
    
    assert score > 0.9  # Should match despite punctuation difference


# Test _search_genius
@patch('song_metadata_lyrics.requests.get')
@patch('song_metadata_lyrics.GENIUS_TOKEN', 'fake_token')
def test_search_genius_success(mock_get, mock_genius_response):
    """Test successful Genius API search"""
    mock_response = Mock()
    mock_response.json.return_value = mock_genius_response
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response
    
    result = _search_genius('Test Artist', 'Test Song')
    
    assert result is not None
    assert result['title'] == 'Test Song'
    assert result['artist'] == 'Test Artist'
    assert 'url' in result


@patch('song_metadata_lyrics.requests.get')
@patch('song_metadata_lyrics.GENIUS_TOKEN', 'fake_token')
def test_search_genius_no_results(mock_get):
    """Test Genius search with no results"""
    mock_response = Mock()
    mock_response.json.return_value = {'response': {'hits': []}}
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response
    
    result = _search_genius('Unknown Artist', 'Unknown Song')
    
    assert result is None


@patch('song_metadata_lyrics.requests.get')
@patch('song_metadata_lyrics.GENIUS_TOKEN', 'fake_token')
def test_search_genius_api_error(mock_get):
    """Test Genius search with API error"""
    mock_get.side_effect = Exception("API Error")
    
    result = _search_genius('Artist', 'Song')
    
    assert result is None


# Test _scrape_genius_lyrics
@patch('song_metadata_lyrics.requests.get')
def test_scrape_genius_lyrics_success(mock_get, mock_genius_lyrics_html):
    """Test successful lyrics scraping"""
    mock_response = Mock()
    mock_response.text = mock_genius_lyrics_html
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response
    
    result = _scrape_genius_lyrics('https://genius.com/test-song')
    
    assert result is not None
    assert len(result) > 0
    assert '[Verse 1]' in result
    assert 'First line of lyrics' in result


@patch('song_metadata_lyrics.requests.get')
def test_scrape_genius_lyrics_no_container(mock_get):
    """Test lyrics scraping when no lyrics container found"""
    mock_response = Mock()
    mock_response.text = '<html><body>No lyrics here</body></html>'
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response
    
    result = _scrape_genius_lyrics('https://genius.com/test-song')
    
    assert result is None


@patch('song_metadata_lyrics.requests.get')
def test_scrape_genius_lyrics_error(mock_get):
    """Test lyrics scraping with network error"""
    mock_get.side_effect = Exception("Network error")
    
    result = _scrape_genius_lyrics('https://genius.com/test-song')
    
    assert result is None


# Test _parse_lyric_sections
def test_parse_lyric_sections(sample_lyrics):
    """Test parsing lyrics into sections"""
    sections = _parse_lyric_sections(sample_lyrics)
    
    # Should have headers and content sections
    assert len(sections) > 0
    
    # Check for headers
    headers = [s for s in sections if s['is_header']]
    assert len(headers) == 3  # [Verse 1], [Chorus], [Verse 2]
    
    # Check for content sections
    content = [s for s in sections if not s['is_header']]
    assert len(content) == 3


def test_parse_lyric_sections_no_headers():
    """Test parsing lyrics without section headers"""
    lyrics = ['Line 1', 'Line 2', 'Line 3']
    sections = _parse_lyric_sections(lyrics)
    
    assert len(sections) == 1
    assert not sections[0]['is_header']
    assert len(sections[0]['lines']) == 3


def test_parse_lyric_sections_empty():
    """Test parsing empty lyrics"""
    sections = _parse_lyric_sections([])
    
    assert len(sections) == 0


# Test _align_lyrics_to_measures
def test_align_lyrics_to_measures_basic():
    """Test basic lyrics alignment to measures"""
    lines = [
        '[Verse 1]',
        'First line',
        'Second line',
        '[Chorus]',
        'Chorus line',
    ]
    
    result = _align_lyrics_to_measures(
        lines,
        total_measures=20,
        tempo=120.0,
        time_signature='4/4',
        first_downbeat=0.5
    )
    
    assert len(result) == 20
    assert all('measure' in m for m in result)
    assert all('lyric' in m for m in result)
    assert all('section' in m for m in result)
    
    # Check that some measures have lyrics
    lyrics_count = sum(1 for m in result if m['lyric'])
    assert lyrics_count > 0


def test_align_lyrics_to_measures_no_lyrics():
    """Test alignment with no lyrics"""
    result = _align_lyrics_to_measures(
        [],
        total_measures=10,
        tempo=120.0,
        time_signature='4/4',
        first_downbeat=0.5
    )
    
    assert len(result) == 10
    assert all(m['lyric'] == '' for m in result)


def test_align_lyrics_to_measures_many_lyrics():
    """Test alignment with many lyrics for few measures"""
    lines = [f'Line {i}' for i in range(50)]
    
    result = _align_lyrics_to_measures(
        lines,
        total_measures=10,
        tempo=120.0,
        time_signature='4/4',
        first_downbeat=0.5
    )
    
    assert len(result) == 10
    # Should distribute lyrics across measures


# Test format_measure_lyrics_for_output
def test_format_measure_lyrics_for_output():
    """Test formatting measure lyrics for output"""
    measure_lyrics = [
        {'measure': 1, 'lyric': 'First line', 'section': 'Verse 1'},
        {'measure': 2, 'lyric': 'Second line', 'section': ''},
        {'measure': 3, 'lyric': '', 'section': ''},
    ]
    
    measures = [
        {'measure': 1, 'nns': '1 3 5'},
        {'measure': 2, 'nns': '4 5 1'},
        {'measure': 3, 'nns': '1 1 1'},
    ]
    
    result = format_measure_lyrics_for_output(measure_lyrics, measures)
    
    assert len(result) == 3
    assert result[0]['lyric'] == 'First line'
    assert result[0]['section'] == 'Verse 1'
    assert result[1]['lyric'] == 'Second line'
    assert result[2]['lyric'] == ''


# Test _fetch_lyrics_from_genius
@patch('song_metadata_lyrics._search_genius')
@patch('song_metadata_lyrics._scrape_genius_lyrics')
@patch('song_metadata_lyrics.GENIUS_TOKEN', 'fake_token')
def test_fetch_lyrics_from_genius_success(mock_scrape, mock_search):
    """Test successful lyrics fetching from Genius"""
    mock_search.return_value = {
        'title': 'Test Song',
        'artist': 'Test Artist',
        'url': 'https://genius.com/test-song'
    }
    mock_scrape.return_value = ['Line 1', 'Line 2', 'Line 3']
    
    result = _fetch_lyrics_from_genius('Test Artist', 'Test Song')
    
    assert result['found'] is True
    assert result['line_count'] == 3
    assert 'url' in result


@patch('song_metadata_lyrics._search_genius')
@patch('song_metadata_lyrics.GENIUS_TOKEN', 'fake_token')
def test_fetch_lyrics_from_genius_not_found(mock_search):
    """Test lyrics fetching when song not found"""
    mock_search.return_value = None
    
    result = _fetch_lyrics_from_genius('Unknown Artist', 'Unknown Song')
    
    assert result['found'] is False
    assert 'reason' in result


@patch('song_metadata_lyrics.GENIUS_TOKEN', '')
def test_fetch_lyrics_from_genius_no_token():
    """Test lyrics fetching without API token"""
    result = _fetch_lyrics_from_genius('Artist', 'Song')
    
    assert result['found'] is False
    assert 'GENIUS_ACCESS_TOKEN' in result['reason']


# Test get_song_metadata_and_lyrics (integration)
@patch('song_metadata_lyrics._identify_song')
@patch('song_metadata_lyrics._fetch_lyrics_from_genius')
def test_get_song_metadata_and_lyrics_success(mock_fetch, mock_identify, sample_audio_file):
    """Test full metadata and lyrics retrieval"""
    mock_identify.return_value = {
        'artist': 'Test Artist',
        'title': 'Test Song',
        'source': 'embedded_tags'
    }
    
    mock_fetch.return_value = {
        'found': True,
        'url': 'https://genius.com/test',
        'lines': ['Line 1', 'Line 2'],
        'line_count': 2,
        'matched_artist': 'Test Artist',
        'matched_title': 'Test Song'
    }
    
    result = get_song_metadata_and_lyrics(
        sample_audio_file,
        tempo=120.0,
        time_signature='4/4',
        total_measures=10,
        first_downbeat=0.5
    )
    
    assert result['lyrics_available'] is True
    assert 'metadata' in result
    assert 'measure_lyrics' in result
    assert len(result['measure_lyrics']) == 10


@patch('song_metadata_lyrics._identify_song')
def test_get_song_metadata_and_lyrics_no_identification(mock_identify, sample_audio_file):
    """Test when song cannot be identified"""
    mock_identify.return_value = {
        'artist': '',
        'title': '',
        'source': 'unknown'
    }
    
    result = get_song_metadata_and_lyrics(
        sample_audio_file,
        tempo=120.0,
        time_signature='4/4',
        total_measures=10,
        first_downbeat=0.5
    )
    
    assert result['lyrics_available'] is False
    assert 'Song could not be identified' in result['reason']


@patch('song_metadata_lyrics._identify_song')
@patch('song_metadata_lyrics._fetch_lyrics_from_genius')
def test_get_song_metadata_and_lyrics_no_lyrics(mock_fetch, mock_identify, sample_audio_file):
    """Test when lyrics are not available"""
    mock_identify.return_value = {
        'artist': 'Test Artist',
        'title': 'Test Song',
        'source': 'embedded_tags'
    }
    
    mock_fetch.return_value = {
        'found': False,
        'reason': 'Lyrics not found'
    }
    
    result = get_song_metadata_and_lyrics(
        sample_audio_file,
        tempo=120.0,
        time_signature='4/4',
        total_measures=10,
        first_downbeat=0.5
    )
    
    assert result['lyrics_available'] is False
    assert 'Lyrics not found' in result['reason']


# Test error handling
def test_parse_filename_edge_cases():
    """Test filename parsing with edge cases"""
    # Empty filename
    result = _parse_filename('')
    assert 'title' in result
    
    # Very long filename
    long_name = 'A' * 500 + '.m4a'
    result = _parse_filename(long_name)
    assert 'title' in result


def test_align_lyrics_edge_cases():
    """Test lyrics alignment with edge cases"""
    # Zero measures
    result = _align_lyrics_to_measures(['Line 1'], 0, 120.0, '4/4', 0.5)
    assert len(result) == 0
    
    # Very fast tempo
    result = _align_lyrics_to_measures(['Line 1'], 10, 300.0, '4/4', 0.5)
    assert len(result) == 10


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

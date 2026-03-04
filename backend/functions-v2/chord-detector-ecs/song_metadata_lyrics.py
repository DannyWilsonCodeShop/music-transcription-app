"""
Song Metadata & Lyrics Fetcher
Identifies the uploaded song and fetches synced lyrics for measure-by-measure display.

Dependencies to add to requirements.txt:
  mutagen
  requests
  beautifulsoup4

Environment variable required:
  GENIUS_ACCESS_TOKEN — get free token at https://genius.com/api-clients
"""

import os, re, time, logging, unicodedata
from typing import Dict, List, Optional, Tuple
import requests

log = logging.getLogger(__name__)

GENIUS_BASE_URL = "https://api.genius.com"
GENIUS_TOKEN    = os.environ.get('GENIUS_ACCESS_TOKEN', '')
REQUEST_DELAY   = 0.3
NOTE_NAMES      = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']


def get_song_metadata_and_lyrics(
    audio_path: str,
    tempo: float,
    time_signature: str,
    total_measures: int,
    first_downbeat: float,
    user_provided: Optional[Dict] = None
) -> Dict:
    log.info("=" * 70)
    log.info("SONG METADATA & LYRICS")

    metadata = _identify_song(audio_path, user_provided)
    log.info(f"  Song: {metadata.get('artist')} — {metadata.get('title')} ({metadata.get('source')})")

    if not metadata.get('title'):
        return {'metadata': metadata, 'lyrics_available': False,
                'reason': 'Song could not be identified', 'measure_lyrics': []}

    lyrics_data = _fetch_lyrics_from_genius(metadata['artist'], metadata['title'])

    if not lyrics_data.get('found'):
        return {'metadata': metadata, 'lyrics_available': False,
                'reason': lyrics_data.get('reason', 'Lyrics not found'), 'measure_lyrics': []}

    log.info(f"  Lyrics: {lyrics_data['line_count']} lines")

    measure_lyrics = _align_lyrics_to_measures(
        lyrics_data['lines'], total_measures, tempo, time_signature, first_downbeat
    )

    return {
        'metadata': metadata, 'lyrics_available': True,
        'genius_url': lyrics_data.get('url'),
        'measure_lyrics': measure_lyrics,
        'full_lyrics': lyrics_data['lines'],
        'line_count': lyrics_data['line_count'],
    }


def _identify_song(audio_path: str, user_provided: Optional[Dict] = None) -> Dict:
    if user_provided and user_provided.get('title'):
        return {**user_provided, 'source': 'user_provided', 'confidence': 'high'}
    meta = _read_embedded_metadata(audio_path)
    if meta.get('title'):
        return {**meta, 'source': 'embedded_tags', 'confidence': 'high'}
    meta = _parse_filename(audio_path)
    if meta.get('title'):
        return {**meta, 'source': 'filename', 'confidence': 'low'}
    return {'artist': '', 'title': '', 'source': 'unknown', 'confidence': 'none'}


def _read_embedded_metadata(audio_path: str) -> Dict:
    try:
        from mutagen import File as MutagenFile
        f = MutagenFile(audio_path, easy=True)
        if f is None:
            return {}
        def _get(tag):
            v = f.get(tag)
            return str(v[0]) if v else ''
        return {'artist': _get('artist') or _get('albumartist'),
                'title': _get('title'), 'album': _get('album'),
                'year': _get('date') or _get('year')}
    except Exception as e:
        log.warning(f"  Metadata read error: {e}")
        return {}


def _parse_filename(audio_path: str) -> Dict:
    name = os.path.splitext(os.path.basename(audio_path))[0]
    if ' - ' in name:
        parts = name.split(' - ', 1)
        return {'artist': parts[0].strip(), 'title': parts[1].strip()}
    if '_' in name and ' ' not in name:
        parts = name.split('_', 1)
        return {'artist': parts[0].strip(), 'title': parts[1].strip()}
    cleaned = re.sub(r'^\d+[\s\.\-_]+', '', name).strip()
    return {'artist': '', 'title': cleaned or name}


def _fetch_lyrics_from_genius(artist: str, title: str) -> Dict:
    if not GENIUS_TOKEN:
        return {'found': False, 'reason': 'GENIUS_ACCESS_TOKEN not configured'}
    song = _search_genius(artist, title)
    if not song:
        return {'found': False, 'reason': f'No Genius match for "{artist} — {title}"'}
    lines = _scrape_genius_lyrics(song['url'])
    if not lines:
        return {'found': False, 'reason': 'Could not parse lyrics page'}
    return {'found': True, 'url': song['url'], 'lines': lines,
            'line_count': len(lines), 'matched_artist': song['artist'],
            'matched_title': song['title']}


def _search_genius(artist: str, title: str) -> Optional[Dict]:
    try:
        time.sleep(REQUEST_DELAY)
        resp = requests.get(f"{GENIUS_BASE_URL}/search",
            params={'q': f"{artist} {title}".strip()},
            headers={'Authorization': f'Bearer {GENIUS_TOKEN}'}, timeout=10)
        resp.raise_for_status()
        hits = resp.json().get('response', {}).get('hits', [])
        best, best_score = None, 0
        for hit in hits[:5]:
            r = hit.get('result', {})
            score = _match_score(artist, title,
                r.get('primary_artist', {}).get('name', ''), r.get('title', ''))
            if score > best_score:
                best_score = score
                best = {'title': r.get('title', ''), 'url': r.get('url', ''),
                        'artist': r.get('primary_artist', {}).get('name', ''), 'score': score}
        return best if best_score >= 0.5 else None
    except Exception as e:
        log.error(f"  Genius API error: {e}")
        return None


def _match_score(q_artist, q_title, r_artist, r_title) -> float:
    def norm(s):
        s = unicodedata.normalize('NFD', s.lower().strip())
        return re.sub(r'[^\w\s]', '', s)
    def overlap(a, b):
        ta, tb = set(norm(a).split()), set(norm(b).split())
        return len(ta & tb) / len(ta | tb) if ta and tb else 0.0
    return overlap(q_title, r_title) * 0.7 + (overlap(q_artist, r_artist) if q_artist else 0.5) * 0.3


def _scrape_genius_lyrics(url: str) -> Optional[List[str]]:
    try:
        from bs4 import BeautifulSoup
        time.sleep(REQUEST_DELAY)
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        containers = (soup.find_all('div', attrs={'data-lyrics-container': 'true'}) or
                      soup.find_all('div', class_=re.compile(r'Lyrics__Container')))
        if not containers:
            return None
        lines = []
        for c in containers:
            for br in c.find_all('br'):
                br.replace_with('\n')
            for line in c.get_text(separator='\n').split('\n'):
                cleaned = line.strip()
                if cleaned and not cleaned.startswith('You might also like'):
                    lines.append(cleaned)
        return lines or None
    except Exception as e:
        log.error(f"  Genius scrape error: {e}")
        return None


def _align_lyrics_to_measures(lines, total_measures, tempo, time_signature,
                                first_downbeat) -> List[Dict]:
    beats_per_measure = int(time_signature.split('/')[0])
    sections = _parse_lyric_sections(lines)
    total_sung = sum(len(s['lines']) for s in sections if not s['is_header'])

    measure_lyrics = [{'measure': i + 1, 'lyric': '', 'section': ''} for i in range(total_measures)]
    if total_sung == 0:
        return measure_lyrics

    instrumental_buffer = min(8, total_measures // 8)
    measures_per_line = max(1, (total_measures - instrumental_buffer * 2) / total_sung)
    current_measure = instrumental_buffer
    current_section = ''

    for section in sections:
        if section['is_header']:
            current_section = section['label']
            if current_measure < total_measures:
                measure_lyrics[current_measure]['section'] = current_section
                current_measure += 1
            continue
        for line in section['lines']:
            if current_measure >= total_measures:
                break
            measure_lyrics[current_measure]['lyric'] = line
            measure_lyrics[current_measure]['section'] = current_section
            current_section = ''
            current_measure += int(round(measures_per_line))

    return measure_lyrics


def _parse_lyric_sections(lines: List[str]) -> List[Dict]:
    sections, current = [], {'label': '', 'lines': [], 'is_header': False}
    header_re = re.compile(r'^\[.+\]$')
    for line in lines:
        if header_re.match(line):
            if current['lines']:
                sections.append(current)
            sections.append({'label': line, 'lines': [], 'is_header': True})
            current = {'label': line, 'lines': [], 'is_header': False}
        else:
            current['lines'].append(line)
    if current['lines']:
        sections.append(current)
    return sections


def format_measure_lyrics_for_output(measure_lyrics: List[Dict], measures: List[Dict]) -> List[Dict]:
    lyric_map = {m['measure']: m for m in measure_lyrics}
    return [{**m, 'lyric': lyric_map.get(m['measure'], {}).get('lyric', ''),
             'section': lyric_map.get(m['measure'], {}).get('section', '')}
            for m in measures]

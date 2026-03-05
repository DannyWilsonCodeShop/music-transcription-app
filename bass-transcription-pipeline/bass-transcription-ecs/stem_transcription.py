"""
Multi-Stem Transcription Handler
Extracts and transcribes piano and guitar stems using Demucs mdx_extra.
Supports NNS note-by-note output, chord detection, or both.

Demucs mdx_extra stem indices:
  sources[0] = drums
  sources[1] = bass
  sources[2] = other (piano, keys, synths)
  sources[3] = vocals
  sources[4] = guitar  (mdx_extra_q model only — see note below)

NOTE: Standard mdx_extra separates into 4 stems: drums, bass, other, vocals.
The 'other' stem contains piano, keys, and any non-guitar melodic instruments.
mdx_extra_q provides a 6-stem split including guitar as a separate stem.
This module handles both models gracefully.
"""

import numpy as np
import librosa
import logging
from typing import Dict, List, Tuple, Optional

log = logging.getLogger(__name__)

STEM_DRUMS  = 0
STEM_BASS   = 1
STEM_OTHER  = 2
STEM_VOCALS = 3
STEM_GUITAR_Q = 4
STEM_PIANO_Q  = 5

INTERVAL_TO_NNS = {
    0: '1', 1: 'b2', 2: '2', 3: 'b3', 4: '3', 5: '4',
    6: 'b5', 7: '5', 8: 'b6', 9: '6', 10: 'b7', 11: '7'
}

NOTE_NAMES = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']

CHORD_TEMPLATES = {
    'maj':  [0, 4, 7],
    'min':  [0, 3, 7],
    'dom7': [0, 4, 7, 10],
    'maj7': [0, 4, 7, 11],
    'min7': [0, 3, 7, 10],
    'dim':  [0, 3, 6],
    'aug':  [0, 4, 8],
    'sus4': [0, 5, 7],
    'sus2': [0, 2, 7],
}


def transcribe_stems(
    sources,
    sr: int,
    tempo: float,
    time_signature: str,
    first_downbeat: float,
    key_info: Dict,
    output_mode: str = 'both',
    stems_to_process: List[str] = None,
    model_type: str = 'mdx_extra'
) -> Dict:
    if stems_to_process is None:
        stems_to_process = ['piano', 'guitar']

    log.info("=" * 70)
    log.info("MULTI-STEM TRANSCRIPTION")
    log.info(f"  Stems: {stems_to_process} | Mode: {output_mode} | Key: {key_info['relativeMajor']} major")
    log.info("=" * 70)

    results = {}
    for stem_name in stems_to_process:
        audio = extract_stem_audio(sources, stem_name, sr, model_type)
        if audio is None:
            results[stem_name] = {'available': False, 'reason': f'Not separated by {model_type}'}
            continue

        stem_result = {'available': True, 'stem': stem_name, 'output_mode': output_mode}

        if output_mode in ('notes', 'both'):
            stem_result['notes_data'] = transcribe_stem_notes(
                audio, 22050, tempo, time_signature, first_downbeat, key_info
            )

        if output_mode in ('chords', 'both'):
            stem_result['chords_data'] = detect_stem_chords(
                audio, 22050, tempo, time_signature, first_downbeat, key_info
            )

        results[stem_name] = stem_result

    return results


def extract_stem_audio(sources, stem_name: str, original_sr: int, model_type: str = 'mdx_extra') -> Optional[np.ndarray]:
    import torch

    stem_index = _get_stem_index(stem_name, model_type, sources.shape[0])
    if stem_index is None:
        return None

    if isinstance(sources, torch.Tensor):
        stem_mono = torch.mean(sources[stem_index], dim=0).numpy()
    else:
        stem_mono = np.mean(sources[stem_index], axis=0)

    if original_sr != 22050:
        stem_mono = librosa.resample(stem_mono, orig_sr=original_sr, target_sr=22050)

    max_val = np.max(np.abs(stem_mono))
    if max_val > 0:
        stem_mono = stem_mono / max_val * 0.9

    return stem_mono


def _get_stem_index(stem_name: str, model_type: str, n_stems: int) -> Optional[int]:
    name = stem_name.lower()
    if model_type == 'mdx_extra_q' and n_stems >= 6:
        mapping = {'drums': 0, 'bass': 1, 'other': 2, 'vocals': 3, 'guitar': 4, 'piano': 5}
    else:
        mapping = {'drums': 0, 'bass': 1, 'other': 2, 'piano': 2, 'vocals': 3, 'guitar': None}

    index = mapping.get(name)
    if index is None:
        log.warning(f"Stem '{name}' not available in {model_type}. Use mdx_extra_q for guitar.")
    elif index >= n_stems:
        log.warning(f"Stem index {index} out of range")
        return None
    return index


def transcribe_stem_notes(audio, sr, tempo, time_signature, first_downbeat, key_info) -> Dict:
    notes = _detect_notes_basic_pitch(audio, sr, tempo)
    if notes is None:
        notes = _detect_notes_onset_fallback(audio, sr)

    notes = _filter_by_frequency_range(notes)
    notes = [n for n in notes if n.get('velocity', 1.0) >= 0.45]

    eighth_duration = 60.0 / tempo / 2
    notes = [n for n in notes if (n['end'] - n['start']) >= eighth_duration * 0.60]
    notes = _quantize_to_eighth_grid(notes, tempo, time_signature, first_downbeat)
    notes = _convert_notes_to_nns(notes, key_info)

    duration = len(audio) / sr
    measures = _group_notes_by_measure(notes, tempo, time_signature, first_downbeat, duration)

    return {
        'notes': notes, 'measures': measures,
        'totalNotes': len(notes), 'totalMeasures': len(measures),
        'key': key_info['key'], 'mode': key_info['mode'],
        'relativeMajor': key_info['relativeMajor'],
        'quantizationResolution': '8th',
    }


def _detect_notes_basic_pitch(audio, sr, tempo):
    try:
        import tempfile, soundfile as sf
        from basic_pitch.inference import predict
        from basic_pitch import ICASSP_2022_MODEL_PATH

        if sr != 22050:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=22050)

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            sf.write(f.name, audio, 22050)
            tmp_path = f.name

        try:
            eighth_note_ms = int((60.0 / tempo / 2) * 1000) if tempo else 125
            _, _, note_events = predict(
                tmp_path,
                ICASSP_2022_MODEL_PATH,
                minimum_note_length=eighth_note_ms * 0.6,
                minimum_frequency=librosa.note_to_hz('C2'),
                maximum_frequency=librosa.note_to_hz('C7'),
                onset_threshold=0.5,
                frame_threshold=0.3,
            )
        finally:
            import os
            os.path.exists(tmp_path) and os.unlink(tmp_path)

        return [{'pitch': int(n[2]), 'start': float(n[0]), 'end': float(n[1]),
                 'velocity': float(n[3]), 'note_name': librosa.midi_to_note(int(n[2]))}
                for n in note_events]
    except Exception as e:
        log.warning(f"Basic Pitch failed: {e}")
        return None


def _detect_notes_onset_fallback(audio, sr):
    onset_frames = librosa.onset.onset_detect(y=audio, sr=sr, units='samples')
    onset_times = librosa.samples_to_time(onset_frames, sr=sr)
    C = np.abs(librosa.cqt(audio, sr=sr, fmin=librosa.note_to_hz('C2'), n_bins=72))
    notes = []
    for i, t in enumerate(onset_times):
        end = onset_times[i + 1] if i + 1 < len(onset_times) else t + 0.5
        frame = min(librosa.time_to_frames(t, sr=sr), C.shape[1] - 1)
        pitch_bin = np.argmax(C[:, frame])
        midi = int(np.clip(librosa.hz_to_midi(
            librosa.cqt_frequencies(72, fmin=librosa.note_to_hz('C2'))[pitch_bin]), 24, 108))
        notes.append({'pitch': midi, 'start': float(t), 'end': float(end),
                      'velocity': float(C[pitch_bin, frame] / (np.max(C) + 1e-8)),
                      'note_name': librosa.midi_to_note(midi)})
    return notes


def _filter_by_frequency_range(notes, midi_min=36, midi_max=96):
    return [n for n in notes if midi_min <= n['pitch'] <= midi_max]


def _quantize_to_eighth_grid(notes, tempo, time_signature, first_downbeat):
    beat_duration = 60.0 / tempo
    eighth_duration = beat_duration / 2
    beats_per_measure = int(time_signature.split('/')[0])
    quantized = []

    for note in notes:
        t = note['start'] - first_downbeat
        if t < 0:
            continue
        idx = round(t / eighth_duration)
        q_time = first_downbeat + (idx * eighth_duration)
        distance = abs(note['start'] - q_time)
        conf = note.get('velocity', 1.0)
        tolerance = eighth_duration * (0.40 if conf >= 0.65 else 0.30)

        beats_from_db = idx / 2
        measure = int(beats_from_db / beats_per_measure) + 1
        beat_in_measure = (beats_from_db % beats_per_measure) + 1

        quantized.append({**note, 'quantized_start': q_time, 'measure': measure,
                          'beat': beat_in_measure, 'subdivision': (idx % 2) + 1,
                          'eighth_index': idx, 'off_grid': distance > tolerance})
    return quantized


def _convert_notes_to_nns(notes, key_info):
    key_index = NOTE_NAMES.index(key_info['relativeMajor'])
    for note in notes:
        note['nns'] = INTERVAL_TO_NNS.get((note['pitch'] % 12 - key_index) % 12, '1')
    return notes


def _group_notes_by_measure(notes, tempo, time_signature, first_downbeat, duration):
    beats_per_measure = int(time_signature.split('/')[0])
    beat_duration = 60.0 / tempo
    measure_duration = beat_duration * beats_per_measure
    total_measures = int((duration - first_downbeat) / measure_duration) + 1
    measures = []

    for m in range(1, total_measures + 1):
        m_start = first_downbeat + ((m - 1) * measure_duration)
        m_end = m_start + measure_duration
        m_notes = [n for n in notes if m_start <= n['quantized_start'] < m_end]
        if not m_notes:
            continue
        measures.append({
            'measure': m, 'start': m_start, 'end': m_end, 'notes': m_notes,
            'nns': [n['nns'] for n in m_notes],
            'noteNames': [n['note_name'] for n in m_notes],
            'nns_display': ' '.join(n['nns'] for n in m_notes),
            'notes_display': ' '.join(n['note_name'] for n in m_notes),
            'attack_count': len(m_notes),
            'off_grid_count': sum(1 for n in m_notes if n.get('off_grid')),
        })
    return measures


def detect_stem_chords(audio, sr, tempo, time_signature, first_downbeat, key_info) -> Dict:
    beats_per_measure = int(time_signature.split('/')[0])
    beat_duration = 60.0 / tempo
    measure_duration = beat_duration * beats_per_measure
    duration = len(audio) / sr
    hop_length = 512

    chroma = librosa.feature.chroma_cqt(y=audio, sr=sr, hop_length=hop_length)
    times = librosa.frames_to_time(np.arange(chroma.shape[1]), sr=sr, hop_length=hop_length)
    key_index = NOTE_NAMES.index(key_info['relativeMajor'])
    total_measures = int((duration - first_downbeat) / measure_duration) + 1
    chord_sequence = []

    for m in range(1, total_measures + 1):
        m_start = first_downbeat + ((m - 1) * measure_duration)
        m_end = m_start + measure_duration
        mask = (times >= m_start) & (times < m_end)
        if not np.any(mask):
            continue
        mean_chroma = np.mean(chroma[:, mask], axis=1)
        root, quality, confidence = _match_chord_template(mean_chroma)
        nns_root = INTERVAL_TO_NNS.get((root - key_index) % 12, '1')
        chord_sequence.append({
            'measure': m, 'start': m_start,
            'chord_root': NOTE_NAMES[root], 'chord_quality': quality,
            'nns_chord': _format_nns_chord(nns_root, quality),
            'confidence': float(confidence),
        })

    return {'chord_sequence': chord_sequence, 'key': key_info['key'],
            'mode': key_info['mode'], 'relativeMajor': key_info['relativeMajor']}


def _match_chord_template(chroma_vector):
    best_score, best_root, best_quality = -1, 0, 'maj'
    chroma_norm = chroma_vector / (np.sum(chroma_vector) + 1e-8)
    for root in range(12):
        for quality, intervals in CHORD_TEMPLATES.items():
            template = np.zeros(12)
            for i in intervals:
                template[(root + i) % 12] = 1.0
            template /= np.sum(template)
            score = float(np.dot(chroma_norm, template))
            if score > best_score:
                best_score, best_root, best_quality = score, root, quality
    return best_root, best_quality, best_score


def _format_nns_chord(nns_root, quality):
    return nns_root + {'maj': '', 'min': '-', 'dom7': '7', 'maj7': 'maj7',
                        'min7': '-7', 'dim': 'dim', 'aug': '+',
                        'sus4': 'sus4', 'sus2': 'sus2'}.get(quality, '')

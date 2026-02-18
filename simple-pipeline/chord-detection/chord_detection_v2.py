"""
Chord Detection V2 - Beat-Aligned 16th-Note Resolution System

This module implements a complete rewrite of the chord detection algorithm:
- Beat-aligned analysis with 16th-note subdivisions
- Stem separation (removes drums and vocals)
- CQT chromagram with high resolution
- Template matching with HMM smoothing
- ML-based key detection

Author: Music Transcription App
Version: 2.0.0
Date: 2026-02-11
"""

import numpy as np
import librosa
import time
from typing import Tuple, List, Dict, Optional
from dataclasses import dataclass

# Optional dependencies
try:
    import essentia.standard as es
    ESSENTIA_AVAILABLE = True
except ImportError:
    ESSENTIA_AVAILABLE = False
    print("WARNING: Essentia not available, using librosa only")

try:
    import torch
    import torchaudio
    from demucs import pretrained
    from demucs.apply import apply_model
    DEMUCS_AVAILABLE = True
except ImportError:
    DEMUCS_AVAILABLE = False
    print("WARNING: Demucs not available, stem separation disabled")


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class TimingGrid:
    """Timing information for beat-aligned analysis"""
    tempo: float  # BPM
    beats: np.ndarray  # Beat timestamps in seconds
    subdivisions: np.ndarray  # 16th note timestamps
    time_signature: str  # e.g., "4/4"
    beats_per_measure: int  # e.g., 4 for 4/4


@dataclass
class Chord:
    """Single chord with timing and confidence"""
    name: str
    start: float  # seconds
    end: float  # seconds
    duration: float  # seconds
    confidence: float  # 0.0 to 1.0


@dataclass
class KeyDetection:
    """Key detection result"""
    key: str  # e.g., "C"
    scale: str  # "major" or "minor"
    confidence: float  # 0.0 to 1.0
    method: str  # "essentia" or "chromagram"


# ============================================================================
# Part 1: Tempo & Beat Detection
# ============================================================================

def detect_tempo_and_beats(audio_path: str, sr: int = 22050) -> TimingGrid:
    """
    Detect tempo and generate beat grid with 16th-note subdivisions
    
    This is the foundation for all subsequent analysis. We need precise
    timing to align chroma frames correctly.
    
    Args:
        audio_path: Path to audio file
        sr: Sample rate (default 22050 Hz)
    
    Returns:
        TimingGrid with tempo, beats, subdivisions, and time signature
    """
    print("=" * 80)
    print("PART 1: TEMPO & BEAT DETECTION")
    print("=" * 80)
    
    start_time = time.time()
    
    # Load audio
    print(f"Loading audio: {audio_path}")
    y, sr = librosa.load(audio_path, sr=sr)
    duration = librosa.get_duration(y=y, sr=sr)
    print(f"  Duration: {duration:.2f}s")
    print(f"  Sample rate: {sr} Hz")
    print(f"  Samples: {len(y)}")
    
    # Detect tempo and beats using librosa
    print("\nDetecting tempo with librosa...")
    tempo_librosa, beats_librosa = librosa.beat.beat_track(y=y, sr=sr)
    tempo = float(tempo_librosa) if isinstance(tempo_librosa, (int, float)) else float(tempo_librosa[0])
    beats = librosa.frames_to_time(beats_librosa, sr=sr)
    
    # Handle edge case: no beats detected (very short audio or no rhythm)
    if len(beats) == 0 or tempo == 0:
        print(f"  WARNING: No beats detected (audio too short or no clear rhythm)")
        print(f"  Using fallback: 120 BPM with estimated beats")
        tempo = 120.0
        # Generate estimated beats at 120 BPM
        beat_duration = 60.0 / tempo
        num_beats = int(duration / beat_duration)
        beats = np.array([i * beat_duration for i in range(num_beats)])
    
    print(f"  Tempo detected: {tempo:.1f} BPM")
    print(f"  Beats detected: {len(beats)}")
    
    # Optional: Use Essentia for comparison/validation
    if ESSENTIA_AVAILABLE:
        print("\nValidating with Essentia...")
        tempo_essentia, beats_essentia = detect_tempo_essentia(audio_path)
        
        # Compare results
        tempo_diff = abs(tempo - tempo_essentia)
        print(f"  Essentia tempo: {tempo_essentia:.1f} BPM")
        print(f"  Difference: {tempo_diff:.1f} BPM")
        
        # Use Essentia if significantly different and more confident
        if tempo_diff > 5:
            print(f"  WARNING: Large tempo difference detected")
            print(f"  Using librosa result: {tempo:.1f} BPM")
        # Could implement confidence-based selection here
    
    # Detect time signature
    print("\nDetecting time signature...")
    time_signature, beats_per_measure = detect_time_signature(beats)
    print(f"  Time signature: {time_signature}")
    print(f"  Beats per measure: {beats_per_measure}")
    
    # Generate 16th note subdivisions
    print("\nGenerating 16th-note subdivisions...")
    subdivisions = generate_subdivisions(beats, level=4)
    print(f"  Subdivisions generated: {len(subdivisions)}")
    print(f"  Subdivision resolution: 16th notes")
    print(f"  Average subdivision interval: {np.mean(np.diff(subdivisions)):.3f}s")
    
    # Create timing grid
    timing_grid = TimingGrid(
        tempo=tempo,
        beats=beats,
        subdivisions=subdivisions,
        time_signature=time_signature,
        beats_per_measure=beats_per_measure
    )
    
    elapsed = time.time() - start_time
    print(f"\n✓ Tempo & beat detection complete ({elapsed:.2f}s)")
    print("=" * 80)
    
    return timing_grid


def detect_tempo_essentia(audio_path: str) -> Tuple[float, np.ndarray]:
    """
    Detect tempo using Essentia (alternative/validation method)
    
    Args:
        audio_path: Path to audio file
    
    Returns:
        tempo: BPM
        beats: Beat timestamps
    """
    if not ESSENTIA_AVAILABLE:
        raise ImportError("Essentia not available")
    
    # Load audio with Essentia
    loader = es.MonoLoader(filename=audio_path, sampleRate=44100)
    audio = loader()
    
    # Use RhythmExtractor2013 (multi-feature method)
    rhythm_extractor = es.RhythmExtractor2013(method="multifeature")
    bpm, beats, beats_confidence, _, beats_intervals = rhythm_extractor(audio)
    
    tempo = float(bpm)
    
    return tempo, beats


def detect_time_signature(beats: np.ndarray) -> Tuple[str, int]:
    """
    Detect time signature by analyzing beat patterns
    
    This is a simplified implementation. More sophisticated methods could:
    - Analyze beat strength patterns
    - Use autocorrelation on beat intervals
    - Detect meter changes
    
    Args:
        beats: Beat timestamps
    
    Returns:
        time_signature: String like "4/4", "3/4", "6/8"
        beats_per_measure: Integer (4 for 4/4, 3 for 3/4, etc.)
    """
    if len(beats) < 8:
        # Not enough beats to determine, default to 4/4
        return "4/4", 4
    
    # Calculate inter-beat intervals
    intervals = np.diff(beats)
    
    # Analyze interval patterns
    # For now, default to 4/4 (most common in popular music)
    # TODO: Implement more sophisticated time signature detection
    # - Use beat strength analysis
    # - Detect strong/weak beat patterns
    # - Handle compound meters (6/8, 9/8, 12/8)
    
    time_signature = "4/4"
    beats_per_measure = 4
    
    return time_signature, beats_per_measure


def generate_subdivisions(beats: np.ndarray, level: int = 4) -> np.ndarray:
    """
    Generate subdivisions between beats
    
    This creates a timing grid at the specified subdivision level:
    - level=2: 8th notes (2 subdivisions per beat)
    - level=4: 16th notes (4 subdivisions per beat) - DEFAULT for chromagram
    - level=8: 32nd notes (8 subdivisions per beat)
    
    Args:
        beats: Beat timestamps in seconds
        level: Number of subdivisions per beat (default 4 = 16th notes)
    
    Returns:
        Array of subdivision timestamps
    """
    if len(beats) < 2:
        return beats
    
    subdivisions = []
    
    # Generate subdivisions between consecutive beats
    for i in range(len(beats) - 1):
        beat_duration = beats[i + 1] - beats[i]
        subdivision_duration = beat_duration / level
        
        # Add subdivisions for this beat
        for j in range(level):
            subdivisions.append(beats[i] + j * subdivision_duration)
    
    # Handle last beat (estimate duration from previous beat)
    if len(beats) >= 2:
        last_beat_duration = beats[-1] - beats[-2]
        for j in range(level):
            subdivisions.append(beats[-1] + j * last_beat_duration / level)
    
    return np.array(subdivisions)


def calculate_eighth_note_duration(tempo: float) -> float:
    """
    Calculate duration of 1/8 note in seconds
    
    This is used for minimum chord duration enforcement.
    
    Args:
        tempo: BPM (beats per minute)
    
    Returns:
        Duration in seconds
    """
    if tempo <= 0:
        # Default to 120 BPM if tempo is invalid
        tempo = 120.0
    quarter_note_duration = 60.0 / tempo  # seconds per beat
    eighth_note_duration = quarter_note_duration / 2
    return eighth_note_duration


def calculate_sixteenth_note_duration(tempo: float) -> float:
    """
    Calculate duration of 1/16 note in seconds
    
    Args:
        tempo: BPM
    
    Returns:
        Duration in seconds
    """
    if tempo <= 0:
        # Default to 120 BPM if tempo is invalid
        tempo = 120.0
    quarter_note_duration = 60.0 / tempo
    sixteenth_note_duration = quarter_note_duration / 4
    return sixteenth_note_duration


# ============================================================================
# Part 2: Stem Separation
# ============================================================================

def separate_stems(audio_path: str, chunk_duration: int = 30) -> Tuple[np.ndarray, int]:
    """
    Separate audio into stems and isolate harmonic content
    Removes drums and vocals, keeps bass + other (guitar, piano, strings, synths)
    
    Uses chunked processing to avoid memory issues with long audio files.
    
    Args:
        audio_path: Path to audio file
        chunk_duration: Duration of each chunk in seconds (default 30s)
    
    Returns:
        harmonic_audio: Bass + other stems combined (no drums, no vocals)
        sr: Sample rate (22050 Hz for librosa compatibility)
    """
    if not DEMUCS_AVAILABLE:
        print("=" * 80)
        print("PART 2: STEM SEPARATION - SKIPPED")
        print("=" * 80)
        print("WARNING: Demucs not available, using full mix")
        print("Install with: pip install demucs")
        print("Falling back to full audio (includes drums and vocals)")
        print("=" * 80)
        # Return full audio without separation
        y, sr = librosa.load(audio_path, sr=22050)
        return y, sr
    
    print("=" * 80)
    print("PART 2: STEM SEPARATION")
    print("=" * 80)
    
    start_time = time.time()
    
    # Load Demucs model
    print("Loading Demucs model...")
    from demucs import pretrained
    from demucs.apply import apply_model
    import torch
    import torchaudio
    
    # Use htdemucs for best quality (or mdx_extra for faster processing)
    model_name = 'htdemucs'
    print(f"  Model: {model_name}")
    model = pretrained.get_model(model_name)
    model.eval()
    print(f"  Model sample rate: {model.samplerate} Hz")
    
    # Get audio info using librosa (more compatible)
    y_temp, sr_temp = librosa.load(audio_path, sr=None, duration=1)
    total_duration = librosa.get_duration(path=audio_path)
    print(f"\nAudio info:")
    print(f"  Duration: {total_duration:.1f}s")
    print(f"  Sample rate: {sr_temp} Hz (will resample to {model.samplerate})")
    
    # Process in chunks to avoid memory issues
    # Load full audio with librosa (more compatible than torchaudio)
    print(f"\nLoading full audio for chunked processing...")
    wav_np, sr_orig = librosa.load(audio_path, sr=model.samplerate, mono=False)
    
    # Ensure stereo (Demucs expects stereo)
    if wav_np.ndim == 1:
        wav_np = np.stack([wav_np, wav_np])
        print(f"  Converted mono to stereo")
    elif wav_np.shape[0] == 1:
        wav_np = np.repeat(wav_np, 2, axis=0)
        print(f"  Converted mono to stereo")
    
    # Convert to torch tensor
    wav_full = torch.from_numpy(wav_np).float()
    
    total_frames = wav_full.shape[1]
    chunk_size = chunk_duration * model.samplerate
    num_chunks = int(np.ceil(total_frames / chunk_size))
    print(f"\nProcessing in {num_chunks} chunks of {chunk_duration}s each")
    
    harmonic_chunks = []
    
    for i, start_frame in enumerate(range(0, total_frames, chunk_size)):
        chunk_start_time = time.time()
        print(f"\n  Chunk {i+1}/{num_chunks}:")
        
        # Extract chunk from full audio
        num_frames = min(chunk_size, total_frames - start_frame)
        wav = wav_full[:, start_frame:start_frame + num_frames]
        print(f"    Processing {num_frames / model.samplerate:.1f}s of audio")
        
        # Separate stems (no gradient needed for inference)
        print(f"    Separating stems...")
        with torch.no_grad():
            sources = apply_model(model, wav[None], device='cpu')[0]
        
        # Extract stems
        # sources: [drums, bass, other, vocals]
        drums = sources[0]
        bass = sources[1]
        other = sources[2]  # Guitar, piano, strings, synths, etc.
        vocals = sources[3]
        
        print(f"    Stems extracted:")
        print(f"      - Drums: {drums.shape}")
        print(f"      - Bass: {bass.shape}")
        print(f"      - Other: {other.shape}")
        print(f"      - Vocals: {vocals.shape}")
        
        # Use ONLY "other" stem (no bass, no drums, no vocals)
        # This focuses on harmonic instruments: piano, guitar, strings, synths
        harmonic = other
        print(f"    Using ONLY 'other' stem (piano/guitar/keys - no bass)")
        
        # Convert to mono
        harmonic_mono = torch.mean(harmonic, dim=0).numpy()
        harmonic_chunks.append(harmonic_mono)
        
        # Clear memory
        del wav, sources, drums, bass, other, vocals, harmonic
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        chunk_time = time.time() - chunk_start_time
        print(f"    ✓ Chunk {i+1}/{num_chunks} complete ({chunk_time:.1f}s)")
    
    # Clean up full audio
    del wav_full
    
    # Concatenate all chunks
    print(f"\nConcatenating {len(harmonic_chunks)} chunks...")
    full_harmonic = np.concatenate(harmonic_chunks)
    
    # Resample to 22050 for librosa
    if model.samplerate != 22050:
        print(f"Resampling from {model.samplerate}Hz to 22050Hz for librosa...")
        full_harmonic = librosa.resample(full_harmonic, orig_sr=model.samplerate, target_sr=22050)
        sr_final = 22050
    else:
        sr_final = model.samplerate
    
    elapsed = time.time() - start_time
    print(f"\n✓ Stem separation complete ({elapsed:.2f}s)")
    print(f"  Output duration: {len(full_harmonic) / sr_final:.1f}s")
    print(f"  Output sample rate: {sr_final} Hz")
    print(f"  Drums removed: ✓")
    print(f"  Bass removed: ✓")
    print(f"  Vocals removed: ✓")
    print(f"  Harmonic content: ONLY 'other' (guitar, piano, strings, synths)")
    print("=" * 80)
    
    return full_harmonic, sr_final


def separate_stems_simple(audio_path: str) -> Tuple[np.ndarray, int]:
    """
    Simple stem separation without chunking (for short audio files < 1 minute)
    
    Args:
        audio_path: Path to audio file
    
    Returns:
        harmonic_audio: Bass + other stems combined
        sr: Sample rate
    """
    if not DEMUCS_AVAILABLE:
        print("WARNING: Demucs not available, using full mix")
        y, sr = librosa.load(audio_path, sr=22050)
        return y, sr
    
    print("Separating stems (simple mode)...")
    
    from demucs import pretrained
    from demucs.apply import apply_model
    import torch
    import torchaudio
    
    # Load model
    model = pretrained.get_model('htdemucs')
    model.eval()
    
    # Load audio
    wav, sr = torchaudio.load(audio_path)
    
    # Ensure stereo
    if wav.shape[0] == 1:
        wav = wav.repeat(2, 1)
    
    # Resample if needed
    if sr != model.samplerate:
        resampler = torchaudio.transforms.Resample(sr, model.samplerate)
        wav = resampler(wav)
        sr = model.samplerate
    
    # Separate stems
    with torch.no_grad():
        sources = apply_model(model, wav[None], device='cpu')[0]
    
    # Extract harmonic content (bass + other)
    bass = sources[1]
    other = sources[2]
    harmonic = bass + other
    
    # Convert to mono
    harmonic_mono = torch.mean(harmonic, dim=0).numpy()
    
    # Resample to 22050
    if sr != 22050:
        harmonic_mono = librosa.resample(harmonic_mono, orig_sr=sr, target_sr=22050)
        sr = 22050
    
    print(f"✓ Stem separation complete")
    
    return harmonic_mono, sr


# ============================================================================
# Part 3: CQT Chromagram with Beat Alignment
# ============================================================================

def compute_beat_aligned_chromagram(
    audio: np.ndarray,
    sr: int,
    subdivisions: np.ndarray,
    hop_length_ms: int = 20
) -> np.ndarray:
    """
    Compute CQT chromagram aligned to beat subdivisions
    
    This creates a high-resolution chromagram and aligns it to the 16th-note
    timing grid. Each subdivision gets an averaged chroma vector representing
    the harmonic content during that time window.
    
    Args:
        audio: Audio signal (harmonic content, ideally with drums/vocals removed)
        sr: Sample rate
        subdivisions: 16th note timestamps from Part 1
        hop_length_ms: Hop length in milliseconds (20ms default, 10ms for fast changes)
    
    Returns:
        aligned_chroma: Chromagram aligned to subdivisions [12 x n_subdivisions]
    """
    print("=" * 80)
    print("PART 3: CQT CHROMAGRAM WITH BEAT ALIGNMENT")
    print("=" * 80)
    
    start_time = time.time()
    
    # Calculate hop length in samples
    hop_length = int(sr * hop_length_ms / 1000)
    print(f"Chromagram parameters:")
    print(f"  Sample rate: {sr} Hz")
    print(f"  Hop length: {hop_length_ms}ms ({hop_length} samples)")
    print(f"  Window size: 4096 samples")
    print(f"  Bins per octave: 36 (high resolution)")
    
    # Compute CQT chromagram
    print(f"\nComputing CQT chromagram...")
    chroma = librosa.feature.chroma_cqt(
        y=audio,
        sr=sr,
        hop_length=hop_length,
        n_chroma=12,
        bins_per_octave=36,  # High resolution for better pitch accuracy
        fmin=librosa.note_to_hz('C2'),  # Start at C2 (65.4 Hz)
        n_octaves=7  # Cover C2 to C9
    )
    
    print(f"  Chromagram shape: {chroma.shape}")
    print(f"  Chroma bins: {chroma.shape[0]}")
    print(f"  Time frames: {chroma.shape[1]}")
    
    # Apply median filtering to reduce noise
    print(f"\nApplying median filter to reduce noise...")
    from scipy.ndimage import median_filter
    chroma_filtered = median_filter(chroma, size=(1, 5))
    
    # Align to subdivisions
    print(f"\nAligning chromagram to {len(subdivisions)} subdivisions...")
    aligned_chroma = align_chroma_to_grid(
        chroma_filtered,
        subdivisions,
        sr,
        hop_length
    )
    
    print(f"  Aligned chroma shape: {aligned_chroma.shape}")
    
    elapsed = time.time() - start_time
    print(f"\n✓ Chromagram computation complete ({elapsed:.2f}s)")
    print("=" * 80)
    
    return aligned_chroma


def align_chroma_to_grid(
    chroma: np.ndarray,
    subdivisions: np.ndarray,
    sr: int,
    hop_length: int
) -> np.ndarray:
    """
    Align chromagram frames to subdivision grid
    
    For each subdivision, we average the chroma frames that fall within
    the time window from this subdivision to the next. This gives us a
    single chroma vector per subdivision that represents the average
    harmonic content during that time period.
    
    Args:
        chroma: Chromagram [12 x n_frames]
        subdivisions: Subdivision timestamps in seconds
        sr: Sample rate
        hop_length: Hop length in samples
    
    Returns:
        aligned: Aligned chromagram [12 x n_subdivisions]
    """
    n_subdivisions = len(subdivisions)
    aligned = np.zeros((12, n_subdivisions))
    
    for i, subdivision_time in enumerate(subdivisions):
        # Convert time to frame index
        frame_idx = librosa.time_to_frames(
            subdivision_time,
            sr=sr,
            hop_length=hop_length
        )
        
        # Define window: from this subdivision to the next
        if i < n_subdivisions - 1:
            next_time = subdivisions[i + 1]
            window_duration = next_time - subdivision_time
        else:
            # Last subdivision: use same duration as previous
            if i > 0:
                window_duration = subdivisions[i] - subdivisions[i - 1]
            else:
                window_duration = 0.125  # Default to 16th note at 120 BPM
        
        # Calculate window in frames
        window_frames = int(window_duration * sr / hop_length)
        
        # Average chroma within window
        start_frame = max(0, frame_idx)
        end_frame = min(chroma.shape[1], frame_idx + window_frames)
        
        if start_frame < end_frame:
            # Average chroma across the window
            aligned[:, i] = np.mean(chroma[:, start_frame:end_frame], axis=1)
        else:
            # Edge case: use single frame
            if frame_idx < chroma.shape[1]:
                aligned[:, i] = chroma[:, frame_idx]
            # else: leave as zeros (shouldn't happen in practice)
    
    return aligned


def visualize_chromagram(chroma: np.ndarray, subdivisions: np.ndarray, output_path: str = None):
    """
    Visualize chromagram for debugging/validation
    
    Args:
        chroma: Aligned chromagram [12 x n_subdivisions]
        subdivisions: Subdivision timestamps
        output_path: Optional path to save figure
    """
    try:
        import matplotlib.pyplot as plt
        
        plt.figure(figsize=(15, 6))
        
        # Plot chromagram
        plt.imshow(
            chroma,
            aspect='auto',
            origin='lower',
            cmap='hot',
            interpolation='nearest'
        )
        
        plt.colorbar(label='Chroma Intensity')
        plt.xlabel('Subdivision (16th notes)')
        plt.ylabel('Pitch Class')
        plt.yticks(range(12), ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'])
        plt.title('Beat-Aligned Chromagram (16th-note resolution)')
        
        # Add time axis on top
        ax2 = plt.gca().twiny()
        ax2.set_xlim(plt.gca().get_xlim())
        time_ticks = np.linspace(0, len(subdivisions) - 1, 10, dtype=int)
        ax2.set_xticks(time_ticks)
        ax2.set_xticklabels([f'{subdivisions[i]:.1f}s' for i in time_ticks])
        ax2.set_xlabel('Time (seconds)')
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"Chromagram visualization saved to: {output_path}")
        else:
            plt.show()
        
        plt.close()
        
    except ImportError:
        print("WARNING: matplotlib not available, skipping visualization")


# ============================================================================
# Part 4: Template Matching with Simple Merging
# ============================================================================

def get_analysis_parameters(tempo: float) -> Dict:
    """
    Get optimal analysis parameters based on tempo
    
    Different tempos require different time resolutions:
    - Slow songs: Need finer resolution to catch subtle changes
    - Fast songs: Need coarser resolution to avoid over-sampling
    
    Args:
        tempo: BPM
    
    Returns:
        Dictionary with subdivision_level, hop_length_ms, median_window
    """
    if tempo < 80:
        # Slow ballad (60-80 BPM)
        # Use 32nd notes for fine resolution
        return {
            'subdivision_level': 8,  # 32nd notes
            'hop_length_ms': 10,     # 10ms hop for high resolution
            'median_window': 7,      # Larger window for more smoothing
            'description': 'Slow ballad (32nd notes, 10ms hop)'
        }
    elif tempo < 100:
        # Moderate slow (80-100 BPM)
        # Use 16th notes with fine hop
        return {
            'subdivision_level': 4,  # 16th notes
            'hop_length_ms': 15,     # 15ms hop
            'median_window': 5,
            'description': 'Moderate slow (16th notes, 15ms hop)'
        }
    elif tempo < 140:
        # Normal tempo (100-140 BPM)
        # Use 16th notes - standard resolution
        return {
            'subdivision_level': 4,  # 16th notes
            'hop_length_ms': 20,     # 20ms hop (standard)
            'median_window': 5,
            'description': 'Normal tempo (16th notes, 20ms hop)'
        }
    elif tempo < 180:
        # Fast tempo (140-180 BPM)
        # Use 16th notes but coarser hop
        return {
            'subdivision_level': 4,  # 16th notes
            'hop_length_ms': 25,     # 25ms hop
            'median_window': 3,
            'description': 'Fast tempo (16th notes, 25ms hop)'
        }
    else:
        # Very fast (>180 BPM)
        # Use 8th notes to avoid over-sampling
        return {
            'subdivision_level': 2,  # 8th notes
            'hop_length_ms': 30,     # 30ms hop
            'median_window': 3,
            'description': 'Very fast (8th notes, 30ms hop)'
        }


def calculate_samples_per_subdivision(tempo: float, sr: int, hop_length_ms: int, subdivision_level: int) -> float:
    """
    Calculate how many chroma samples fall within each subdivision
    
    This helps understand the time resolution we're working with.
    
    Args:
        tempo: BPM
        sr: Sample rate
        hop_length_ms: Hop length in milliseconds
        subdivision_level: Subdivisions per beat (2=8th, 4=16th, 8=32nd)
    
    Returns:
        Number of chroma samples per subdivision
    """
    # Duration of one beat in seconds
    beat_duration = 60.0 / tempo
    
    # Duration of one subdivision in seconds
    subdivision_duration = beat_duration / subdivision_level
    
    # Duration of one subdivision in milliseconds
    subdivision_duration_ms = subdivision_duration * 1000
    
    # Number of chroma samples per subdivision
    samples_per_subdivision = subdivision_duration_ms / hop_length_ms
    
    return samples_per_subdivision


def create_chord_templates() -> Dict[str, np.ndarray]:
    """
    Create comprehensive chord templates
    
    Each template is a 12-element vector representing the expected
    chroma distribution for that chord type.
    
    Returns:
        Dictionary of chord_name -> chroma template (normalized)
    """
    templates = {}
    chord_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    for root_idx in range(12):
        root = chord_names[root_idx]
        
        # Major (1, 3, 5)
        major = np.zeros(12)
        major[[0, 4, 7]] = [1.0, 0.8, 0.9]  # Root, major 3rd, perfect 5th
        templates[root] = np.roll(major, root_idx)
        
        # Minor (1, b3, 5)
        minor = np.zeros(12)
        minor[[0, 3, 7]] = [1.0, 0.8, 0.9]  # Root, minor 3rd, perfect 5th
        templates[root + 'm'] = np.roll(minor, root_idx)
        
        # Dominant 7th (1, 3, 5, b7)
        dom7 = np.zeros(12)
        dom7[[0, 4, 7, 10]] = [1.0, 0.7, 0.8, 0.6]
        templates[root + '7'] = np.roll(dom7, root_idx)
        
        # Major 7th (1, 3, 5, 7)
        maj7 = np.zeros(12)
        maj7[[0, 4, 7, 11]] = [1.0, 0.7, 0.8, 0.6]
        templates[root + 'maj7'] = np.roll(maj7, root_idx)
        
        # Minor 7th (1, b3, 5, b7)
        min7 = np.zeros(12)
        min7[[0, 3, 7, 10]] = [1.0, 0.7, 0.8, 0.6]
        templates[root + 'm7'] = np.roll(min7, root_idx)
        
        # Sus4 (1, 4, 5)
        sus4 = np.zeros(12)
        sus4[[0, 5, 7]] = [1.0, 0.7, 0.9]
        templates[root + 'sus4'] = np.roll(sus4, root_idx)
        
        # Diminished (1, b3, b5)
        dim = np.zeros(12)
        dim[[0, 3, 6]] = [1.0, 0.8, 0.8]
        templates[root + 'dim'] = np.roll(dim, root_idx)
        
        # Augmented (1, 3, #5)
        aug = np.zeros(12)
        aug[[0, 4, 8]] = [1.0, 0.8, 0.8]
        templates[root + 'aug'] = np.roll(aug, root_idx)
        
        # Sus2 (1, 2, 5)
        sus2 = np.zeros(12)
        sus2[[0, 2, 7]] = [1.0, 0.7, 0.9]
        templates[root + 'sus2'] = np.roll(sus2, root_idx)
        
        # 6th (1, 3, 5, 6)
        sixth = np.zeros(12)
        sixth[[0, 4, 7, 9]] = [1.0, 0.7, 0.8, 0.6]
        templates[root + '6'] = np.roll(sixth, root_idx)
        
        # Minor 6th (1, b3, 5, 6)
        m6 = np.zeros(12)
        m6[[0, 3, 7, 9]] = [1.0, 0.7, 0.8, 0.6]
        templates[root + 'm6'] = np.roll(m6, root_idx)
    
    # Normalize all templates
    for chord_name in templates:
        template = templates[chord_name]
        if np.sum(template) > 0:
            templates[chord_name] = template / np.sum(template)
    
    return templates


def detect_chords_with_templates(
    aligned_chroma: np.ndarray,
    tempo: float,
    subdivisions: np.ndarray,
    use_hmm: bool = True
) -> List[Chord]:
    """
    Detect chords using template matching with simple merging
    
    Strategy: 
    1. Chromagram is already aligned to subdivisions (16th notes typically)
    2. Each subdivision has averaged chroma from multiple samples
    3. Match best chord template for each subdivision
    4. Apply median filter to remove single-frame outliers
    5. Merge consecutive identical chords
    
    Args:
        aligned_chroma: Beat-aligned chromagram [12 x n_subdivisions]
        tempo: BPM
        subdivisions: Timing grid (subdivision timestamps)
        use_hmm: Ignored (kept for compatibility)
    
    Returns:
        List of Chord objects with timing and confidence
    """
    print("=" * 80)
    print("PART 4: TEMPLATE MATCHING WITH SIMPLE MERGING")
    print("=" * 80)
    
    start_time = time.time()
    
    # Get tempo-dependent parameters
    params = get_analysis_parameters(tempo)
    print(f"\nTempo-dependent parameters:")
    print(f"  Tempo: {tempo:.1f} BPM")
    print(f"  Configuration: {params['description']}")
    print(f"  Subdivision level: {params['subdivision_level']} per beat")
    print(f"  Median filter window: {params['median_window']}")
    
    # Calculate actual samples per subdivision
    # Note: This is informational - chromagram was already computed
    subdivision_duration_ms = (60.0 / tempo / 4) * 1000  # Assuming 16th notes
    print(f"  Subdivision duration: {subdivision_duration_ms:.1f}ms")
    print(f"  Chroma samples per subdivision: ~{subdivision_duration_ms / 20:.1f} (at 20ms hop)")
    
    # Create chord templates
    print("\nCreating chord templates...")
    templates = create_chord_templates()
    print(f"  Templates created: {len(templates)} chord types")
    
    # Template matching at each subdivision
    print(f"\nMatching templates to {aligned_chroma.shape[1]} subdivisions...")
    
    chord_sequence = []
    chord_confidences = []
    
    for i in range(aligned_chroma.shape[1]):
        chroma_vector = aligned_chroma[:, i]
        
        # Normalize chroma vector
        if np.sum(chroma_vector) > 0:
            chroma_vector = chroma_vector / np.sum(chroma_vector)
        
        # Find best matching chord template
        best_chord = None
        best_similarity = -1
        
        for chord_name, template in templates.items():
            # Cosine similarity
            similarity = np.dot(chroma_vector, template) / (
                np.linalg.norm(chroma_vector) * np.linalg.norm(template) + 1e-10
            )
            if similarity > best_similarity:
                best_similarity = similarity
                best_chord = chord_name
        
        chord_sequence.append(best_chord)
        chord_confidences.append(max(0, best_similarity))
    
    print(f"  Template matching complete")
    print(f"  Raw detections: {len(chord_sequence)} chords (one per subdivision)")
    
    # Count unique chords and changes before filtering
    unique_before = len(set(chord_sequence))
    changes_before = sum(1 for i in range(1, len(chord_sequence)) if chord_sequence[i] != chord_sequence[i-1])
    print(f"  Unique chords before filtering: {unique_before}")
    print(f"  Chord changes before filtering: {changes_before}")
    
    # Apply median filter with tempo-dependent window
    median_window = params['median_window']
    print(f"\nApplying median filter (window={median_window}) to remove outliers...")
    filtered_sequence = apply_median_filter_to_chords(chord_sequence, window=median_window)
    
    unique_after = len(set(filtered_sequence))
    changes_after = sum(1 for i in range(1, len(filtered_sequence)) if filtered_sequence[i] != filtered_sequence[i-1])
    print(f"  Unique chords after filtering: {unique_after}")
    print(f"  Chord changes after filtering: {changes_after}")
    print(f"  Removed {changes_before - changes_after} spurious changes")
    
    # Merge consecutive identical chords
    print(f"\nMerging consecutive identical chords...")
    merged_chords = merge_consecutive_chords(
        filtered_sequence,
        chord_confidences,
        subdivisions
    )
    
    print(f"  Chords after merging: {len(merged_chords)}")
    
    # Convert to Chord objects
    chords = []
    for chord_dict in merged_chords:
        chords.append(Chord(
            name=chord_dict['chord'],
            start=chord_dict['start'],
            end=chord_dict['end'],
            duration=chord_dict['duration'],
            confidence=chord_dict['confidence']
        ))
    
    elapsed = time.time() - start_time
    print(f"\n✓ Chord detection complete ({elapsed:.2f}s)")
    print(f"  Total chords detected: {len(chords)}")
    if len(chords) > 0:
        print(f"  Average chord duration: {np.mean([c.duration for c in chords]):.2f}s")
        print(f"  Average confidence: {np.mean([c.confidence for c in chords]):.2f}")
    print("=" * 80)
    
    return chords


def apply_median_filter_to_chords(
    chord_sequence: List[str],
    window: int = 3
) -> List[str]:
    """
    Apply median filter to chord sequence to remove single-frame outliers
    
    For each position, if the chord is different from both neighbors,
    replace it with the most common chord in the window.
    
    Args:
        chord_sequence: List of chord names
        window: Window size (default 3 = look at current + 1 before + 1 after)
    
    Returns:
        Filtered chord sequence
    """
    if len(chord_sequence) < window:
        return chord_sequence
    
    filtered = chord_sequence.copy()
    half_window = window // 2
    
    for i in range(half_window, len(chord_sequence) - half_window):
        # Get window around current position
        window_chords = chord_sequence[i - half_window:i + half_window + 1]
        
        # If current chord is different from both neighbors, it might be an outlier
        if i > 0 and i < len(chord_sequence) - 1:
            if chord_sequence[i] != chord_sequence[i-1] and chord_sequence[i] != chord_sequence[i+1]:
                # Check if neighbors agree
                if chord_sequence[i-1] == chord_sequence[i+1]:
                    # Neighbors agree, current is likely an outlier
                    filtered[i] = chord_sequence[i-1]
    
    return filtered


def merge_consecutive_chords(
    chord_sequence: List[str],
    confidences: List[float],
    subdivisions: np.ndarray
) -> List[Dict]:
    """
    Merge consecutive identical chords into segments
    
    Args:
        chord_sequence: Chord name for each subdivision
        confidences: Confidence for each subdivision
        subdivisions: Timing grid
    
    Returns:
        List of chord segments with timing and confidence
    """
    if len(chord_sequence) == 0:
        return []
    
    segments = []
    current_chord = chord_sequence[0]
    current_start = subdivisions[0]
    current_start_idx = 0
    
    for i in range(1, len(chord_sequence)):
        if chord_sequence[i] != current_chord:
            # Chord changed - save current segment
            avg_confidence = np.mean(confidences[current_start_idx:i])
            
            segments.append({
                'chord': current_chord,
                'start': float(current_start),
                'end': float(subdivisions[i]),
                'duration': float(subdivisions[i] - current_start),
                'confidence': float(avg_confidence)
            })
            
            # Start new segment
            current_chord = chord_sequence[i]
            current_start = subdivisions[i]
            current_start_idx = i
    
    # Add last segment
    avg_confidence = np.mean(confidences[current_start_idx:])
    segments.append({
        'chord': current_chord,
        'start': float(current_start),
        'end': float(subdivisions[-1]),
        'duration': float(subdivisions[-1] - current_start),
        'confidence': float(avg_confidence)
    })
    
    return segments


def apply_hmm_smoothing(
    chord_probabilities: List[Dict[str, float]],
    chord_names: List[str],
    tempo: float
) -> List[str]:
    """
    Apply simplified HMM-like smoothing using Viterbi algorithm
    
    This prevents rapid chord changes that are musically unlikely.
    Uses a simple transition model where staying on the same chord
    is more likely than changing.
    
    Args:
        chord_probabilities: List of probability dicts for each subdivision
        chord_names: List of all possible chord names
        tempo: BPM (used to adjust transition probabilities)
    
    Returns:
        Smoothed chord sequence
    """
    n_states = len(chord_names)
    n_observations = len(chord_probabilities)
    
    if n_observations == 0:
        return []
    
    # Create state index mapping
    state_to_idx = {chord: i for i, chord in enumerate(chord_names)}
    idx_to_state = {i: chord for i, chord in enumerate(chord_names)}
    
    # Transition probabilities
    # 0.7 allows more chord changes for pop/funk
    # Lower values (0.5-0.6) for very fast chord changes
    # Higher values (0.9) for jazz with long chords
    stay_prob = 0.7
    change_prob = (1.0 - stay_prob) / (n_states - 1)
    
    transition_matrix = np.full((n_states, n_states), change_prob)
    np.fill_diagonal(transition_matrix, stay_prob)
    
    # Viterbi algorithm
    # Initialize
    viterbi = np.zeros((n_states, n_observations))
    backpointer = np.zeros((n_states, n_observations), dtype=int)
    
    # Emission weight: higher values give more weight to observations vs transitions
    # This makes the HMM more responsive to actual chroma changes
    # Higher values (3-5) make it follow observations more closely
    emission_weight = 5.0
    
    # Initial probabilities (from first observation)
    first_probs = chord_probabilities[0]
    for i, chord in enumerate(chord_names):
        viterbi[i, 0] = first_probs.get(chord, 0.0) ** emission_weight
    
    # Forward pass
    for t in range(1, n_observations):
        obs_probs = chord_probabilities[t]
        
        for s in range(n_states):
            # Calculate probability of being in state s at time t
            trans_probs = viterbi[:, t-1] * transition_matrix[:, s]
            backpointer[s, t] = np.argmax(trans_probs)
            # Apply emission weight to give more importance to observations
            viterbi[s, t] = np.max(trans_probs) * (obs_probs.get(chord_names[s], 0.0) ** emission_weight)
    
    # Backward pass (find best path)
    path = np.zeros(n_observations, dtype=int)
    path[-1] = np.argmax(viterbi[:, -1])
    
    for t in range(n_observations - 2, -1, -1):
        path[t] = backpointer[path[t + 1], t + 1]
    
    # Convert indices back to chord names
    chord_sequence = [idx_to_state[idx] for idx in path]
    
    return chord_sequence


def convert_chord_sequence_to_segments(
    chord_sequence: List[str],
    subdivisions: np.ndarray,
    chord_probabilities: List[Dict[str, float]],
    chord_names: List[str]
) -> List[Dict]:
    """
    Convert chord sequence to timed segments without minimum duration filtering
    
    Args:
        chord_sequence: Detected chord sequence
        subdivisions: Timing grid
        chord_probabilities: Original probabilities for confidence calculation
        chord_names: List of all chord names
    
    Returns:
        List of chord dictionaries with timing and confidence
    """
    if len(chord_sequence) == 0:
        return []
    
    segments = []
    current_chord = chord_sequence[0]
    current_start = subdivisions[0]
    current_start_idx = 0
    
    for i in range(1, len(chord_sequence)):
        if chord_sequence[i] != current_chord:
            # Chord changed - save current chord
            confidence = calculate_chord_confidence(
                current_chord,
                chord_probabilities[current_start_idx:i]
            )
            
            segments.append({
                'chord': current_chord,
                'start': float(current_start),
                'end': float(subdivisions[i]),
                'duration': float(subdivisions[i] - current_start),
                'confidence': float(confidence)
            })
            
            # Start new chord
            current_chord = chord_sequence[i]
            current_start = subdivisions[i]
            current_start_idx = i
    
    # Add last chord
    confidence = calculate_chord_confidence(
        current_chord,
        chord_probabilities[current_start_idx:]
    )
    
    segments.append({
        'chord': current_chord,
        'start': float(current_start),
        'end': float(subdivisions[-1]),
        'duration': float(subdivisions[-1] - current_start),
        'confidence': float(confidence)
    })
    
    return segments


def enforce_minimum_duration(
    chord_sequence: List[str],
    subdivisions: np.ndarray,
    min_duration: float,
    chord_probabilities: List[Dict[str, float]],
    chord_names: List[str]
) -> List[Dict]:
    """
    Enforce minimum chord duration (1/8 note)
    Merge chords shorter than minimum
    
    Args:
        chord_sequence: Detected chord sequence
        subdivisions: Timing grid
        min_duration: Minimum duration in seconds
        chord_probabilities: Original probabilities for confidence calculation
        chord_names: List of all chord names
    
    Returns:
        List of chord dictionaries with timing and confidence
    """
    if len(chord_sequence) == 0:
        return []
    
    filtered = []
    current_chord = chord_sequence[0]
    current_start = subdivisions[0]
    current_start_idx = 0
    
    for i in range(1, len(chord_sequence)):
        if chord_sequence[i] != current_chord:
            # Chord changed
            duration = subdivisions[i] - current_start
            
            if duration >= min_duration:
                # Keep this chord - calculate average confidence
                confidence = calculate_chord_confidence(
                    current_chord,
                    chord_probabilities[current_start_idx:i]
                )
                
                filtered.append({
                    'chord': current_chord,
                    'start': float(current_start),
                    'end': float(subdivisions[i]),
                    'duration': float(duration),
                    'confidence': float(confidence)
                })
                current_chord = chord_sequence[i]
                current_start = subdivisions[i]
                current_start_idx = i
            else:
                # Too short, merge with next
                # Keep current chord, don't update
                pass
    
    # Add last chord
    duration = subdivisions[-1] - current_start
    if duration >= min_duration:
        confidence = calculate_chord_confidence(
            current_chord,
            chord_probabilities[current_start_idx:]
        )
        
        filtered.append({
            'chord': current_chord,
            'start': float(current_start),
            'end': float(subdivisions[-1]),
            'duration': float(duration),
            'confidence': float(confidence)
        })
    
    return filtered


def calculate_chord_confidence(
    chord_name: str,
    probabilities: List[Dict[str, float]]
) -> float:
    """
    Calculate average confidence for a chord across multiple subdivisions
    
    Args:
        chord_name: Name of the chord
        probabilities: List of probability dicts
    
    Returns:
        Average confidence (0.0 to 1.0)
    """
    if len(probabilities) == 0:
        return 0.0
    
    confidences = [probs.get(chord_name, 0.0) for probs in probabilities]
    return np.mean(confidences)


# ============================================================================
# Part 5: ML-Based Key Detection
# ============================================================================

def detect_key_from_chromagram(
    chroma: np.ndarray,
    chords: Optional[List[Chord]] = None
) -> KeyDetection:
    """
    Detect key using Krumhansl-Schmuckler algorithm from chromagram
    
    This is the fallback method when Essentia is not available.
    Uses correlation with key profiles to determine the most likely key.
    
    Args:
        chroma: Chromagram (12 x n_frames) or aligned chromagram
        chords: Optional list of detected chords for validation
    
    Returns:
        KeyDetection object with key, scale, confidence, and method
    """
    print("=" * 80)
    print("PART 5: KEY DETECTION")
    print("=" * 80)
    
    start_time = time.time()
    
    # Krumhansl-Schmuckler key profiles
    # These represent the expected distribution of pitch classes in each key
    major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
    
    # Average chroma over time
    print("Computing average chroma distribution...")
    chroma_mean = np.mean(chroma, axis=1)
    
    # Normalize
    if np.sum(chroma_mean) > 0:
        chroma_mean = chroma_mean / np.sum(chroma_mean)
    
    print(f"  Chroma mean shape: {chroma_mean.shape}")
    
    # Calculate correlation with each key
    chord_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    best_corr = -1
    best_key = 'C'
    best_scale = 'major'
    
    print("\nCalculating correlations with key profiles...")
    correlations = {}
    
    for i in range(12):
        # Rotate profiles to match each key
        major_rot = np.roll(major_profile, i)
        minor_rot = np.roll(minor_profile, i)
        
        # Normalize profiles
        major_rot = major_rot / np.sum(major_rot)
        minor_rot = minor_rot / np.sum(minor_rot)
        
        # Calculate correlation
        major_corr = np.corrcoef(chroma_mean, major_rot)[0, 1]
        minor_corr = np.corrcoef(chroma_mean, minor_rot)[0, 1]
        
        correlations[f"{chord_names[i]} major"] = major_corr
        correlations[f"{chord_names[i]} minor"] = minor_corr
        
        if major_corr > best_corr:
            best_corr = major_corr
            best_key = chord_names[i]
            best_scale = 'major'
        
        if minor_corr > best_corr:
            best_corr = minor_corr
            best_key = chord_names[i]
            best_scale = 'minor'
    
    # Show top 5 candidates
    print("\nTop 5 key candidates:")
    sorted_keys = sorted(correlations.items(), key=lambda x: x[1], reverse=True)
    for i, (key_name, corr) in enumerate(sorted_keys[:5], 1):
        print(f"  {i}. {key_name:12s}: {corr:.3f}")
    
    # Validate with chord progression if available
    if chords and len(chords) > 0:
        print("\nValidating with chord progression...")
        progression_key, progression_scale, progression_conf = detect_key_from_chords(chords)
        print(f"  Progression suggests: {progression_key} {progression_scale} (confidence: {progression_conf:.3f})")
        
        # If progression confidence is high and disagrees, use progression
        if progression_conf > 0.5 and progression_key != best_key:
            print(f"  Using progression-based key (higher confidence)")
            best_key = progression_key
            best_scale = progression_scale
            best_corr = (best_corr + progression_conf) / 2  # Average confidences
    
    elapsed = time.time() - start_time
    print(f"\n✓ Key detection complete ({elapsed:.2f}s)")
    print(f"  Detected key: {best_key} {best_scale}")
    print(f"  Confidence: {best_corr:.3f}")
    print(f"  Method: chromagram (Krumhansl-Schmuckler)")
    print("=" * 80)
    
    return KeyDetection(
        key=best_key,
        scale=best_scale,
        confidence=float(best_corr),
        method='chromagram'
    )


def detect_key_from_chords(chords: List[Chord]) -> Tuple[str, str, float]:
    """
    Detect key by analyzing chord progression
    
    This looks at which chords appear most frequently and their relationships
    to determine the most likely key.
    
    Args:
        chords: List of detected chords
    
    Returns:
        (key, scale, confidence) tuple
    """
    if len(chords) == 0:
        return 'C', 'major', 0.0
    
    chord_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    # Count chord frequency (weighted by duration)
    chord_weights = {}
    for chord in chords:
        # Extract root note
        root = chord.name[0]
        if len(chord.name) > 1 and chord.name[1] in ['#', 'b']:
            root = chord.name[:2]
        
        # Weight by duration
        chord_weights[root] = chord_weights.get(root, 0) + chord.duration
    
    if not chord_weights:
        return 'C', 'major', 0.0
    
    # Most common chord is likely tonic or dominant
    most_common = max(chord_weights, key=chord_weights.get)
    total_duration = sum(chord_weights.values())
    confidence = chord_weights[most_common] / total_duration
    
    # Determine if major or minor by looking at chord qualities
    major_count = 0
    minor_count = 0
    
    for chord in chords:
        if 'm' in chord.name.lower() and 'maj' not in chord.name.lower():
            minor_count += chord.duration
        else:
            major_count += chord.duration
    
    scale = 'major' if major_count >= minor_count else 'minor'
    
    return most_common, scale, confidence


def detect_key_essentia(audio_path: str) -> KeyDetection:
    """
    Detect key using Essentia's ML-based KeyExtractor
    
    This is the preferred method when Essentia is available.
    
    Args:
        audio_path: Path to audio file
    
    Returns:
        KeyDetection object
    """
    if not ESSENTIA_AVAILABLE:
        raise ImportError("Essentia not available")
    
    print("Using Essentia KeyExtractor (ML-based)...")
    
    import essentia.standard as es
    
    # Load audio
    loader = es.MonoLoader(filename=audio_path, sampleRate=44100)
    audio = loader()
    
    # Use KeyExtractor with Temperley profile
    key_extractor = es.KeyExtractor(profileType='temperley')
    key, scale, strength = key_extractor(audio)
    
    print(f"  Essentia result: {key} {scale} (strength: {strength:.3f})")
    
    return KeyDetection(
        key=key,
        scale=scale,
        confidence=float(strength),
        method='essentia'
    )


def detect_key_complete(
    audio_path: str,
    chroma: np.ndarray,
    chords: List[Chord]
) -> KeyDetection:
    """
    Complete key detection using best available method
    
    Tries Essentia first (if available), falls back to chromagram method.
    Validates with chord progression.
    
    Args:
        audio_path: Path to audio file
        chroma: Chromagram for fallback method
        chords: Detected chords for validation
    
    Returns:
        KeyDetection object with best result
    """
    # Try Essentia first
    if ESSENTIA_AVAILABLE:
        try:
            essentia_result = detect_key_essentia(audio_path)
            
            # Validate with chromagram method
            chroma_result = detect_key_from_chromagram(chroma, chords)
            
            # If both agree, use Essentia (higher confidence)
            if essentia_result.key == chroma_result.key:
                print(f"\n✓ Both methods agree: {essentia_result.key} {essentia_result.scale}")
                return essentia_result
            else:
                print(f"\n⚠️ Methods disagree:")
                print(f"  Essentia: {essentia_result.key} {essentia_result.scale} ({essentia_result.confidence:.3f})")
                print(f"  Chromagram: {chroma_result.key} {chroma_result.scale} ({chroma_result.confidence:.3f})")
                
                # Use higher confidence
                if essentia_result.confidence > chroma_result.confidence:
                    print(f"  Using Essentia result (higher confidence)")
                    return essentia_result
                else:
                    print(f"  Using chromagram result (higher confidence)")
                    return chroma_result
        
        except Exception as e:
            print(f"Essentia key detection failed: {e}")
            print("Falling back to chromagram method...")
    
    # Fallback to chromagram method
    return detect_key_from_chromagram(chroma, chords)


# ============================================================================
# Complete Pipeline
# ============================================================================

def detect_chords_complete(
    audio_path: str,
    confirmed_downbeat: float = None,
    confirmed_time_signature: str = None
) -> Dict:
    """
    Complete chord detection pipeline
    
    Runs all 5 parts:
    1. Tempo & beat detection
    2. Stem separation
    3. Chromagram computation
    4. Chord detection
    5. Key detection
    
    Args:
        audio_path: Path to audio file
        confirmed_downbeat: User-confirmed first downbeat time (seconds)
        confirmed_time_signature: User-confirmed time signature (e.g., "4/4")
    
    Returns:
        Dictionary with all results
    """
    print("\n" + "=" * 80)
    print("COMPLETE CHORD DETECTION PIPELINE")
    print("=" * 80)
    print(f"Audio file: {audio_path}")
    if confirmed_downbeat is not None:
        print(f"Using confirmed downbeat: {confirmed_downbeat:.3f}s")
    if confirmed_time_signature is not None:
        print(f"Using confirmed time signature: {confirmed_time_signature}")
    print("=" * 80)
    
    pipeline_start = time.time()
    
    # Part 1: Tempo & Beat Detection
    timing_grid = detect_tempo_and_beats(audio_path)
    
    # Override with confirmed values if provided
    if confirmed_downbeat is not None:
        print(f"Adjusting beat grid to start from confirmed downbeat: {confirmed_downbeat:.3f}s")
        # Adjust beats to align with confirmed downbeat
        beat_duration = 60.0 / timing_grid.tempo
        # Find closest beat to confirmed downbeat
        beat_offset = confirmed_downbeat % beat_duration
        # Regenerate beats starting from confirmed downbeat
        duration = timing_grid.beats[-1] + beat_duration * 2  # Extend a bit
        num_beats = int((duration - confirmed_downbeat) / beat_duration) + 1
        timing_grid.beats = np.array([confirmed_downbeat + i * beat_duration for i in range(num_beats)])
        # Regenerate subdivisions
        timing_grid.subdivisions = generate_subdivisions(timing_grid.beats, level=4)
        print(f"  Adjusted to {len(timing_grid.beats)} beats starting from {confirmed_downbeat:.3f}s")
    
    if confirmed_time_signature is not None:
        timing_grid.time_signature = confirmed_time_signature
        print(f"  Using time signature: {confirmed_time_signature}")
    
    # Part 2: Stem Separation
    harmonic_audio, sr = separate_stems(audio_path, chunk_duration=30)
    
    # Part 3: Chromagram
    aligned_chroma = compute_beat_aligned_chromagram(
        harmonic_audio,
        sr,
        timing_grid.subdivisions,
        hop_length_ms=20
    )
    
    # Part 4: Chord Detection
    chords = detect_chords_with_templates(
        aligned_chroma,
        timing_grid.tempo,
        timing_grid.subdivisions,
        use_hmm=True
    )
    
    # Part 5: Key Detection
    key_detection = detect_key_complete(audio_path, aligned_chroma, chords)
    
    pipeline_elapsed = time.time() - pipeline_start
    
    # Summary
    print("\n" + "=" * 80)
    print("PIPELINE COMPLETE")
    print("=" * 80)
    print(f"Total processing time: {pipeline_elapsed:.2f}s")
    print(f"Audio duration: {len(harmonic_audio) / sr:.2f}s")
    print(f"Processing speed: {(len(harmonic_audio) / sr) / pipeline_elapsed:.1f}x realtime")
    print(f"\nResults:")
    print(f"  Tempo: {timing_grid.tempo:.1f} BPM")
    print(f"  Time signature: {timing_grid.time_signature}")
    print(f"  Key: {key_detection.key} {key_detection.scale} (confidence: {key_detection.confidence:.3f})")
    print(f"  Chords detected: {len(chords)}")
    print("=" * 80)
    
    return {
        'tempo': timing_grid.tempo,
        'time_signature': timing_grid.time_signature,
        'key': key_detection.key,
        'scale': key_detection.scale,
        'key_confidence': key_detection.confidence,
        'chords': [
            {
                'name': c.name,
                'start': c.start,
                'end': c.end,
                'duration': c.duration,
                'confidence': c.confidence
            }
            for c in chords
        ],
        'duration': len(harmonic_audio) / sr,
        'processing_time': pipeline_elapsed
    }


# ============================================================================
# Testing & Validation
# ============================================================================

def test_tempo_detection():
    """
    Test tempo and beat detection with sample audio
    """
    print("\n" + "=" * 80)
    print("TESTING TEMPO & BEAT DETECTION")
    print("=" * 80)
    
    # This would test with actual audio files
    # For now, just demonstrate the API
    
    test_cases = [
        {
            'name': 'Simple 4/4 at 120 BPM',
            'expected_tempo': 120,
            'expected_time_sig': '4/4',
        },
        {
            'name': 'Waltz 3/4 at 180 BPM',
            'expected_tempo': 180,
            'expected_time_sig': '3/4',
        },
        {
            'name': 'Slow ballad 4/4 at 60 BPM',
            'expected_tempo': 60,
            'expected_time_sig': '4/4',
        }
    ]
    
    print("\nTest cases defined:")
    for i, test in enumerate(test_cases, 1):
        print(f"  {i}. {test['name']}")
        print(f"     Expected: {test['expected_tempo']} BPM, {test['expected_time_sig']}")
    
    print("\nTo run tests, provide audio files and call:")
    print("  timing_grid = detect_tempo_and_beats('path/to/audio.mp3')")
    print("=" * 80)


if __name__ == "__main__":
    """
    Test the tempo detection module
    """
    print("Chord Detection V2 - Part 1: Tempo & Beat Detection")
    print("=" * 80)
    
    # Run test suite
    test_tempo_detection()
    
    print("\nModule loaded successfully!")
    print("\nNext steps:")
    print("  1. Test with real audio files")
    print("  2. Validate subdivision accuracy")
    print("  3. Proceed to Part 2: Stem Separation")

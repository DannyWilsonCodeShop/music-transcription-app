#!/usr/bin/env python3
"""
Downbeat Detection - Identify measure starts (beat 1)

Methods:
1. Beat strength analysis - downbeats are typically stronger
2. Onset strength patterns - look for periodic strong onsets
3. Spectral flux - energy changes at measure boundaries
4. User confirmation - play with click track for verification
"""

import numpy as np
import librosa
from typing import Tuple, List, Optional
import soundfile as sf
import tempfile
import os

def detect_downbeats(
    audio_path: str,
    beats: np.ndarray,
    tempo: float,
    time_signature: str = "4/4"
) -> Tuple[np.ndarray, float, dict]:
    """
    Detect downbeats (measure starts) from beat positions
    
    Args:
        audio_path: Path to audio file
        beats: Beat timestamps in seconds
        tempo: BPM
        time_signature: Time signature (e.g., "4/4")
    
    Returns:
        downbeats: Array of downbeat timestamps
        first_downbeat: Timestamp of first downbeat
        info: Dictionary with detection details
    """
    print("=" * 80)
    print("DOWNBEAT DETECTION")
    print("=" * 80)
    
    # Load audio
    print(f"\nLoading audio: {audio_path}")
    y, sr = librosa.load(audio_path, sr=22050)
    
    # Parse time signature
    beats_per_measure = int(time_signature.split('/')[0])
    print(f"Time signature: {time_signature} ({beats_per_measure} beats per measure)")
    print(f"Tempo: {tempo:.1f} BPM")
    print(f"Total beats detected: {len(beats)}")
    
    # Method 1: Beat strength analysis
    print("\nMethod 1: Analyzing beat strength...")
    downbeats_strength, strength_scores = detect_downbeats_by_strength(
        y, sr, beats, beats_per_measure
    )
    print(f"  Found {len(downbeats_strength)} downbeat candidates")
    
    # Method 2: Onset strength patterns
    print("\nMethod 2: Analyzing onset patterns...")
    downbeats_onset, onset_scores = detect_downbeats_by_onset_pattern(
        y, sr, beats, beats_per_measure
    )
    print(f"  Found {len(downbeats_onset)} downbeat candidates")
    
    # Method 3: Spectral flux
    print("\nMethod 3: Analyzing spectral flux...")
    downbeats_flux, flux_scores = detect_downbeats_by_spectral_flux(
        y, sr, beats, beats_per_measure
    )
    print(f"  Found {len(downbeats_flux)} downbeat candidates")
    
    # Combine methods (voting)
    print("\nCombining methods...")
    downbeats, confidence_scores = combine_downbeat_detections(
        beats,
        [downbeats_strength, downbeats_onset, downbeats_flux],
        [strength_scores, onset_scores, flux_scores],
        beats_per_measure
    )
    
    print(f"  Final downbeats: {len(downbeats)}")
    print(f"  Average confidence: {np.mean(confidence_scores):.3f}")
    
    # Find first downbeat
    first_downbeat = downbeats[0] if len(downbeats) > 0 else beats[0]
    first_confidence = confidence_scores[0] if len(confidence_scores) > 0 else 0.0
    
    print(f"\nFirst downbeat:")
    print(f"  Time: {first_downbeat:.3f}s")
    print(f"  Confidence: {first_confidence:.3f}")
    
    # Show first few downbeats
    print(f"\nFirst 10 downbeats:")
    for i in range(min(10, len(downbeats))):
        print(f"  Measure {i+1}: {downbeats[i]:.3f}s (confidence: {confidence_scores[i]:.3f})")
    
    info = {
        'method_1_strength': len(downbeats_strength),
        'method_2_onset': len(downbeats_onset),
        'method_3_flux': len(downbeats_flux),
        'combined': len(downbeats),
        'first_downbeat': first_downbeat,
        'first_confidence': first_confidence,
        'average_confidence': float(np.mean(confidence_scores)) if len(confidence_scores) > 0 else 0.0
    }
    
    print("=" * 80)
    
    return downbeats, first_downbeat, info


def detect_downbeats_by_strength(
    y: np.ndarray,
    sr: int,
    beats: np.ndarray,
    beats_per_measure: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Detect downbeats by analyzing beat strength
    
    Downbeats (measure starts) are typically stronger than other beats.
    In 4/4 time, beat 1 is strongest, beat 3 is medium, beats 2 and 4 are weakest.
    
    Args:
        y: Audio signal
        sr: Sample rate
        beats: Beat timestamps
        beats_per_measure: Beats per measure (4 for 4/4)
    
    Returns:
        downbeats: Downbeat timestamps
        scores: Confidence scores for each downbeat
    """
    # Compute onset strength
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    onset_times = librosa.frames_to_time(np.arange(len(onset_env)), sr=sr)
    
    # Get onset strength at each beat
    beat_strengths = []
    for beat_time in beats:
        # Find closest onset frame
        idx = np.argmin(np.abs(onset_times - beat_time))
        # Average strength around beat (±50ms window)
        window = int(0.05 * sr / 512)  # 50ms window
        start = max(0, idx - window)
        end = min(len(onset_env), idx + window + 1)
        strength = np.mean(onset_env[start:end])
        beat_strengths.append(strength)
    
    beat_strengths = np.array(beat_strengths)
    
    # Normalize strengths
    if np.max(beat_strengths) > 0:
        beat_strengths = beat_strengths / np.max(beat_strengths)
    
    # Find periodic peaks (every beats_per_measure beats)
    # Try different phase offsets to find the best alignment
    best_phase = 0
    best_score = 0
    
    for phase in range(beats_per_measure):
        # Sum strengths at this phase
        phase_strengths = beat_strengths[phase::beats_per_measure]
        score = np.mean(phase_strengths)
        
        if score > best_score:
            best_score = score
            best_phase = phase
    
    # Extract downbeats at best phase
    downbeat_indices = np.arange(best_phase, len(beats), beats_per_measure)
    downbeats = beats[downbeat_indices]
    scores = beat_strengths[downbeat_indices]
    
    return downbeats, scores


def detect_downbeats_by_onset_pattern(
    y: np.ndarray,
    sr: int,
    beats: np.ndarray,
    beats_per_measure: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Detect downbeats by analyzing onset patterns
    
    Look for strong onsets that occur periodically at measure boundaries.
    
    Args:
        y: Audio signal
        sr: Sample rate
        beats: Beat timestamps
        beats_per_measure: Beats per measure
    
    Returns:
        downbeats: Downbeat timestamps
        scores: Confidence scores
    """
    # Compute onset strength with higher sensitivity
    onset_env = librosa.onset.onset_strength(
        y=y, sr=sr, aggregate=np.median, fmax=8000
    )
    
    # Detect onset peaks
    onset_frames = librosa.onset.onset_detect(
        onset_envelope=onset_env,
        sr=sr,
        backtrack=True
    )
    onset_times = librosa.frames_to_time(onset_frames, sr=sr)
    onset_strengths = onset_env[onset_frames]
    
    # For each beat, find if there's a strong onset nearby
    beat_has_onset = []
    beat_onset_strength = []
    
    for beat_time in beats:
        # Find onsets within ±100ms of beat
        nearby = np.abs(onset_times - beat_time) < 0.1
        if np.any(nearby):
            # Take strongest nearby onset
            strength = np.max(onset_strengths[nearby])
            beat_has_onset.append(True)
            beat_onset_strength.append(strength)
        else:
            beat_has_onset.append(False)
            beat_onset_strength.append(0.0)
    
    beat_onset_strength = np.array(beat_onset_strength)
    
    # Normalize
    if np.max(beat_onset_strength) > 0:
        beat_onset_strength = beat_onset_strength / np.max(beat_onset_strength)
    
    # Find best phase (same as strength method)
    best_phase = 0
    best_score = 0
    
    for phase in range(beats_per_measure):
        phase_strengths = beat_onset_strength[phase::beats_per_measure]
        score = np.mean(phase_strengths)
        
        if score > best_score:
            best_score = score
            best_phase = phase
    
    downbeat_indices = np.arange(best_phase, len(beats), beats_per_measure)
    downbeats = beats[downbeat_indices]
    scores = beat_onset_strength[downbeat_indices]
    
    return downbeats, scores


def detect_downbeats_by_spectral_flux(
    y: np.ndarray,
    sr: int,
    beats: np.ndarray,
    beats_per_measure: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Detect downbeats using spectral flux
    
    Measure changes typically have larger spectral changes.
    
    Args:
        y: Audio signal
        sr: Sample rate
        beats: Beat timestamps
        beats_per_measure: Beats per measure
    
    Returns:
        downbeats: Downbeat timestamps
        scores: Confidence scores
    """
    # Compute STFT
    D = np.abs(librosa.stft(y))
    
    # Compute spectral flux (change in spectrum)
    flux = np.sqrt(np.sum(np.diff(D, axis=1)**2, axis=0))
    flux = np.concatenate([[0], flux])  # Prepend 0 for first frame
    
    flux_times = librosa.frames_to_time(np.arange(len(flux)), sr=sr)
    
    # Get flux at each beat
    beat_flux = []
    for beat_time in beats:
        idx = np.argmin(np.abs(flux_times - beat_time))
        # Average flux around beat
        window = 5
        start = max(0, idx - window)
        end = min(len(flux), idx + window + 1)
        beat_flux.append(np.mean(flux[start:end]))
    
    beat_flux = np.array(beat_flux)
    
    # Normalize
    if np.max(beat_flux) > 0:
        beat_flux = beat_flux / np.max(beat_flux)
    
    # Find best phase
    best_phase = 0
    best_score = 0
    
    for phase in range(beats_per_measure):
        phase_flux = beat_flux[phase::beats_per_measure]
        score = np.mean(phase_flux)
        
        if score > best_score:
            best_score = score
            best_phase = phase
    
    downbeat_indices = np.arange(best_phase, len(beats), beats_per_measure)
    downbeats = beats[downbeat_indices]
    scores = beat_flux[downbeat_indices]
    
    return downbeats, scores


def combine_downbeat_detections(
    beats: np.ndarray,
    downbeat_arrays: List[np.ndarray],
    score_arrays: List[np.ndarray],
    beats_per_measure: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Combine multiple downbeat detection methods using voting
    
    Args:
        beats: All beat timestamps
        downbeat_arrays: List of downbeat arrays from different methods
        score_arrays: List of confidence score arrays
        beats_per_measure: Beats per measure
    
    Returns:
        downbeats: Combined downbeat timestamps
        confidence_scores: Confidence for each downbeat
    """
    # Find which phase (offset) each method chose
    phases = []
    for downbeats in downbeat_arrays:
        if len(downbeats) > 0:
            # Find which beat index is the first downbeat
            first_downbeat_idx = np.argmin(np.abs(beats - downbeats[0]))
            phase = first_downbeat_idx % beats_per_measure
            phases.append(phase)
    
    if len(phases) == 0:
        # No downbeats detected, use first beat
        return beats[::beats_per_measure], np.ones(len(beats[::beats_per_measure]))
    
    # Vote for most common phase
    phase_counts = np.bincount(phases, minlength=beats_per_measure)
    best_phase = np.argmax(phase_counts)
    
    # Extract downbeats at best phase
    downbeat_indices = np.arange(best_phase, len(beats), beats_per_measure)
    downbeats = beats[downbeat_indices]
    
    # Combine confidence scores from methods that agree
    combined_scores = []
    for i, downbeat in enumerate(downbeats):
        scores_for_this_downbeat = []
        
        for j, (method_downbeats, method_scores) in enumerate(zip(downbeat_arrays, score_arrays)):
            # Check if this method has this downbeat
            if len(method_downbeats) > i:
                # Check if downbeats match (within 0.1s)
                if np.abs(method_downbeats[i] - downbeat) < 0.1:
                    scores_for_this_downbeat.append(method_scores[i])
        
        # Average scores from agreeing methods
        if len(scores_for_this_downbeat) > 0:
            combined_scores.append(np.mean(scores_for_this_downbeat))
        else:
            combined_scores.append(0.5)  # Default confidence
    
    return downbeats, np.array(combined_scores)


def generate_click_track(
    tempo: float,
    duration: float,
    downbeat_times: np.ndarray,
    beat_times: np.ndarray,
    sr: int = 22050
) -> np.ndarray:
    """
    Generate click track with emphasized downbeats
    
    Args:
        tempo: BPM
        duration: Duration in seconds
        downbeat_times: Downbeat timestamps
        beat_times: All beat timestamps
        sr: Sample rate
    
    Returns:
        click_track: Audio array with clicks
    """
    click_track = np.zeros(int(duration * sr))
    
    # Generate click sounds
    # Downbeat: 1000 Hz, 50ms
    # Regular beat: 800 Hz, 30ms
    
    t_downbeat = np.linspace(0, 0.05, int(0.05 * sr))
    downbeat_click = 0.5 * np.sin(2 * np.pi * 1000 * t_downbeat) * np.exp(-t_downbeat * 20)
    
    t_beat = np.linspace(0, 0.03, int(0.03 * sr))
    beat_click = 0.3 * np.sin(2 * np.pi * 800 * t_beat) * np.exp(-t_beat * 30)
    
    # Add downbeat clicks
    for downbeat_time in downbeat_times:
        start_sample = int(downbeat_time * sr)
        end_sample = start_sample + len(downbeat_click)
        if end_sample <= len(click_track):
            click_track[start_sample:end_sample] += downbeat_click
    
    # Add regular beat clicks
    for beat_time in beat_times:
        # Skip if this is a downbeat
        if not np.any(np.abs(downbeat_times - beat_time) < 0.01):
            start_sample = int(beat_time * sr)
            end_sample = start_sample + len(beat_click)
            if end_sample <= len(click_track):
                click_track[start_sample:end_sample] += beat_click
    
    return click_track


def create_verification_audio(
    audio_path: str,
    downbeat_times: np.ndarray,
    beat_times: np.ndarray,
    tempo: float,
    duration: float = 15.0,
    output_path: Optional[str] = None
) -> str:
    """
    Create audio file with click track for user verification
    
    Args:
        audio_path: Original audio file
        downbeat_times: Downbeat timestamps
        beat_times: All beat timestamps
        tempo: BPM
        duration: Duration to export (default 15s)
        output_path: Output path (default: temp file)
    
    Returns:
        Path to verification audio file
    """
    # Load audio
    y, sr = librosa.load(audio_path, sr=22050, duration=duration)
    
    # Generate click track
    click_track = generate_click_track(
        tempo,
        duration,
        downbeat_times[downbeat_times < duration],
        beat_times[beat_times < duration],
        sr
    )
    
    # Trim click track to match audio length
    click_track = click_track[:len(y)]
    
    # Mix audio with clicks (clicks at 30% volume)
    mixed = y + click_track * 0.3
    
    # Normalize
    mixed = mixed / np.max(np.abs(mixed))
    
    # Save
    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix='_with_clicks.wav')
        os.close(fd)
    
    sf.write(output_path, mixed, sr)
    
    return output_path


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python downbeat_detection.py <audio_file>")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    
    # Detect tempo and beats first
    print("Detecting tempo and beats...")
    y, sr = librosa.load(audio_path, sr=22050)
    tempo_raw, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    tempo = float(tempo_raw) if isinstance(tempo_raw, (int, float)) else float(tempo_raw[0])
    beats = librosa.frames_to_time(beat_frames, sr=sr)
    
    print(f"Tempo: {tempo:.1f} BPM")
    print(f"Beats: {len(beats)}")
    
    # Detect downbeats
    downbeats, first_downbeat, info = detect_downbeats(
        audio_path,
        beats,
        tempo,
        time_signature="4/4"
    )
    
    # Create verification audio
    print("\nCreating verification audio with click track...")
    verification_path = create_verification_audio(
        audio_path,
        downbeats,
        beats,
        tempo,
        duration=15.0,
        output_path="/tmp/downbeat_verification.wav"
    )
    
    print(f"\n✓ Verification audio created: {verification_path}")
    print("\nListen to this file:")
    print("  - Loud clicks = downbeats (measure starts)")
    print("  - Soft clicks = regular beats")
    print("  - Check if loud clicks align with measure 1")

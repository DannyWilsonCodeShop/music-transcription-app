#!/usr/bin/env python3
"""
Downbeat Detection Script for Lambda
Outputs JSON to stdout for Lambda to parse
"""

import sys
import json
import numpy as np
import librosa

def detect_downbeats(audio_path, beat_times, tempo, time_signature="4/4"):
    """
    Detect downbeats using multiple methods
    
    Returns:
        downbeats: Array of downbeat timestamps
        first_downbeat: First downbeat timestamp
        info: Dictionary with confidence and method info
    """
    y, sr = librosa.load(audio_path, sr=22050)
    beats_per_measure = int(time_signature.split('/')[0])
    
    # Method 1: Beat strength analysis
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    beat_frames = librosa.time_to_frames(beat_times, sr=sr)
    beat_strengths = np.array([onset_env[min(frame, len(onset_env)-1)] for frame in beat_frames])
    
    # Normalize strengths
    if len(beat_strengths) > 0:
        beat_strengths = (beat_strengths - np.mean(beat_strengths)) / (np.std(beat_strengths) + 1e-10)
    
    # Find phase with strongest beats
    phase_scores = []
    for phase in range(beats_per_measure):
        phase_beats = beat_strengths[phase::beats_per_measure]
        phase_score = np.mean(phase_beats) if len(phase_beats) > 0 else 0
        phase_scores.append(phase_score)
    
    best_phase_strength = int(np.argmax(phase_scores))
    
    # Method 2: Onset pattern detection
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr, units='frames')
    onset_times = librosa.frames_to_time(onset_frames, sr=sr)
    
    phase_onset_counts = []
    for phase in range(beats_per_measure):
        phase_beat_times = beat_times[phase::beats_per_measure]
        onset_count = 0
        for beat_time in phase_beat_times:
            nearby_onsets = np.sum(np.abs(onset_times - beat_time) < 0.1)
            onset_count += nearby_onsets
        phase_onset_counts.append(onset_count)
    
    best_phase_onset = int(np.argmax(phase_onset_counts))
    
    # Method 3: Spectral flux analysis
    S = np.abs(librosa.stft(y))
    flux = np.sqrt(np.sum(np.diff(S, axis=1)**2, axis=0))
    flux = np.pad(flux, (1, 0), mode='constant')
    
    phase_flux_scores = []
    for phase in range(beats_per_measure):
        phase_beat_frames = beat_frames[phase::beats_per_measure]
        flux_values = [flux[min(frame, len(flux)-1)] for frame in phase_beat_frames]
        phase_flux_scores.append(np.mean(flux_values) if len(flux_values) > 0 else 0)
    
    best_phase_flux = int(np.argmax(phase_flux_scores))
    
    # Combine methods (voting)
    phases = [best_phase_strength, best_phase_onset, best_phase_flux]
    phase_counts = [phases.count(i) for i in range(beats_per_measure)]
    best_phase = int(np.argmax(phase_counts))
    agreement = phase_counts[best_phase] / 3.0
    
    # Generate downbeats
    downbeats = beat_times[best_phase::beats_per_measure]
    first_downbeat = float(downbeats[0]) if len(downbeats) > 0 else float(beat_times[0])
    
    # Calculate confidence
    confidence = agreement * (phase_scores[best_phase] / (np.max(phase_scores) + 1e-10))
    
    return downbeats, first_downbeat, {
        'confidence': float(confidence),
        'agreement': float(agreement),
        'best_phase': best_phase,
        'method_phases': {
            'strength': best_phase_strength,
            'onset': best_phase_onset,
            'flux': best_phase_flux
        }
    }

def main():
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Usage: detect_downbeat.py <audio_path>'}))
        sys.exit(1)
    
    audio_path = sys.argv[1]
    
    try:
        # Load audio and detect tempo/beats
        y, sr = librosa.load(audio_path, sr=22050)
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        
        # Handle tempo as array or scalar
        if isinstance(tempo, np.ndarray):
            tempo = float(tempo[0])
        else:
            tempo = float(tempo)
        
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)
        
        # Detect time signature (simplified - default to 4/4)
        time_signature = "4/4"
        
        # Detect downbeats
        downbeats, first_downbeat, info = detect_downbeats(
            audio_path,
            beat_times,
            tempo,
            time_signature
        )
        
        # Prepare output
        result = {
            'tempo': tempo,
            'timeSignature': time_signature,
            'detectedDownbeat': first_downbeat,
            'confidence': info['confidence'],
            'beatTimes': beat_times.tolist(),
            'downbeats': downbeats.tolist(),
            'totalBeats': len(beat_times),
            'totalMeasures': len(downbeats),
            'methodInfo': info
        }
        
        # Output JSON to stdout
        print(json.dumps(result))
        
    except Exception as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()

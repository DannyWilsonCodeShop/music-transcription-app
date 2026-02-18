#!/usr/bin/env python3
"""
Interactive Downbeat Confirmation Tool

Plays audio clips with click tracks and asks user to confirm:
1. Is the downbeat correct?
2. What is the time signature?
3. Manual adjustment if needed
"""

import numpy as np
import librosa
import soundfile as sf
import sounddevice as sd
import sys
import os
from downbeat_detection import (
    detect_downbeats,
    generate_click_track,
    create_verification_audio
)

def play_audio(audio_path_or_array, sr=22050, wait=True):
    """Play audio file or array"""
    if isinstance(audio_path_or_array, str):
        audio, sr = librosa.load(audio_path_or_array, sr=sr)
    else:
        audio = audio_path_or_array
    
    sd.play(audio, sr)
    if wait:
        sd.wait()

def create_clip_with_clicks(
    audio_path: str,
    downbeat_time: float,
    beat_times: np.ndarray,
    tempo: float,
    beats_per_measure: int,
    clip_duration: float = 8.0
) -> tuple:
    """
    Create a clip starting from downbeat with click track
    
    Args:
        audio_path: Original audio
        downbeat_time: Start time of downbeat
        beat_times: All beat timestamps
        tempo: BPM
        beats_per_measure: Beats per measure
        clip_duration: Duration of clip in seconds
    
    Returns:
        (mixed_audio, sr)
    """
    # Load clip starting from downbeat
    y, sr = librosa.load(
        audio_path,
        sr=22050,
        offset=max(0, downbeat_time - 0.5),  # Start 0.5s before downbeat
        duration=clip_duration
    )
    
    # Adjust beat times relative to clip start
    clip_start = max(0, downbeat_time - 0.5)
    adjusted_beats = beat_times - clip_start
    adjusted_beats = adjusted_beats[(adjusted_beats >= 0) & (adjusted_beats < clip_duration)]
    
    # Find downbeats in this clip
    downbeat_indices = []
    for i, beat in enumerate(beat_times):
        if clip_start <= beat < clip_start + clip_duration:
            # Check if this is a downbeat
            beat_index_in_song = np.argmin(np.abs(beat_times - beat))
            first_downbeat_index = np.argmin(np.abs(beat_times - downbeat_time))
            if (beat_index_in_song - first_downbeat_index) % beats_per_measure == 0:
                downbeat_indices.append(beat - clip_start)
    
    adjusted_downbeats = np.array(downbeat_indices)
    
    # Generate click track
    click_track = generate_click_track(
        tempo,
        clip_duration,
        adjusted_downbeats,
        adjusted_beats,
        sr
    )
    
    # Trim to match audio length
    click_track = click_track[:len(y)]
    
    # Mix (clicks at 40% volume for clarity)
    mixed = y + click_track * 0.4
    mixed = mixed / np.max(np.abs(mixed))
    
    return mixed, sr

def confirm_downbeat_interactive(
    audio_path: str,
    detected_downbeat: float,
    beat_times: np.ndarray,
    tempo: float,
    detected_time_signature: str = "4/4"
) -> tuple:
    """
    Interactive confirmation of downbeat and time signature
    
    Returns:
        (confirmed_downbeat, confirmed_time_signature, beats_per_measure)
    """
    print("\n" + "=" * 80)
    print("DOWNBEAT & TIME SIGNATURE CONFIRMATION")
    print("=" * 80)
    
    print(f"\nDetected:")
    print(f"  Tempo: {tempo:.1f} BPM")
    print(f"  First downbeat: {detected_downbeat:.3f}s")
    print(f"  Time signature: {detected_time_signature}")
    
    beats_per_measure = int(detected_time_signature.split('/')[0])
    
    # Play clip with clicks
    print(f"\nPreparing audio clip with click track...")
    print(f"  - LOUD clicks = downbeats (measure starts)")
    print(f"  - soft clicks = regular beats")
    print(f"  - Clip starts 0.5s before first downbeat")
    
    mixed, sr = create_clip_with_clicks(
        audio_path,
        detected_downbeat,
        beat_times,
        tempo,
        beats_per_measure,
        clip_duration=8.0
    )
    
    # Confirmation loop
    while True:
        print("\n" + "-" * 80)
        print("Playing 8-second clip...")
        print("-" * 80)
        
        play_audio(mixed, sr, wait=True)
        
        print("\nQuestions:")
        print("1. Did the LOUD click align with the first beat of the measure?")
        response = input("   (y/n): ").strip().lower()
        
        if response == 'y':
            # Downbeat is correct, now confirm time signature
            print(f"\n2. Is the time signature {detected_time_signature}?")
            print(f"   (Count beats between loud clicks: should be {beats_per_measure})")
            ts_response = input(f"   (y/n or enter correct time signature like '3/4'): ").strip()
            
            if ts_response.lower() == 'y':
                print("\n✓ Downbeat and time signature confirmed!")
                return detected_downbeat, detected_time_signature, beats_per_measure
            elif '/' in ts_response:
                # User provided different time signature
                new_time_sig = ts_response
                new_beats_per_measure = int(new_time_sig.split('/')[0])
                print(f"\n✓ Using time signature: {new_time_sig}")
                
                # Regenerate clip with new time signature
                mixed, sr = create_clip_with_clicks(
                    audio_path,
                    detected_downbeat,
                    beat_times,
                    tempo,
                    new_beats_per_measure,
                    clip_duration=8.0
                )
                
                print("\nPlaying again with updated time signature...")
                play_audio(mixed, sr, wait=True)
                
                confirm = input("\nDoes this sound correct? (y/n): ").strip().lower()
                if confirm == 'y':
                    return detected_downbeat, new_time_sig, new_beats_per_measure
            else:
                print("\nLet's try again...")
                continue
        
        elif response == 'n':
            # Downbeat is wrong, need adjustment
            print("\n3. The downbeat needs adjustment.")
            print("   Options:")
            print("   a) Try next beat as downbeat")
            print("   b) Try previous beat as downbeat")
            print("   c) Enter manual offset in seconds (+ or -)")
            print("   d) Replay current clip")
            
            adjustment = input("   Choice (a/b/c/d): ").strip().lower()
            
            if adjustment == 'a':
                # Try next beat
                next_beat_idx = np.argmin(np.abs(beat_times - detected_downbeat)) + 1
                if next_beat_idx < len(beat_times):
                    detected_downbeat = beat_times[next_beat_idx]
                    print(f"\n→ Trying next beat: {detected_downbeat:.3f}s")
                    mixed, sr = create_clip_with_clicks(
                        audio_path, detected_downbeat, beat_times, tempo,
                        beats_per_measure, clip_duration=8.0
                    )
            
            elif adjustment == 'b':
                # Try previous beat
                prev_beat_idx = np.argmin(np.abs(beat_times - detected_downbeat)) - 1
                if prev_beat_idx >= 0:
                    detected_downbeat = beat_times[prev_beat_idx]
                    print(f"\n→ Trying previous beat: {detected_downbeat:.3f}s")
                    mixed, sr = create_clip_with_clicks(
                        audio_path, detected_downbeat, beat_times, tempo,
                        beats_per_measure, clip_duration=8.0
                    )
            
            elif adjustment == 'c':
                # Manual offset
                try:
                    offset = float(input("   Enter offset in seconds (+ or -): "))
                    detected_downbeat += offset
                    print(f"\n→ New downbeat: {detected_downbeat:.3f}s")
                    mixed, sr = create_clip_with_clicks(
                        audio_path, detected_downbeat, beat_times, tempo,
                        beats_per_measure, clip_duration=8.0
                    )
                except ValueError:
                    print("Invalid offset, please try again")
            
            elif adjustment == 'd':
                # Replay
                continue
            
            else:
                print("Invalid choice, please try again")
        
        else:
            print("Please answer 'y' or 'n'")

def main():
    if len(sys.argv) < 2:
        print("Usage: python confirm_downbeat.py <audio_file>")
        print("\nThis tool will:")
        print("  1. Detect tempo, beats, and downbeat")
        print("  2. Play audio clip with click track")
        print("  3. Ask you to confirm downbeat and time signature")
        print("  4. Allow adjustments if needed")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    
    if not os.path.exists(audio_path):
        print(f"Error: File not found: {audio_path}")
        sys.exit(1)
    
    print("=" * 80)
    print("INTERACTIVE DOWNBEAT CONFIRMATION")
    print("=" * 80)
    print(f"\nAudio file: {audio_path}")
    
    # Step 1: Detect tempo and beats
    print("\nStep 1: Detecting tempo and beats...")
    y, sr = librosa.load(audio_path, sr=22050)
    tempo_raw, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    tempo = float(tempo_raw) if isinstance(tempo_raw, (int, float)) else float(tempo_raw[0])
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    
    print(f"  Tempo: {tempo:.1f} BPM")
    print(f"  Beats detected: {len(beat_times)}")
    
    # Step 2: Detect downbeats
    print("\nStep 2: Detecting downbeats...")
    downbeats, first_downbeat, info = detect_downbeats(
        audio_path,
        beat_times,
        tempo,
        time_signature="4/4"
    )
    
    # Step 3: Interactive confirmation
    print("\nStep 3: User confirmation...")
    confirmed_downbeat, confirmed_time_sig, beats_per_measure = confirm_downbeat_interactive(
        audio_path,
        first_downbeat,
        beat_times,
        tempo,
        detected_time_signature="4/4"
    )
    
    # Step 4: Save results
    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    print(f"Tempo: {tempo:.1f} BPM")
    print(f"Time signature: {confirmed_time_sig}")
    print(f"First downbeat: {confirmed_downbeat:.3f}s")
    print(f"Beats per measure: {beats_per_measure}")
    
    # Calculate all downbeats from confirmed first downbeat
    beat_duration = 60.0 / tempo
    measure_duration = beat_duration * beats_per_measure
    
    # Find which beat index is the confirmed downbeat
    first_downbeat_idx = np.argmin(np.abs(beat_times - confirmed_downbeat))
    
    # Calculate all downbeats
    all_downbeats = []
    for i in range(first_downbeat_idx, len(beat_times), beats_per_measure):
        all_downbeats.append(beat_times[i])
    
    all_downbeats = np.array(all_downbeats)
    
    print(f"\nTotal measures: {len(all_downbeats)}")
    print(f"\nFirst 5 measures:")
    for i in range(min(5, len(all_downbeats))):
        print(f"  Measure {i+1}: {all_downbeats[i]:.3f}s")
    
    # Save to file
    output_file = "/tmp/confirmed_downbeat.txt"
    with open(output_file, 'w') as f:
        f.write(f"tempo={tempo}\n")
        f.write(f"time_signature={confirmed_time_sig}\n")
        f.write(f"first_downbeat={confirmed_downbeat}\n")
        f.write(f"beats_per_measure={beats_per_measure}\n")
        f.write(f"downbeats={','.join([str(d) for d in all_downbeats])}\n")
    
    print(f"\n✓ Results saved to: {output_file}")
    print("\nYou can now use these confirmed values in chord detection!")
    print("=" * 80)

if __name__ == "__main__":
    main()

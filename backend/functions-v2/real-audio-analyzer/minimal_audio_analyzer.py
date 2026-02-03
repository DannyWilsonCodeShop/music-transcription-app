#!/usr/bin/env python3
"""
Minimal Real Audio Analysis Engine
Lightweight chord detection using only librosa, numpy, and scipy
"""

import librosa
import numpy as np
import scipy.signal
import soundfile as sf
import requests
import tempfile
import os
import json
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class MinimalAudioAnalyzer:
    """Lightweight audio analysis engine using only essential libraries"""
    
    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate
        self.hop_length = 512
        self.frame_length = 2048
        
        # Basic chord templates (major and minor only)
        self.chord_templates = self._create_basic_chord_templates()
        self.chord_names = self._create_basic_chord_names()
        
    def analyze_audio_file(self, audio_url: str, analysis_interval: float = 0.5) -> Dict:
        """
        Perform lightweight audio analysis
        
        Args:
            audio_url: URL or path to audio file
            analysis_interval: Interval in seconds for chord analysis (0.5s for efficiency)
            
        Returns:
            Complete musical analysis dictionary
        """
        print(f"🎼 Starting minimal audio analysis for: {audio_url}")
        
        # Load audio
        audio_data, duration = self._load_audio(audio_url)
        print(f"📊 Audio loaded: {duration:.2f} seconds")
        
        # Perform lightweight analyses
        tempo_analysis = self._analyze_tempo_simple(audio_data)
        key_analysis = self._analyze_key_simple(audio_data)
        time_signature_analysis = self._analyze_time_signature_simple(tempo_analysis['bpm'], duration)
        chord_analysis = self._analyze_chords_simple(audio_data, duration, analysis_interval)
        
        # Combine results
        complete_analysis = {
            'tempo': tempo_analysis,
            'key': key_analysis,
            'timeSignature': time_signature_analysis,
            'chords': chord_analysis,
            'metadata': {
                'duration': duration,
                'sample_rate': self.sample_rate,
                'analysis_interval': analysis_interval,
                'analysis_method': 'minimal_real_analysis',
                'libraries_used': ['librosa', 'numpy', 'scipy']
            }
        }
        
        print(f"✅ Minimal analysis complete: {len(chord_analysis['chords'])} chord detections")
        return complete_analysis
    
    def _load_audio(self, audio_url: str) -> Tuple[np.ndarray, float]:
        """Load audio from URL or file path"""
        try:
            if audio_url.startswith(('http://', 'https://')):
                # Download from URL
                response = requests.get(audio_url, timeout=30)
                response.raise_for_status()
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                    temp_file.write(response.content)
                    temp_path = temp_file.name
                
                try:
                    audio_data, sr = librosa.load(temp_path, sr=self.sample_rate)
                    duration = len(audio_data) / sr
                    return audio_data, duration
                finally:
                    os.unlink(temp_path)
            else:
                # Load from file path
                audio_data, sr = librosa.load(audio_url, sr=self.sample_rate)
                duration = len(audio_data) / sr
                return audio_data, duration
                
        except Exception as e:
            raise Exception(f"Failed to load audio: {str(e)}")
    
    def _analyze_tempo_simple(self, audio_data: np.ndarray) -> Dict:
        """Simple tempo detection using librosa"""
        try:
            tempo, beats = librosa.beat.beat_track(
                y=audio_data, 
                sr=self.sample_rate,
                hop_length=self.hop_length
            )
            
            # Convert beat frames to time
            beat_times = librosa.frames_to_time(beats, sr=self.sample_rate, hop_length=self.hop_length)
            
            # Simple confidence calculation
            if len(beat_times) > 1:
                beat_intervals = np.diff(beat_times)
                tempo_confidence = max(0.3, min(1.0, 1.0 - (np.std(beat_intervals) / np.mean(beat_intervals))))
            else:
                tempo_confidence = 0.5
            
            return {
                'bpm': float(tempo),
                'confidence': float(tempo_confidence),
                'beat_times': beat_times.tolist(),
                'method': 'librosa_simple'
            }
            
        except Exception as e:
            print(f"Warning: Tempo analysis failed: {e}")
            return {
                'bpm': 120.0,
                'confidence': 0.3,
                'beat_times': [],
                'method': 'fallback'
            }
    
    def _analyze_key_simple(self, audio_data: np.ndarray) -> Dict:
        """Simple key detection using chromagram"""
        try:
            # Compute chromagram
            chroma = librosa.feature.chroma_stft(
                y=audio_data, 
                sr=self.sample_rate,
                hop_length=self.hop_length
            )
            
            # Average chromagram over time
            chroma_mean = np.mean(chroma, axis=1)
            
            # Simple key detection - find strongest chroma bin
            strongest_chroma = np.argmax(chroma_mean)
            note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            
            # Simple major/minor detection based on chroma pattern
            # Major tends to have strong 1st, 3rd, and 5th
            major_strength = chroma_mean[strongest_chroma] + chroma_mean[(strongest_chroma + 4) % 12] + chroma_mean[(strongest_chroma + 7) % 12]
            minor_strength = chroma_mean[strongest_chroma] + chroma_mean[(strongest_chroma + 3) % 12] + chroma_mean[(strongest_chroma + 7) % 12]
            
            mode = 'major' if major_strength > minor_strength else 'minor'
            confidence = max(0.3, min(1.0, max(major_strength, minor_strength) / np.sum(chroma_mean)))
            
            return {
                'root': note_names[strongest_chroma],
                'mode': mode,
                'confidence': float(confidence),
                'method': 'simple_chroma'
            }
            
        except Exception as e:
            print(f"Warning: Key analysis failed: {e}")
            return {
                'root': 'C',
                'mode': 'major',
                'confidence': 0.3,
                'method': 'fallback'
            }
    
    def _analyze_time_signature_simple(self, bpm: float, duration: float) -> Dict:
        """Simple time signature analysis (assumes 4/4)"""
        try:
            beat_duration = 60.0 / bpm
            measure_duration = beat_duration * 4  # Assume 4/4
            
            measures = []
            time = 0
            measure_num = 1
            
            while time < duration:
                measures.append({
                    'start': time,
                    'end': min(time + measure_duration, duration),
                    'downbeatTime': time,
                    'measureNumber': measure_num,
                    'beatsInMeasure': 4
                })
                time += measure_duration
                measure_num += 1
            
            return {
                'numerator': 4,
                'denominator': 4,
                'confidence': 0.7,  # Reasonable confidence for 4/4 assumption
                'beatsPerMeasure': 4,
                'measureDuration': measure_duration,
                'measures': measures,
                'method': 'simple_4_4'
            }
            
        except Exception as e:
            print(f"Warning: Time signature analysis failed: {e}")
            return {
                'numerator': 4,
                'denominator': 4,
                'confidence': 0.5,
                'beatsPerMeasure': 4,
                'measureDuration': 2.0,
                'measures': [],
                'method': 'fallback'
            }
    
    def _analyze_chords_simple(self, audio_data: np.ndarray, duration: float, interval: float) -> Dict:
        """Simple chord analysis using basic templates"""
        try:
            # Compute chromagram
            chroma = librosa.feature.chroma_stft(
                y=audio_data,
                sr=self.sample_rate,
                hop_length=self.hop_length
            )
            
            # Convert to time frames
            time_frames = librosa.frames_to_time(
                np.arange(chroma.shape[1]), 
                sr=self.sample_rate, 
                hop_length=self.hop_length
            )
            
            # Analyze chords at specified intervals
            chords = []
            current_time = 0
            
            while current_time < duration:
                # Find closest time frame
                frame_idx = np.argmin(np.abs(time_frames - current_time))
                
                if frame_idx < chroma.shape[1]:
                    chroma_frame = chroma[:, frame_idx]
                    
                    # Detect chord using simple template matching
                    chord_name, confidence = self._detect_chord_simple(chroma_frame)
                    
                    # Simple downbeat detection (every 2 seconds)
                    is_downbeat = (current_time % 2.0) < 0.1
                    
                    chords.append({
                        'chord': chord_name,
                        'start': current_time,
                        'end': min(current_time + interval, duration),
                        'confidence': confidence,
                        'isDownbeat': is_downbeat,
                        'isPassingChord': not is_downbeat
                    })
                
                current_time += interval
            
            return {
                'analysisInterval': interval,
                'totalChords': len(chords),
                'chords': chords,
                'method': 'simple_template_matching'
            }
            
        except Exception as e:
            print(f"Warning: Chord analysis failed: {e}")
            return {
                'analysisInterval': interval,
                'totalChords': 0,
                'chords': [],
                'method': 'fallback_failed'
            }
    
    def _detect_chord_simple(self, chroma_vector: np.ndarray) -> Tuple[str, float]:
        """Simple chord detection using basic templates"""
        try:
            # Normalize chroma vector
            chroma_norm = chroma_vector / (np.linalg.norm(chroma_vector) + 1e-8)
            
            best_match = 'N'  # No chord
            best_score = 0.0
            
            # Compare with basic chord templates
            for i, template in enumerate(self.chord_templates):
                # Calculate dot product similarity
                similarity = np.dot(chroma_norm, template)
                
                if similarity > best_score:
                    best_score = similarity
                    best_match = self.chord_names[i]
            
            # Threshold for chord detection
            if best_score < 0.4:
                best_match = 'N'
                best_score = 0.0
            
            return best_match, float(best_score)
            
        except Exception as e:
            return 'N', 0.0
    
    def _create_basic_chord_templates(self) -> List[np.ndarray]:
        """Create basic chord templates (major and minor only)"""
        templates = []
        
        # Major chord intervals: root, major third, perfect fifth
        major_intervals = [0, 4, 7]
        # Minor chord intervals: root, minor third, perfect fifth  
        minor_intervals = [0, 3, 7]
        
        for root in range(12):
            # Major chord template
            major_template = np.zeros(12)
            for interval in major_intervals:
                major_template[(root + interval) % 12] = 1.0
            templates.append(major_template / np.linalg.norm(major_template))
            
            # Minor chord template
            minor_template = np.zeros(12)
            for interval in minor_intervals:
                minor_template[(root + interval) % 12] = 1.0
            templates.append(minor_template / np.linalg.norm(minor_template))
        
        return templates
    
    def _create_basic_chord_names(self) -> List[str]:
        """Create basic chord names (major and minor only)"""
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        chord_names = []
        
        for note in note_names:
            chord_names.append(note)      # Major chord
            chord_names.append(note + 'm') # Minor chord
        
        return chord_names

def analyze_audio_file_minimal(audio_url: str, analysis_interval: float = 0.5) -> Dict:
    """
    Minimal audio analysis function
    
    Args:
        audio_url: URL or path to audio file
        analysis_interval: Interval in seconds (0.5s recommended for efficiency)
        
    Returns:
        Complete musical analysis dictionary
    """
    analyzer = MinimalAudioAnalyzer()
    return analyzer.analyze_audio_file(audio_url, analysis_interval)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
        print(f"Testing minimal audio analysis with: {audio_file}")
        
        try:
            result = analyze_audio_file_minimal(audio_file)
            print("\n🎯 Minimal Analysis Results:")
            print(f"Duration: {result['metadata']['duration']:.2f}s")
            print(f"Tempo: {result['tempo']['bpm']:.1f} BPM")
            print(f"Key: {result['key']['root']} {result['key']['mode']}")
            print(f"Chords Detected: {len(result['chords']['chords'])}")
            
            if result['chords']['chords']:
                print("\nFirst 5 chords:")
                for i, chord in enumerate(result['chords']['chords'][:5]):
                    print(f"  {i+1}. {chord['start']:.1f}s: {chord['chord']} (confidence: {chord['confidence']:.2f})")
                    
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
    else:
        print("Usage: python minimal_audio_analyzer.py <audio_file_path>")
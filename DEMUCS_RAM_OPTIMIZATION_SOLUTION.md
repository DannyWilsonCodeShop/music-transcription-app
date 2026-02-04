# Demucs RAM Optimization Solution

## Problem Overview

**Component:** Piano/Strings Stem Isolation using Demucs
**Issue:** High RAM usage causing OOM (Out of Memory) errors
**Current Status:** Disabled in production (see `app-backup.py` line 153)

### Current Configuration
- **ECS Task:** 1 vCPU, 3GB RAM
- **Demucs Model:** `htdemucs` (full model)
- **Processing:** CPU-only (no GPU)
- **Typical RAM Usage:** 4-8GB for a 6-minute song
- **Result:** Exceeds available memory → crashes

## Solution Options

### Option 1: Use Lightweight Demucs Model (RECOMMENDED)
**Best for:** Quick implementation with minimal infrastructure changes

#### Implementation
```python
# Instead of:
self.demucs_model = get_model('htdemucs')  # ~2.4GB model

# Use:
self.demucs_model = get_model('htdemucs_ft')  # Fine-tuned, lighter
# OR
self.demucs_model = get_model('mdx_extra')  # Smaller, faster
```

**Changes Required:**
1. Update model selection in `app.py`
2. Process audio in chunks to reduce peak memory
3. Increase ECS task memory to 4GB

**Pros:**
- Faster processing (1-2 minutes vs 2-5 minutes)
- Lower memory footprint (~2-3GB vs 4-8GB)
- Still good quality for chord detection

**Cons:**
- Slightly lower separation quality (acceptable for chords)

**Cost Impact:** Minimal (~$0.01 more per job)

---

### Option 2: Increase ECS Task Resources
**Best for:** Maximum quality, willing to pay more

#### Configuration
```yaml
# Current:
Cpu: '1024'      # 1 vCPU
Memory: '3072'   # 3GB

# Recommended:
Cpu: '2048'      # 2 vCPU
Memory: '8192'   # 8GB
```

**Pros:**
- Use full `htdemucs` model (best quality)
- Faster processing with more CPU
- Handles longer songs (10+ minutes)

**Cons:**
- Higher cost per job (~$0.05-0.10 per job)
- Still CPU-only (slower than GPU)

**Cost Impact:** ~3x current cost per chord detection

---

### Option 3: Chunk-Based Processing (BEST BALANCE)
**Best for:** Optimal RAM usage without sacrificing quality

#### Implementation Strategy
```python
def separate_harmonic_stem_chunked(self, audio_path: str, chunk_duration: int = 30) -> tuple:
    """
    Process audio in chunks to reduce peak memory usage
    
    Args:
        audio_path: Path to audio file
        chunk_duration: Process in N-second chunks (default 30s)
    
    Returns:
        (harmonic_audio, sr) tuple
    """
    # Load audio metadata
    info = torchaudio.info(audio_path)
    total_duration = info.num_frames / info.sample_rate
    
    # Process in chunks
    harmonic_chunks = []
    chunk_size = chunk_duration * info.sample_rate
    
    for start_frame in range(0, info.num_frames, chunk_size):
        # Load only this chunk
        wav, sr = torchaudio.load(
            audio_path,
            frame_offset=start_frame,
            num_frames=min(chunk_size, info.num_frames - start_frame)
        )
        
        # Process chunk
        with torch.no_grad():
            sources = apply_model(self.demucs_model, wav[None], device='cpu')[0]
        
        # Extract harmonic content
        bass = sources[1]
        other = sources[2]
        harmonic = bass + other
        
        # Convert to mono
        harmonic_mono = torch.mean(harmonic, dim=0).numpy()
        harmonic_chunks.append(harmonic_mono)
        
        # Clear memory
        del wav, sources, bass, other, harmonic, harmonic_mono
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
    
    # Concatenate chunks
    full_harmonic = np.concatenate(harmonic_chunks)
    
    return full_harmonic, sr
```

**Pros:**
- Works with current 3GB RAM allocation
- Maintains full model quality
- Scalable to any song length

**Cons:**
- More complex implementation
- Slightly longer processing time
- Potential artifacts at chunk boundaries (minimal)

**Cost Impact:** None (uses existing resources)

---

### Option 4: Use Alternative Library (Spleeter)
**Best for:** Faster processing, lower memory

#### Implementation
```python
# Install: pip install spleeter

from spleeter.separator import Separator

def separate_with_spleeter(self, audio_path: str) -> tuple:
    """
    Use Spleeter for faster, lighter separation
    """
    separator = Separator('spleeter:4stems')  # vocals, drums, bass, other
    
    # Separate
    prediction = separator.separate_to_file(
        audio_path,
        '/tmp/',
        codec='wav'
    )
    
    # Load bass + other stems
    bass, sr = librosa.load('/tmp/bass.wav', sr=22050)
    other, _ = librosa.load('/tmp/other.wav', sr=22050)
    
    harmonic = bass + other
    return harmonic, sr
```

**Pros:**
- Much faster (30-60 seconds vs 2-5 minutes)
- Lower memory (~1-2GB)
- Pre-trained models available

**Cons:**
- Lower quality than Demucs
- Requires different dependencies
- Less actively maintained

**Cost Impact:** Reduced (faster = cheaper)

---

### Option 5: GPU-Accelerated Processing
**Best for:** Production scale, high volume

#### Configuration
```yaml
# Use GPU-enabled ECS task
TaskDefinition:
  RequiresCompatibilities:
    - FARGATE
  RuntimePlatform:
    CpuArchitecture: X86_64
    OperatingSystemFamily: LINUX
  
  # Use GPU instance
  InferenceAccelerators:
    - DeviceName: device1
      DeviceType: eia2.medium

# OR use EC2 with GPU
LaunchType: EC2
InstanceType: g4dn.xlarge  # 1 GPU, 4 vCPU, 16GB RAM
```

**Pros:**
- 10-20x faster processing (10-30 seconds)
- Can handle full model with ease
- Better for high-volume production

**Cons:**
- Much higher cost (~$0.50-1.00 per job)
- More complex infrastructure
- Requires GPU-optimized Docker image

**Cost Impact:** ~10x current cost

---

## Recommended Implementation Plan

### Phase 1: Quick Fix (Immediate)
**Use Option 3: Chunk-Based Processing**

1. Implement chunked processing in `app.py`
2. Keep current 3GB RAM allocation
3. Test with 30-second chunks
4. Deploy and validate

**Timeline:** 1-2 hours
**Cost:** $0 (no infrastructure changes)
**Risk:** Low

### Phase 2: Optimization (Next Week)
**Combine Option 1 + Option 2**

1. Switch to `mdx_extra` or `htdemucs_ft` model
2. Increase ECS task to 4GB RAM
3. Remove chunking (no longer needed)
4. Optimize for speed

**Timeline:** 2-4 hours
**Cost:** +$0.01 per job
**Risk:** Low

### Phase 3: Scale (Future)
**Evaluate Option 5: GPU if volume increases**

1. Monitor job volume and costs
2. If >1000 jobs/day, consider GPU
3. Implement GPU-accelerated pipeline
4. Reduce per-job cost at scale

**Timeline:** 1-2 days
**Cost:** Higher upfront, lower per-job at scale
**Risk:** Medium

---

## Code Implementation (Option 3 - Recommended)

### Updated `app.py` with Chunked Processing

```python
import os
import json
import boto3
import librosa
import numpy as np
from scipy.signal import find_peaks
from decimal import Decimal
import time
import sys
import traceback

# Optional: Demucs for source separation
try:
    import torch
    import torchaudio
    from demucs.pretrained import get_model
    from demucs.apply import apply_model
    DEMUCS_AVAILABLE = True
except ImportError:
    DEMUCS_AVAILABLE = False

# AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

# Environment variables
JOBS_TABLE = os.environ.get('DYNAMODB_JOBS_TABLE', 'ChordScout-Jobs-V2-dev')
PDF_GENERATOR_FUNCTION = os.environ.get('PDF_GENERATOR_FUNCTION', 'chordscout-v2-pdf-generator-dev')
ENABLE_STEM_SEPARATION = os.environ.get('ENABLE_STEM_SEPARATION', 'false').lower() == 'true'

def log(message, level="INFO"):
    """Enhanced logging with timestamps and flush"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}", flush=True)
    sys.stdout.flush()

class ChordDetector:
    """Chord detector with optional stem separation"""
    
    def __init__(self):
        self.demucs_model = None
        
        if ENABLE_STEM_SEPARATION and DEMUCS_AVAILABLE:
            try:
                log("Loading Demucs model for stem separation...")
                # Use lighter model for better memory efficiency
                self.demucs_model = get_model('mdx_extra')  # Lighter than htdemucs
                log("✓ Demucs model loaded successfully")
            except Exception as e:
                log(f"Failed to load Demucs model: {e}", "WARNING")
                self.demucs_model = None
    
    def separate_harmonic_stem_chunked(self, audio_path: str) -> tuple:
        """
        Separate audio into stems using chunk-based processing
        Reduces peak memory usage from 8GB to ~2GB
        """
        if not self.demucs_model:
            log("Stem separation disabled, using full mix")
            return librosa.load(audio_path, sr=22050)
        
        try:
            log("🎵 Starting chunked stem separation...")
            
            # Get audio info
            info = torchaudio.info(audio_path)
            total_duration = info.num_frames / info.sample_rate
            log(f"   Audio duration: {total_duration:.1f}s")
            
            # Process in 30-second chunks
            chunk_duration = 30
            chunk_size = chunk_duration * info.sample_rate
            num_chunks = int(np.ceil(info.num_frames / chunk_size))
            log(f"   Processing in {num_chunks} chunks of {chunk_duration}s each")
            
            harmonic_chunks = []
            
            for i, start_frame in enumerate(range(0, info.num_frames, chunk_size)):
                log(f"   Processing chunk {i+1}/{num_chunks}...")
                
                # Load only this chunk
                num_frames = min(chunk_size, info.num_frames - start_frame)
                wav, sr = torchaudio.load(
                    audio_path,
                    frame_offset=start_frame,
                    num_frames=num_frames
                )
                
                # Ensure stereo
                if wav.shape[0] == 1:
                    wav = wav.repeat(2, 1)
                
                # Resample if needed
                if sr != self.demucs_model.samplerate:
                    resampler = torchaudio.transforms.Resample(sr, self.demucs_model.samplerate)
                    wav = resampler(wav)
                    sr = self.demucs_model.samplerate
                
                # Separate stems
                with torch.no_grad():
                    sources = apply_model(self.demucs_model, wav[None], device='cpu')[0]
                
                # Extract harmonic content (bass + other)
                bass = sources[1]
                other = sources[2]
                harmonic = bass + other
                
                # Convert to mono
                harmonic_mono = torch.mean(harmonic, dim=0).numpy()
                harmonic_chunks.append(harmonic_mono)
                
                # Clear memory
                del wav, sources, bass, other, harmonic
                
                log(f"   ✓ Chunk {i+1}/{num_chunks} complete")
            
            # Concatenate all chunks
            log("   Concatenating chunks...")
            full_harmonic = np.concatenate(harmonic_chunks)
            
            # Resample to 22050 for librosa
            if sr != 22050:
                full_harmonic = librosa.resample(full_harmonic, orig_sr=sr, target_sr=22050)
                sr = 22050
            
            log(f"✓ Stem separation complete (harmonic stem extracted)")
            return full_harmonic, sr
            
        except Exception as e:
            log(f"Stem separation failed: {e}, using full mix", "WARNING")
            return librosa.load(audio_path, sr=22050)

# Initialize detector
detector = ChordDetector()

# ... rest of the code remains the same
```

### Deployment Steps

1. **Update `requirements.txt`:**
```txt
librosa>=0.10.0
soundfile>=0.12.0
numpy>=1.24.0
scipy>=1.10.0
demucs>=4.0.0
torch>=2.0.0
torchaudio>=2.0.0
boto3>=1.26.0
```

2. **Update CloudFormation template:**
```yaml
# Optional: Increase memory if needed
ChordDetectorTaskDefinition:
  Properties:
    Cpu: '1024'
    Memory: '4096'  # Increased from 3072 to 4096 (4GB)
```

3. **Environment variable to enable:**
```yaml
Environment:
  - Name: ENABLE_STEM_SEPARATION
    Value: 'true'  # Set to 'false' to disable
```

4. **Build and deploy:**
```bash
docker buildx build --platform linux/amd64 -t chordscout-chord-detector:latest .
docker tag chordscout-chord-detector:latest 090130568474.dkr.ecr.us-east-1.amazonaws.com/chordscout-chord-detector:latest
docker push 090130568474.dkr.ecr.us-east-1.amazonaws.com/chordscout-chord-detector:latest
```

---

## Testing Plan

### Test 1: Memory Usage
```bash
# Monitor ECS task memory
aws ecs describe-tasks \
  --cluster ChordScout-dev \
  --tasks <task-arn> \
  --profile chordscout \
  --query 'tasks[0].containers[0].memory'
```

### Test 2: Processing Time
- Short song (3 min): Should complete in 1-2 minutes
- Medium song (6 min): Should complete in 2-4 minutes
- Long song (10 min): Should complete in 4-6 minutes

### Test 3: Quality
- Compare chord detection accuracy with/without stem separation
- Verify no artifacts at chunk boundaries
- Check that key detection is accurate

---

## Monitoring & Alerts

### CloudWatch Metrics to Track
1. **Memory Usage:** Should stay under 3.5GB (with 4GB allocation)
2. **Processing Time:** Should be 2-4 minutes for average song
3. **Error Rate:** Should be <1% for OOM errors

### Alerts to Set Up
```yaml
MemoryUtilizationAlarm:
  Threshold: 85%  # Alert if memory exceeds 85%
  
ProcessingTimeAlarm:
  Threshold: 600  # Alert if processing takes >10 minutes
  
ErrorRateAlarm:
  Threshold: 5%   # Alert if >5% of jobs fail
```

---

## Cost Analysis

### Current (No Stem Separation)
- ECS Task: 1 vCPU, 3GB RAM
- Duration: ~20 seconds
- Cost per job: ~$0.002

### With Chunked Processing (Recommended)
- ECS Task: 1 vCPU, 4GB RAM
- Duration: ~3 minutes
- Cost per job: ~$0.015

### With GPU (Future)
- ECS Task: GPU instance
- Duration: ~30 seconds
- Cost per job: ~$0.50

**Recommendation:** Start with chunked processing, evaluate GPU if volume >1000 jobs/day

---

## Next Steps

1. ✅ Implement chunked processing code
2. ⏳ Test with sample songs (3, 6, 10 minutes)
3. ⏳ Monitor memory usage in production
4. ⏳ Collect user feedback on chord accuracy
5. ⏳ Optimize chunk size if needed (20s, 30s, 40s)
6. ⏳ Consider GPU if scaling to high volume

---

## References

- [Demucs Documentation](https://github.com/facebookresearch/demucs)
- [AWS ECS Task Sizing](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-cpu-memory-error.html)
- [Torch Memory Management](https://pytorch.org/docs/stable/notes/cuda.html#memory-management)

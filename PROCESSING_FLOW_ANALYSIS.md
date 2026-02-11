# Processing Flow Analysis

## Current Flow (Batch Processing)

### Step 1: Upload (Frontend → S3)
**Time**: ~1-2 seconds

```
User selects file
  ↓
Frontend requests presigned URL from Lambda
  ↓
Frontend uploads file directly to S3
  ↓
Upload complete, job status = "UPLOADING"
```

**Progress**: 0% → 5%

---

### Step 2: S3 Event Trigger
**Time**: ~1-2 seconds

```
S3 detects new file
  ↓
S3 triggers Processing Lambda
  ↓
Processing Lambda updates job status to "PROCESSING"
  ↓
Processing Lambda launches ECS task
```

**Progress**: 5% → 10%

---

### Step 3: ECS Task Startup
**Time**: ~10-30 seconds (Docker image pull + container start)

```
ECS pulls Docker image (if not cached)
  ↓
Container starts
  ↓
Python environment initializes
  ↓
Libraries load (librosa, numpy, scipy, etc.)
```

**Progress**: 10% (stuck here during startup)

---

### Step 4: Audio Processing (ALL AT ONCE)
**Time**: ~30-60 seconds for 3-minute song

This is where ALL the work happens in one batch:

#### 4a. Audio Loading (~5-10s)
```
Download file from S3
  ↓
Load audio with librosa
  ↓
Resample to 22050 Hz
  ↓
Convert to mono
```

#### 4b. Tempo Detection (~2-3s)
```
Detect beats
  ↓
Calculate tempo
  ↓
Detect time signature
```

#### 4c. HPSS Separation (~3-5s)
```
Separate harmonic from percussive
  ↓
Calculate energy percentages
```

#### 4d. Chromagram Computation (~5-8s)
```
Compute full spectrum chromagram
  ↓
Compute bass chromagram (C2-C4)
  ↓
Apply median filtering
```

#### 4e. Chord Detection (~10-15s)
```
Extract downbeats (every 4th beat)
  ↓
For each downbeat:
  - Extract chromagram slice
  - Extract bass chromagram slice
  - Weight bass 2:1
  - Match against 84 chord templates
  - Select best match
  ↓
Consolidate consecutive identical chords
  ↓
Filter short chords (<0.5s)
```

#### 4f. Key Detection (~1-2s)
```
Count chord frequency
  ↓
Find most common chord
  ↓
Determine major/minor
  ↓
Calculate relative major (if minor)
```

#### 4g. Pattern Analysis (~2-3s)
```
Find repeating chord patterns
  ↓
Calculate Nashville numbers
  ↓
Identify pattern positions
```

#### 4h. Structure Detection (~3-5s)
```
Try MSAF audio segmentation
  ↓
Fall back to pattern-based structure
  ↓
Label sections (Verse, Chorus, etc.)
```

#### 4i. Data Formatting (~1-2s)
```
Convert floats to Decimals for DynamoDB
  ↓
Format chord data
  ↓
Format pattern analysis
  ↓
Format song structure
```

#### 4j. Database Update (~1-2s)
```
Update DynamoDB with all results
  ↓
Set status to "COMPLETED"
  ↓
Set progress to 100%
```

**Progress**: 10% → 100% (happens all at once at the end)

---

### Step 5: Frontend Polling
**Time**: Continuous (every 2 seconds)

```
Frontend polls /jobs/{jobId} every 2 seconds
  ↓
Receives status update
  ↓
Updates UI
```

---

## Why It Feels Slow

### 1. No Incremental Updates
- Progress stays at 10% for 30-60 seconds
- Then jumps to 100%
- User sees no feedback during processing

### 2. All Processing in One Function
- Can't update progress mid-processing
- No way to show "Detecting chords..." vs "Analyzing patterns..."
- Everything happens in the ECS task

### 3. ECS Cold Start
- Docker image pull: ~10-20s (if not cached)
- Container startup: ~5-10s
- Library loading: ~3-5s
- Total: ~20-30s before processing even starts

---

## Current Progress Updates

```
0%   - Job created
5%   - File uploaded to S3
10%  - ECS task launched
...  - (stuck here for 30-60 seconds)
100% - Everything complete
```

---

## What Could Be Improved

### Option 1: Incremental Progress Updates
Update DynamoDB progress during processing:

```python
# After tempo detection
update_progress(job_id, 20, "Detecting tempo...")

# After chromagram
update_progress(job_id, 40, "Computing chromagram...")

# After chord detection
update_progress(job_id, 70, "Detecting chords...")

# After key detection
update_progress(job_id, 85, "Analyzing key...")

# After patterns
update_progress(job_id, 95, "Finding patterns...")

# Complete
update_progress(job_id, 100, "Complete!")
```

**Pros**: 
- User sees progress
- Knows what's happening
- Feels faster

**Cons**:
- More DynamoDB writes
- Slightly slower overall
- More complex code

---

### Option 2: Streaming Results
Send results as they're computed:

```
Tempo detected → Update DB → Frontend shows tempo
Chords detected → Update DB → Frontend shows chords
Key detected → Update DB → Frontend shows key
Patterns found → Update DB → Frontend shows patterns
```

**Pros**:
- Immediate feedback
- Progressive enhancement
- Feels much faster

**Cons**:
- Complex state management
- Multiple DB updates
- Frontend needs to handle partial data

---

### Option 3: Pre-warm ECS Tasks
Keep containers warm to avoid cold starts:

```
Keep 1-2 ECS tasks always running
  ↓
New job uses warm task
  ↓
No Docker pull or startup delay
```

**Pros**:
- Eliminates 20-30s cold start
- Faster processing

**Cons**:
- Costs money (always-on containers)
- ~$10-20/month for 1 task

---

### Option 4: Optimize Processing
Make the actual processing faster:

```
- Use smaller hop length (less accurate but faster)
- Skip MSAF (use pattern-based only)
- Reduce chord templates (84 → 36)
- Skip pattern analysis
- Skip structure detection
```

**Pros**:
- Faster processing
- Lower costs

**Cons**:
- Less accurate
- Fewer features
- Not recommended

---

## Recommended Approach

### Quick Win: Add Progress Updates
Add 5-6 progress updates during processing:

```python
# Current: 10% → 100% (one jump)
# New:     10% → 20% → 40% → 70% → 85% → 95% → 100%
```

**Implementation**: ~30 minutes
**Impact**: High (user sees progress)
**Cost**: Minimal (few extra DB writes)

---

### Medium Term: Pre-warm Containers
Keep 1 ECS task always running:

```yaml
Service:
  DesiredCount: 1  # Keep 1 task always running
  MinimumHealthyPercent: 0
  MaximumPercent: 200
```

**Implementation**: ~1 hour
**Impact**: High (eliminates cold start)
**Cost**: ~$15/month

---

### Long Term: Streaming Results
Send results incrementally:

```
Step 1: Tempo + Time Signature → Show immediately
Step 2: Chords → Show as detected
Step 3: Key → Show when found
Step 4: Patterns → Show when analyzed
Step 5: Structure → Show when complete
```

**Implementation**: ~4-6 hours
**Impact**: Very High (feels instant)
**Cost**: More complex code

---

## Current Timing Breakdown

For a 3-minute song:

```
Upload:           2s   (5%)
S3 → Lambda:      1s   (5%)
ECS Cold Start:  25s   (stuck at 10%)
Audio Loading:   10s   (still at 10%)
Processing:      35s   (still at 10%)
DB Update:        2s   (jumps to 100%)
─────────────────────
Total:           75s
```

**User Experience**: 
- Sees 5% immediately
- Sees 10% after 3 seconds
- Waits 70 seconds at 10%
- Suddenly sees 100%

---

## Ideal Timing (with improvements)

```
Upload:           2s   (0% → 5%)
S3 → Lambda:      1s   (5% → 10%)
ECS Warm Start:   2s   (10% → 15%)
Audio Loading:   10s   (15% → 25%)
Tempo:            3s   (25% → 35%)
Chromagram:       8s   (35% → 50%)
Chords:          15s   (50% → 75%)
Key:              2s   (75% → 80%)
Patterns:         3s   (80% → 90%)
Structure:        5s   (90% → 95%)
DB Update:        2s   (95% → 100%)
─────────────────────
Total:           53s
```

**User Experience**:
- Smooth progress bar
- Status messages
- Feels much faster

---

## Next Steps

Would you like me to:

1. **Add progress updates** (quick, high impact)
2. **Pre-warm ECS containers** (medium effort, eliminates cold start)
3. **Both** (best user experience)
4. **Keep as-is** (works but feels slow)

Let me know and I can implement whichever you prefer!

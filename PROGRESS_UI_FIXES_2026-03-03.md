# Progress UI Fixes - March 3, 2026

## Issues Fixed

### 1. Progress Parsing Bug
**Problem**: Backend was returning `progress` as a string (`'10'`, `'40'`, `'100'`) but frontend expected a number, causing UI to disappear.

**Fix**: Convert progress to number in `transcriptionService.ts`:
```typescript
progress: parseInt(data.progress) || 0,  // Convert string to number
```

### 2. Results Not Displaying for Bass Transcription
**Problem**: Results section required `job.chordsData` to exist, but bass transcription stores data in `job.bassData`.

**Fix**: Updated condition to show results for either type:
```typescript
{job?.status === 'COMPLETED' && (job.chordsData || job.bassData) && (
```

Also made song metadata and lyrics sections conditional on `job.chordsData` existing.

### 3. Unclear Container Warmup Messaging
**Problem**: Initial 10% progress said "Starting bass line analysis..." but was actually just spinning up the container (takes ~3-6 minutes).

**Fix**: Updated message to be more accurate:
```python
':statusMessage': f'Warming up analysis container (this takes a few minutes)...',
```

## Timeline Breakdown

For a typical bass transcription job:

- **0-3 minutes (10%)**: "Warming up analysis container..." 
  - ECS spinning up Fargate task
  - Pulling 4.8GB Docker image
  - Loading TensorFlow and ML models into memory
  
- **3-4 minutes (40%)**: "Extracting bass stem..."
  - Demucs separating bass track from mix
  
- **4-5 minutes (50%)**: "Detecting tempo and beats..."
  - Analyzing rhythm and timing
  
- **5-6 minutes (70%)**: "Transcribing bass notes..."
  - basic-pitch transcribing notes to MIDI
  
- **6-7 minutes (90%)**: "Generating NNS chart..."
  - Creating Nashville Number System chart
  - Generating PDF
  
- **7 minutes (100%)**: "Complete! Your bass NNS chart is ready."
  - Results displayed with PDF download link

## Optimization Opportunities

The 3-6 minute container warmup is the biggest bottleneck. Options to improve:

1. **Keep containers warm**: Use ECS service with minimum 1 task always running (costs ~$20/month)
2. **Smaller Docker image**: Current image is 4.8GB, could optimize layers
3. **Lazy load models**: Load TensorFlow/models only when needed
4. **Use Lambda with EFS**: Mount models on EFS, faster cold starts
5. **Pre-warmed pool**: Keep 1-2 containers in a pool, assign to jobs

## Files Changed

- `src/services/transcriptionService.ts` - Fixed progress parsing, added bassData support
- `src/App.tsx` - Fixed results display condition, made metadata conditional
- `simple-pipeline/process-audio-lambda.py` - Updated warmup messaging

## Testing

After Amplify deploys:
1. Hard refresh browser (Cmd+Shift+R)
2. Upload a bass transcription test file
3. Verify progress UI stays visible throughout
4. Verify results display when complete
5. Verify PDF download link works

## Commits

- `80ebe74` - Fix progress parsing: convert string to number and add bassData support
- `22b4f83` - Fix results display: show results for bass transcription (bassData) not just chord detection
- (pending) - Update container warmup messaging

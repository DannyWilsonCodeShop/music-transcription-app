# Progress UI Fix - March 3, 2026

## Issue
Progress tracker UI was disappearing during long-running bass transcription jobs, even though the backend was processing correctly and polling was working.

## Root Cause
The visibility condition for the progress UI had two separate blocks:
1. Main progress UI: Required `job && job.status !== 'COMPLETED' && job.status !== 'FAILED' && uploadProgress === 100`
2. Fallback UI: Required `jobId && !job && uploadProgress === 100`

The problem was that these conditions created a gap where neither would render:
- If polling started but `job` was null (not loaded yet), the main UI wouldn't show
- If polling encountered errors and `job` remained null, the fallback UI would show but then disappear
- The two separate blocks caused flickering and inconsistent behavior

## Solution

### 1. Consolidated Progress UI Logic
Merged the two separate UI blocks into a single, simpler condition:
```tsx
{jobId && uploadProgress === 100 && (!job || (job.status !== 'COMPLETED' && job.status !== 'FAILED')) && (
```

This ensures the progress UI stays visible as long as:
- We have a `jobId` (job was created)
- Upload is complete (`uploadProgress === 100`)
- Job is not finished yet (either `job` is null OR status is not COMPLETED/FAILED)

### 2. Enhanced Logging
Added comprehensive console logging to track the entire flow:

**App.tsx polling:**
- Log when polling starts/stops
- Log each polling attempt with elapsed time
- Log when job status is received and updated
- Log when job completes or fails

**transcriptionService.ts:**
- Log every API call with full URL
- Log response status codes
- Log parsed job data
- Log network errors

This will help diagnose any future issues by showing exactly what's happening at each step.

### 3. Improved Fallback Display
When `job` data hasn't loaded yet, the UI now shows:
- "Initializing processing..." message
- Job ID for reference
- Timer continues to run
- Progress bar at 0%

## Testing Instructions

1. **Hard refresh your browser** (Cmd+Shift+R on Mac, Ctrl+Shift+R on Windows)
   - This is critical to get the latest deployed code
   - Regular refresh may use cached JavaScript

2. Upload a test file (preferably a longer one like "Leave the Door Open")

3. Watch the browser console for detailed logs:
   - Should see "Starting polling for jobId: ..."
   - Should see "Polling attempt for ... (elapsed: Xs)"
   - Should see "[transcriptionService] getJobStatus called..."
   - Should see job status updates with progress percentages

4. Verify the progress UI:
   - Stays visible throughout the entire process
   - Shows "Initializing processing..." if job data hasn't loaded
   - Updates with status messages and progress as job runs
   - Timer continues counting up
   - Never disappears until job completes or fails

## Expected Console Output

```
Requesting upload URL for: 02 Leave the Door Open.m4a audio/x-m4a
Upload URL response: Object
Uploading file to S3...
Upload complete!
Starting chord detection...
Starting polling for jobId: abc123...
Polling attempt for abc123 (elapsed: 0s)
[transcriptionService] getJobStatus called for jobId: abc123
[transcriptionService] Fetching: https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com/jobs/abc123
[transcriptionService] Response status: 200
[transcriptionService] Job data received: {jobId: "abc123", status: "PROCESSING", progress: 10, ...}
Poll result: {hasStatus: true, status: "PROCESSING", progress: 10, ...}
Job status updated: PROCESSING 10 Analyzing audio...
Polling attempt for abc123 (elapsed: 2s)
...
```

## Files Changed
- `src/App.tsx` - Consolidated progress UI visibility logic, added logging
- `src/services/transcriptionService.ts` - Added comprehensive logging

## Deployment
- Committed: `835658b`
- Pushed to: `origin/dev`
- Amplify will auto-deploy (takes ~2-3 minutes)

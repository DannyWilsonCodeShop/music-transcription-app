# Debugging: 60% Stuck Issue - RESOLVED

## Issue Summary
Jobs were getting stuck at 60% progress with status "TRANSCRIBED" and never completing.

## Root Cause Analysis

### Investigation Steps
1. Checked Step Functions execution history
2. Reviewed ECS CloudWatch logs
3. Identified the actual failure point

### Root Cause Found
The chord detection ECS task **completed successfully** but **failed when saving to DynamoDB** with this error:

```
TypeError: Float types are not supported. Use Decimal types instead.
```

**What happened:**
1. ✅ YouTube audio download completed
2. ✅ Lyrics transcription completed (60% progress)
3. ✅ ECS chord detection task started
4. ✅ Chord detection completed (258 chords detected in 18.5 seconds)
5. ❌ **FAILED** when trying to save chord data to DynamoDB
6. ❌ Step Functions workflow stuck waiting for ECS task (using `runTask.sync`)

### Technical Details

**The Problem:**
- Chord detection returns float values (timestamps, confidence scores, durations)
- DynamoDB doesn't support Python `float` types
- DynamoDB requires `Decimal` types for numeric values
- The code was trying to save raw float values directly

**Error Location:**
```python
# This failed:
table.update_item(
    Key={'jobId': job_id},
    UpdateExpression='SET chordsData = :chords, ...',
    ExpressionAttributeValues={
        ':chords': chords_data,  # Contains floats!
        ...
    }
)
```

## Solution Implemented

### Code Changes
Added a recursive conversion function to convert all float values to Decimal:

```python
from decimal import Decimal

def convert_floats_to_decimal(obj):
    """Recursively convert all float values to Decimal for DynamoDB"""
    if isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_floats_to_decimal(value) for key, value in obj.items()}
    elif isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return Decimal('0')
        return Decimal(str(obj))
    elif isinstance(obj, (np.floating, np.float32, np.float64)):
        val = float(obj)
        if np.isnan(val) or np.isinf(val):
            return Decimal('0')
        return Decimal(str(val))
    elif isinstance(obj, (np.integer, np.int32, np.int64)):
        return int(obj)
    else:
        return obj
```

Updated the `update_job_with_chords` function:

```python
def update_job_with_chords(job_id, chords_data):
    log(f"Updating job with {len(chords_data['chords'])} chords")
    table = dynamodb.Table(JOBS_TABLE)
    
    # Convert all floats to Decimal for DynamoDB compatibility
    log("Converting float values to Decimal for DynamoDB...")
    chords_data_decimal = convert_floats_to_decimal(chords_data)
    log(f"✓ Converted {len(chords_data['chords'])} chords to DynamoDB format")
    
    table.update_item(
        Key={'jobId': job_id},
        UpdateExpression='SET chordsData = :chords, #status = :status, progress = :progress, updatedAt = :updated',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={
            ':chords': chords_data_decimal,  # Now uses Decimal!
            ':status': 'CHORDS_DETECTED',
            ':progress': 80,
            ':updated': time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
        }
    )
```

### Deployment
1. Updated `backend/functions-v2/chord-detector-ecs/app.py`
2. Rebuilt Docker image: `docker buildx build --platform linux/amd64`
3. Pushed to ECR: `090130568474.dkr.ecr.us-east-1.amazonaws.com/chordscout-chord-detector:latest`
4. New digest: `sha256:efee88d2206d863c150a0f2974b0b539a92dd59d3fcdd5cd427f974a23fd6a12`

## Expected Behavior After Fix

### Workflow Progress
1. **0%** - Job created
2. **20%** - YouTube audio downloaded
3. **60%** - Lyrics transcribed
4. **70%** - Chord detection started (ECS task)
5. **80%** - Chord detection completed, data saved to DynamoDB ✅ (FIXED)
6. **90%** - PDF generation started
7. **100%** - PDF generated and uploaded

### Next Test
The next job submission will use the fixed Docker image and should:
- Complete chord detection successfully
- Save chord data to DynamoDB without errors
- Progress from 60% → 70% → 80% → 90% → 100%
- Generate the final PDF

## Files Modified
- `backend/functions-v2/chord-detector-ecs/app.py`
  - Added `from decimal import Decimal` import
  - Added `convert_floats_to_decimal()` function
  - Updated `update_job_with_chords()` to convert data before saving

## Lessons Learned
1. **DynamoDB Type Requirements**: Always convert Python floats to Decimal when saving to DynamoDB
2. **Enhanced Logging**: The comprehensive logging we added helped identify the exact failure point
3. **Step Functions Sync Tasks**: When using `runTask.sync`, Step Functions waits for the task to complete - if the task fails, the workflow gets stuck
4. **Error Handling**: Need better error propagation from ECS tasks back to Step Functions

## Status
✅ **FIXED** - Docker image rebuilt and deployed with Decimal conversion
🔄 **READY FOR TESTING** - Next job submission will validate the fix

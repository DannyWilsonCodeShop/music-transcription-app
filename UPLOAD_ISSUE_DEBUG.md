# Upload Issue Debugging

**Date**: February 10, 2026  
**Issue**: Upload gets stuck at 5%

## Changes Made

### 1. UI Improvements
- ✅ Reduced upload box padding from 48px to 32px (more compact)
- ✅ Reduced icon sizes from 64px to 48px
- ✅ Reduced font sizes slightly for better proportions

### 2. Upload Fix
- ✅ Removed `Content-Type` header from S3 PUT request
  - Presigned URLs already include content-type in query parameters
  - Adding it again can cause conflicts
- ✅ Added fallback to `audio/mpeg` if `file.type` is empty
- ✅ Added extensive console logging for debugging

### 3. Error Handling
- ✅ Better error messages from API responses
- ✅ Log error response data for debugging
- ✅ Log each step of the upload process

## How to Debug

### Option 1: Browser Console
1. Open browser DevTools (F12)
2. Go to Console tab
3. Try uploading a file
4. Look for these logs:
   ```
   Requesting upload URL for: filename.mp3 audio/mpeg
   Upload URL response: {jobId: "...", uploadUrl: "..."}
   Uploading file to S3...
   Upload progress: 5%
   Upload progress: 10%
   ...
   Upload complete!
   ```

### Option 2: Test Script
Run the test script to simulate the frontend flow:
```bash
./test-frontend-upload.sh
```

This will:
1. Request an upload URL
2. Upload a test file
3. Poll for job status
4. Show results

### Option 3: Network Tab
1. Open browser DevTools (F12)
2. Go to Network tab
3. Try uploading a file
4. Look for:
   - POST to `/upload` - Should return 200 with jobId and uploadUrl
   - PUT to S3 - Should return 200 (no body)
   - GET to `/jobs/{jobId}` - Should return job status

## Common Issues

### Issue 1: CORS Error
**Symptom**: Console shows CORS error  
**Solution**: API Gateway CORS is configured, but check:
- Browser is not blocking requests
- No browser extensions interfering
- Try in incognito mode

### Issue 2: Presigned URL Expired
**Symptom**: S3 PUT returns 403  
**Solution**: Presigned URLs expire after 15 minutes
- Upload immediately after getting URL
- Don't refresh page with URL in state

### Issue 3: File Type Not Accepted
**Symptom**: Upload fails with 400 error  
**Solution**: 
- Check file.type is set correctly
- Fallback to `audio/mpeg` is now in place
- Supported types: audio/mpeg, audio/wav, audio/x-m4a, audio/flac, audio/ogg

### Issue 4: File Too Large
**Symptom**: Upload progress stops  
**Solution**: 
- Max file size is 50MB
- Check file size before upload
- Consider compressing large files

### Issue 5: S3 Upload Fails
**Symptom**: PUT to S3 returns error  
**Solution**:
- Don't add extra headers (presigned URL handles it)
- Use binary upload (axios handles this)
- Check network connection

## What to Check in Console

Look for these specific errors:

### 1. Request Upload URL Failed
```
Upload failed: Error: Request failed with status code 400
Error response: {error: "Invalid filename"}
```
**Fix**: Check filename is valid (no special characters)

### 2. S3 Upload Failed
```
Upload failed: Error: Request failed with status code 403
Error response: undefined
```
**Fix**: Presigned URL expired or CORS issue

### 3. Network Error
```
Upload failed: Error: Network Error
Error response: undefined
```
**Fix**: Check internet connection or API endpoint

## Testing Locally

1. Start dev server:
   ```bash
   npm run dev
   ```

2. Open http://localhost:5173

3. Open browser console (F12)

4. Try uploading a small MP3 file (< 5MB)

5. Watch console logs for errors

## API Endpoints

**Upload Endpoint**:
```
POST https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com/upload
Body: {filename, contentType, userId}
Response: {jobId, uploadUrl, s3Key}
```

**Status Endpoint**:
```
GET https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com/jobs/{jobId}
Response: {jobId, status, progress, chordsData, ...}
```

## Next Steps

1. Test in browser with console open
2. Check for specific error messages
3. If stuck at 5%, check:
   - Network tab for failed requests
   - Console for error logs
   - S3 PUT request status code
4. Share console logs if issue persists

## Expected Flow

```
1. User selects file
   → File object created with name, size, type

2. Click "Upload & Process"
   → POST /upload with filename, contentType
   → Response: {jobId, uploadUrl}

3. Upload to S3
   → PUT uploadUrl with file binary
   → Progress: 0% → 100%
   → Response: 200 OK (empty body)

4. Poll status
   → GET /jobs/{jobId} every 2 seconds
   → Status: PENDING → PROCESSING → COMPLETED
   → Progress: 0% → 100%

5. Show results
   → Display chordsData
   → Show PDF download button
```

## Files Modified

- `src/App.tsx` - Reduced padding, removed Content-Type header, added logging
- `test-frontend-upload.sh` - Test script to simulate upload flow

## Commit

```
git commit -m "Fix: Reduce upload box size and improve upload debugging"
git push origin dev
```

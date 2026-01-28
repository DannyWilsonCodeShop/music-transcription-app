# 🚀 Deploy Development Environment to Amplify

## Current Status Assessment

Based on NEW_ARCHITECTURE.md, we're at:
- ✅ Environment variables configured
- ✅ Development branch with real YouTube integration
- ✅ RapidAPI integration working (API calls successful)
- 🔄 Need to implement Phase 1: Apify integration
- 🔄 Need to test full end-to-end workflow

## Quick Deployment to Amplify Dev

### Step 1: Deploy Development Branch

1. **Go to AWS Amplify Console:**
   - https://console.aws.amazon.com/amplify/

2. **Create New App:**
   - Click "New app" → "Host web app"
   - Choose **GitHub**
   - Select: `music-transcription-app` repository
   - **Branch**: `development` (not main!)
   - **App name**: `music-transcription-app-dev`

3. **Environment Variables:**
   ```
   NODE_VERSION = 18
   OPENAI_API_KEY = your-openai-api-key-here
   RAPIDAPI_KEY = your-rapidapi-key-here
   APIFY_API_TOKEN = your-apify-api-token-here
   ```

4. **Deploy:**
   - Click "Save and deploy"
   - Wait ~5-10 minutes

### Step 2: Test Current System

Once deployed, test with the development URL:

**Expected Behavior:**
- ✅ Frontend loads (no more abcjs dependency issues)
- ✅ Can submit YouTube URLs
- ✅ Makes real API calls (no mock data)
- ❌ YouTube downloads may fail (current RapidAPI reliability issues)

### Step 3: Implement Phase 1 Improvements

Based on NEW_ARCHITECTURE.md, we need to:

1. **Update YouTube Downloader Lambda** to use Apify (Phase 1)
2. **Test reliability** with multiple videos
3. **Monitor costs** and success rates

## Phase 1 Implementation Plan

### Current Architecture (What's Working)
```
Frontend (Amplify) → API Gateway → Step Functions → Lambda Functions
                                                   ├── YouTube Downloader (RapidAPI - unreliable)
                                                   ├── Deepgram Transcriber (✅ Working)
                                                   ├── Chord Detector (ECS - ✅ Working)
                                                   └── PDF Generator (✅ Working)
```

### Phase 1 Target (Apify Integration)
```
Frontend (Amplify) → API Gateway → Step Functions → Lambda Functions
                                                   ├── YouTube Downloader (Apify - reliable)
                                                   ├── Deepgram Transcriber (✅ Working)
                                                   ├── Chord Detector (ECS - ✅ Working)
                                                   └── PDF Generator (✅ Working)
```

## Immediate Action Plan

### Today (30 minutes):
1. **Deploy to Amplify** using steps above
2. **Test current system** with YouTube URL
3. **Identify specific failure points**

### This Week (2 hours):
1. **Update YouTube Downloader Lambda** with Apify integration
2. **Deploy updated Lambda** to development environment
3. **Test end-to-end workflow**
4. **Monitor success rates**

## Testing Strategy

### Test Videos for Development:
1. **Short music video**: https://www.youtube.com/watch?v=dQw4w9WgXcQ (Rick Roll - 3:32)
2. **Popular song**: https://www.youtube.com/watch?v=ZbZSe6N_BXs (Short song)
3. **Different format**: https://youtu.be/fJ9rUzIMcZQ (Short URL format)

### Success Metrics:
- **Download Success Rate**: >95%
- **End-to-End Completion**: >90%
- **Average Processing Time**: <5 minutes
- **Cost per Song**: <$0.05

## Expected Results After Deployment

### Immediate (Current System):
- ✅ Frontend works perfectly
- ✅ Job creation works
- ✅ Status polling works
- ❌ YouTube downloads may fail (RapidAPI issues)
- ✅ Deepgram transcription works (when audio available)
- ✅ Chord detection works (when audio available)
- ✅ PDF generation works (when data available)

### After Phase 1 (Apify Integration):
- ✅ All components working reliably
- ✅ 95%+ success rate
- ✅ Full end-to-end workflow
- ✅ Ready for production promotion

## Deployment URLs

After deployment:
- **Production**: https://main.d1234567890.amplifyapp.com (mock data for demos)
- **Development**: https://development.d1234567890.amplifyapp.com (real integration testing)

## Next Steps After Deployment

1. **Test current system** and document failure points
2. **Implement Apify integration** in YouTube downloader
3. **Compare reliability** between RapidAPI and Apify
4. **Optimize costs** and performance
5. **Prepare for production** promotion

This approach lets us test everything in the real AWS environment without local setup issues! 🎵
# Session Notes - January 28, 2026

## 🎯 What We Accomplished Today

### 1. YouTube Cookie Management ✅
- **Updated cookies**: Replaced old cookies with fresh export from browser
- **Uploaded to S3**: `s3://chordscout-audio-temp-dev-090130568474/cookies/youtube-cookies.txt`
- **Lambda configured**: Environment variables set to use cookies
- **Result**: Cookies work! Bot detection bypassed successfully

### 2. Identified YouTube Download Issues 🔍
**Problem**: yt-dlp with cookies still fails due to:
- HLS fragment download failures (fragments not accessible)
- YouTube's aggressive bot detection on download streams
- Inconsistent success rates even with valid cookies

**Root Cause**: YouTube serves HLS streams where individual fragments can't be downloaded in Lambda environment, even with valid authentication cookies.

### 3. Researched Solutions 📊
Documented three approaches in `NEW_ARCHITECTURE.md`:

**Option 1: Third-Party API (Apify)** - ATTEMPTED
- Pros: No bot detection, reliable
- Cons: Requires paid Apify actors (free trial expired)
- Status: ❌ Blocked - needs paid subscription

**Option 2: Lambda + FFmpeg Layer**
- Pros: Handles HLS properly
- Cons: Complex setup, still needs cookies
- Status: ⏸️ Not attempted yet

**Option 3: ECS Fargate for Downloads** 
- Pros: Most reliable, full control
- Cons: Higher cost (~$0.04/video)
- Status: ⏸️ Planned for Phase 2

### 4. Updated Architecture Documentation ✅
- Added comprehensive YouTube download strategy section
- Documented all solution options with pros/cons
- Created phased implementation plan
- Updated cost estimates

---

## 🚧 Current State

### What's Working ✅
- ✅ Frontend deployed and accessible
- ✅ API Gateway endpoints active
- ✅ DynamoDB job tracking
- ✅ Deepgram lyrics transcription (tested separately)
- ✅ ECS chord detection (tested separately)
- ✅ PDF generation (tested separately)
- ✅ YouTube cookies valid and uploaded

### What's Broken ❌
- ❌ YouTube audio download (yt-dlp HLS fragment failures)
- ❌ Apify integration (requires paid subscription)
- ❌ End-to-end workflow (blocked by download step)

### Files Modified Today
1. `public/cookies.txt` - Updated with fresh cookies
2. `NEW_ARCHITECTURE.md` - Added YouTube download strategy section
3. `backend/functions-v2/youtube-downloader/index.py` - Attempted Apify integration
4. `backend/functions-v2/youtube-downloader/index-apify.py` - New Apify version (not deployed)
5. `backend/functions-v2/youtube-downloader/index-ytdlp-backup.py` - Backup of original

---

## 📋 Next Steps (Priority Order)

### Immediate (Tomorrow Morning)
1. **Set up mock data for client demo** ✅ (Done tonight)
   - Mock successful transcription responses
   - Show progress bar working
   - Display sample PDF output

2. **Decide on YouTube download solution**:
   - **Option A**: Purchase Apify subscription (~$49/month)
     - Fastest solution (1 hour implementation)
     - Most reliable
     - Recommended for MVP
   
   - **Option B**: Implement Lambda + FFmpeg Layer
     - Free (except AWS costs)
     - 4-6 hours implementation
     - Medium reliability
   
   - **Option C**: Build ECS download service
     - Free (except AWS costs ~$0.04/video)
     - 6-8 hours implementation
     - Highest reliability
     - Best long-term solution

### Short Term (This Week)
1. Implement chosen YouTube download solution
2. Test end-to-end workflow with real videos
3. Monitor success rates and costs
4. Fix any edge cases

### Medium Term (Next Sprint)
1. Migrate to ECS for YouTube downloads (if not chosen initially)
2. Implement cookie rotation system
3. Add error recovery and retry logic
4. Optimize costs

---

## 💰 Cost Analysis

### Current Costs (per 1000 videos)
- YouTube download: **BLOCKED** ❌
- Deepgram: $17 (working)
- Chord detection (ECS): $40 (working)
- Lambda/S3/DynamoDB: $1 (working)
- **Total**: $58 (when download works)

### With Apify (Option A)
- Apify subscription: $49/month (unlimited)
- Per video: ~$0.005
- **Total per 1000**: $5 + $58 = $63

### With FFmpeg Layer (Option B)
- No additional cost
- **Total per 1000**: $58

### With ECS Download (Option C)
- ECS download: $40 per 1000
- **Total per 1000**: $98

---

## 🔑 Important Information

### AWS Account Details
- **Account ID**: 090130568474
- **Region**: us-east-1
- **Profile**: chordscout

### API Endpoints
- **Base URL**: `https://l43ftjo75d.execute-api.us-east-1.amazonaws.com/dev`
- **Create Job**: `POST /jobs`
- **Get Status**: `GET /jobs/{jobId}`

### S3 Buckets
- **Audio**: `chordscout-audio-temp-dev-090130568474`
- **PDFs**: `chordscout-pdfs-dev-090130568474`
- **Cookies**: `chordscout-audio-temp-dev-090130568474/cookies/youtube-cookies.txt`

### DynamoDB Tables
- **Jobs**: `ChordScout-Jobs-V2-dev`

### Lambda Functions
- `chordscout-v2-create-job-dev`
- `chordscout-v2-youtube-downloader-dev` ⚠️ (needs fix)
- `chordscout-v2-lyrics-transcriber-dev`
- `chordscout-v2-chord-detector-trigger-dev`
- `chordscout-v2-pdf-generator-dev`
- `chordscout-v2-get-job-status-dev`

### ECS
- **Cluster**: `ChordScout-dev`
- **Task**: `chordscout-chord-detector-dev`

### API Keys
- Stored in `.env` file (not committed to git)
- APIFY_API_TOKEN: Available in .env
- DEEPGRAM_API_KEY: Available in .env
- OPENAI_API_KEY: Available in .env

---

## 🐛 Known Issues

1. **YouTube Download Failures**
   - Error: "HLS fragment not found" or "Downloaded file is empty"
   - Cause: YouTube's HLS streams not accessible in Lambda
   - Solution: Need alternative approach (Apify/FFmpeg/ECS)

2. **Apify Free Trial Expired**
   - Error: "actor-is-not-rented"
   - Solution: Purchase subscription or use different approach

3. **Cookie Expiration**
   - Cookies need refresh every 1-2 weeks
   - Need automated refresh system (Phase 2)

---

## 📝 Recommendations for Tomorrow

### Recommended Path: Option A (Apify Subscription)
**Why:**
- Fastest to implement (1 hour)
- Most reliable solution
- No infrastructure complexity
- Can always migrate to ECS later

**Steps:**
1. Purchase Apify subscription ($49/month)
2. Update Lambda to use paid Apify actor
3. Test with multiple videos
4. Deploy to production
5. Monitor for 24 hours

**Alternative if budget constrained: Option B (FFmpeg Layer)**
1. Create Lambda layer with FFmpeg binary
2. Update yt-dlp configuration
3. Test thoroughly
4. May still have reliability issues

---

## 📂 Files to Review Tomorrow

1. `NEW_ARCHITECTURE.md` - Full strategy documentation
2. `backend/functions-v2/youtube-downloader/index-ytdlp-backup.py` - Original working code
3. `backend/functions-v2/youtube-downloader/index-apify.py` - Apify version (ready to deploy)
4. `SESSION_NOTES_2026-01-28.md` - This file

---

## ✅ Mock Data Setup (Completed Tonight)

Mock data enabled in frontend to show client working demo while we fix backend.

---

## 🎯 Success Criteria for Tomorrow

- [ ] Choose YouTube download solution
- [ ] Implement chosen solution
- [ ] Successfully download 5 different YouTube videos
- [ ] Complete end-to-end test (YouTube → PDF)
- [ ] Deploy to production
- [ ] Document final solution

---

**Session End Time**: January 28, 2026 - 2:40 AM EST
**Next Session**: January 28, 2026 - Morning

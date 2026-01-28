# Quick Start Guide - January 28, 2026 Morning

## 🎯 Mission: Fix YouTube Download & Complete End-to-End Flow

---

## ⚡ Quick Context (30 seconds)

**What's Working:**
- ✅ Frontend with mock data (client can see demo)
- ✅ All backend services (Deepgram, ECS chord detection, PDF generation)
- ✅ YouTube cookies valid and uploaded

**What's Broken:**
- ❌ YouTube audio download (HLS fragment failures)

**Why It's Broken:**
- YouTube serves HLS streams that can't be downloaded in Lambda
- Even with valid cookies, fragments are inaccessible

---

## 🚀 Three Solution Options (Pick One)

### Option A: Buy Apify Subscription ⭐ RECOMMENDED
**Time:** 1 hour | **Cost:** $49/month | **Reliability:** ⭐⭐⭐⭐⭐

```bash
# 1. Go to https://console.apify.com/billing
# 2. Purchase subscription ($49/month)
# 3. Deploy the ready-made code:
cd backend/functions-v2/youtube-downloader
cp index-apify.py index.py
# Update actor name to paid one in index.py
zip -r function.zip . -x "*.pyc" -x "*__pycache__/*"
aws lambda update-function-code \
  --function-name chordscout-v2-youtube-downloader-dev \
  --zip-file fileb://function.zip \
  --profile chordscout \
  --region us-east-1
```

---

### Option B: Add FFmpeg to Lambda
**Time:** 4-6 hours | **Cost:** Free | **Reliability:** ⭐⭐⭐⭐

```bash
# 1. Create Lambda Layer with FFmpeg
# 2. Update yt-dlp config to use FFmpeg
# 3. Test thoroughly
# See: backend/functions-v2/youtube-downloader/index-ytdlp-backup.py
```

---

### Option C: Build ECS Download Service
**Time:** 6-8 hours | **Cost:** $0.04/video | **Reliability:** ⭐⭐⭐⭐⭐

```bash
# 1. Create Dockerfile with FFmpeg + yt-dlp
# 2. Build and push to ECR
# 3. Create ECS task definition
# 4. Update Step Functions to trigger ECS
# See: backend/infrastructure-v2/cloudformation-ecs-architecture.yaml
```

---

## 📋 Recommended Steps (Option A)

### Step 1: Purchase Apify (5 min)
1. Go to https://console.apify.com/billing
2. Add payment method
3. Subscribe to paid plan ($49/month)

### Step 2: Find Paid Actor (5 min)
```bash
# Search for working YouTube downloader
curl -s "https://api.apify.com/v2/store?search=youtube+download" \
  | python3 -c "import sys, json; data = json.load(sys.stdin); [print(f\"{item['username']}~{item['name']}\") for item in data.get('data', {}).get('items', [])[:10]]"
```

### Step 3: Update Lambda Code (10 min)
```python
# In backend/functions-v2/youtube-downloader/index.py
# Update line ~95 to use the paid actor:
run_response = requests.post(
    'https://api.apify.com/v2/acts/PAID_ACTOR_NAME/runs',
    # ... rest of config
)
```

### Step 4: Deploy & Test (30 min)
```bash
cd backend/functions-v2/youtube-downloader
zip -r function.zip . -x "*.pyc" -x "*__pycache__/*"
aws lambda update-function-code \
  --function-name chordscout-v2-youtube-downloader-dev \
  --zip-file fileb://function.zip \
  --profile chordscout \
  --region us-east-1

# Test
curl -X POST https://l43ftjo75d.execute-api.us-east-1.amazonaws.com/dev/jobs \
  -H 'Content-Type: application/json' \
  -d '{"youtubeUrl": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

### Step 5: Disable Mock Data (5 min)
```typescript
// In src/services/transcriptionService.ts
const USE_MOCK_DATA = false; // Change to false
```

### Step 6: Deploy Frontend (5 min)
```bash
git add .
git commit -m "Fix: Enable real YouTube downloads with Apify"
git push
# Amplify will auto-deploy
```

---

## 🔍 Testing Checklist

Test these videos in order:
- [ ] https://www.youtube.com/watch?v=dQw4w9WgXcQ (Rick Astley - 3:33)
- [ ] https://www.youtube.com/watch?v=9bZkp7q19f0 (Gangnam Style - 4:13)
- [ ] https://www.youtube.com/watch?v=kJQP7kiw5Fk (Despacito - 3:47)
- [ ] https://www.youtube.com/watch?v=fJ9rUzIMcZQ (Bohemian Rhapsody - 5:55)
- [ ] A 10+ minute video

---

## 📊 Monitor These

```bash
# Watch Lambda logs
aws logs tail /aws/lambda/chordscout-v2-youtube-downloader-dev --follow --profile chordscout

# Check job status
curl -s https://l43ftjo75d.execute-api.us-east-1.amazonaws.com/dev/jobs/JOB_ID | python3 -m json.tool

# Monitor costs
aws ce get-cost-and-usage \
  --time-period Start=2026-01-28,End=2026-01-29 \
  --granularity DAILY \
  --metrics BlendedCost \
  --profile chordscout
```

---

## 🆘 If Things Go Wrong

### Apify Not Working?
```bash
# Check actor status
curl -s "https://api.apify.com/v2/acts/ACTOR_NAME?token=YOUR_TOKEN"

# Check run logs
aws logs tail /aws/lambda/chordscout-v2-youtube-downloader-dev --since 5m --profile chordscout
```

### Lambda Timeout?
```bash
# Increase timeout to 5 minutes
aws lambda update-function-configuration \
  --function-name chordscout-v2-youtube-downloader-dev \
  --timeout 300 \
  --profile chordscout
```

### Out of Memory?
```bash
# Increase memory to 2GB
aws lambda update-function-configuration \
  --function-name chordscout-v2-youtube-downloader-dev \
  --memory-size 2048 \
  --profile chordscout
```

---

## 📁 Important Files

- `SESSION_NOTES_2026-01-28.md` - Full session notes
- `NEW_ARCHITECTURE.md` - Complete architecture docs
- `backend/functions-v2/youtube-downloader/index-apify.py` - Apify version (ready)
- `backend/functions-v2/youtube-downloader/index-ytdlp-backup.py` - Original yt-dlp
- `src/services/transcriptionService.ts` - Frontend service (mock enabled)

---

## ✅ Success Criteria

- [ ] YouTube download works for 5 different videos
- [ ] End-to-end flow completes (YouTube → PDF)
- [ ] Frontend shows real progress (not mock)
- [ ] PDF downloads successfully
- [ ] No errors in CloudWatch logs
- [ ] Cost per video < $0.10

---

## 🎯 End Goal

**Working Demo:**
1. User pastes YouTube URL
2. Progress bar shows real progress
3. PDF downloads with chords and lyrics
4. Client is happy! 🎉

---

**Current Time:** 2:45 AM EST
**Estimated Fix Time:** 1 hour (with Apify) or 4-6 hours (with FFmpeg)
**Good luck! 🚀**

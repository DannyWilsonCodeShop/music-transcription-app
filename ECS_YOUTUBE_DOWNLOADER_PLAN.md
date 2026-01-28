# 🚀 ECS YouTube Downloader Implementation Plan

## 🎯 Goal
Replace the failing Apify YouTube downloader with a reliable ECS-based solution using `yt-dlp`.

## 📋 Current Status
- ✅ **Amplify deployed**: https://development.dq27rbwjwqxrg.amplifyapp.com
- ✅ **Frontend working perfectly**
- ✅ **API Gateway + Lambda + Step Functions working**
- ❌ **YouTube download failing** (Apify trial expired)

## 🏗️ Architecture Pattern (Copy Chord Detector)

### **Existing Chord Detector ECS Pattern:**
```
Lambda → ECS Task → Process → Upload to S3 → Continue Workflow
```

### **New YouTube Downloader ECS Pattern:**
```
Lambda → ECS Task → yt-dlp download → Upload audio to S3 → Continue Workflow
```

## 📁 Implementation Structure

### **1. ECS Task Definition**
- **Container**: Python with `yt-dlp` installed
- **CPU/Memory**: 1024 CPU, 2048 Memory (similar to chord detector)
- **Task Role**: S3 write permissions

### **2. Lambda Function**
- **File**: `backend/lambda-functions/youtube-downloader-ecs.py`
- **Purpose**: Trigger ECS task with YouTube URL
- **Pattern**: Copy from existing chord detector Lambda

### **3. ECS Container Code**
- **Directory**: `backend/ecs-tasks/youtube-downloader/`
- **Main file**: `download_youtube.py`
- **Dockerfile**: Python + yt-dlp setup

### **4. Step Function Update**
- **Replace**: Apify call with ECS task call
- **Keep**: Same input/output format for seamless integration

## 🛠️ Implementation Steps

### **Phase 1: Create ECS Task (30 minutes)**
1. Create container code with `yt-dlp`
2. Build and push Docker image
3. Create ECS task definition
4. Test with sample YouTube URL

### **Phase 2: Create Lambda Trigger (15 minutes)**
1. Copy chord detector Lambda pattern
2. Modify for YouTube download task
3. Deploy and test

### **Phase 3: Update Step Function (15 minutes)**
1. Replace Apify step with ECS step
2. Test end-to-end workflow
3. Deploy to production

### **Phase 4: Cleanup (15 minutes)**
1. Remove old Apify code
2. Update documentation
3. Final testing

## 🔧 Technical Details

### **yt-dlp Configuration:**
```python
ydl_opts = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '/tmp/%(title)s.%(ext)s',
    'quiet': True
}
```

### **S3 Upload Pattern:**
```python
# Same as chord detector
s3_key = f"audio/{job_id}/youtube_audio.mp3"
s3_client.upload_file(local_file, bucket, s3_key)
```

### **Lambda Response Format:**
```python
# Keep same format as Apify for seamless replacement
return {
    'statusCode': 200,
    'body': {
        'audioUrl': f's3://{bucket}/{s3_key}',
        'duration': duration,
        'title': video_title
    }
}
```

## 📊 Expected Timeline
- **Total Time**: ~1.5 hours
- **Complexity**: Low (copying existing patterns)
- **Risk**: Very low (proven architecture)

## 🎯 Success Criteria
- [ ] ECS task downloads YouTube audio successfully
- [ ] Audio uploaded to S3 correctly
- [ ] Step Function continues to transcription
- [ ] End-to-end workflow completes
- [ ] Deployed system fully functional

## 🚀 Ready to Start?
All infrastructure is proven working. We just need to build one ECS task following the exact same pattern as the chord detector.

**Next Command**: Start with ECS task creation
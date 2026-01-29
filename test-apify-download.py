#!/usr/bin/env python3
"""
Test Apify YouTube download integration
"""

import requests
import json
import time

# Test with a short, popular video
YOUTUBE_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up
API_BASE = "https://l43ftjo75d.execute-api.us-east-1.amazonaws.com/dev"

print("🎬 Testing YouTube Download with Apify Integration")
print(f"Video URL: {YOUTUBE_URL}\n")

# Step 1: Create job
print("Step 1: Creating job...")
response = requests.post(
    f"{API_BASE}/jobs",
    json={"youtubeUrl": YOUTUBE_URL},
    headers={"Content-Type": "application/json"}
)

if response.status_code != 200:
    print(f"❌ Failed to create job: {response.status_code}")
    print(response.text)
    exit(1)

job_data = response.json()
job_id = job_data.get('jobId')
print(f"✅ Job created: {job_id}\n")

# Step 2: Poll for status
print("Step 2: Monitoring job progress...")
max_attempts = 60  # 2 minutes max
attempt = 0

while attempt < max_attempts:
    time.sleep(2)
    attempt += 1
    
    response = requests.get(f"{API_BASE}/jobs/{job_id}")
    
    if response.status_code != 200:
        print(f"❌ Failed to get status: {response.status_code}")
        continue
    
    status_data = response.json()
    status = status_data.get('status')
    progress = status_data.get('progress', 0)
    current_step = status_data.get('currentStep', 'Processing...')
    
    print(f"[{attempt}/{max_attempts}] Status: {status} | Progress: {progress}% | {current_step}")
    
    if status == 'COMPLETE':
        print(f"\n✅ SUCCESS! Job completed")
        print(f"Video Title: {status_data.get('videoTitle')}")
        print(f"PDF URL: {status_data.get('pdfUrl')}")
        break
    elif status == 'FAILED':
        print(f"\n❌ FAILED: {status_data.get('error')}")
        break
    elif status in ['DOWNLOADING', 'DOWNLOADED']:
        print(f"   ✓ Download step working with Apify!")

print("\n🎉 Test complete!")

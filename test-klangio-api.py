#!/usr/bin/env python3
"""
Test Klangio API for chord recognition
"""

import requests
import time
import json
import sys
import os

# Klangio API Configuration
API_BASE_URL = "https://api.klang.io"
API_KEY = os.environ.get('KLANGIO_API_KEY', '')

if not API_KEY:
    print("❌ Error: KLANGIO_API_KEY environment variable not set")
    print("\nTo get an API key:")
    print("1. Go to https://api-dashboard.klang.io")
    print("2. Sign up for an account")
    print("3. Get your API key from the dashboard")
    print("4. Set it: export KLANGIO_API_KEY='your-key-here'")
    sys.exit(1)

# Test audio file
TEST_AUDIO = "public/meetup_ring.mp3"

if not os.path.exists(TEST_AUDIO):
    print(f"❌ Error: Test audio file not found: {TEST_AUDIO}")
    print("Please provide a valid audio file path")
    sys.exit(1)

print("🎵 Testing Klangio API")
print("=" * 60)
print(f"Audio file: {TEST_AUDIO}")
print(f"API Key: {API_KEY[:10]}..." if len(API_KEY) > 10 else "API Key: (too short)")
print()

# Step 1: Submit transcription job
print("1. Submitting transcription job...")
print("-" * 60)

try:
    with open(TEST_AUDIO, 'rb') as audio_file:
        # Request parameters
        params = {
            'model': 'universal',  # General purpose model
        }
        
        # Request data
        data = {
            'outputs': ['mxml', 'json']  # Get MusicXML and JSON
        }
        
        # Files
        files = {
            'file': audio_file
        }
        
        # Headers
        headers = {
            'kl-api-key': API_KEY
        }
        
        # Submit job
        response = requests.post(
            f"{API_BASE_URL}/transcription",
            headers=headers,
            params=params,
            data=data,
            files=files
        )
        
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            sys.exit(1)
        
        job_data = response.json()
        job_id = job_data['job_id']
        
        print(f"✓ Job submitted successfully")
        print(f"  Job ID: {job_id}")
        print(f"  Status endpoint: {job_data.get('status_endpoint_url', 'N/A')}")
        print()

except Exception as e:
    print(f"❌ Error submitting job: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 2: Poll for completion
print("2. Waiting for transcription to complete...")
print("-" * 60)

max_attempts = 60  # 5 minutes max
attempt = 0

while attempt < max_attempts:
    try:
        # Check status
        status_response = requests.get(
            f"{API_BASE_URL}/job/{job_id}/status",
            headers=headers
        )
        
        if status_response.status_code != 200:
            print(f"❌ Error checking status: {status_response.status_code}")
            print(f"Response: {status_response.text}")
            sys.exit(1)
        
        status_data = status_response.json()
        status = status_data.get('status', 'UNKNOWN')
        
        print(f"  Status: {status} (attempt {attempt + 1}/{max_attempts})")
        
        if status == 'COMPLETED':
            print(f"\n✓ Transcription completed!")
            break
        elif status == 'FAILED':
            print(f"\n❌ Transcription failed")
            print(f"Error: {status_data.get('error', 'Unknown error')}")
            sys.exit(1)
        
        # Wait before next check
        time.sleep(5)
        attempt += 1
        
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        sys.exit(1)

if attempt >= max_attempts:
    print(f"\n⏱️  Timeout: Transcription took too long")
    sys.exit(1)

print()

# Step 3: Get results
print("3. Fetching results...")
print("-" * 60)

try:
    # Get JSON result (chord data)
    json_response = requests.get(
        f"{API_BASE_URL}/job/{job_id}/json",
        headers=headers
    )
    
    if json_response.status_code == 200:
        result_data = json_response.json()
        
        print("✓ Results retrieved successfully")
        print()
        
        # Display results
        print("=" * 60)
        print("TRANSCRIPTION RESULTS")
        print("=" * 60)
        print()
        
        # Key
        if 'key' in result_data:
            print(f"🎹 Key: {result_data['key']}")
        
        # Tempo
        if 'tempo' in result_data or 'bpm' in result_data:
            tempo = result_data.get('tempo') or result_data.get('bpm')
            print(f"🥁 Tempo: {tempo} BPM")
        
        # Time signature
        if 'time_signature' in result_data or 'meter' in result_data:
            ts = result_data.get('time_signature') or result_data.get('meter')
            print(f"⏱️  Time Signature: {ts}")
        
        print()
        
        # Chords
        if 'chords' in result_data:
            chords = result_data['chords']
            print(f"🎸 Chords detected: {len(chords)}")
            print()
            print("First 20 chords:")
            for i, chord in enumerate(chords[:20], 1):
                time_str = f"{chord.get('time', 0):.2f}s" if 'time' in chord else "N/A"
                chord_name = chord.get('chord') or chord.get('name') or 'Unknown'
                print(f"  {i}. {chord_name:8s} at {time_str}")
            
            if len(chords) > 20:
                print(f"  ... and {len(chords) - 20} more chords")
        
        print()
        
        # Save full result
        output_file = f"klangio-result-{job_id}.json"
        with open(output_file, 'w') as f:
            json.dump(result_data, f, indent=2)
        print(f"📄 Full result saved to: {output_file}")
        print()
        
        # Try to get MusicXML
        xml_response = requests.get(
            f"{API_BASE_URL}/job/{job_id}/xml",
            headers=headers
        )
        
        if xml_response.status_code == 200:
            xml_file = f"klangio-result-{job_id}.xml"
            with open(xml_file, 'wb') as f:
                f.write(xml_response.content)
            print(f"📄 MusicXML saved to: {xml_file}")
        
        print()
        print("=" * 60)
        print("✅ TEST COMPLETE!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Review the chord accuracy")
        print("2. Check if key detection is correct")
        print("3. Compare with current system")
        print("4. If good, integrate into pipeline")
        
    else:
        print(f"❌ Error fetching results: {json_response.status_code}")
        print(f"Response: {json_response.text}")
        sys.exit(1)

except Exception as e:
    print(f"❌ Error fetching results: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

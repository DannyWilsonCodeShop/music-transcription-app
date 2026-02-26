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
            'model': 'lead',  # Extract melody and chords
        }
        
        # Data parameters (for transcription job)
        data = {
            'outputs': ['mxml']  # MusicXML output
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
            print(f"\nFull status response:")
            print(json.dumps(status_data, indent=2))
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
    # Get MusicXML result
    xml_response = requests.get(
        f"{API_BASE_URL}/job/{job_id}/xml",
        headers=headers
    )
    
    if xml_response.status_code == 200:
        # Save MusicXML
        xml_file = f"klangio-result-{job_id}.xml"
        with open(xml_file, 'wb') as f:
            f.write(xml_response.content)
        print(f"✓ MusicXML saved to: {xml_file}")
        print()
        
        # Parse MusicXML to extract chord data
        print("=" * 60)
        print("TRANSCRIPTION RESULTS")
        print("=" * 60)
        print()
        
        # Try to parse MusicXML with music21 if available
        try:
            from music21 import converter
            
            score = converter.parse(xml_file)
            
            # Extract key
            key = score.analyze('key')
            print(f"🎹 Key: {key}")
            
            # Extract tempo
            tempo_marks = score.flatten().getElementsByClass('MetronomeMark')
            if tempo_marks:
                tempo = tempo_marks[0].number
                print(f"🥁 Tempo: {tempo} BPM")
            
            # Extract time signature
            time_sigs = score.flatten().getElementsByClass('TimeSignature')
            if time_sigs:
                ts = time_sigs[0]
                print(f"⏱️  Time Signature: {ts.ratioString}")
            
            print()
            
            # Extract chords
            from music21 import harmony
            chords = score.flatten().getElementsByClass(harmony.ChordSymbol)
            
            if chords:
                print(f"🎸 Chords detected: {len(chords)}")
                print()
                print("First 20 chords:")
                for i, chord in enumerate(list(chords)[:20], 1):
                    offset = chord.offset
                    chord_name = chord.figure
                    print(f"  {i}. {chord_name:8s} at offset {offset:.2f}")
                
                if len(chords) > 20:
                    print(f"  ... and {len(chords) - 20} more chords")
            else:
                print("⚠️  No chord symbols found in MusicXML")
            
        except ImportError:
            print("⚠️  music21 not installed, showing raw MusicXML file only")
            print(f"   Install with: pip install music21")
        except Exception as e:
            print(f"⚠️  Could not parse MusicXML: {e}")
            print(f"   Raw file saved to: {xml_file}")
        
        print()
        print("=" * 60)
        print("✅ TEST COMPLETE!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Review the MusicXML file")
        print("2. Check if chord detection is accurate")
        print("3. Compare with current system")
        print("4. If good, integrate into pipeline")
        
    else:
        print(f"❌ Error fetching results: {xml_response.status_code}")
        print(f"Response: {xml_response.text}")
        sys.exit(1)

except Exception as e:
    print(f"❌ Error fetching results: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

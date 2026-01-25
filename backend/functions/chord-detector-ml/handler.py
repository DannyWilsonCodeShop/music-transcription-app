"""
AWS Lambda handler for chord detection using Spotify's Basic Pitch
"""
import json
import os
import tempfile
import boto3
from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH
import pretty_midi
from chord_utils import extract_chords_from_midi, format_chord_progression

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    """
    Lambda handler for chord detection
    
    Expected event format:
    {
        "bucket": "bucket-name",
        "key": "path/to/audio.mp3",
        "jobId": "unique-job-id"
    }
    """
    print(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract parameters
        bucket = event.get('bucket')
        key = event.get('key')
        job_id = event.get('jobId')
        
        if not all([bucket, key, job_id]):
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing required parameters: bucket, key, jobId'
                })
            }
        
        # Download audio file from S3
        print(f"Downloading audio from s3://{bucket}/{key}")
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as audio_file:
            audio_path = audio_file.name
            s3_client.download_file(bucket, key, audio_path)
        
        print(f"Audio downloaded to {audio_path}")
        
        # Run Basic Pitch inference
        print("Running Basic Pitch inference...")
        model_output, midi_data, note_events = predict(
            audio_path,
            ICASSP_2022_MODEL_PATH
        )
        
        print(f"Basic Pitch completed. Found {len(midi_data.instruments)} instruments")
        
        # Extract chords from MIDI
        print("Extracting chords from MIDI data...")
        chords_data = extract_chords_from_midi(midi_data, segment_duration=2.0)
        
        print(f"Detected key: {chords_data['key']} {chords_data['mode']}")
        print(f"Found {len(chords_data['chords'])} chord segments")
        
        # Format results
        chord_progression_text = format_chord_progression(chords_data)
        
        # Save MIDI file to S3 (optional, for debugging)
        midi_key = f"midi/{job_id}.mid"
        with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as midi_file:
            midi_path = midi_file.name
            midi_data.write(midi_path)
            s3_client.upload_file(midi_path, bucket, midi_key)
            print(f"MIDI saved to s3://{bucket}/{midi_key}")
            os.unlink(midi_path)
        
        # Clean up
        os.unlink(audio_path)
        
        # Return results
        result = {
            'statusCode': 200,
            'body': json.dumps({
                'jobId': job_id,
                'key': chords_data['key'],
                'mode': chords_data['mode'],
                'chords': chords_data['chords'],
                'chordProgressionText': chord_progression_text,
                'midiUrl': f"s3://{bucket}/{midi_key}",
                'totalChords': len(chords_data['chords'])
            })
        }
        
        print(f"Chord detection completed successfully")
        return result
        
    except Exception as e:
        print(f"Error in chord detection: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'jobId': event.get('jobId', 'unknown')
            })
        }

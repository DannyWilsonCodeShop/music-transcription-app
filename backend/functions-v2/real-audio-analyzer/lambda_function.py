#!/usr/bin/env python3
"""
AWS Lambda Function for Real Audio Analysis
Integrates real audio analysis with AWS services and chord change detection
"""

import json
import boto3
import os
from typing import Dict, Any
import traceback
from real_audio_analyzer import analyze_audio_file

# AWS clients
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')

# Environment variables
JOBS_TABLE = os.environ.get('DYNAMODB_JOBS_TABLE', 'ChordScout-Jobs-dev')
AUDIO_BUCKET = os.environ.get('S3_AUDIO_BUCKET', 'chordscout-audio-dev-463470937777')

def lambda_handler(event, context):
    """
    AWS Lambda handler for real audio analysis
    
    Args:
        event: Lambda event containing jobId and audioUrl
        context: Lambda context
        
    Returns:
        Analysis results with chord change detection applied
    """
    print(f"🎼 Real Audio Analysis Lambda - Event: {json.dumps(event)}")
    
    try:
        # Extract parameters
        job_id = event.get('jobId')
        audio_url = event.get('audioUrl')
        analysis_interval = event.get('analysisInterval', 0.2)
        
        if not job_id or not audio_url:
            raise ValueError("Missing required parameters: jobId and audioUrl")
        
        # Update job status
        update_job_status(job_id, 'PROCESSING', 10, 'Starting real audio analysis')
        
        print(f"📊 Analyzing audio: {audio_url}")
        print(f"⏱️ Analysis interval: {analysis_interval}s")
        
        # Perform real audio analysis
        update_job_status(job_id, 'PROCESSING', 30, 'Performing audio analysis')
        raw_analysis = analyze_audio_file(audio_url, analysis_interval)
        
        print(f"✅ Raw analysis complete: {len(raw_analysis['chords']['chords'])} chord detections")
        
        # Apply chord change detection to reduce data size
        update_job_status(job_id, 'PROCESSING', 70, 'Detecting chord changes')
        chord_changes = detect_chord_changes(raw_analysis)
        
        print(f"🔍 Chord changes detected: {len(chord_changes['chordChanges'])} changes")
        print(f"📉 Data reduction: {chord_changes['summary']['dataReduction']:.1f}%")
        
        # Add Nashville numbers
        update_job_status(job_id, 'PROCESSING', 85, 'Generating Nashville numbers')
        enhanced_analysis = add_nashville_numbers(chord_changes, raw_analysis['key'])
        
        # Prepare final analysis for DynamoDB storage
        final_analysis = {
            'tempo': raw_analysis['tempo'],
            'key': raw_analysis['key'],
            'timeSignature': raw_analysis['timeSignature'],
            'chords': enhanced_analysis['chordChanges'],  # Store only chord changes
            'chordAnalysis': {
                'chordChanges': enhanced_analysis['chordChanges'],
                'measures': enhanced_analysis.get('measures', []),
                'summary': chord_changes['summary']
            },
            'metadata': {
                **raw_analysis['metadata'],
                'chordChangeDetection': True,
                'originalDetections': len(raw_analysis['chords']['chords']),
                'finalChanges': len(enhanced_analysis['chordChanges']),
                'dataReduction': chord_changes['summary']['dataReduction']
            }
        }
        
        # Verify data size for DynamoDB compatibility
        data_size = len(json.dumps(final_analysis))
        print(f"📏 Final analysis size: {data_size} bytes")
        
        if data_size >= 400000:  # 400KB limit
            print("⚠️ Data still too large, applying additional compression")
            final_analysis = compress_analysis_data(final_analysis)
            data_size = len(json.dumps(final_analysis))
            print(f"📏 Compressed analysis size: {data_size} bytes")
        
        # Store analysis in DynamoDB
        update_job_status(job_id, 'PROCESSING', 95, 'Storing analysis results')
        store_analysis_results(job_id, final_analysis)
        
        # Complete job
        update_job_status(job_id, 'CHORD_ANALYSIS_COMPLETE', 100, 'Real audio analysis complete')
        
        return {
            'statusCode': 200,
            'body': {
                'jobId': job_id,
                'message': 'Real audio analysis completed successfully',
                'results': {
                    'duration': raw_analysis['metadata']['duration'],
                    'tempo': raw_analysis['tempo']['bpm'],
                    'key': f"{raw_analysis['key']['root']} {raw_analysis['key']['mode']}",
                    'timeSignature': f"{raw_analysis['timeSignature']['numerator']}/{raw_analysis['timeSignature']['denominator']}",
                    'originalDetections': len(raw_analysis['chords']['chords']),
                    'chordChanges': len(enhanced_analysis['chordChanges']),
                    'dataReduction': chord_changes['summary']['dataReduction'],
                    'dataSize': data_size,
                    'dynamoDbCompatible': data_size < 400000
                }
            }
        }
        
    except Exception as e:
        error_msg = f"Real audio analysis failed: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"Stack trace: {traceback.format_exc()}")
        
        # Update job status to failed
        if 'job_id' in locals():
            update_job_status(job_id, 'FAILED', 0, error_msg)
        
        return {
            'statusCode': 500,
            'body': {
                'error': error_msg,
                'type': type(e).__name__
            }
        }

def detect_chord_changes(raw_analysis: Dict) -> Dict:
    """
    Apply chord change detection to reduce data size
    
    Args:
        raw_analysis: Raw audio analysis with all chord detections
        
    Returns:
        Chord changes with data reduction summary
    """
    raw_chords = raw_analysis['chords']['chords']
    time_signature = raw_analysis['timeSignature']
    
    if not raw_chords:
        return {
            'chordChanges': [],
            'summary': {
                'totalChanges': 0,
                'originalDetections': 0,
                'dataReduction': 0.0
            }
        }
    
    chord_changes = []
    current_chord = None
    chord_start_time = 0
    
    for i, chord in enumerate(raw_chords):
        chord_name = chord['chord']
        chord_time = chord['start']
        
        # Check if chord changed
        if current_chord != chord_name:
            # Save previous chord change
            if current_chord is not None:
                chord_changes.append({
                    'chord': current_chord,
                    'time': chord_start_time,
                    'startTime': chord_start_time,
                    'endTime': chord_time,
                    'duration': chord_time - chord_start_time,
                    'confidence': raw_chords[i-1]['confidence'],
                    'isDownbeat': raw_chords[i-1].get('isDownbeat', False),
                    'isPassingChord': raw_chords[i-1].get('isPassingChord', True)
                })
            
            # Start tracking new chord
            current_chord = chord_name
            chord_start_time = chord_time
    
    # Add final chord
    if current_chord is not None and raw_chords:
        last_chord = raw_chords[-1]
        chord_changes.append({
            'chord': current_chord,
            'time': chord_start_time,
            'startTime': chord_start_time,
            'endTime': last_chord['end'],
            'duration': last_chord['end'] - chord_start_time,
            'confidence': last_chord['confidence'],
            'isDownbeat': last_chord.get('isDownbeat', False),
            'isPassingChord': last_chord.get('isPassingChord', True)
        })
    
    # Calculate data reduction
    original_size = len(json.dumps(raw_chords))
    reduced_size = len(json.dumps(chord_changes))
    reduction_percentage = ((original_size - reduced_size) / original_size * 100) if original_size > 0 else 0
    
    return {
        'chordChanges': chord_changes,
        'summary': {
            'totalChanges': len(chord_changes),
            'originalDetections': len(raw_chords),
            'dataReduction': reduction_percentage,
            'originalSize': original_size,
            'reducedSize': reduced_size
        }
    }

def add_nashville_numbers(chord_changes: Dict, key_info: Dict) -> Dict:
    """
    Add Nashville number notation to chord changes
    
    Args:
        chord_changes: Chord changes data
        key_info: Key analysis information
        
    Returns:
        Enhanced chord changes with Nashville numbers
    """
    key_root = key_info['root']
    key_mode = key_info['mode']
    
    # Note to semitone mapping
    note_to_semitone = {
        'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5,
        'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11
    }
    
    # Nashville number mapping for major keys
    major_numbers = ['1', 'b2', '2', 'b3', '3', '4', 'b5', '5', 'b6', '6', 'b7', '7']
    
    key_semitone = note_to_semitone.get(key_root, 0)
    
    enhanced_changes = []
    for change in chord_changes['chordChanges']:
        chord_name = change['chord']
        
        # Extract root note from chord
        if chord_name == 'N':
            nashville_number = 'N'
        else:
            # Get root note (handle sharps/flats)
            if len(chord_name) > 1 and chord_name[1] in ['#', 'b']:
                root_note = chord_name[:2]
            else:
                root_note = chord_name[0]
            
            chord_semitone = note_to_semitone.get(root_note, 0)
            interval = (chord_semitone - key_semitone + 12) % 12
            nashville_number = major_numbers[interval]
            
            # Add chord quality indicators
            if 'm' in chord_name.lower() and 'maj' not in chord_name.lower():
                nashville_number += 'm'
        
        enhanced_change = {
            **change,
            'nashvilleNumber': nashville_number
        }
        enhanced_changes.append(enhanced_change)
    
    return {
        'chordChanges': enhanced_changes,
        'summary': chord_changes['summary']
    }

def compress_analysis_data(analysis: Dict) -> Dict:
    """
    Compress analysis data if it's still too large for DynamoDB
    
    Args:
        analysis: Analysis data to compress
        
    Returns:
        Compressed analysis data
    """
    # Remove less critical data to fit DynamoDB limits
    compressed = {
        'tempo': {
            'bpm': analysis['tempo']['bpm'],
            'confidence': analysis['tempo']['confidence']
        },
        'key': {
            'root': analysis['key']['root'],
            'mode': analysis['key']['mode'],
            'confidence': analysis['key']['confidence']
        },
        'timeSignature': {
            'numerator': analysis['timeSignature']['numerator'],
            'denominator': analysis['timeSignature']['denominator'],
            'measureDuration': analysis['timeSignature']['measureDuration']
        },
        'chords': analysis['chords'][:100],  # Limit to first 100 chord changes
        'metadata': {
            'duration': analysis['metadata']['duration'],
            'chordChangeDetection': True,
            'compressed': True,
            'originalChanges': len(analysis['chords']),
            'includedChanges': min(100, len(analysis['chords']))
        }
    }
    
    return compressed

def update_job_status(job_id: str, status: str, progress: int, message: str = None):
    """Update job status in DynamoDB"""
    try:
        table = dynamodb.Table(JOBS_TABLE)
        
        update_expression = 'SET #status = :status, progress = :progress, updatedAt = :updated'
        expression_values = {
            ':status': status,
            ':progress': progress,
            ':updated': boto3.dynamodb.conditions.Key('timestamp').eq('now').__dict__['value']
        }
        expression_names = {'#status': 'status'}
        
        if message:
            update_expression += ', statusMessage = :message'
            expression_values[':message'] = message
        
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ExpressionAttributeNames=expression_names
        )
        
    except Exception as e:
        print(f"Warning: Failed to update job status: {e}")

def store_analysis_results(job_id: str, analysis: Dict):
    """Store analysis results in DynamoDB"""
    try:
        table = dynamodb.Table(JOBS_TABLE)
        
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET chords = :chords, chordAnalysis = :chordAnalysis, #key = :key, tempo = :tempo, timeSignature = :timeSignature, analysisMetadata = :metadata, updatedAt = :updated',
            ExpressionAttributeValues={
                ':chords': analysis['chords'],
                ':chordAnalysis': analysis['chordAnalysis'],
                ':key': f"{analysis['key']['root']} {analysis['key']['mode']}",
                ':tempo': analysis['tempo']['bpm'],
                ':timeSignature': f"{analysis['timeSignature']['numerator']}/{analysis['timeSignature']['denominator']}",
                ':metadata': analysis['metadata'],
                ':updated': boto3.dynamodb.conditions.Key('timestamp').eq('now').__dict__['value']
            },
            ExpressionAttributeNames={'#key': 'key'}
        )
        
        print(f"✅ Analysis results stored for job {job_id}")
        
    except Exception as e:
        print(f"❌ Failed to store analysis results: {e}")
        raise
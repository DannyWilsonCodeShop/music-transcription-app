# Implementation Plan: v3.0 ChordScout Accuracy Improvements

## Overview

This implementation plan transforms the bass-only transcription pipeline into a comprehensive multi-instrument analysis system with enhanced accuracy. The core improvements include 8th note quantization (replacing 16th notes), multi-stem transcription support (piano and guitar), song identification with lyrics integration, and user confirmation workflows for transcription mode and key selection.

The implementation maintains full backward compatibility with v2.0 while adding significant new capabilities. The system extends the existing ECS-based processing pipeline with new modules for stem transcription, song identification, and lyrics fetching.

**What's Already Complete:**
- ✅ `backend/functions-v2/chord-detector-ecs/stem_transcription.py` - Multi-stem transcription module
- ✅ `backend/functions-v2/chord-detector-ecs/song_metadata_lyrics.py` - Song identification and lyrics
- ✅ `backend/functions-v2/chord-detector-ecs/bass_note_transcription.py` - Changed from 16th to 8th note quantization

**Implementation Strategy:**
The tasks are organized into 7 phases following the 4-phase migration strategy from the design document:
1. **Backend Integration** - Update dependencies and integrate new modules into ECS pipeline
2. **Lambda Functions** - Create user confirmation endpoints for mode and key selection
3. **Frontend Updates** - Add new job statuses and UI components for user interactions
4. **Testing** - Unit tests, integration tests, and validation
5. **Phase 1 Deployment** - Backward compatible deployment with v2.0 behavior
6. **Phase 2-3 Deployment** - Enable multi-stem and lyrics features
7. **Phase 4 Optimization** - Performance tuning and monitoring

---

## Tasks

### Phase 1: Backend Integration

- [x] 1. Update Python dependencies
  - [x] 1.1 Add new dependencies to requirements.txt
    - Add mutagen==1.47.0 for audio metadata extraction
    - Add requests==2.31.0 for HTTP client (Genius API)
    - Add beautifulsoup4==4.12.0 for HTML parsing (lyrics)
    - Add lyricsgenius==3.0.1 for Genius API client
    - **Files**: `bass-transcription-pipeline/bass-transcription-ecs/requirements.txt`
    - **Complexity**: Small
    - **Requirements**: 10.2
  
  - [x] 1.2 Test dependency installation in Docker
    - Build Docker image locally with new dependencies
    - Verify all imports work correctly
    - Check for version conflicts
    - **Complexity**: Small
    - **Requirements**: 10.3


- [x] 2. Integrate new modules into ECS orchestrator
  - [x] 2.1 Import new modules in app.py
    - Add imports for stem_transcription module
    - Add imports for song_metadata_lyrics module
    - Add imports for updated bass_note_transcription module
    - **Files**: `bass-transcription-pipeline/bass-transcription-ecs/app.py`
    - **Complexity**: Small
    - **Requirements**: All
  
  - [x] 2.2 Add song identification stage
    - Call identify_song() after tempo detection
    - Store song metadata in DynamoDB
    - Handle identification failures gracefully (use filename)
    - Update job status to show "Identifying song..."
    - **Files**: `bass-transcription-pipeline/bass-transcription-ecs/app.py`
    - **Complexity**: Medium
    - **Dependencies**: 2.1
    - **Requirements**: 3.1, 3.2, 3.3, 3.4, 9.2
  
  - [x] 2.3 Add stem separation stage
    - Call Demucs separation after downbeat confirmation
    - Upload separated stems to S3 (audio/{jobId}/stems/)
    - Handle separation failures (fallback to bass-only)
    - Update job status to "Processing stems..."
    - **Files**: `bass-transcription-pipeline/bass-transcription-ecs/app.py`
    - **Complexity**: Medium
    - **Dependencies**: 2.2
    - **Requirements**: 2.1, 2.2, 2.4, 2.5, 9.1

  - [x] 2.4 Implement transcription mode selection workflow
    - Update job status to PENDING_MODE_SELECTION
    - Implement wait_for_mode_selection() with 5-minute timeout
    - Default to "bass-only" on timeout
    - Poll DynamoDB for user selection every 2 seconds
    - **Files**: `bass-transcription-pipeline/bass-transcription-ecs/app.py`
    - **Complexity**: Medium
    - **Dependencies**: 2.3
    - **Requirements**: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8
  
  - [x] 2.5 Implement multi-stem transcription
    - Create transcribe_stems() function
    - Always transcribe bass with 8th note quantization
    - Conditionally transcribe piano based on mode
    - Conditionally transcribe guitar based on mode
    - Handle individual stem transcription failures
    - **Files**: `bass-transcription-pipeline/bass-transcription-ecs/app.py`
    - **Complexity**: Large
    - **Dependencies**: 2.4
    - **Requirements**: 1.1, 1.2, 1.3, 1.4, 1.5, 2.2, 2.3, 2.6, 2.7
  
  - [x] 2.6 Add lyrics fetching stage
    - Call fetch_lyrics() with song metadata
    - Fetch lyrics from Genius API (non-blocking)
    - Handle API failures gracefully
    - Store lyrics in DynamoDB
    - Update job status to "Fetching lyrics..."
    - **Files**: `bass-transcription-pipeline/bass-transcription-ecs/app.py`
    - **Complexity**: Medium
    - **Dependencies**: 2.5
    - **Requirements**: 4.1, 4.2, 4.3, 4.4, 4.7, 9.3

  - [x] 2.7 Implement key detection and confirmation workflow
    - Call detect_key_from_transcription() with transcribed notes
    - Store detected key and confidence in DynamoDB
    - Update job status to PENDING_KEY_CONFIRMATION
    - Implement wait_for_key_confirmation() with 5-minute timeout
    - Default to detected key on timeout
    - **Files**: `bass-transcription-pipeline/bass-transcription-ecs/app.py`
    - **Complexity**: Medium
    - **Dependencies**: 2.6
    - **Requirements**: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 9.4
  
  - [x] 2.8 Implement lyrics-to-measures alignment
    - Call align_lyrics_to_measures() if lyrics available
    - Align lyrics sections to measure boundaries
    - Store aligned lyrics in DynamoDB
    - **Files**: `bass-transcription-pipeline/bass-transcription-ecs/app.py`
    - **Complexity**: Medium
    - **Dependencies**: 2.7
    - **Requirements**: 4.5, 4.6
  
  - [x] 2.9 Update DynamoDB write operations
    - Add transcriptionMode field to job updates
    - Add detectedKey and confirmedKey fields
    - Add songMetadata object (title, artist, album, year)
    - Add lyrics object with sections
    - Add stemData object (piano and guitar notes)
    - Add processingMetrics object
    - **Files**: `bass-transcription-pipeline/bass-transcription-ecs/app.py`
    - **Complexity**: Medium
    - **Dependencies**: 2.8
    - **Requirements**: All

- [x] 3. Update Docker configuration
  - [x] 3.1 Update Dockerfile
    - Copy stem_transcription.py to /app/
    - Copy song_metadata_lyrics.py to /app/
    - Ensure all new modules are included in image
    - **Files**: `bass-transcription-pipeline/bass-transcription-ecs/Dockerfile`
    - **Complexity**: Small
    - **Requirements**: 10.3
  
  - [x] 3.2 Add environment variables
    - Add GENIUS_ACCESS_TOKEN (from Secrets Manager)
    - Add ENABLE_LYRICS flag (default: true)
    - Add ENABLE_MULTI_STEM flag (default: false initially)
    - Add DEFAULT_TRANSCRIPTION_MODE (default: bass-only)
    - Add CONFIRMATION_TIMEOUT (default: 300 seconds)
    - **Files**: ECS task definition, `.env` for local testing
    - **Complexity**: Small
    - **Requirements**: 10.1, 10.5
  
  - [x] 3.3 Build and test Docker image locally
    - Build image with new modules
    - Run container with test audio file
    - Verify all stages execute correctly
    - Check CloudWatch logs for errors
    - **Complexity**: Medium
    - **Dependencies**: 3.1, 3.2
    - **Requirements**: 10.3, 10.4

### Phase 2: Lambda Functions for User Confirmation

- [x] 4. Create transcription mode confirmation Lambda
  - [x] 4.1 Create Lambda function handler
    - Create new file: `backend/functions-v2/confirm-transcription-mode/index.js`
    - Parse jobId from path parameters
    - Parse transcriptionMode from request body
    - Validate mode is one of: bass-only, bass+piano, bass+guitar, all
    - **Files**: `backend/functions-v2/confirm-transcription-mode/index.js`
    - **Complexity**: Medium
    - **Requirements**: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6

  - [x] 4.2 Implement DynamoDB update
    - Update job record with transcriptionMode field
    - Update updatedAt timestamp
    - Return success response with jobId and mode
    - **Files**: `backend/functions-v2/confirm-transcription-mode/index.js`
    - **Complexity**: Small
    - **Dependencies**: 4.1
    - **Requirements**: 5.7
  
  - [x] 4.3 Add error handling
    - Handle invalid mode values
    - Handle job not found errors
    - Handle DynamoDB errors
    - Return appropriate HTTP status codes
    - **Files**: `backend/functions-v2/confirm-transcription-mode/index.js`
    - **Complexity**: Small
    - **Dependencies**: 4.2
    - **Requirements**: 9.1, 9.5, 9.6
  
  - [x] 4.4 Create Lambda deployment package
    - Add package.json with aws-sdk dependency
    - Create deployment script
    - Test Lambda locally with SAM or similar
    - **Files**: `backend/functions-v2/confirm-transcription-mode/package.json`
    - **Complexity**: Small
    - **Dependencies**: 4.3
    - **Requirements**: 10.3

- [x] 5. Create key confirmation Lambda
  - [x] 5.1 Create Lambda function handler
    - Create new file: `backend/functions-v2/confirm-key/index.js`
    - Parse jobId from path parameters
    - Parse confirmedKey from request body
    - Validate key format (e.g., "C major", "A minor")
    - **Files**: `backend/functions-v2/confirm-key/index.js`
    - **Complexity**: Medium
    - **Requirements**: 6.3, 6.4, 6.5

  - [x] 5.2 Implement DynamoDB update
    - Update job record with confirmedKey field
    - Update updatedAt timestamp
    - Return success response with jobId, detectedKey, and confirmedKey
    - **Files**: `backend/functions-v2/confirm-key/index.js`
    - **Complexity**: Small
    - **Dependencies**: 5.1
    - **Requirements**: 6.6
  
  - [x] 5.3 Add error handling
    - Handle invalid key format
    - Handle job not found errors
    - Handle DynamoDB errors
    - Return appropriate HTTP status codes
    - **Files**: `backend/functions-v2/confirm-key/index.js`
    - **Complexity**: Small
    - **Dependencies**: 5.2
    - **Requirements**: 9.4, 9.5, 9.6
  
  - [x] 5.4 Create Lambda deployment package
    - Add package.json with aws-sdk dependency
    - Create deployment script
    - Test Lambda locally
    - **Files**: `backend/functions-v2/confirm-key/package.json`
    - **Complexity**: Small
    - **Dependencies**: 5.3
    - **Requirements**: 10.3

- [x] 6. Update API Gateway configuration
  - [x] 6.1 Add POST /jobs/{jobId}/confirm-mode endpoint
    - Configure API Gateway route
    - Link to confirm-transcription-mode Lambda
    - Add CORS configuration
    - Test endpoint with curl/Postman
    - **Complexity**: Small
    - **Dependencies**: 4.4
    - **Requirements**: 5.1

  - [x] 6.2 Add POST /jobs/{jobId}/confirm-key endpoint
    - Configure API Gateway route
    - Link to confirm-key Lambda
    - Add CORS configuration
    - Test endpoint with curl/Postman
    - **Complexity**: Small
    - **Dependencies**: 5.4
    - **Requirements**: 6.3

### Phase 3: Frontend Updates

- [x] 7. Update TypeScript types and services
  - [x] 7.1 Extend TranscriptionJob interface
    - Add transcriptionMode field
    - Add detectedKey and confirmedKey fields
    - Add keyConfidence field
    - Add songMetadata object type
    - Add lyrics object type
    - Add stemData object type
    - **Files**: `src/services/transcriptionService.ts`
    - **Complexity**: Small
    - **Requirements**: All
  
  - [x] 7.2 Add new job status types
    - Add PROCESSING_STEMS status
    - Add PENDING_MODE_SELECTION status
    - Add TRANSCRIBING_STEMS status
    - Add FETCHING_LYRICS status
    - Add PENDING_KEY_CONFIRMATION status
    - **Files**: `src/services/transcriptionService.ts`
    - **Complexity**: Small
    - **Dependencies**: 7.1
    - **Requirements**: All

  - [x] 7.3 Create API service functions
    - Implement confirmTranscriptionMode(jobId, mode) function
    - Implement confirmKey(jobId, key) function
    - Add error handling and retry logic
    - **Files**: `src/services/transcriptionService.ts`
    - **Complexity**: Medium
    - **Dependencies**: 7.2
    - **Requirements**: 5.1, 6.3

- [x] 8. Create TranscriptionModeSelector component
  - [x] 8.1 Create component file and basic structure
    - Create `src/components/TranscriptionModeSelector.tsx`
    - Define props interface (jobId, onModeSelected)
    - Set up state for selectedMode and isSubmitting
    - **Files**: `src/components/TranscriptionModeSelector.tsx`
    - **Complexity**: Medium
    - **Requirements**: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
  
  - [x] 8.2 Implement mode selection UI
    - Create 4 mode option buttons (bass-only, bass+piano, bass+guitar, all)
    - Add icons and descriptions for each mode
    - Add estimated processing time for each mode
    - Highlight selected mode
    - **Files**: `src/components/TranscriptionModeSelector.tsx`
    - **Complexity**: Medium
    - **Dependencies**: 8.1
    - **Requirements**: 5.2, 5.3, 5.4, 5.5
  
  - [x] 8.3 Implement confirmation logic
    - Add confirm button with loading state
    - Call confirmTranscriptionMode API on submit
    - Handle success and error states
    - Call onModeSelected callback on success
    - **Files**: `src/components/TranscriptionModeSelector.tsx`
    - **Complexity**: Small
    - **Dependencies**: 8.2
    - **Requirements**: 5.6, 5.7

  - [x] 8.4 Add timeout notice
    - Display "Auto-selects Bass Only in 5 minutes" message
    - Add countdown timer (optional enhancement)
    - **Files**: `src/components/TranscriptionModeSelector.tsx`
    - **Complexity**: Small
    - **Dependencies**: 8.3
    - **Requirements**: 5.8
  
  - [x] 8.5 Add styling
    - Create CSS for mode selector layout
    - Style mode option buttons with hover effects
    - Add responsive design for mobile
    - **Files**: `src/components/TranscriptionModeSelector.tsx` or separate CSS file
    - **Complexity**: Small
    - **Dependencies**: 8.4
    - **Requirements**: UI/UX

- [x] 9. Create KeyConfirmation component
  - [x] 9.1 Create component file and basic structure
    - Create `src/components/KeyConfirmation.tsx`
    - Define props interface (jobId, detectedKey, keyConfidence, onKeyConfirmed)
    - Set up state for selectedKey and isSubmitting
    - **Files**: `src/components/KeyConfirmation.tsx`
    - **Complexity**: Medium
    - **Requirements**: 6.2, 6.3, 6.4, 6.5
  
  - [x] 9.2 Implement detected key display
    - Show detected key prominently
    - Display confidence percentage
    - Add visual indicator for confidence level (high/medium/low)
    - **Files**: `src/components/KeyConfirmation.tsx`
    - **Complexity**: Small
    - **Dependencies**: 9.1
    - **Requirements**: 6.2

  - [x] 9.3 Implement key selection dropdown
    - Create dropdown with all 24 keys (12 major, 12 minor)
    - Pre-select detected key
    - Allow user to change selection
    - **Files**: `src/components/KeyConfirmation.tsx`
    - **Complexity**: Small
    - **Dependencies**: 9.2
    - **Requirements**: 6.4
  
  - [x] 9.4 Implement confirmation logic
    - Add confirm button with loading state
    - Call confirmKey API on submit
    - Handle success and error states
    - Call onKeyConfirmed callback on success
    - **Files**: `src/components/KeyConfirmation.tsx`
    - **Complexity**: Small
    - **Dependencies**: 9.3
    - **Requirements**: 6.5, 6.6
  
  - [x] 9.5 Add timeout notice
    - Display "Auto-confirms detected key in 5 minutes" message
    - Add countdown timer (optional enhancement)
    - **Files**: `src/components/KeyConfirmation.tsx`
    - **Complexity**: Small
    - **Dependencies**: 9.4
    - **Requirements**: 6.7
  
  - [x] 9.6 Add styling
    - Create CSS for key confirmation layout
    - Style dropdown and buttons
    - Add responsive design for mobile
    - **Files**: `src/components/KeyConfirmation.tsx` or separate CSS file
    - **Complexity**: Small
    - **Dependencies**: 9.5
    - **Requirements**: UI/UX

- [x] 10. Integrate components into App.tsx
  - [x] 10.1 Add state management for modals
    - Add showModeSelector state
    - Add showKeyConfirmation state
    - **Files**: `src/App.tsx`
    - **Complexity**: Small
    - **Requirements**: All
  
  - [x] 10.2 Add status-based modal triggers
    - Show TranscriptionModeSelector when status is PENDING_MODE_SELECTION
    - Show KeyConfirmation when status is PENDING_KEY_CONFIRMATION
    - Hide modals after user confirmation
    - **Files**: `src/App.tsx`
    - **Complexity**: Medium
    - **Dependencies**: 10.1
    - **Requirements**: 5.1, 6.2
  
  - [x] 10.3 Update status polling logic
    - Continue polling after mode selection
    - Continue polling after key confirmation
    - Handle new status types in UI
    - **Files**: `src/App.tsx`
    - **Complexity**: Small
    - **Dependencies**: 10.2
    - **Requirements**: All
  
  - [x] 10.4 Add status message display
    - Show "Identifying song..." for song identification
    - Show "Separating stems..." for stem separation
    - Show "Transcribing instruments..." for multi-stem transcription
    - Show "Fetching lyrics..." for lyrics retrieval
    - **Files**: `src/App.tsx`
    - **Complexity**: Small
    - **Dependencies**: 10.3
    - **Requirements**: All

- [x] 11. Update results display components
  - [x] 11.1 Display song metadata
    - Show song title, artist, album in results
    - Handle "Unknown Song" gracefully
    - **Files**: `src/components/LeadSheetDisplay.tsx` or similar
    - **Complexity**: Small
    - **Requirements**: 3.1, 3.2, 3.3
  
  - [x] 11.2 Display lyrics in PDF viewer
    - Show lyrics sections if available
    - Align with chord changes
    - Handle missing lyrics gracefully
    - **Files**: PDF display component
    - **Complexity**: Medium
    - **Requirements**: 4.1, 4.2, 4.5, 4.6
  
  - [x] 11.3 Display multi-stem transcription data
    - Show piano notes if transcribed
    - Show guitar notes if transcribed
    - Add toggle to show/hide different stems
    - **Files**: Results display component
    - **Complexity**: Medium
    - **Requirements**: 2.2, 2.3, 2.6

### Phase 4: Testing

- [x] 12. Write unit tests for new modules
  - [x] 12.1 Test stem_transcription.py
    - Test transcribe_stem() with piano audio
    - Test transcribe_stem() with guitar audio
    - Test 8th note quantization
    - Test frequency range constraints
    - Verify output format matches specification
    - **Files**: `backend/functions-v2/chord-detector-ecs/test_stem_transcription.py`
    - **Complexity**: Large
    - **Requirements**: 2.1, 2.2, 2.3, 2.6, 2.7, 11.1, 11.2, 11.3, 11.4, 11.5

  - [x] 12.2 Test song_metadata_lyrics.py
    - Test identify_song() with various audio files
    - Test fetch_lyrics() with known songs
    - Test lyrics parsing and section detection
    - Test align_lyrics_to_measures()
    - Test error handling (API failures, missing data)
    - **Files**: `backend/functions-v2/chord-detector-ecs/test_song_metadata_lyrics.py`
    - **Complexity**: Large
    - **Requirements**: 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 9.2, 9.3
  
  - [x] 12.3 Test bass_note_transcription.py updates
    - Test 8th note quantization (not 16th)
    - Test idempotence property (quantize twice = same result)
    - Verify quantizationResolution field is '8th'
    - Test measure and beat calculations
    - **Files**: `backend/functions-v2/chord-detector-ecs/test_bass_note_transcription.py`
    - **Complexity**: Medium
    - **Requirements**: 1.1, 1.2, 1.3, 1.4, 1.5, 11.1, 11.2, 11.3, 11.4
  
  - [x] 12.4 Test Lambda functions
    - Test confirm-transcription-mode Lambda
    - Test confirm-key Lambda
    - Test error handling and validation
    - Test DynamoDB updates
    - **Files**: `backend/functions-v2/confirm-transcription-mode/test.js`, `backend/functions-v2/confirm-key/test.js`
    - **Complexity**: Medium
    - **Requirements**: 5.1, 5.6, 5.7, 6.3, 6.5, 6.6
  
  - [x] 12.5 Test frontend components
    - Test TranscriptionModeSelector component
    - Test KeyConfirmation component
    - Test API service functions
    - Test App.tsx integration
    - **Files**: `src/components/__tests__/`
    - **Complexity**: Medium
    - **Requirements**: All frontend requirements

- [x] 13. Integration testing
  - [x] 13.1 Test bass-only mode (v2.0 compatibility)
    - Upload test audio
    - Verify bass-only transcription works
    - Verify 8th note quantization applied
    - Verify PDF generation
    - Confirm no breaking changes
    - **Complexity**: Medium
    - **Requirements**: 7.1, 7.2, 7.3, 7.4, 7.5
  
  - [x] 13.2 Test mode selection workflow
    - Upload test audio
    - Wait for PENDING_MODE_SELECTION status
    - Select each mode (bass+piano, bass+guitar, all)
    - Verify correct stems are transcribed
    - Test timeout behavior (wait 5+ minutes)
    - **Complexity**: Large
    - **Requirements**: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8
  
  - [x] 13.3 Test key confirmation workflow
    - Upload test audio
    - Wait for PENDING_KEY_CONFIRMATION status
    - Confirm detected key
    - Change to different key
    - Verify NNS uses confirmed key
    - Test timeout behavior
    - **Complexity**: Medium
    - **Requirements**: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7
  
  - [x] 13.4 Test lyrics integration
    - Upload songs with known lyrics
    - Verify lyrics fetched from Genius
    - Verify lyrics appear in PDF
    - Test songs without lyrics (graceful degradation)
    - **Complexity**: Medium
    - **Requirements**: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7

  - [x] 13.5 Test error handling and resilience
    - Test stem separation failure (fallback to bass-only)
    - Test song identification failure (use filename)
    - Test lyrics fetch failure (continue without lyrics)
    - Test key detection failure (default to C major)
    - Test individual stem transcription failures
    - **Complexity**: Large
    - **Requirements**: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7
  
  - [x] 13.6 Test data integrity
    - Verify all note onset times are non-negative
    - Verify note durations are positive
    - Verify quantized positions align to 8th note grid
    - Verify MIDI pitch values are 0-127
    - Verify JSON schema validation
    - **Complexity**: Medium
    - **Requirements**: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7
  
  - [x] 13.7 Test parser and serializer
    - Test MIDI to JSON parsing
    - Test JSON serialization
    - Test round-trip property (parse → serialize → parse)
    - Test error handling for invalid data
    - **Complexity**: Medium
    - **Requirements**: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7

### Phase 5: Phase 1 Deployment (Backward Compatible)

- [x] 14. Deploy with v2.0 behavior as default
  - [x] 14.1 Set environment variables for Phase 1
    - Set ENABLE_MULTI_STEM=false
    - Set ENABLE_LYRICS=false
    - Set DEFAULT_TRANSCRIPTION_MODE=bass-only
    - **Complexity**: Small
    - **Requirements**: 7.1, 7.2, 7.3

  - [x] 14.2 Build and push Docker image
    - Build Docker image with all new modules
    - Tag as v3.0-phase1
    - Push to ECR
    - **Complexity**: Small
    - **Dependencies**: 3.3
    - **Requirements**: 10.3
  
  - [x] 14.3 Update ECS task definition
    - Update image to v3.0-phase1
    - Add new environment variables
    - Keep CPU/memory same as v2.0 (4 vCPU, 16 GB)
    - **Complexity**: Small
    - **Dependencies**: 14.2
    - **Requirements**: 10.3
  
  - [x] 14.4 Deploy to development environment
    - Update ECS service with new task definition
    - Monitor CloudWatch logs for errors
    - Test with sample audio files
    - **Complexity**: Medium
    - **Dependencies**: 14.3
    - **Requirements**: 10.4, 10.5
  
  - [x] 14.5 Validate Phase 1 deployment
    - Upload test audio files
    - Verify bass-only transcription works
    - Verify 8th note quantization applied
    - Verify PDF generation
    - Check for any regressions
    - Monitor error rates and processing times
    - **Complexity**: Medium
    - **Dependencies**: 14.4
    - **Requirements**: 7.1, 7.2, 7.3, 7.4, 7.5, 8.1, 8.2, 8.3, 8.4, 8.5

### Phase 6: Phase 2-3 Deployment (Enable Multi-Stem and Lyrics)

- [x] 15. Enable multi-stem transcription
  - [x] 15.1 Deploy Lambda functions
    - Deploy confirm-transcription-mode Lambda
    - Deploy confirm-key Lambda
    - Configure API Gateway endpoints
    - Test endpoints with curl/Postman
    - **Complexity**: Medium
    - **Dependencies**: 4.4, 5.4, 6.1, 6.2
    - **Requirements**: 5.1, 6.3
  
  - [x] 15.2 Deploy frontend updates
    - Build frontend with new components
    - Deploy to hosting (S3/CloudFront or similar)
    - Test mode selector UI
    - Test key confirmation UI
    - **Complexity**: Medium
    - **Dependencies**: 8.5, 9.6, 10.4
    - **Requirements**: All frontend requirements
  
  - [x] 15.3 Update environment variables for Phase 2
    - Set ENABLE_MULTI_STEM=true
    - Keep ENABLE_LYRICS=false (enable in Phase 3)
    - **Complexity**: Small
    - **Requirements**: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7
  
  - [x] 15.4 Deploy updated ECS task
    - Build and push Docker image (v3.0-phase2)
    - Update ECS task definition
    - Deploy to development environment
    - **Complexity**: Small
    - **Dependencies**: 15.3
    - **Requirements**: 10.3

  - [x] 15.5 Validate Phase 2 deployment
    - Test all transcription modes
    - Verify stem files uploaded to S3
    - Verify piano and guitar transcription
    - Test timeout behavior (5 min default)
    - Monitor processing times
    - **Complexity**: Large
    - **Dependencies**: 15.4
    - **Requirements**: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 5.1-5.8

- [x] 16. Enable lyrics and key confirmation (Phase 3)
  - [x] 16.1 Add GENIUS_ACCESS_TOKEN to Secrets Manager
    - Create secret in AWS Secrets Manager
    - Grant ECS task role access to secret
    - Test secret retrieval in ECS task
    - **Complexity**: Small
    - **Requirements**: 10.1, 10.5
  
  - [x] 16.2 Update environment variables for Phase 3
    - Set ENABLE_LYRICS=true
    - Verify GENIUS_ACCESS_TOKEN is accessible
    - **Complexity**: Small
    - **Dependencies**: 16.1
    - **Requirements**: 4.7
  
  - [x] 16.3 Deploy updated ECS task
    - Build and push Docker image (v3.0-phase3)
    - Update ECS task definition
    - Deploy to development environment
    - **Complexity**: Small
    - **Dependencies**: 16.2
    - **Requirements**: 10.3
  
  - [x] 16.4 Validate Phase 3 deployment
    - Test song identification
    - Verify lyrics fetching from Genius
    - Test key detection and confirmation
    - Verify lyrics in PDF output
    - Test complete end-to-end workflow
    - **Complexity**: Large
    - **Dependencies**: 16.3
    - **Requirements**: 3.1-3.4, 4.1-4.7, 6.1-6.7

### Phase 7: Phase 4 Optimization and Monitoring

- [ ] 17. Performance optimization
  - [ ] 17.1 Profile ECS task execution
    - Add timing metrics for each stage
    - Identify bottlenecks
    - Log processing times to CloudWatch
    - **Complexity**: Medium
    - **Requirements**: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6
  
  - [ ] 17.2 Optimize stem separation
    - Implement parallel processing if possible
    - Tune Demucs parameters for speed
    - Cache model files in Docker image
    - **Complexity**: Large
    - **Requirements**: 8.3
  
  - [ ] 17.3 Optimize transcription
    - Implement parallel stem transcription
    - Tune Basic Pitch parameters
    - Cache model files in Docker image
    - **Complexity**: Large
    - **Requirements**: 8.4
  
  - [ ] 17.4 Optimize lyrics fetching
    - Implement parallel fetching with transcription
    - Add caching for repeated songs
    - Reduce timeout if needed
    - **Complexity**: Medium
    - **Requirements**: 8.6
  
  - [ ] 17.5 Validate performance targets
    - Bass-only: < 3 minutes for 4-minute song
    - Bass+piano/guitar: < 5 minutes
    - All stems: < 8 minutes
    - **Complexity**: Medium
    - **Dependencies**: 17.1, 17.2, 17.3, 17.4
    - **Requirements**: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6

- [ ] 18. Monitoring and observability
  - [ ] 18.1 Set up CloudWatch custom metrics
    - Add TranscriptionMode metric (dimension: mode)
    - Add ProcessingTime metric (dimension: stage)
    - Add StemSeparationSuccess metric
    - Add LyricsFetchSuccess metric
    - Add KeyDetectionConfidence metric
    - Add UserConfirmationTimeout metric
    - **Complexity**: Medium
    - **Requirements**: 10.5
  
  - [ ] 18.2 Implement structured logging
    - Log all processing steps with context
    - Use JSON format for logs
    - Include jobId, stage, duration, success in all logs
    - **Complexity**: Small
    - **Requirements**: 10.5
  
  - [ ] 18.3 Create CloudWatch dashboards
    - Create dashboard for processing metrics
    - Add graphs for processing times by mode
    - Add graphs for success rates
    - Add graphs for user confirmation timeouts
    - **Complexity**: Medium
    - **Dependencies**: 18.1, 18.2
    - **Requirements**: 10.5
  
  - [ ] 18.4 Set up CloudWatch alarms
    - Alarm for ECS task failure rate > 5%
    - Alarm for processing time > 15 minutes (timeout)
    - Alarm for stem separation failure rate > 10%
    - Alarm for DynamoDB throttling
    - **Complexity**: Medium
    - **Dependencies**: 18.1
    - **Requirements**: 9.5, 9.6

- [ ] 19. Production deployment
  - [ ] 19.1 Deploy to production environment
    - Deploy Lambda functions to production
    - Deploy frontend to production
    - Deploy ECS task to production
    - Update production environment variables
    - **Complexity**: Medium
    - **Dependencies**: All previous tasks
    - **Requirements**: All
  
  - [ ] 19.2 Smoke test production
    - Upload test audio files
    - Test all transcription modes
    - Test lyrics integration
    - Test key confirmation
    - Verify PDF generation
    - **Complexity**: Medium
    - **Dependencies**: 19.1
    - **Requirements**: All
  
  - [ ] 19.3 Monitor production metrics
    - Watch CloudWatch dashboards
    - Monitor error rates
    - Monitor processing times
    - Check user feedback
    - **Complexity**: Small
    - **Dependencies**: 19.2
    - **Requirements**: 10.5

- [ ] 20. Documentation and handoff
  - [ ] 20.1 Update API documentation
    - Document new endpoints
    - Document new job statuses
    - Document new DynamoDB fields
    - Document new S3 structure
    - **Complexity**: Medium
    - **Requirements**: All

  - [ ] 20.2 Create user guide
    - Document transcription mode selection
    - Document key confirmation workflow
    - Document lyrics feature
    - Add screenshots and examples
    - **Complexity**: Medium
    - **Requirements**: All
  
  - [ ] 20.3 Create developer guide
    - Document architecture changes
    - Document new modules and their interfaces
    - Document deployment process
    - Document troubleshooting steps
    - **Complexity**: Large
    - **Requirements**: All
  
  - [ ] 20.4 Create runbook for operations
    - Document monitoring procedures
    - Document common issues and solutions
    - Document rollback procedures
    - Document scaling considerations
    - **Complexity**: Medium
    - **Requirements**: All

---

## Success Criteria

The v3.0 implementation will be considered successful when:

1. **Accuracy**: 8th note quantization reduces false positives by 30% compared to v2.0
2. **Features**: All 4 transcription modes (bass-only, bass+piano, bass+guitar, all) work reliably
3. **Metadata**: 80%+ of songs are correctly identified with metadata
4. **Lyrics**: 70%+ of songs have lyrics displayed in PDF output
5. **Performance**: Processing times meet targets:
   - Bass-only: < 3 minutes for 4-minute song
   - Bass+piano/guitar: < 5 minutes
   - All stems: < 8 minutes
6. **Reliability**: < 5% failure rate across all modes
7. **Compatibility**: Zero breaking changes to v2.0 API - existing clients continue to work
8. **User Experience**: Confirmation workflows complete in < 1 minute on average
9. **Testing**: All unit tests pass with >80% coverage
10. **Monitoring**: CloudWatch dashboards show healthy metrics

---

## Notes

- Each task references specific requirements from requirements.md for traceability
- Tasks are organized by implementation phase following the migration strategy
- Dependencies are clearly marked to ensure proper implementation order
- Complexity estimates help with sprint planning and resource allocation
- Checkpoints at end of each phase ensure incremental validation
- Focus on backward compatibility ensures smooth migration from v2.0
- Graceful degradation ensures system continues to work even when optional features fail


# Requirements Document: v3.0 ChordScout Accuracy Improvements

## Introduction

ChordScout v3.0 addresses critical accuracy issues in the music transcription pipeline by improving quantization granularity, adding multi-stem harmonic context, integrating song metadata and lyrics, and implementing user confirmation workflows. This version maintains backward compatibility with v2.0 while significantly enhancing transcription quality and user control.

## Glossary

- **ChordScout**: The music transcription application system
- **Bass_Transcription_Pipeline**: The core processing system that analyzes audio and generates transcriptions
- **Quantization_Engine**: The component that aligns detected notes to rhythmic grid positions
- **Stem_Separator**: The component that separates audio into individual instrument tracks using Demucs
- **Note_Transcriber**: The component that converts audio to MIDI notes using Basic Pitch
- **Song_Identifier**: The component that identifies songs from audio fingerprints
- **Lyrics_Fetcher**: The component that retrieves lyrics from the Genius API
- **NNS_Generator**: The Nashville Number System chart generation component
- **User_Confirmation_Flow**: Interactive workflow requiring user input before proceeding
- **Transcription_Mode**: User-selected option for which stems to transcribe (bass-only, bass+piano, bass+guitar, all)
- **8th_Note_Grid**: Rhythmic quantization grid with 8th note resolution
- **16th_Note_Grid**: Rhythmic quantization grid with 16th note resolution (v2.0 legacy)
- **Harmonic_Context**: Chord and melodic information from piano and guitar stems
- **Downbeat**: The first beat of a musical measure
- **Key_Detection**: The process of determining the musical key from transcribed notes
- **Genius_API**: Third-party service for song metadata and lyrics retrieval

## Requirements

### Requirement 1: 8th Note Quantization

**User Story:** As a bass player, I want transcriptions quantized to 8th notes instead of 16th notes, so that the notation matches typical bass line rhythms and reduces false positives from over-granular quantization.

#### Acceptance Criteria

1. THE Quantization_Engine SHALL align all detected bass notes to an 8th_Note_Grid
2. WHEN processing bass audio, THE Note_Transcriber SHALL use 8th note time resolution
3. FOR ALL bass transcriptions, quantizing to 8th notes then re-quantizing to 8th notes SHALL produce identical results (idempotence property)
4. THE Bass_Transcription_Pipeline SHALL NOT use 16th_Note_Grid for new v3.0 transcriptions
5. WHEN a v2.0 transcription is reprocessed, THE ChordScout SHALL apply 8th_Note_Grid quantization

### Requirement 2: Multi-Stem Transcription Support

**User Story:** As a musician, I want the system to transcribe piano and guitar parts in addition to bass, so that harmonic context improves chord detection accuracy.

#### Acceptance Criteria

1. WHEN audio is uploaded, THE Stem_Separator SHALL separate the audio into bass, piano, guitar, drums, and vocals stems
2. WHERE Transcription_Mode includes piano, THE Note_Transcriber SHALL transcribe the piano stem with 8th_Note_Grid quantization
3. WHERE Transcription_Mode includes guitar, THE Note_Transcriber SHALL transcribe the guitar stem with 8th_Note_Grid quantization
4. THE Stem_Separator SHALL use the Demucs mdx_extra model for separation
5. WHEN stem separation completes, THE ChordScout SHALL store all separated stems in S3
6. FOR ALL transcribed stems, THE Note_Transcriber SHALL output MIDI note data with pitch, onset time, and duration
7. THE Bass_Transcription_Pipeline SHALL provide Harmonic_Context from piano and guitar stems to the chord detection algorithm

### Requirement 3: Song Identification and Metadata

**User Story:** As a user, I want the system to automatically identify songs and retrieve metadata, so that I can see song titles, artists, and album information on my transcriptions.

#### Acceptance Criteria

1. WHEN audio is uploaded, THE Song_Identifier SHALL attempt to identify the song using audio fingerprinting
2. WHEN a song is identified, THE Song_Identifier SHALL retrieve title, artist, and album metadata
3. IF song identification fails, THEN THE ChordScout SHALL proceed with transcription using "Unknown Song" as the title
4. THE Song_Identifier SHALL complete identification within 30 seconds
5. WHEN metadata is retrieved, THE ChordScout SHALL store it in DynamoDB with the job record
6. THE NNS_Generator SHALL include song metadata in generated PDF charts

### Requirement 4: Lyrics Integration

**User Story:** As a musician, I want lyrics displayed on my chord charts, so that I can see chord changes aligned with the words being sung.

#### Acceptance Criteria

1. WHEN a song is identified, THE Lyrics_Fetcher SHALL retrieve lyrics from Genius_API
2. IF lyrics are unavailable, THEN THE ChordScout SHALL generate charts without lyrics overlay
3. THE Lyrics_Fetcher SHALL parse lyrics into lines and sections (verse, chorus, bridge)
4. WHEN lyrics are retrieved, THE ChordScout SHALL store them in DynamoDB with the job record
5. THE NNS_Generator SHALL align lyrics with chord changes based on timing information
6. WHERE lyrics are available, THE NNS_Generator SHALL include lyrics in the PDF output
7. THE Lyrics_Fetcher SHALL require a valid GENIUS_ACCESS_TOKEN environment variable

### Requirement 5: Transcription Mode Selection

**User Story:** As a user, I want to choose which instruments to transcribe, so that I can control processing time and focus on the parts I need.

#### Acceptance Criteria

1. WHEN tempo and downbeat detection complete, THE ChordScout SHALL present a User_Confirmation_Flow for Transcription_Mode selection
2. THE ChordScout SHALL offer four Transcription_Mode options: bass-only, bass+piano, bass+guitar, all
3. WHEN the user selects bass-only, THE Bass_Transcription_Pipeline SHALL transcribe only the bass stem
4. WHEN the user selects bass+piano, THE Bass_Transcription_Pipeline SHALL transcribe bass and piano stems
5. WHEN the user selects bass+guitar, THE Bass_Transcription_Pipeline SHALL transcribe bass and guitar stems
6. WHEN the user selects all, THE Bass_Transcription_Pipeline SHALL transcribe bass, piano, and guitar stems
7. THE ChordScout SHALL store the selected Transcription_Mode in DynamoDB with the job record
8. IF the user does not respond within 5 minutes, THEN THE ChordScout SHALL default to bass-only mode

### Requirement 6: Key Confirmation Workflow

**User Story:** As a musician, I want to confirm or correct the detected musical key, so that the Nashville Number System notation is accurate for my song.

#### Acceptance Criteria

1. WHEN transcription completes, THE Key_Detection SHALL analyze transcribed notes to determine the musical key
2. WHEN a key is detected, THE ChordScout SHALL present a User_Confirmation_Flow displaying the detected key
3. THE ChordScout SHALL allow the user to confirm the detected key or select a different key
4. THE ChordScout SHALL offer all 24 possible keys (12 major, 12 minor) for selection
5. WHEN the user confirms or selects a key, THE NNS_Generator SHALL use that key for chart generation
6. THE ChordScout SHALL store the confirmed key in DynamoDB with the job record
7. IF the user does not respond within 5 minutes, THEN THE ChordScout SHALL use the detected key

### Requirement 7: Backward Compatibility

**User Story:** As an existing user, I want v3.0 to support my existing v2.0 workflows, so that I can continue using bass-only transcription without disruption.

#### Acceptance Criteria

1. WHERE Transcription_Mode is bass-only, THE Bass_Transcription_Pipeline SHALL execute the same processing steps as v2.0
2. THE ChordScout SHALL support v2.0 API endpoints for backward compatibility
3. WHEN a v2.0 client uploads audio, THE ChordScout SHALL process it using v3.0 improvements with bass-only mode
4. THE ChordScout SHALL maintain the same DynamoDB schema with additional optional fields for v3.0 features
5. THE ChordScout SHALL maintain the same S3 bucket structure with additional paths for stem audio files

### Requirement 8: Performance Requirements

**User Story:** As a user, I want transcription to complete in a reasonable time, so that I can quickly get my chord charts.

#### Acceptance Criteria

1. WHEN processing bass-only mode, THE Bass_Transcription_Pipeline SHALL complete within 3 minutes for a 4-minute song
2. WHEN processing all stems mode, THE Bass_Transcription_Pipeline SHALL complete within 8 minutes for a 4-minute song
3. THE Stem_Separator SHALL process audio at a rate of at least 0.5x realtime on ECS infrastructure
4. THE Note_Transcriber SHALL process each stem at a rate of at least 1.0x realtime
5. THE Song_Identifier SHALL complete identification within 30 seconds
6. THE Lyrics_Fetcher SHALL retrieve lyrics within 10 seconds

### Requirement 9: Error Handling and Resilience

**User Story:** As a user, I want the system to handle errors gracefully, so that I receive useful feedback when something goes wrong.

#### Acceptance Criteria

1. IF stem separation fails, THEN THE ChordScout SHALL fall back to bass-only transcription and notify the user
2. IF song identification fails, THEN THE ChordScout SHALL proceed with transcription using default metadata
3. IF lyrics retrieval fails, THEN THE ChordScout SHALL generate charts without lyrics
4. IF Key_Detection produces no result, THEN THE ChordScout SHALL default to C major and notify the user
5. WHEN any processing step fails, THE ChordScout SHALL log the error with context to CloudWatch
6. WHEN a critical error occurs, THE ChordScout SHALL update the job status to "failed" with an error message
7. THE ChordScout SHALL retry transient failures up to 3 times with exponential backoff

### Requirement 10: Configuration and Deployment

**User Story:** As a developer, I want clear configuration requirements, so that I can deploy v3.0 successfully.

#### Acceptance Criteria

1. THE ChordScout SHALL require GENIUS_ACCESS_TOKEN environment variable for lyrics functionality
2. THE Bass_Transcription_Pipeline SHALL include mutagen, requests, and beautifulsoup4 dependencies
3. THE ChordScout SHALL use the same ECS task definition structure as v2.0 with updated Docker image
4. WHEN deployed, THE ChordScout SHALL expose health check endpoints for ECS monitoring
5. THE ChordScout SHALL log all processing steps to CloudWatch with structured JSON format
6. THE ChordScout SHALL use the same IAM roles and permissions as v2.0 with added S3 permissions for stem storage

### Requirement 11: Data Integrity and Correctness

**User Story:** As a developer, I want to ensure data correctness throughout the pipeline, so that users receive accurate transcriptions.

#### Acceptance Criteria

1. FOR ALL audio processing, THE ChordScout SHALL preserve the original sample rate and bit depth metadata
2. FOR ALL note transcriptions, onset times SHALL be non-negative and within the audio duration
3. FOR ALL note transcriptions, note durations SHALL be positive values
4. FOR ALL quantized notes, positions SHALL align exactly to the 8th_Note_Grid boundaries
5. FOR ALL MIDI output, pitch values SHALL be integers between 0 and 127
6. WHEN storing transcription data, THE ChordScout SHALL validate JSON schema before writing to DynamoDB
7. FOR ALL stem separation operations, the sum of stem durations SHALL equal the original audio duration within 100ms tolerance

### Requirement 12: Parser and Serializer Requirements

**User Story:** As a developer, I want robust parsing and serialization of transcription data, so that data integrity is maintained throughout the pipeline.

#### Acceptance Criteria

1. WHEN Basic Pitch outputs MIDI data, THE Note_Transcriber SHALL parse it into structured note objects with pitch, onset, and duration
2. WHEN storing transcription results, THE ChordScout SHALL serialize note data to JSON format
3. THE ChordScout SHALL include a Pretty_Printer that formats transcription data back into human-readable JSON
4. FOR ALL valid transcription objects, parsing JSON then serializing then parsing SHALL produce equivalent objects (round-trip property)
5. WHEN parsing MIDI data, THE Note_Transcriber SHALL validate that all required fields are present
6. IF MIDI parsing fails, THEN THE Note_Transcriber SHALL return a descriptive error with the invalid data location
7. THE ChordScout SHALL validate all JSON payloads against defined schemas before processing

## Non-Functional Requirements

### Maintainability
- Code SHALL follow existing ChordScout Python style conventions
- All new modules SHALL include unit tests with >80% coverage
- All new API endpoints SHALL include integration tests

### Scalability
- The system SHALL support concurrent processing of up to 10 jobs on ECS
- S3 storage SHALL accommodate stem files (4x original audio size per job)

### Security
- GENIUS_ACCESS_TOKEN SHALL be stored in AWS Secrets Manager or environment variables
- All API calls to external services SHALL use HTTPS
- User-uploaded audio SHALL be deleted from S3 after 7 days

### Observability
- All processing steps SHALL emit CloudWatch metrics for duration and success rate
- Failed jobs SHALL include stack traces in CloudWatch logs
- User confirmation workflows SHALL track response times and timeout rates

## Integration Points

### v2.0 System Integration
- Reuse existing tempo detection, time signature detection, and downbeat detection modules
- Reuse existing DynamoDB schema with additive changes only
- Reuse existing S3 bucket structure with new prefixes for stems
- Reuse existing PDF generation infrastructure with enhanced input data

### External Service Integration
- Genius API for song identification and lyrics (requires API token)
- Demucs model files (downloaded during Docker image build)
- Basic Pitch model files (downloaded during Docker image build)

### Frontend Integration
- New job statuses: "awaiting_mode_selection", "awaiting_key_confirmation"
- New DynamoDB fields: transcription_mode, detected_key, confirmed_key, lyrics, song_metadata
- New S3 paths: stems/{job_id}/{stem_name}.wav

## Success Criteria

The v3.0 system will be considered successful when:
1. Bass transcription accuracy improves by reducing false 16th note detections
2. Chord detection accuracy improves with multi-stem harmonic context
3. Users can successfully select transcription modes and confirm keys
4. Song metadata and lyrics appear correctly on generated charts
5. All v2.0 bass-only workflows continue to function without modification
6. Processing times remain within acceptable limits for user experience

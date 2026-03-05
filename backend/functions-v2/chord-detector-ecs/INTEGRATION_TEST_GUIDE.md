# Integration Test Guide - v3.0 ChordScout

This guide provides instructions for running integration tests for the v3.0 ChordScout accuracy improvements.

## Overview

The integration tests validate the complete v3.0 feature set including:
- Bass-only mode (v2.0 compatibility)
- Multi-stem transcription (bass+piano, bass+guitar, all)
- Key confirmation workflow
- Lyrics integration
- Error handling and resilience
- Data integrity
- Parser and serializer functionality

## Test Files

### 1. Bass-Only Mode Tests
**File**: `test_integration_bass_only.py`

Tests v2.0 compatibility and 8th note quantization:
- Bass transcription with 8th note quantization
- Idempotence property (quantize twice = same result)
- 8th note grid alignment
- No 16th note quantization
- Measure and beat calculations
- Output format compatibility
- Data integrity

**Run**:
```bash
pytest test_integration_bass_only.py -v
```

### 2. Mode Selection Workflow Tests
**File**: `test_integration_mode_selection.py`

Tests transcription mode selection:
- Bass-only mode
- Bass+piano mode
- Bass+guitar mode
- All stems mode
- 8th note quantization for all stems
- Mode validation
- Timeout defaults to bass-only
- API response format
- Parallel stem transcription

**Run**:
```bash
pytest test_integration_mode_selection.py -v
```

### 3. Key Confirmation Workflow Tests
**File**: `test_integration_key_confirmation.py`

Tests key detection and confirmation:
- Key detection from notes
- All 24 keys available
- Key confirmation and correction
- Timeout uses detected key
- NNS generation uses confirmed key
- Key confidence storage
- Key format validation

**Run**:
```bash
pytest test_integration_key_confirmation.py -v
```

### 4. Lyrics Integration Tests
**File**: `test_integration_lyrics.py`

Tests lyrics fetching and integration:
- Lyrics fetch from Genius API
- Graceful degradation on failure
- Section parsing (verse, chorus, bridge)
- Alignment to measure boundaries
- Storage format
- PDF integration
- Special characters handling
- Long lyrics handling

**Run**:
```bash
pytest test_integration_lyrics.py -v
```

### 5. Error Handling Tests
**File**: `test_integration_error_handling.py`

Tests error handling and resilience:
- Stem separation failure fallback
- Song identification failure
- Lyrics fetch failure
- Key detection failure
- Individual stem transcription failure
- DynamoDB write retry
- S3 upload retry
- Timeout handling
- Invalid/corrupted audio handling
- Error logging

**Run**:
```bash
pytest test_integration_error_handling.py -v
```

### 6. Data Integrity Tests
**File**: `test_integration_data_integrity.py`

Tests data correctness requirements:
- Note onset times non-negative
- Note durations positive
- Quantized positions align to 8th note grid
- MIDI pitch values 0-127
- Velocity values 0.0-1.0
- Measure numbers positive
- Beat numbers within time signature
- Subdivision values valid (1 or 2)
- Note ordering by time
- No duplicate notes
- JSON schema validation

**Run**:
```bash
pytest test_integration_data_integrity.py -v
```

### 7. Parser and Serializer Tests
**File**: `test_integration_parser_serializer.py`

Tests parsing and serialization:
- MIDI to JSON parsing
- JSON serialization
- Round-trip property (parse → serialize → parse)
- Missing fields validation
- Invalid types validation
- Numpy types handling
- Pretty print formatting
- Error handling
- Special values handling
- Data format conversions (MIDI ↔ note names, time ↔ measure/beat)

**Run**:
```bash
pytest test_integration_parser_serializer.py -v
```

## Running All Tests

### Run All Integration Tests
```bash
pytest test_integration_*.py -v
```

### Run with Coverage
```bash
pytest test_integration_*.py -v --cov=. --cov-report=html
```

### Run Specific Test Class
```bash
pytest test_integration_bass_only.py::TestBassOnlyMode -v
```

### Run Specific Test Method
```bash
pytest test_integration_bass_only.py::TestBassOnlyMode::test_bass_transcription_8th_note_quantization -v
```

## Test Environment Setup

### Prerequisites
1. Python 3.9+
2. Required dependencies installed:
   ```bash
   pip install -r requirements-test.txt
   ```

### Environment Variables
For lyrics tests, set:
```bash
export GENIUS_ACCESS_TOKEN="your_genius_api_token"
```

### Test Data
Some tests use synthetic audio generated with numpy. For full integration testing with real audio files:

1. Place test audio files in `test_data/` directory
2. Update test paths in test files
3. Run tests with real audio:
   ```bash
   pytest test_integration_*.py -v --use-real-audio
   ```

## Manual Integration Testing

For end-to-end manual testing:

### 1. Bass-Only Mode (v2.0 Compatibility)
```bash
# Upload test audio
curl -X POST https://api.chordscout.com/upload \
  -F "file=@test_audio.mp3"

# Monitor job status
curl https://api.chordscout.com/jobs/{jobId}

# Verify:
# - Bass transcription completes
# - 8th note quantization applied
# - PDF generated
# - No breaking changes from v2.0
```

### 2. Mode Selection Workflow
```bash
# Upload audio
curl -X POST https://api.chordscout.com/upload \
  -F "file=@test_audio.mp3"

# Wait for PENDING_MODE_SELECTION status
curl https://api.chordscout.com/jobs/{jobId}

# Select mode
curl -X POST https://api.chordscout.com/jobs/{jobId}/confirm-mode \
  -H "Content-Type: application/json" \
  -d '{"transcriptionMode": "bass+piano"}'

# Verify:
# - Correct stems transcribed
# - Processing continues
# - Results include selected stems
```

### 3. Key Confirmation Workflow
```bash
# Wait for PENDING_KEY_CONFIRMATION status
curl https://api.chordscout.com/jobs/{jobId}

# Confirm or correct key
curl -X POST https://api.chordscout.com/jobs/{jobId}/confirm-key \
  -H "Content-Type: application/json" \
  -d '{"confirmedKey": "G major"}'

# Verify:
# - NNS uses confirmed key
# - PDF shows correct key
```

### 4. Timeout Testing
```bash
# Upload audio
curl -X POST https://api.chordscout.com/upload \
  -F "file=@test_audio.mp3"

# Wait for PENDING_MODE_SELECTION
# DO NOT confirm (wait 5+ minutes)

# Verify:
# - Job defaults to bass-only mode
# - Processing continues automatically
```

## Expected Results

### Success Criteria
- ✅ All unit tests pass
- ✅ Bass-only mode works identically to v2.0
- ✅ 8th note quantization applied (not 16th)
- ✅ Multi-stem transcription works for all modes
- ✅ Key confirmation workflow completes
- ✅ Lyrics appear in PDF when available
- ✅ Graceful degradation on failures
- ✅ Data integrity maintained
- ✅ Round-trip parsing works

### Performance Targets
- Bass-only: < 3 minutes for 4-minute song
- Bass+piano/guitar: < 5 minutes
- All stems: < 8 minutes

### Failure Handling
- Stem separation failure → fallback to bass-only
- Song identification failure → use filename
- Lyrics fetch failure → continue without lyrics
- Key detection failure → default to C major

## Troubleshooting

### Tests Fail with Import Errors
```bash
# Ensure all dependencies installed
pip install -r requirements-test.txt

# Ensure modules are in Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Tests Fail with Audio Processing Errors
```bash
# Check librosa and soundfile installed
pip install librosa soundfile

# Check audio file format
file test_audio.mp3
```

### Tests Timeout
```bash
# Increase timeout for slow operations
pytest test_integration_*.py -v --timeout=300
```

### Genius API Tests Fail
```bash
# Check API token is set
echo $GENIUS_ACCESS_TOKEN

# Check API rate limits
# Genius API: 1000 requests per day
```

## Continuous Integration

### GitHub Actions Workflow
```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install -r requirements-test.txt
      - name: Run integration tests
        run: |
          pytest test_integration_*.py -v --cov=. --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Test Maintenance

### Adding New Tests
1. Create test file: `test_integration_<feature>.py`
2. Follow existing test structure
3. Add to this documentation
4. Update CI workflow if needed

### Updating Tests
1. Update test file
2. Run tests locally
3. Update documentation
4. Commit changes

### Test Data Management
- Keep test audio files small (< 1MB)
- Use synthetic audio when possible
- Document test data requirements
- Version control test data or use fixtures

## Contact

For questions or issues with integration tests:
- Check existing test documentation
- Review test output for error messages
- Check CloudWatch logs for ECS task errors
- Contact development team

## References

- [v3.0 Requirements](../../../.kiro/specs/v3-accuracy-improvements/requirements.md)
- [v3.0 Design](../../../.kiro/specs/v3-accuracy-improvements/design.md)
- [v3.0 Tasks](../../../.kiro/specs/v3-accuracy-improvements/tasks.md)
- [Unit Test Results](./test_results/)

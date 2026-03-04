# Systematic Troubleshooting Plan

## Current Issues Identified

1. **Chord symbols corrupted**: `A !' F# !' A !' D !' E !' E` instead of proper chord names
2. **No lyrics**: Lyrics extraction not working or not being included
3. **Pattern-only display**: Showing chord patterns instead of full song structure
4. **Key signature inaccurate**: Key detection producing wrong results
5. **Cannot verify downbeat**: Not enough accurate data to validate downbeat detection
6. **Chord accuracy unverifiable**: Cannot determine if detected chords are correct
7. **Missing NNS numbers**: Nashville Number System notation not appearing in output

## Root Cause Analysis

These issues suggest a **data pipeline corruption** - likely the chord detection output format has changed or is being incorrectly parsed/stored.

## Troubleshooting Strategy

### Phase 1: Inspect Raw Data (15 minutes)
**Goal**: See exactly what data is being stored in DynamoDB

1. Get the most recent job ID from your test
2. Query DynamoDB directly to see raw `chordsData` structure
3. Check ECS logs to see what the chord detector is outputting
4. Compare with expected format

### Phase 2: Isolate the Problem Layer (20 minutes)
**Goal**: Determine where corruption happens

Test each layer independently:
1. **Chord Detection Output**: Does ECS task produce correct data?
2. **DynamoDB Storage**: Is data stored correctly?
3. **API Retrieval**: Does API return correct data?
4. **Frontend Parsing**: Does frontend parse correctly?
5. **PDF Generation**: Does PDF generator handle data correctly?

### Phase 3: Fix Root Cause (30-60 minutes)
**Goal**: Fix the identified issue

Based on findings, fix the specific layer causing corruption.

### Phase 4: Verify End-to-End (15 minutes)
**Goal**: Confirm all issues resolved

Test with a known-good audio file and verify:
- Chord symbols are correct
- Lyrics are present
- Full song structure (not just patterns)
- Key signature is accurate
- Downbeat alignment is correct

## Immediate Action: Data Inspection

Let's start by inspecting the actual data from your recent test.

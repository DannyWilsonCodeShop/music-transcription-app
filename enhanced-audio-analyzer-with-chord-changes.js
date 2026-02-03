// Enhanced Audio Analyzer with Chord Change Detection
// Solves DynamoDB size limit by storing only chord changes instead of all detections

const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, UpdateCommand } = require('@aws-sdk/lib-dynamodb');

const dynamoClient = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(dynamoClient);

const JOBS_TABLE = process.env.DYNAMODB_JOBS_TABLE || 'ChordScout-Jobs-dev';

exports.handler = async (event) => {
  console.log('🎵 Enhanced Audio Analyzer with Chord Change Detection', JSON.stringify(event, null, 2));
  
  try {
    const { audioUrl, jobId } = event;
    
    if (!jobId) {
      throw new Error('Missing jobId in event');
    }
    
    // Step 1: Perform high-resolution chord analysis (0.2s intervals)
    console.log('🎼 Performing high-resolution chord analysis...');
    const rawChordAnalysis = await performHighResolutionChordAnalysis(audioUrl);
    
    console.log(`📊 Raw analysis: ${rawChordAnalysis.chords.length} chord detections`);
    
    // Step 2: Detect actual chord changes
    console.log('🔍 Detecting chord changes...');
    const chordChangeResult = detectChordChanges(rawChordAnalysis.chords, rawChordAnalysis.timeSignature);
    
    console.log(`✅ Found ${chordChangeResult.chordChanges.length} chord changes`);
    console.log(`📉 Data reduction: ${chordChangeResult.summary.dataReduction}%`);
    
    // Step 3: Consolidate chord changes per measure (max 8 per measure)
    const consolidatedChanges = consolidateChordChangesPerMeasure(chordChangeResult.chordChanges, 8);
    
    // Step 4: Create measure-based structure for PDF generation
    const measureStructure = createMeasureBasedChordStructure(consolidatedChanges, rawChordAnalysis.timeSignature);
    
    // Step 5: Prepare compact data for DynamoDB storage
    const compactChordData = {
      chordChanges: consolidatedChanges,
      measures: measureStructure,
      summary: {
        totalChanges: consolidatedChanges.length,
        totalMeasures: measureStructure.length,
        originalDetections: rawChordAnalysis.chords.length,
        dataReduction: chordChangeResult.summary.dataReduction,
        analysisInterval: rawChordAnalysis.analysisInterval
      },
      analysis: {
        tempo: rawChordAnalysis.tempo,
        key: rawChordAnalysis.key,
        timeSignature: rawChordAnalysis.timeSignature
      }
    };
    
    // Step 6: Verify data size is under DynamoDB limit
    const dataSize = JSON.stringify(compactChordData).length;
    console.log(`📏 Compact data size: ${dataSize} bytes`);
    
    if (dataSize >= 400000) {
      throw new Error(`Data still too large for DynamoDB: ${dataSize} bytes`);
    }
    
    // Step 7: Store compact chord data in DynamoDB
    await docClient.send(new UpdateCommand({
      TableName: JOBS_TABLE,
      Key: { jobId },
      UpdateExpression: 'SET chords = :chords, #key = :key, tempo = :tempo, timeSignature = :timeSignature, #status = :status, progress = :progress, updatedAt = :updated',
      ExpressionAttributeNames: {
        '#key': 'key',
        '#status': 'status'
      },
      ExpressionAttributeValues: {
        ':chords': compactChordData.chordChanges, // Store chord changes array for PDF compatibility
        ':key': `${rawChordAnalysis.key.root} ${rawChordAnalysis.key.mode}`,
        ':tempo': rawChordAnalysis.tempo.bpm,
        ':timeSignature': `${rawChordAnalysis.timeSignature.numerator}/${rawChordAnalysis.timeSignature.denominator}`,
        ':status': 'CHORD_ANALYSIS_COMPLETE',
        ':progress': 70,
        ':updated': new Date().toISOString()
      }
    }));
    
    console.log('✅ Compact chord data stored in DynamoDB');
    
    return {
      statusCode: 200,
      body: {
        message: 'Chord analysis completed with change detection',
        jobId: jobId,
        chordChanges: consolidatedChanges.length,
        measures: measureStructure.length,
        dataReduction: chordChangeResult.summary.dataReduction,
        dataSize: dataSize,
        dynamoDbCompatible: true
      }
    };
    
  } catch (error) {
    console.error('❌ Enhanced audio analysis failed:', error);
    
    // Update job status to failed
    await docClient.send(new UpdateCommand({
      TableName: JOBS_TABLE,
      Key: { jobId: event.jobId },
      UpdateExpression: 'SET #status = :status, error = :error, updatedAt = :updated',
      ExpressionAttributeNames: { '#status': 'status' },
      ExpressionAttributeValues: {
        ':status': 'FAILED',
        ':error': error.message,
        ':updated': new Date().toISOString()
      }
    }));
    
    throw error;
  }
};

// Chord change detection functions (same as in chord-change-detector.cjs)
function detectChordChanges(rawChordData, timeSignature) {
  const chordChanges = [];
  let currentChord = null;
  let chordStartTime = 0;
  let chordStartMeasure = 0;
  let chordStartBeat = 0;
  
  rawChordData.forEach((chord, index) => {
    const chordName = chord.chord || chord.name;
    const chordTime = chord.start || chord.time || chord.timestamp || (index * 0.2);
    
    const measureInfo = calculateMeasureAndBeat(chordTime, timeSignature);
    
    if (currentChord !== chordName) {
      if (currentChord !== null) {
        const chordChange = {
          chord: currentChord,
          nashvilleNumber: getPreviousNashvilleNumber(rawChordData, index - 1),
          time: chordStartTime, // Use 'time' field for PDF compatibility
          startTime: chordStartTime,
          endTime: chordTime,
          duration: chordTime - chordStartTime,
          measure: chordStartMeasure,
          beat: chordStartBeat,
          measurePosition: calculateMeasurePosition(chordStartTime, timeSignature),
          isDownbeat: chordStartBeat === 1,
          confidence: getPreviousConfidence(rawChordData, index - 1)
        };
        
        chordChanges.push(chordChange);
      }
      
      currentChord = chordName;
      chordStartTime = chordTime;
      chordStartMeasure = measureInfo.measure;
      chordStartBeat = measureInfo.beat;
    }
  });
  
  // Add final chord
  if (currentChord !== null && rawChordData.length > 0) {
    const lastChord = rawChordData[rawChordData.length - 1];
    const endTime = (lastChord.end || lastChord.start || lastChord.time || 0) + 0.2;
    
    chordChanges.push({
      chord: currentChord,
      nashvilleNumber: lastChord.nashvilleNumber || '?',
      time: chordStartTime,
      startTime: chordStartTime,
      endTime: endTime,
      duration: endTime - chordStartTime,
      measure: chordStartMeasure,
      beat: chordStartBeat,
      measurePosition: calculateMeasurePosition(chordStartTime, timeSignature),
      isDownbeat: chordStartBeat === 1,
      confidence: lastChord.confidence || 0.8
    });
  }
  
  const originalSize = JSON.stringify(rawChordData).length;
  const reducedSize = JSON.stringify(chordChanges).length;
  const reductionPercentage = ((originalSize - reducedSize) / originalSize * 100).toFixed(1);
  
  return {
    chordChanges: chordChanges,
    summary: {
      totalChanges: chordChanges.length,
      originalDetections: rawChordData.length,
      dataReduction: parseFloat(reductionPercentage),
      originalSize: originalSize,
      reducedSize: reducedSize
    }
  };
}

function consolidateChordChangesPerMeasure(chordChanges, maxChangesPerMeasure = 8) {
  const measureGroups = {};
  
  chordChanges.forEach(change => {
    const measure = change.measure;
    if (!measureGroups[measure]) {
      measureGroups[measure] = [];
    }
    measureGroups[measure].push(change);
  });
  
  const consolidatedChanges = [];
  
  Object.keys(measureGroups).forEach(measure => {
    const measureChanges = measureGroups[measure];
    
    if (measureChanges.length <= maxChangesPerMeasure) {
      consolidatedChanges.push(...measureChanges);
    } else {
      const sortedChanges = measureChanges.sort((a, b) => {
        const durationDiff = b.duration - a.duration;
        if (Math.abs(durationDiff) > 0.1) return durationDiff;
        return b.confidence - a.confidence;
      });
      
      const selectedChanges = sortedChanges.slice(0, maxChangesPerMeasure);
      selectedChanges.sort((a, b) => a.startTime - b.startTime);
      consolidatedChanges.push(...selectedChanges);
    }
  });
  
  consolidatedChanges.sort((a, b) => a.startTime - b.startTime);
  return consolidatedChanges;
}

function createMeasureBasedChordStructure(chordChanges, timeSignature) {
  const measures = {};
  
  chordChanges.forEach(change => {
    const measure = change.measure;
    
    if (!measures[measure]) {
      measures[measure] = {
        measureNumber: measure,
        chords: [],
        startTime: (measure - 1) * timeSignature.measureDuration,
        endTime: measure * timeSignature.measureDuration,
        timeSignature: `${timeSignature.numerator}/${timeSignature.denominator}`
      };
    }
    
    measures[measure].chords.push({
      chord: change.chord,
      nashvilleNumber: change.nashvilleNumber,
      beat: change.beat,
      measurePosition: change.measurePosition,
      duration: change.duration,
      isDownbeat: change.isDownbeat,
      confidence: change.confidence
    });
  });
  
  return Object.values(measures).sort((a, b) => a.measureNumber - b.measureNumber);
}

// Helper functions
function calculateMeasureAndBeat(time, timeSignature) {
  const { measureDuration, numerator } = timeSignature;
  const beatDuration = measureDuration / numerator;
  
  const measure = Math.floor(time / measureDuration) + 1;
  const timeInMeasure = time % measureDuration;
  const beat = Math.floor(timeInMeasure / beatDuration) + 1;
  
  return { measure, beat, timeInMeasure, beatDuration };
}

function calculateMeasurePosition(time, timeSignature) {
  const { measureDuration } = timeSignature;
  const timeInMeasure = time % measureDuration;
  return timeInMeasure / measureDuration;
}

function getPreviousNashvilleNumber(rawChordData, index) {
  if (index >= 0 && index < rawChordData.length) {
    return rawChordData[index].nashvilleNumber || '?';
  }
  return '?';
}

function getPreviousConfidence(rawChordData, index) {
  if (index >= 0 && index < rawChordData.length) {
    return rawChordData[index].confidence || 0.8;
  }
  return 0.8;
}

// Mock function for high-resolution chord analysis
async function performHighResolutionChordAnalysis(audioUrl) {
  // This would be replaced with actual chord analysis logic
  // For now, return mock data similar to the local analyzer
  
  const mockChords = [];
  const chordProgression = ['G', 'G', 'G', 'G', 'C', 'C', 'G', 'G', 'D', 'D', 'G', 'G'];
  
  for (let i = 0; i < 900; i++) {
    const time = i * 0.2;
    const chord = chordProgression[i % chordProgression.length];
    
    mockChords.push({
      chord: chord,
      start: time,
      end: time + 0.2,
      nashvilleNumber: convertChordToNashvilleNumber(chord, 'G', 'major'),
      confidence: 0.8 + Math.random() * 0.15,
      isDownbeat: (i % 15) === 0, // Every 3 seconds (15 * 0.2s)
      isPassingChord: (i % 15) !== 0
    });
  }
  
  return {
    chords: mockChords,
    analysisInterval: 0.2,
    tempo: { bpm: 120, confidence: 0.95 },
    key: { root: 'G', mode: 'major', confidence: 0.89 },
    timeSignature: { numerator: 3, denominator: 4, measureDuration: 1.5 }
  };
}

function convertChordToNashvilleNumber(chordName, keyRoot = 'G', keyMode = 'major') {
  const noteToSemitone = {
    'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5,
    'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11
  };

  const rootNote = chordName[0];
  const keySemitone = noteToSemitone[keyRoot] || 0;
  const chordSemitone = noteToSemitone[rootNote] || 0;

  let interval = (chordSemitone - keySemitone + 12) % 12;
  const majorNumbers = ['1', 'b2', '2', 'b3', '3', '4', 'b5', '5', 'b6', '6', 'b7', '7'];
  
  return majorNumbers[interval];
}
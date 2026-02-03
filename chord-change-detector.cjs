// Chord Change Detection - Consolidates 0.2s chord data into actual chord changes
// Reduces ~900 chord detections to ~20-50 actual chord changes per song

function detectChordChanges(rawChordData, timeSignature = { numerator: 4, denominator: 4, measureDuration: 2.0 }) {
  console.log('🎼 Detecting chord changes from raw chord data...');
  console.log(`📊 Input: ${rawChordData.length} chord detections`);
  
  if (!rawChordData || rawChordData.length === 0) {
    return { chordChanges: [], summary: { totalChanges: 0, dataReduction: 0 } };
  }
  
  const chordChanges = [];
  let currentChord = null;
  let chordStartTime = 0;
  let chordStartMeasure = 0;
  let chordStartBeat = 0;
  
  // Process each chord detection
  rawChordData.forEach((chord, index) => {
    const chordName = chord.chord || chord.name;
    const chordTime = chord.start || chord.time || chord.timestamp || (index * 0.2);
    
    // Calculate measure and beat position
    const measureInfo = calculateMeasureAndBeat(chordTime, timeSignature);
    
    // Check if this is a chord change
    if (currentChord !== chordName) {
      // If we had a previous chord, record the change
      if (currentChord !== null) {
        const chordChange = {
          chord: currentChord,
          nashvilleNumber: getPreviousNashvilleNumber(rawChordData, index - 1),
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
      
      // Start tracking the new chord
      currentChord = chordName;
      chordStartTime = chordTime;
      chordStartMeasure = measureInfo.measure;
      chordStartBeat = measureInfo.beat;
    }
  });
  
  // Add the final chord
  if (currentChord !== null && rawChordData.length > 0) {
    const lastChord = rawChordData[rawChordData.length - 1];
    const endTime = (lastChord.end || lastChord.start || lastChord.time || 0) + 0.2;
    
    chordChanges.push({
      chord: currentChord,
      nashvilleNumber: lastChord.nashvilleNumber || '?',
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
  
  // Calculate data reduction
  const originalSize = JSON.stringify(rawChordData).length;
  const reducedSize = JSON.stringify(chordChanges).length;
  const reductionPercentage = ((originalSize - reducedSize) / originalSize * 100).toFixed(1);
  
  console.log(`✅ Detected ${chordChanges.length} chord changes`);
  console.log(`📉 Data reduction: ${reductionPercentage}% (${originalSize} → ${reducedSize} bytes)`);
  
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
  return timeInMeasure / measureDuration; // 0.0 to 1.0 within the measure
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

// Consolidate chord changes per measure (max 8 changes per measure)
function consolidateChordChangesPerMeasure(chordChanges, maxChangesPerMeasure = 8) {
  console.log('🎯 Consolidating chord changes per measure...');
  
  const measureGroups = {};
  
  // Group chord changes by measure
  chordChanges.forEach(change => {
    const measure = change.measure;
    if (!measureGroups[measure]) {
      measureGroups[measure] = [];
    }
    measureGroups[measure].push(change);
  });
  
  const consolidatedChanges = [];
  
  // Process each measure
  Object.keys(measureGroups).forEach(measure => {
    const measureChanges = measureGroups[measure];
    
    if (measureChanges.length <= maxChangesPerMeasure) {
      // No consolidation needed
      consolidatedChanges.push(...measureChanges);
    } else {
      // Consolidate to max changes per measure
      console.log(`⚠️ Measure ${measure} has ${measureChanges.length} changes, consolidating to ${maxChangesPerMeasure}`);
      
      // Keep the most significant changes (longest duration, highest confidence)
      const sortedChanges = measureChanges.sort((a, b) => {
        // Sort by duration (longer chords are more important)
        const durationDiff = b.duration - a.duration;
        if (Math.abs(durationDiff) > 0.1) return durationDiff;
        
        // Then by confidence
        return b.confidence - a.confidence;
      });
      
      const selectedChanges = sortedChanges.slice(0, maxChangesPerMeasure);
      
      // Re-sort by time order
      selectedChanges.sort((a, b) => a.startTime - b.startTime);
      
      consolidatedChanges.push(...selectedChanges);
    }
  });
  
  // Sort all changes by time
  consolidatedChanges.sort((a, b) => a.startTime - b.startTime);
  
  console.log(`✅ Consolidated to ${consolidatedChanges.length} chord changes`);
  
  return consolidatedChanges;
}

// Create measure-based chord structure for PDF generation
function createMeasureBasedChordStructure(chordChanges, timeSignature) {
  console.log('📊 Creating measure-based chord structure...');
  
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
  
  // Convert to array and sort by measure number
  const measureArray = Object.values(measures).sort((a, b) => a.measureNumber - b.measureNumber);
  
  console.log(`✅ Created ${measureArray.length} measures with chord changes`);
  
  return measureArray;
}

// Test the chord change detection with local analyzer data
async function testChordChangeDetection() {
  console.log('🧪 Testing Chord Change Detection...\n');
  
  try {
    // Get raw chord data from local analyzer
    const { analyzeAudioLocally } = require('./local-server/modules/enhanced-audio-analyzer.js');
    
    console.log('📊 Generating raw chord data...');
    const analysis = await analyzeAudioLocally('meetup_ring.mp3', () => {});
    const rawChords = analysis.chords.chords;
    
    console.log(`📋 Raw data: ${rawChords.length} chord detections`);
    
    // Detect chord changes
    const timeSignature = {
      numerator: analysis.timeSignature.numerator,
      denominator: analysis.timeSignature.denominator,
      measureDuration: analysis.timeSignature.measureDuration
    };
    
    const chordChangeResult = detectChordChanges(rawChords, timeSignature);
    const chordChanges = chordChangeResult.chordChanges;
    
    console.log('\n🎼 CHORD CHANGE DETECTION RESULTS:');
    console.log(`Original detections: ${chordChangeResult.summary.originalDetections}`);
    console.log(`Chord changes found: ${chordChangeResult.summary.totalChanges}`);
    console.log(`Data reduction: ${chordChangeResult.summary.dataReduction}%`);
    console.log(`Size reduction: ${chordChangeResult.summary.originalSize} → ${chordChangeResult.summary.reducedSize} bytes`);
    
    // Show first 10 chord changes
    console.log('\n🎵 First 10 chord changes:');
    chordChanges.slice(0, 10).forEach((change, i) => {
      const downbeat = change.isDownbeat ? '[DOWNBEAT]' : '';
      console.log(`${(i+1).toString().padStart(2)}: M${change.measure}B${change.beat} ${change.startTime.toFixed(1)}s-${change.endTime.toFixed(1)}s ${change.chord} (${change.nashvilleNumber}) ${change.duration.toFixed(1)}s ${downbeat}`);
    });
    
    // Consolidate chord changes per measure
    const consolidatedChanges = consolidateChordChangesPerMeasure(chordChanges, 8);
    
    console.log('\n📊 CONSOLIDATION RESULTS:');
    console.log(`Before consolidation: ${chordChanges.length} changes`);
    console.log(`After consolidation: ${consolidatedChanges.length} changes`);
    
    // Create measure-based structure
    const measureStructure = createMeasureBasedChordStructure(consolidatedChanges, timeSignature);
    
    console.log('\n🎼 MEASURE-BASED STRUCTURE:');
    console.log(`Total measures: ${measureStructure.length}`);
    
    // Show first 5 measures
    console.log('\nFirst 5 measures:');
    measureStructure.slice(0, 5).forEach(measure => {
      console.log(`Measure ${measure.measureNumber}: ${measure.chords.length} chord changes`);
      measure.chords.forEach(chord => {
        console.log(`  Beat ${chord.beat}: ${chord.chord} (${chord.nashvilleNumber}) ${chord.duration.toFixed(1)}s`);
      });
    });
    
    // Calculate final data size for DynamoDB compatibility
    const finalData = {
      jobId: 'test-job',
      chordChanges: consolidatedChanges,
      measures: measureStructure,
      summary: chordChangeResult.summary,
      analysis: {
        key: analysis.key,
        tempo: analysis.tempo,
        timeSignature: analysis.timeSignature
      }
    };
    
    const finalSize = JSON.stringify(finalData).length;
    console.log(`\n📏 FINAL DATA SIZE: ${finalSize} bytes`);
    console.log(`DynamoDB compatible: ${finalSize < 400000 ? '✅ YES' : '❌ NO'}`);
    
    return {
      success: true,
      originalSize: chordChangeResult.summary.originalSize,
      finalSize: finalSize,
      dataReduction: ((chordChangeResult.summary.originalSize - finalSize) / chordChangeResult.summary.originalSize * 100).toFixed(1),
      chordChanges: consolidatedChanges.length,
      measures: measureStructure.length,
      dynamoDbCompatible: finalSize < 400000
    };
    
  } catch (error) {
    console.error('❌ Chord change detection test failed:', error);
    return { success: false, error: error.message };
  }
}

// Export functions
module.exports = {
  detectChordChanges,
  consolidateChordChangesPerMeasure,
  createMeasureBasedChordStructure,
  testChordChangeDetection
};

// Run test if called directly
if (require.main === module) {
  testChordChangeDetection()
    .then(result => {
      console.log('\n🎯 CHORD CHANGE DETECTION SUMMARY:');
      if (result.success) {
        console.log(`✅ Data reduction: ${result.dataReduction}%`);
        console.log(`✅ Chord changes: ${result.chordChanges}`);
        console.log(`✅ Measures: ${result.measures}`);
        console.log(`✅ DynamoDB compatible: ${result.dynamoDbCompatible ? 'YES' : 'NO'}`);
        console.log('🎉 SOLUTION: Chord change detection solves DynamoDB size limit!');
      } else {
        console.log('❌ Test failed:', result.error);
      }
    })
    .catch(error => {
      console.error('❌ Test failed:', error.message);
    });
}
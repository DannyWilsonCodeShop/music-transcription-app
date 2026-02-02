// Test Local Chord Recognition with meetup_ring.mp3
// This test uses the local enhanced audio analyzer directly

const fs = require('fs');
const path = require('path');

async function testLocalChordRecognition() {
  console.log('🎸 Testing Local Chord Recognition with meetup_ring.mp3...');
  
  const audioFilePath = path.join(__dirname, 'public', 'meetup_ring.mp3');
  
  // Check if the audio file exists
  if (!fs.existsSync(audioFilePath)) {
    console.error('❌ Audio file not found:', audioFilePath);
    return { success: false, error: 'Audio file not found' };
  }
  
  console.log('✅ Audio file found:', audioFilePath);
  
  // Get file stats
  const stats = fs.statSync(audioFilePath);
  console.log('📊 File size:', (stats.size / 1024 / 1024).toFixed(2), 'MB');
  
  try {
    // Load the local enhanced audio analyzer
    const localAnalyzerPath = path.join(__dirname, 'local-server', 'modules', 'enhanced-audio-analyzer.js');
    
    if (!fs.existsSync(localAnalyzerPath)) {
      console.error('❌ Local enhanced audio analyzer not found');
      return { success: false, error: 'Local analyzer not found' };
    }
    
    console.log('✅ Local enhanced audio analyzer found');
    const { analyzeAudioLocally } = require(localAnalyzerPath);
    
    console.log('🚀 Starting local chord recognition...');
    const startTime = Date.now();
    
    // Progress callback to show analysis progress
    const progressCallback = (progress, message) => {
      const percentage = Math.round(progress * 100);
      console.log(`⏱️ [${percentage}%] ${message}`);
    };
    
    // Analyze the audio using the local analyzer
    const analysis = await analyzeAudioLocally(audioFilePath, progressCallback);
    const processingTime = Date.now() - startTime;
    
    console.log('✅ Local chord recognition completed!');
    console.log('⏱️ Processing time:', processingTime, 'ms');
    
    // Extract chord information
    const chordAnalysis = analysis.chords;
    const tempoAnalysis = analysis.tempo;
    const keyAnalysis = analysis.key;
    const timeSignatureAnalysis = analysis.timeSignature;
    
    if (chordAnalysis && chordAnalysis.chords) {
      const chords = chordAnalysis.chords;
      console.log('\n🎼 Local Chord Recognition Results:');
      console.log('📊 Total chord detections:', chords.length);
      console.log('⏱️ Analysis interval:', chordAnalysis.analysisInterval, 'seconds');
      console.log('🎯 Detection rate:', (chords.length * chordAnalysis.analysisInterval / 60).toFixed(1), 'chords per minute');
      
      // Show tempo and key information
      console.log('🥁 Detected BPM:', tempoAnalysis.bpm);
      console.log('🎵 Tempo confidence:', (tempoAnalysis.confidence * 100).toFixed(1) + '%');
      console.log('🗝️ Detected key:', keyAnalysis.root, keyAnalysis.mode);
      console.log('🎵 Key confidence:', (keyAnalysis.confidence * 100).toFixed(1) + '%');
      console.log('🎼 Time signature:', timeSignatureAnalysis.numerator + '/' + timeSignatureAnalysis.denominator);
      console.log('📏 Beats per measure:', timeSignatureAnalysis.beatsPerMeasure);
      console.log('⏱️ Measure duration:', timeSignatureAnalysis.measureDuration, 'seconds');
      
      // Show first 20 chord detections
      console.log('\n🎼 First 20 chord detections:');
      chords.slice(0, 20).forEach((chord, index) => {
        const downbeatIndicator = chord.isDownbeat ? '[DOWNBEAT]' : '';
        const passingIndicator = chord.isPassingChord ? '[PASSING]' : '';
        const measureInfo = `M${chord.measureIndex + 1}`;
        
        console.log(`[${index.toString().padStart(2, '0')}] ${chord.start.toFixed(1)}s: ${chord.chord.padEnd(4)} (${chord.nashvilleNumber}) ${measureInfo} ${downbeatIndicator}${passingIndicator}`);
      });
      
      // Analyze chord distribution
      const chordCounts = {};
      chords.forEach(chord => {
        chordCounts[chord.chord] = (chordCounts[chord.chord] || 0) + 1;
      });
      
      console.log('\n📊 Chord Distribution:');
      Object.entries(chordCounts)
        .sort(([,a], [,b]) => b - a)
        .slice(0, 10)
        .forEach(([chord, count]) => {
          const percentage = ((count / chords.length) * 100).toFixed(1);
          console.log(`${chord.padEnd(6)}: ${count.toString().padStart(3)} times (${percentage}%)`);
        });
      
      // Analyze Nashville number distribution
      const nashvilleCounts = {};
      chords.forEach(chord => {
        nashvilleCounts[chord.nashvilleNumber] = (nashvilleCounts[chord.nashvilleNumber] || 0) + 1;
      });
      
      console.log('\n🔢 Nashville Number Distribution:');
      Object.entries(nashvilleCounts)
        .sort(([,a], [,b]) => b - a)
        .slice(0, 8)
        .forEach(([number, count]) => {
          const percentage = ((count / chords.length) * 100).toFixed(1);
          console.log(`${number.padEnd(4)}: ${count.toString().padStart(3)} times (${percentage}%)`);
        });
      
      // Analyze downbeats vs passing chords
      const downbeats = chords.filter(c => c.isDownbeat);
      const passingChords = chords.filter(c => c.isPassingChord);
      
      console.log('\n🎯 Beat Analysis:');
      console.log('🔴 Downbeats:', downbeats.length);
      console.log('⚫ Passing chords:', passingChords.length);
      console.log('📊 Downbeat ratio:', ((downbeats.length / chords.length) * 100).toFixed(1) + '%');
      
      // Show measure analysis
      const totalMeasures = Math.max(...chords.map(c => c.measureIndex)) + 1;
      console.log('\n📏 Measure Analysis:');
      console.log('📊 Total measures:', totalMeasures);
      console.log('⏱️ Average chords per measure:', (chords.length / totalMeasures).toFixed(1));
      
      return {
        success: true,
        totalChords: chords.length,
        analysisInterval: chordAnalysis.analysisInterval,
        detectionRate: (chords.length * chordAnalysis.analysisInterval / 60).toFixed(1),
        tempo: tempoAnalysis,
        key: keyAnalysis,
        timeSignature: timeSignatureAnalysis,
        chordDistribution: chordCounts,
        nashvilleDistribution: nashvilleCounts,
        downbeats: downbeats.length,
        passingChords: passingChords.length,
        totalMeasures: totalMeasures,
        processingTime: processingTime,
        sampleChords: chords.slice(0, 20),
        analysis: analysis // Full analysis for further processing
      };
      
    } else {
      console.log('⚠️ No chord analysis found in local response');
      return {
        success: false,
        error: 'No chord analysis in local response',
        analysis: analysis
      };
    }
    
  } catch (error) {
    console.error('❌ Local chord recognition test failed:', error);
    return { 
      success: false, 
      error: error.message,
      stack: error.stack
    };
  }
}

// Test the complete local analysis pipeline
async function testCompleteLocalAnalysis() {
  console.log('🔄 Testing Complete Local Analysis Pipeline...\n');
  
  const result = await testLocalChordRecognition();
  
  if (result.success) {
    console.log('\n✅ Local chord recognition test PASSED!');
    console.log('📊 Summary:');
    console.log(`   - Total chords: ${result.totalChords}`);
    console.log(`   - Analysis interval: ${result.analysisInterval}s`);
    console.log(`   - Key: ${result.key.root} ${result.key.mode}`);
    console.log(`   - Tempo: ${result.tempo.bpm} BPM`);
    console.log(`   - Time signature: ${result.timeSignature.numerator}/${result.timeSignature.denominator}`);
    console.log(`   - Processing time: ${result.processingTime}ms`);
    
    return result;
  } else {
    console.log('\n❌ Local chord recognition test FAILED!');
    console.log('Error:', result.error);
    return result;
  }
}

// Export for use in other tests
module.exports = {
  testLocalChordRecognition,
  testCompleteLocalAnalysis
};

// Run if called directly
if (require.main === module) {
  console.log('🚀 Starting local chord recognition test...');
  testCompleteLocalAnalysis().catch(error => {
    console.error('❌ Test failed with error:', error);
    process.exit(1);
  });
}
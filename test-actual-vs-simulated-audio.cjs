// Test: Actual vs Simulated Audio Analysis
// Shows the difference between real audio file and simulated data

const fs = require('fs');
const path = require('path');

async function testActualVsSimulatedAudio() {
  console.log('🔍 Testing Actual vs Simulated Audio Analysis...\n');
  
  try {
    // Check the actual audio file
    const audioFilePath = path.join(__dirname, 'public', 'meetup_ring.mp3');
    
    if (fs.existsSync(audioFilePath)) {
      const stats = fs.statSync(audioFilePath);
      const fileSizeKB = (stats.size / 1024).toFixed(1);
      
      console.log('📁 ACTUAL AUDIO FILE:');
      console.log(`   File: meetup_ring.mp3`);
      console.log(`   Size: ${stats.size} bytes (${fileSizeKB} KB)`);
      
      // Estimate duration based on file size (rough calculation)
      // MP3 at 128kbps ≈ 16KB per second
      const estimatedDurationSeconds = stats.size / (16 * 1024);
      console.log(`   Estimated duration: ~${estimatedDurationSeconds.toFixed(1)} seconds`);
      
      if (estimatedDurationSeconds < 10) {
        console.log('   ⚠️ This appears to be a very short audio clip!');
      }
      
    } else {
      console.log('❌ Audio file not found');
    }
    
    // Check what the local analyzer simulates
    console.log('\n🎭 SIMULATED DATA (Local Analyzer):');
    const { analyzeAudioLocally } = require('./local-server/modules/enhanced-audio-analyzer.js');
    
    console.log('   Simulated duration: 180 seconds (3 minutes)');
    console.log('   Analysis interval: 0.2 seconds');
    console.log('   Expected chord detections: 180 ÷ 0.2 = 900');
    console.log('   Song: Amazing Grace chord progression');
    
    // Run the simulation to confirm
    const analysis = await analyzeAudioLocally('meetup_ring.mp3', () => {});
    
    console.log('\n📊 SIMULATION RESULTS:');
    console.log(`   Actual chord detections: ${analysis.chords.chords.length}`);
    console.log(`   Analysis method: ${analysis.processingMetadata.method}`);
    console.log(`   Key: ${analysis.key.root} ${analysis.key.mode}`);
    console.log(`   BPM: ${analysis.tempo.bpm}`);
    console.log(`   Time signature: ${analysis.timeSignature.numerator}/${analysis.timeSignature.denominator}`);
    
    // Show the discrepancy
    console.log('\n⚠️ DISCREPANCY IDENTIFIED:');
    console.log('   The local analyzer is NOT analyzing the actual audio file!');
    console.log('   It generates mock data for a 3-minute Amazing Grace song');
    console.log('   The actual meetup_ring.mp3 is probably only a few seconds long');
    
    // Show first few chords to confirm it's Amazing Grace pattern
    console.log('\n🎼 First 10 simulated chords (Amazing Grace pattern):');
    analysis.chords.chords.slice(0, 10).forEach((chord, i) => {
      console.log(`   ${i+1}. ${chord.start.toFixed(1)}s: ${chord.chord} (${chord.nashvilleNumber})`);
    });
    
    return {
      actualFileSize: fs.existsSync(audioFilePath) ? fs.statSync(audioFilePath).size : 0,
      estimatedActualDuration: fs.existsSync(audioFilePath) ? fs.statSync(audioFilePath).size / (16 * 1024) : 0,
      simulatedDuration: 180,
      simulatedChords: analysis.chords.chords.length,
      isActualAnalysis: false,
      analysisMethod: analysis.processingMetadata.method
    };
    
  } catch (error) {
    console.error('❌ Test failed:', error);
    return { success: false, error: error.message };
  }
}

// Run the test
if (require.main === module) {
  testActualVsSimulatedAudio()
    .then(result => {
      console.log('\n🎯 CONCLUSION:');
      console.log('The "900 chord detections" are from simulated 3-minute Amazing Grace data,');
      console.log('NOT from analyzing the actual short meetup_ring.mp3 file!');
      console.log('\nFor real audio analysis, we would need to:');
      console.log('1. Actually analyze the audio file duration');
      console.log('2. Perform real chord detection (not simulation)');
      console.log('3. Generate chord changes based on actual audio content');
    })
    .catch(error => {
      console.error('❌ Test failed:', error.message);
    });
}

module.exports = { testActualVsSimulatedAudio };
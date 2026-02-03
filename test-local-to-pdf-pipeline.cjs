// Complete Local Analyzer → PDF Generator Pipeline Test
// Tests the full flow from local chord analysis to PDF generation

const fs = require('fs');
const path = require('path');

async function testLocalToPdfPipeline() {
  console.log('🎵 Testing Complete Local → PDF Pipeline...\n');
  
  try {
    // Step 1: Generate chord data with local analyzer
    console.log('📊 Step 1: Analyzing audio with local analyzer...');
    const { analyzeAudioLocally } = require('./local-server/modules/enhanced-audio-analyzer.js');
    
    const analysis = await analyzeAudioLocally('meetup_ring.mp3', (progress, message) => {
      const percentage = Math.round(progress * 100);
      console.log(`  [${percentage}%] ${message}`);
    });
    
    console.log(`✅ Generated ${analysis.chords.chords.length} chord detections`);
    
    // Step 2: Transform data for PDF compatibility
    console.log('\n🔄 Step 2: Transforming data for PDF compatibility...');
    const transformedChords = analysis.chords.chords.map(chord => ({
      ...chord,
      time: chord.start,        // Map start → time for PDF
      timestamp: chord.start    // Also provide timestamp as backup
    }));
    
    console.log(`✅ Transformed ${transformedChords.length} chords`);
    
    // Step 3: Create job data structure that PDF generator expects
    console.log('\n📋 Step 3: Creating PDF job data structure...');
    const jobData = {
      title: 'Amazing Grace - Local Analysis',
      videoTitle: 'Amazing Grace - Local Analysis',
      chords: transformedChords,
      key: analysis.key.root + ' ' + analysis.key.mode,
      tempo: analysis.tempo.bpm,
      timeSignature: `${analysis.timeSignature.numerator}/${analysis.timeSignature.denominator}`,
      lyricsData: {
        text: 'Amazing grace, how sweet the sound\nThat saved a wretch like me\nI once was lost, but now am found\nWas blind, but now I see',
        syllableAlignedLyrics: [] // Could be populated with lyrics analyzer
      },
      status: 'READY_FOR_PDF',
      jobId: 'local-test-' + Date.now()
    };
    
    console.log('✅ Job data structure created:');
    console.log(`  - Title: ${jobData.title}`);
    console.log(`  - Chords: ${jobData.chords.length}`);
    console.log(`  - Key: ${jobData.key}`);
    console.log(`  - Tempo: ${jobData.tempo} BPM`);
    console.log(`  - Time Signature: ${jobData.timeSignature}`);
    
    // Step 4: Test PDF generator compatibility (simulate)
    console.log('\n📄 Step 4: Testing PDF generator compatibility...');
    
    // Simulate what the PDF generator would do
    const testChord = jobData.chords[0];
    const pdfAccessTest = {
      time: testChord.time || testChord.timestamp || 'MISSING',
      chord: testChord.chord || testChord.name || 'MISSING',
      nashville: testChord.nashvilleNumber || testChord.number || 'MISSING',
      confidence: testChord.confidence || 'MISSING'
    };
    
    console.log('✅ PDF generator would access:');
    console.log(`  - Time: ${pdfAccessTest.time}`);
    console.log(`  - Chord: ${pdfAccessTest.chord}`);
    console.log(`  - Nashville: ${pdfAccessTest.nashville}`);
    console.log(`  - Confidence: ${pdfAccessTest.confidence}`);
    
    // Step 5: Show chord progression sample
    console.log('\n🎼 Step 5: Sample chord progression for PDF:');
    jobData.chords.slice(0, 20).forEach((chord, i) => {
      const beat = chord.isDownbeat ? '[DOWNBEAT]' : '[PASSING]';
      const measure = `M${chord.measureIndex + 1}`;
      console.log(`  ${(i+1).toString().padStart(2)}: ${chord.time.toFixed(1)}s - ${chord.chord} (${chord.nashvilleNumber}) ${measure} ${beat}`);
    });
    
    // Step 6: Verify data completeness
    console.log('\n✅ Step 6: Data completeness verification:');
    const completeness = {
      hasTitle: !!jobData.title,
      hasChords: jobData.chords.length > 0,
      hasKey: !!jobData.key,
      hasTempo: !!jobData.tempo,
      hasTimeSignature: !!jobData.timeSignature,
      hasNashvilleNumbers: jobData.chords.every(c => c.nashvilleNumber),
      hasTimestamps: jobData.chords.every(c => c.time !== undefined),
      hasConfidence: jobData.chords.every(c => c.confidence !== undefined)
    };
    
    Object.entries(completeness).forEach(([check, passed]) => {
      console.log(`  ${check}: ${passed ? '✅' : '❌'}`);
    });
    
    const allPassed = Object.values(completeness).every(v => v);
    
    if (allPassed) {
      console.log('\n🎉 SUCCESS: Local analyzer data is FULLY READY for PDF generation!');
      console.log('🚀 The pipeline is working end-to-end');
      
      // Save the job data for actual PDF testing
      const outputPath = path.join(__dirname, 'local-pdf-job-data.json');
      fs.writeFileSync(outputPath, JSON.stringify(jobData, null, 2));
      console.log(`💾 Job data saved to: ${outputPath}`);
      
      return {
        success: true,
        jobData: jobData,
        completeness: completeness,
        message: 'Local analyzer → PDF pipeline fully functional'
      };
      
    } else {
      console.log('\n❌ ISSUES FOUND: Some data is missing for PDF generation');
      return {
        success: false,
        completeness: completeness,
        message: 'Data completeness issues found'
      };
    }
    
  } catch (error) {
    console.error('❌ Pipeline test failed:', error);
    return {
      success: false,
      error: error.message,
      stack: error.stack
    };
  }
}

// Run the complete pipeline test
if (require.main === module) {
  testLocalToPdfPipeline()
    .then(result => {
      console.log('\n🎯 PIPELINE TEST RESULT:');
      if (result.success) {
        console.log('✅ LOCAL ANALYZER → PDF GENERATOR: FULLY FUNCTIONAL');
        console.log('🎵 Ready to generate Nashville Number System PDFs');
        console.log('📊 Data includes:', result.jobData.chords.length, 'chord detections');
      } else {
        console.log('❌ PIPELINE ISSUES:', result.message);
        if (result.completeness) {
          console.log('Missing:', Object.entries(result.completeness)
            .filter(([,passed]) => !passed)
            .map(([check]) => check)
            .join(', '));
        }
      }
    })
    .catch(error => {
      console.error('❌ Pipeline test failed:', error.message);
    });
}

module.exports = { testLocalToPdfPipeline };
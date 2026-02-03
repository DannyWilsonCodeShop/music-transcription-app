// Test Enhanced PDF Generator with Known Good Data
const AWS = require('aws-sdk');

const lambda = new AWS.Lambda({ region: 'us-east-1' });

async function testEnhancedPDFGenerator() {
  console.log('📄 Testing Enhanced PDF Generator with Known Good Data...');
  
  // Create perfect test data that should produce the enhanced layout
  const mockMusicalAnalysis = {
    enhancedChords: [],
    detectedKey: 'G',
    tempo: 120,
    timeSignature: '4/4'
  };
  
  const mockLyricsAnalysis = {
    syllableAlignedLyrics: [
      { text: 'A', startTime: 0.0, endTime: 0.5 },
      { text: 'maz', startTime: 0.5, endTime: 1.0 },
      { text: 'ing', startTime: 1.0, endTime: 1.5 },
      { text: 'Grace', startTime: 1.5, endTime: 2.5 },
      { text: 'how', startTime: 3.0, endTime: 3.5 },
      { text: 'sweet', startTime: 3.5, endTime: 4.0 },
      { text: 'the', startTime: 4.0, endTime: 4.3 },
      { text: 'sound', startTime: 4.3, endTime: 5.0 }
    ]
  };
  
  // Generate 900 enhanced chords for 3-minute song (0.2s intervals)
  for (let i = 0; i < 900; i++) {
    const time = i * 0.2;
    const chordIndex = Math.floor(time / 4) % 4;
    const chords = ['G', 'C', 'D', 'Em'];
    const nashvilleNumbers = ['1', '4', '5', '6m'];
    
    mockMusicalAnalysis.enhancedChords.push({
      time: time,
      chord: chords[chordIndex],
      nashvilleNumber: nashvilleNumbers[chordIndex],
      confidence: 0.85 + Math.random() * 0.1,
      isDownbeat: i % 20 === 0 // Every 4 seconds (downbeat)
    });
  }
  
  try {
    const params = {
      FunctionName: 'chordscout-v2-pdf-generator-dev',
      Payload: JSON.stringify({
        jobId: 'test-pdf-enhanced-' + Date.now(),
        musicalAnalysis: mockMusicalAnalysis,
        lyricsAnalysis: mockLyricsAnalysis
      })
    };
    
    console.log('🚀 Invoking enhanced PDF generator...');
    console.log(`📊 Test data: ${mockMusicalAnalysis.enhancedChords.length} chords, ${mockLyricsAnalysis.syllableAlignedLyrics.length} syllables`);
    console.log(`🎵 Key: ${mockMusicalAnalysis.detectedKey}, Tempo: ${mockMusicalAnalysis.tempo} BPM`);
    
    const result = await lambda.invoke(params).promise();
    
    if (result.StatusCode === 200) {
      const response = JSON.parse(result.Payload);
      console.log('✅ Enhanced PDF generation completed!');
      console.log('📄 Full Response:', JSON.stringify(response, null, 2));
      
      if (response.body && response.body.pdfUrl) {
        const pdfUrl = response.body.pdfUrl;
        console.log('📄 PDF URL:', pdfUrl);
        
        // Check enhanced features
        const features = response.body.enhancedFeatures;
        if (features) {
          console.log('🎯 Enhanced Features:');
          console.log(`  📊 Chords Detected: ${features.chordsDetected}`);
          console.log(`  📐 Measure-based Layout: ${features.measureBasedLayout}`);
          console.log(`  🎤 Syllable Alignment: ${features.syllableAlignment}`);
          console.log(`  🎨 Color-coded Chords: ${features.colorCodedChords}`);
          console.log(`  🎼 Nashville Number System: ${features.nashvilleNumberSystem}`);
        }
        
        return {
          success: true,
          pdfUrl: pdfUrl,
          enhancedFeatures: features,
          chordsProcessed: mockMusicalAnalysis.enhancedChords.length,
          syllablesProcessed: mockLyricsAnalysis.syllableAlignedLyrics.length
        };
      } else {
        console.log('⚠️ No PDF URL found in response');
        return {
          success: false,
          error: 'No PDF URL in response',
          response: response.body
        };
      }
    } else {
      console.error('❌ Lambda invocation failed');
      console.error('Status:', result.StatusCode);
      console.error('Error:', result.Payload);
      return { success: false, error: result.Payload };
    }
    
  } catch (error) {
    console.error('❌ Test failed:', error);
    return { success: false, error: error.message };
  }
}

// Run the test
testEnhancedPDFGenerator().then(result => {
  console.log('\n🎯 Enhanced PDF Generator Test Result:');
  console.log(JSON.stringify(result, null, 2));
}).catch(console.error);
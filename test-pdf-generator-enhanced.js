// Test 5: Enhanced PDF Generator with Known Good Data
// Tests if the PDF generator creates the correct measure-based layout

const AWS = require('aws-sdk');

const lambda = new AWS.Lambda({ region: 'us-east-1' });
const s3 = new AWS.S3({ region: 'us-east-1' });

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
    const chordIndex = Math.floor(time / 4) % 4; // Change chord every 4 seconds
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
        
        // Try to download and check PDF size
        try {
          const pdfResponse = await fetch(pdfUrl, { method: 'HEAD' });
          const pdfSize = pdfResponse.headers.get('content-length');
          console.log(`📏 PDF Size: ${pdfSize} bytes`);
          
          // A measure-based PDF should be larger than a simple table
          const isEnhanced = parseInt(pdfSize) > 50000; // > 50KB indicates enhanced layout
          console.log(`🎯 Enhanced Layout Detected: ${isEnhanced ? 'YES' : 'NO'}`);
          
          return {
            success: true,
            pdfUrl: pdfUrl,
            pdfSize: pdfSize,
            enhancedFeatures: features,
            isEnhancedLayout: isEnhanced,
            chordsProcessed: mockMusicalAnalysis.enhancedChords.length,
            syllablesProcessed: mockLyricsAnalysis.syllableAlignedLyrics.length
          };
        } catch (fetchError) {
          console.log('⚠️ Could not fetch PDF details:', fetchError.message);
          return {
            success: true,
            pdfUrl: pdfUrl,
            enhancedFeatures: features,
            chordsProcessed: mockMusicalAnalysis.enhancedChords.length,
            syllablesProcessed: mockLyricsAnalysis.syllableAlignedLyrics.length
          };
        }
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

// Test PDF generator with legacy data (should fall back gracefully)
async function testPDFGeneratorFallback() {
  console.log('📄 Testing PDF Generator Fallback (Legacy Data)...');
  
  try {
    const params = {
      FunctionName: 'chordscout-v2-pdf-generator-dev',
      Payload: JSON.stringify({
        jobId: 'test-pdf-fallback-' + Date.now(),
        // No enhanced data - should use fallback
        musicalAnalysis: null,
        lyricsAnalysis: null
      })
    };
    
    console.log('🚀 Testing fallback behavior...');
    
    const result = await lambda.invoke(params).promise();
    
    console.log('📊 Lambda Response Status:', result.StatusCode);
    
    if (result.StatusCode === 200) {
      const response = JSON.parse(result.Payload);
      console.log('📄 Fallback response:', JSON.stringify(response, null, 2));
      
      return {
        success: true,
        response: response.body
      };
    } else {
      return {
        success: false,
        error: result.Payload
      };
    }
    
  } catch (error) {
    console.error('❌ Fallback test failed:', error);
    return { success: false, error: error.message };
  }
}

// Run PDF generator tests
async function runPDFTests() {
  console.log('🧪 Running Enhanced PDF Generator Tests...\n');
  
  const test1 = await testEnhancedPDFGenerator();
  console.log('\n' + '='.repeat(50) + '\n');
  const test2 = await testPDFGeneratorFallback();
  
  console.log('\n🎯 PDF Generator Test Results:');
  console.log('Test 1 (Enhanced Data):', JSON.stringify(test1, null, 2));
  console.log('Test 2 (Fallback):', JSON.stringify(test2, null, 2));
}

runPDFTests().catch(console.error);
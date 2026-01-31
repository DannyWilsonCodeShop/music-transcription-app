// Test PDF Generator Directly with Mock Data
const AWS = require('aws-sdk');

const lambda = new AWS.Lambda({ region: 'us-east-1' });

async function testPDFGeneratorDirect() {
  console.log('📄 Testing PDF Generator with Mock Enhanced Data...');
  
  // Create perfect mock data that should trigger enhanced features
  const mockEvent = {
    jobId: 'test-direct-' + Date.now(),
    musicalAnalysis: {
      enhancedChords: [
        { time: 0.0, chord: 'G', nashvilleNumber: '1', confidence: 0.9, isDownbeat: true },
        { time: 0.2, chord: 'G', nashvilleNumber: '1', confidence: 0.8, isDownbeat: false },
        { time: 0.4, chord: 'G', nashvilleNumber: '1', confidence: 0.8, isDownbeat: false },
        { time: 0.6, chord: 'C', nashvilleNumber: '4', confidence: 0.9, isDownbeat: false },
        { time: 0.8, chord: 'C', nashvilleNumber: '4', confidence: 0.8, isDownbeat: false },
        { time: 1.0, chord: 'D', nashvilleNumber: '5', confidence: 0.9, isDownbeat: true },
        { time: 1.2, chord: 'D', nashvilleNumber: '5', confidence: 0.8, isDownbeat: false },
        { time: 1.4, chord: 'G', nashvilleNumber: '1', confidence: 0.9, isDownbeat: false }
      ],
      detectedKey: 'G',
      tempo: 120,
      timeSignature: '4/4'
    },
    lyricsAnalysis: {
      syllableAlignedLyrics: [
        { text: 'A', startTime: 0.0, endTime: 0.5, confidence: 0.9 },
        { text: 'maz', startTime: 0.5, endTime: 1.0, confidence: 0.9 },
        { text: 'ing', startTime: 1.0, endTime: 1.5, confidence: 0.9 },
        { text: 'Grace', startTime: 1.5, endTime: 2.5, confidence: 0.9 }
      ]
    }
  };
  
  try {
    console.log('🚀 Invoking PDF generator with enhanced mock data...');
    console.log('📊 Mock data includes:');
    console.log(`  • ${mockEvent.musicalAnalysis.enhancedChords.length} enhanced chords`);
    console.log(`  • ${mockEvent.lyricsAnalysis.syllableAlignedLyrics.length} syllable-aligned lyrics`);
    console.log(`  • Key: ${mockEvent.musicalAnalysis.detectedKey}`);
    console.log(`  • Tempo: ${mockEvent.musicalAnalysis.tempo} BPM`);
    
    const result = await lambda.invoke({
      FunctionName: 'chordscout-v2-pdf-generator-dev',
      Payload: JSON.stringify(mockEvent)
    }).promise();
    
    console.log('📊 Lambda Response Status:', result.StatusCode);
    
    if (result.StatusCode === 200) {
      const response = JSON.parse(result.Payload);
      console.log('✅ PDF generation completed!');
      console.log('📄 Full Response:', JSON.stringify(response, null, 2));
      
      // Check if enhanced features are working
      if (response.body && response.body.enhancedFeatures) {
        const features = response.body.enhancedFeatures;
        console.log('\n🎯 Enhanced Features Status:');
        console.log(`  📊 Chords Detected: ${features.chordsDetected}`);
        console.log(`  📐 Measure-based Layout: ${features.measureBasedLayout}`);
        console.log(`  🎤 Syllable Alignment: ${features.syllableAlignment}`);
        console.log(`  🎨 Color-coded Chords: ${features.colorCodedChords}`);
        console.log(`  🎼 Nashville Number System: ${features.nashvilleNumberSystem}`);
        
        // Determine if enhanced system is working
        const isEnhanced = features.measureBasedLayout && 
                          features.syllableAlignment && 
                          features.colorCodedChords &&
                          features.chordsDetected > 0;
        
        console.log(`\n🎉 Enhanced System Status: ${isEnhanced ? '✅ WORKING' : '❌ NOT WORKING'}`);
        
        if (response.body.pdfUrl) {
          console.log(`📄 PDF URL: ${response.body.pdfUrl}`);
        }
        
        return {
          success: true,
          enhancedSystemWorking: isEnhanced,
          features: features,
          pdfUrl: response.body.pdfUrl
        };
      } else {
        console.log('⚠️ No enhanced features found in response');
        return {
          success: false,
          error: 'No enhanced features in response',
          response: response
        };
      }
    } else {
      console.error('❌ Lambda invocation failed');
      const errorResponse = JSON.parse(result.Payload);
      console.error('Error Response:', JSON.stringify(errorResponse, null, 2));
      return { 
        success: false, 
        error: errorResponse,
        statusCode: result.StatusCode 
      };
    }
    
  } catch (error) {
    console.error('❌ Test failed:', error);
    return { success: false, error: error.message };
  }
}

// Also test with no enhanced data (fallback)
async function testPDFGeneratorFallback() {
  console.log('\n📄 Testing PDF Generator Fallback (No Enhanced Data)...');
  
  const mockEvent = {
    jobId: 'test-fallback-' + Date.now()
    // No musicalAnalysis or lyricsAnalysis - should use job data
  };
  
  try {
    console.log('🚀 Testing fallback behavior...');
    
    const result = await lambda.invoke({
      FunctionName: 'chordscout-v2-pdf-generator-dev',
      Payload: JSON.stringify(mockEvent)
    }).promise();
    
    console.log('📊 Fallback Response Status:', result.StatusCode);
    
    if (result.StatusCode === 200) {
      const response = JSON.parse(result.Payload);
      console.log('✅ Fallback PDF generation completed!');
      console.log('📄 Fallback Response:', JSON.stringify(response, null, 2));
      
      return {
        success: true,
        response: response.body
      };
    } else {
      const errorResponse = JSON.parse(result.Payload);
      console.log('❌ Fallback failed:', JSON.stringify(errorResponse, null, 2));
      return {
        success: false,
        error: errorResponse
      };
    }
    
  } catch (error) {
    console.error('❌ Fallback test failed:', error);
    return { success: false, error: error.message };
  }
}

// Run both tests
async function runPDFTests() {
  console.log('🧪 Running Direct PDF Generator Tests...\n');
  
  const test1 = await testPDFGeneratorDirect();
  console.log('\n' + '='.repeat(60) + '\n');
  const test2 = await testPDFGeneratorFallback();
  
  console.log('\n🎯 PDF Generator Test Results:');
  console.log('Enhanced Data Test:', JSON.stringify(test1, null, 2));
  console.log('Fallback Test:', JSON.stringify(test2, null, 2));
  
  // Analysis
  console.log('\n🔍 Analysis:');
  if (test1.success && test1.enhancedSystemWorking) {
    console.log('✅ Enhanced PDF generation is working correctly!');
    console.log('💡 The issue is likely in the Step Functions workflow not passing enhanced data.');
  } else if (test1.success && !test1.enhancedSystemWorking) {
    console.log('⚠️ PDF generator is working but not using enhanced features.');
    console.log('💡 Check if enhanced data is being processed correctly.');
  } else {
    console.log('❌ PDF generator has issues that need to be fixed.');
    console.log('💡 Fix the PDF generator before testing the full pipeline.');
  }
}

runPDFTests().catch(console.error);
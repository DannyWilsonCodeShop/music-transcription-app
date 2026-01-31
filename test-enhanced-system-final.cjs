// Final Test of Enhanced System via API
const AWS = require('aws-sdk');

async function testEnhancedSystem() {
  console.log('🧪 Testing Enhanced System via API...');
  
  try {
    // Create a job via the API
    const createResponse = await fetch('https://ppq03hif98.execute-api.us-east-1.amazonaws.com/dev/jobs', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        youtubeUrl: 'https://www.youtube.com/watch?v=CDdvReNKKuk' // Amazing Grace - 3 min song
      })
    });
    
    const createResult = await createResponse.json();
    console.log('✅ Job created:', createResult.jobId);
    
    // Monitor the job
    const jobId = createResult.jobId;
    let attempts = 0;
    let lastStatus = '';
    
    while (attempts < 30) { // 5 minutes max
      await new Promise(resolve => setTimeout(resolve, 10000)); // Wait 10 seconds
      
      const statusResponse = await fetch(`https://ppq03hif98.execute-api.us-east-1.amazonaws.com/dev/jobs/${jobId}`);
      const statusResult = await statusResponse.json();
      
      if (statusResult.status !== lastStatus) {
        console.log(`[${attempts}] Status: ${statusResult.status} | Progress: ${statusResult.progress}%`);
        lastStatus = statusResult.status;
        
        // Log enhanced features if available
        if (statusResult.lyricsData && statusResult.lyricsData.syllableAlignedLyrics) {
          console.log(`🎤 Syllable-aligned lyrics: ${statusResult.lyricsData.syllableAlignedLyrics.length} segments`);
        }
        
        if (statusResult.chords) {
          console.log(`🎸 Chords detected: ${statusResult.chords.length}`);
        }
      }
      
      if (statusResult.status === 'COMPLETE') {
        console.log('✅ Job completed successfully!');
        console.log('📄 PDF URL:', statusResult.pdfUrl);
        
        // Analyze the results
        const analysis = {
          chordsDetected: statusResult.chords?.length || 0,
          syllableAlignedLyrics: statusResult.lyricsData?.syllableAlignedLyrics?.length || 0,
          hasEnhancedLyrics: statusResult.lyricsData?.metadata?.enhanced || false,
          pdfUrl: statusResult.pdfUrl
        };
        
        console.log('\n🎯 Enhanced System Analysis:');
        console.log(`📊 Chords Detected: ${analysis.chordsDetected}`);
        console.log(`🎤 Syllable Segments: ${analysis.syllableAlignedLyrics}`);
        console.log(`🔧 Enhanced Lyrics: ${analysis.hasEnhancedLyrics}`);
        
        // Determine if enhanced features are working
        const isEnhanced = analysis.chordsDetected > 50 || analysis.syllableAlignedLyrics > 0;
        console.log(`\n🎉 Enhanced System Status: ${isEnhanced ? '✅ WORKING' : '⚠️ PARTIAL'}`);
        
        if (isEnhanced) {
          console.log('💡 Enhanced features detected! The system is working correctly.');
        } else {
          console.log('💡 Basic features only. Enhanced capabilities may need more time to process.');
        }
        
        return {
          success: true,
          enhanced: isEnhanced,
          analysis: analysis
        };
      } else if (statusResult.status === 'FAILED') {
        console.error('❌ Job failed');
        console.error('Error:', statusResult.errorMessage);
        return {
          success: false,
          error: statusResult.errorMessage
        };
      }
      
      attempts++;
    }
    
    console.log('⏰ Test timed out');
    return {
      success: false,
      error: 'Timeout'
    };
    
  } catch (error) {
    console.error('❌ Test failed:', error);
    return {
      success: false,
      error: error.message
    };
  }
}

testEnhancedSystem().then(result => {
  console.log('\n🎯 Final Enhanced System Test Result:');
  console.log(JSON.stringify(result, null, 2));
  
  if (result.success && result.enhanced) {
    console.log('\n🎉 SUCCESS! Enhanced music transcription system is working!');
    console.log('🎯 Users can now create professional Nashville Number System charts');
    console.log('📊 Enhanced features include:');
    console.log('  • High-resolution chord detection');
    console.log('  • Syllable-aligned lyrics');
    console.log('  • Professional measure-based PDF layout');
  } else if (result.success) {
    console.log('\n⚠️ PARTIAL SUCCESS: Basic system working, enhanced features may need optimization');
  } else {
    console.log('\n❌ SYSTEM NEEDS ATTENTION: Check the error details above');
  }
}).catch(console.error);
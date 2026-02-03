// Test 4: Musical Integration Orchestrator
// Tests downbeat detection, tempo analysis, and syllable alignment

const AWS = require('aws-sdk');

const lambda = new AWS.Lambda({ region: 'us-east-1' });

async function testMusicalIntegration() {
  console.log('🎼 Testing Musical Integration Orchestrator...');
  
  // Create mock enhanced data to test the integration
  const mockEnhancedChords = [];
  const mockSyllableAlignedLyrics = [];
  
  // Generate 900 mock chord detections for 3-minute song (0.2s intervals)
  for (let i = 0; i < 900; i++) {
    const time = i * 0.2;
    mockEnhancedChords.push({
      time: time,
      chord: i % 4 === 0 ? 'C' : i % 4 === 1 ? 'Am' : i % 4 === 2 ? 'F' : 'G',
      nashvilleNumber: i % 4 === 0 ? '1' : i % 4 === 1 ? '6m' : i % 4 === 2 ? '4' : '5',
      confidence: 0.85 + Math.random() * 0.1,
      isDownbeat: i % 20 === 0 // Every 4 seconds (20 * 0.2s)
    });
  }
  
  // Generate mock syllable-aligned lyrics
  const lyrics = ['A', 'maz', 'ing', 'Grace', 'how', 'sweet', 'the', 'sound'];
  for (let i = 0; i < lyrics.length; i++) {
    const startTime = i * 2; // 2 seconds per syllable
    mockSyllableAlignedLyrics.push({
      text: lyrics[i],
      startTime: startTime,
      endTime: startTime + 1.8,
      confidence: 0.9
    });
  }
  
  try {
    const params = {
      FunctionName: 'chordscout-v2-musical-integration-orchestrator-dev',
      Payload: JSON.stringify({
        jobId: 'test-integration-' + Date.now(),
        enhancedChords: mockEnhancedChords,
        syllableAlignedLyrics: mockSyllableAlignedLyrics,
        audioMetadata: {
          duration: 180,
          sampleRate: 44100,
          channels: 2
        }
      })
    };
    
    console.log('🚀 Invoking musical integration orchestrator...');
    console.log(`📊 Input data: ${mockEnhancedChords.length} chords, ${mockSyllableAlignedLyrics.length} syllables`);
    
    const result = await lambda.invoke(params).promise();
    
    if (result.StatusCode === 200) {
      const response = JSON.parse(result.Payload);
      console.log('✅ Musical integration completed!');
      
      if (response.body) {
        const integration = response.body;
        
        console.log('🎵 Integration Results:');
        console.log(`🎯 Detected Key: ${integration.detectedKey || 'Unknown'}`);
        console.log(`⏱️ Detected Tempo: ${integration.tempo || 'Unknown'} BPM`);
        console.log(`🎼 Time Signature: ${integration.timeSignature || 'Unknown'}`);
        console.log(`🥁 Downbeats Detected: ${integration.downbeats?.length || 0}`);
        console.log(`🎤 Syllable Alignments: ${integration.syllableChordAlignments?.length || 0}`);
        
        // Check downbeat detection
        if (integration.downbeats && integration.downbeats.length > 0) {
          console.log('\n🥁 First 5 downbeats:');
          integration.downbeats.slice(0, 5).forEach((downbeat, index) => {
            console.log(`[${index}] ${downbeat.time}s: ${downbeat.chord} (${downbeat.nashvilleNumber})`);
          });
        }
        
        // Check syllable-chord alignments
        if (integration.syllableChordAlignments && integration.syllableChordAlignments.length > 0) {
          console.log('\n🎤 First 5 syllable-chord alignments:');
          integration.syllableChordAlignments.slice(0, 5).forEach((alignment, index) => {
            console.log(`[${index}] "${alignment.syllable}" → ${alignment.chord} (${alignment.time}s)`);
          });
        }
        
        return {
          success: true,
          detectedKey: integration.detectedKey,
          tempo: integration.tempo,
          timeSignature: integration.timeSignature,
          downbeatsCount: integration.downbeats?.length || 0,
          alignmentsCount: integration.syllableChordAlignments?.length || 0,
          processingTime: integration.processingTime
        };
      } else {
        console.log('⚠️ No integration data found in response');
        return {
          success: false,
          error: 'No integration data in response',
          response: response
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

// Test tempo detection specifically
async function testTempoDetection() {
  console.log('⏱️ Testing Tempo Detection...');
  
  // Create mock data with known tempo pattern
  const mockChords = [];
  const bpm = 120; // Known tempo
  const beatInterval = 60 / bpm; // 0.5 seconds per beat
  
  // Generate chords with consistent tempo
  for (let i = 0; i < 100; i++) {
    const time = i * 0.2; // 0.2s intervals
    const isDownbeat = (time % beatInterval) < 0.1; // Close to beat
    
    mockChords.push({
      time: time,
      chord: 'C',
      nashvilleNumber: '1',
      isDownbeat: isDownbeat,
      confidence: 0.9
    });
  }
  
  try {
    const params = {
      FunctionName: 'chordscout-v2-musical-integration-orchestrator-dev',
      Payload: JSON.stringify({
        jobId: 'test-tempo-' + Date.now(),
        enhancedChords: mockChords,
        testMode: 'TEMPO_ONLY'
      })
    };
    
    console.log(`🚀 Testing tempo detection with known ${bpm} BPM pattern...`);
    
    const result = await lambda.invoke(params).promise();
    
    if (result.StatusCode === 200) {
      const response = JSON.parse(result.Payload);
      const detectedTempo = response.body?.tempo;
      
      console.log(`🎯 Expected Tempo: ${bpm} BPM`);
      console.log(`📊 Detected Tempo: ${detectedTempo} BPM`);
      
      const accuracy = detectedTempo ? Math.abs(1 - Math.abs(detectedTempo - bpm) / bpm) * 100 : 0;
      console.log(`📈 Tempo Accuracy: ${accuracy.toFixed(1)}%`);
      
      return {
        success: true,
        expectedTempo: bpm,
        detectedTempo: detectedTempo,
        accuracy: accuracy.toFixed(1) + '%'
      };
    } else {
      return { success: false, error: result.Payload };
    }
    
  } catch (error) {
    console.error('❌ Tempo test failed:', error);
    return { success: false, error: error.message };
  }
}

// Run all integration tests
async function runIntegrationTests() {
  console.log('🧪 Running Musical Integration Tests...\n');
  
  const test1 = await testMusicalIntegration();
  console.log('\n' + '='.repeat(50) + '\n');
  const test2 = await testTempoDetection();
  
  console.log('\n🎯 Musical Integration Test Results:');
  console.log('Test 1 (Full Integration):', JSON.stringify(test1, null, 2));
  console.log('Test 2 (Tempo Detection):', JSON.stringify(test2, null, 2));
}

runIntegrationTests().catch(console.error);
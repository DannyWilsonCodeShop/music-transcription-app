// Master Test Runner - Tests All Components in Isolation
// This will run all component tests and provide a comprehensive report

import { execSync } from 'child_process';

async function runAllComponentTests() {
  console.log('🧪 COMPREHENSIVE COMPONENT TESTING');
  console.log('=' .repeat(60));
  console.log('Testing each component of the enhanced music transcription system in isolation');
  console.log('This will help identify exactly which components are working and which need fixes.\n');
  
  const tests = [
    {
      name: 'Audio Extraction from YouTube',
      file: 'test-audio-extraction.js',
      description: 'Tests if YouTube audio can be properly extracted and stored',
      expectedResult: 'Audio file URL with valid MP3/WAV format'
    },
    {
      name: 'Lyrics Extraction from Audio',
      file: 'test-lyrics-extraction.js', 
      description: 'Tests if lyrics can be extracted and syllable-aligned from audio',
      expectedResult: 'Syllable-aligned lyrics with timestamps'
    },
    {
      name: 'Enhanced Chord Detection',
      file: 'test-chord-detection.js',
      description: 'Tests if 0.2s interval chord detection works (1500 chords for 5min)',
      expectedResult: '900 chords for 3min song, 1500 chords for 5min song'
    },
    {
      name: 'Musical Integration',
      file: 'test-musical-integration.js',
      description: 'Tests downbeat detection, tempo analysis, and syllable alignment',
      expectedResult: 'Detected key, tempo, downbeats, and syllable-chord alignments'
    },
    {
      name: 'Enhanced PDF Generator',
      file: 'test-pdf-generator-enhanced.js',
      description: 'Tests measure-based PDF layout with known good data',
      expectedResult: 'Professional measure-based PDF with color-coded chords'
    }
  ];
  
  const results = [];
  
  for (let i = 0; i < tests.length; i++) {
    const test = tests[i];
    console.log(`\n🔍 TEST ${i + 1}/${tests.length}: ${test.name}`);
    console.log(`📋 Description: ${test.description}`);
    console.log(`🎯 Expected: ${test.expectedResult}`);
    console.log('─'.repeat(50));
    
    try {
      console.log(`🚀 Running ${test.file}...`);
      
      // Run the test
      const output = execSync(`node ${test.file}`, { 
        cwd: process.cwd(),
        encoding: 'utf8',
        timeout: 120000 // 2 minute timeout per test
      });
      
      console.log('✅ Test completed successfully');
      console.log('📄 Output preview:', output.substring(0, 300) + '...');
      
      results.push({
        test: test.name,
        status: 'PASSED',
        output: output,
        file: test.file
      });
      
    } catch (error) {
      console.error('❌ Test failed');
      console.error('Error:', error.message);
      
      results.push({
        test: test.name,
        status: 'FAILED',
        error: error.message,
        file: test.file
      });
    }
    
    console.log('─'.repeat(50));
  }
  
  // Generate comprehensive report
  console.log('\n\n🎯 COMPREHENSIVE TEST RESULTS');
  console.log('=' .repeat(60));
  
  const passed = results.filter(r => r.status === 'PASSED').length;
  const failed = results.filter(r => r.status === 'FAILED').length;
  
  console.log(`📊 Overall Results: ${passed}/${results.length} tests passed`);
  console.log(`✅ Passed: ${passed}`);
  console.log(`❌ Failed: ${failed}`);
  
  console.log('\n📋 Detailed Results:');
  results.forEach((result, index) => {
    const status = result.status === 'PASSED' ? '✅' : '❌';
    console.log(`${status} ${index + 1}. ${result.test} - ${result.status}`);
    if (result.status === 'FAILED') {
      console.log(`   Error: ${result.error}`);
    }
  });
  
  // Identify the pipeline bottleneck
  console.log('\n🔍 PIPELINE ANALYSIS:');
  
  if (failed === 0) {
    console.log('🎉 All components working! The issue is likely in the Step Functions workflow integration.');
    console.log('💡 Recommendation: Create a new Step Functions workflow that properly calls the enhanced functions.');
  } else {
    console.log('🚨 Component failures detected:');
    results.filter(r => r.status === 'FAILED').forEach(result => {
      console.log(`   • ${result.test}: Fix required in ${result.file}`);
    });
    console.log('💡 Recommendation: Fix failing components before testing the full pipeline.');
  }
  
  // Generate next steps
  console.log('\n🚀 NEXT STEPS:');
  
  if (passed >= 3) {
    console.log('1. ✅ Core components are working');
    console.log('2. 🔧 Create new Step Functions workflow with proper function calls');
    console.log('3. 🧪 Test end-to-end pipeline with new workflow');
    console.log('4. 🚀 Deploy enhanced system to production');
  } else {
    console.log('1. 🔧 Fix failing component tests');
    console.log('2. 🧪 Re-run component tests until all pass');
    console.log('3. 🔧 Create new Step Functions workflow');
    console.log('4. 🚀 Deploy enhanced system');
  }
  
  console.log('\n📄 Full test logs saved to individual test files');
  console.log('🎯 Use this analysis to determine the exact fix needed for the enhanced system');
}

// Run all tests
runAllComponentTests().catch(console.error);
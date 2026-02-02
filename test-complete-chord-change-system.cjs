// Complete Chord Change Detection System Test
// Tests the entire pipeline from audio analysis to PDF generation

const fs = require('fs');
const path = require('path');
const AWS = require('aws-sdk');

const lambda = new AWS.Lambda({ region: 'us-east-1' });

async function testCompleteChordChangeSystem() {
  console.log('🧪 Testing Complete Chord Change Detection System...\n');
  
  const results = {
    localAnalyzer: null,
    chordChangeDetection: null,
    lambdaCompatibility: null,
    pdfGeneration: null,
    dataReduction: null
  };
  
  try {
    // Test 1: Local Analyzer
    console.log('📊 Test 1: Local Analyzer Performance...');
    const localResult = await testLocalAnalyzer();
    results.localAnalyzer = localResult;
    
    if (localResult.success) {
      console.log(`✅ Local analyzer: ${localResult.chordCount} chord detections`);
    } else {
      console.log(`❌ Local analyzer failed: ${localResult.error}`);
    }
    
    // Test 2: Chord Change Detection
    console.log('\n🔍 Test 2: Chord Change Detection...');
    const chordChangeResult = await testChordChangeDetection();
    results.chordChangeDetection = chordChangeResult;
    
    if (chordChangeResult.success) {
      console.log(`✅ Chord changes: ${chordChangeResult.chordChanges} (${chordChangeResult.dataReduction}% reduction)`);
    } else {
      console.log(`❌ Chord change detection failed: ${chordChangeResult.error}`);
    }
    
    // Test 3: Lambda Compatibility
    console.log('\n🔗 Test 3: Lambda Function Compatibility...');
    const lambdaResult = await testLambdaCompatibility();
    results.lambdaCompatibility = lambdaResult;
    
    if (lambdaResult.success) {
      console.log(`✅ Lambda compatible: ${lambdaResult.dataSize} bytes (${lambdaResult.dynamoDbCompatible ? 'Under' : 'Over'} DynamoDB limit)`);
    } else {
      console.log(`❌ Lambda compatibility failed: ${lambdaResult.error}`);
    }
    
    // Test 4: PDF Generation
    console.log('\n📄 Test 4: PDF Generation with Chord Changes...');
    const pdfResult = await testPdfGeneration();
    results.pdfGeneration = pdfResult;
    
    if (pdfResult.success) {
      console.log(`✅ PDF generated: ${pdfResult.chordsInPdf} chord changes included`);
    } else {
      console.log(`❌ PDF generation failed: ${pdfResult.error}`);
    }
    
    // Test 5: Data Reduction Analysis
    console.log('\n📉 Test 5: Data Reduction Analysis...');
    const reductionResult = analyzeDataReduction(results);
    results.dataReduction = reductionResult;
    
    console.log(`✅ Overall data reduction: ${reductionResult.overallReduction}%`);
    
    // Generate comprehensive report
    const report = generateTestReport(results);
    
    console.log('\n📋 COMPLETE SYSTEM TEST RESULTS:');
    console.log('='.repeat(50));
    
    Object.entries(results).forEach(([test, result]) => {
      const status = result?.success ? '✅ PASS' : '❌ FAIL';
      console.log(`${test.padEnd(20)}: ${status}`);
    });
    
    console.log('\n🎯 SYSTEM READINESS:');
    const allPassed = Object.values(results).every(r => r?.success);
    
    if (allPassed) {
      console.log('✅ ALL TESTS PASSED - SYSTEM READY FOR PRODUCTION');
      console.log('🚀 Chord change detection solution is fully functional');
    } else {
      console.log('❌ SOME TESTS FAILED - REVIEW REQUIRED');
      const failedTests = Object.entries(results)
        .filter(([, result]) => !result?.success)
        .map(([test]) => test);
      console.log(`Failed tests: ${failedTests.join(', ')}`);
    }
    
    // Save detailed report
    const reportPath = path.join(__dirname, 'chord-change-system-test-report.json');
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
    console.log(`\n📄 Detailed report saved: ${reportPath}`);
    
    return {
      success: allPassed,
      results: results,
      report: report
    };
    
  } catch (error) {
    console.error('❌ Complete system test failed:', error);
    return {
      success: false,
      error: error.message,
      results: results
    };
  }
}

async function testLocalAnalyzer() {
  try {
    const { analyzeAudioLocally } = require('./local-server/modules/enhanced-audio-analyzer.js');
    
    const analysis = await analyzeAudioLocally('meetup_ring.mp3', () => {});
    
    return {
      success: true,
      chordCount: analysis.chords.chords.length,
      key: `${analysis.key.root} ${analysis.key.mode}`,
      tempo: analysis.tempo.bpm,
      timeSignature: `${analysis.timeSignature.numerator}/${analysis.timeSignature.denominator}`,
      processingTime: 'simulated'
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

async function testChordChangeDetection() {
  try {
    const { detectChordChanges, consolidateChordChangesPerMeasure } = require('./chord-change-detector.cjs');
    const { analyzeAudioLocally } = require('./local-server/modules/enhanced-audio-analyzer.js');
    
    const analysis = await analyzeAudioLocally('meetup_ring.mp3', () => {});
    const rawChords = analysis.chords.chords;
    
    const timeSignature = {
      numerator: analysis.timeSignature.numerator,
      denominator: analysis.timeSignature.denominator,
      measureDuration: analysis.timeSignature.measureDuration
    };
    
    const chordChangeResult = detectChordChanges(rawChords, timeSignature);
    const consolidatedChanges = consolidateChordChangesPerMeasure(chordChangeResult.chordChanges, 8);
    
    return {
      success: true,
      originalDetections: chordChangeResult.summary.originalDetections,
      chordChanges: consolidatedChanges.length,
      dataReduction: chordChangeResult.summary.dataReduction,
      originalSize: chordChangeResult.summary.originalSize,
      reducedSize: chordChangeResult.summary.reducedSize
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

async function testLambdaCompatibility() {
  try {
    // Load the job data we created earlier
    const jobDataPath = path.join(__dirname, 'local-pdf-job-data.json');
    
    if (!fs.existsSync(jobDataPath)) {
      // Create test data if it doesn't exist
      const { testLocalToPdfPipeline } = require('./test-local-to-pdf-pipeline.cjs');
      await testLocalToPdfPipeline();
    }
    
    const jobData = JSON.parse(fs.readFileSync(jobDataPath, 'utf8'));
    const dataSize = JSON.stringify(jobData).length;
    
    return {
      success: true,
      dataSize: dataSize,
      dynamoDbCompatible: dataSize < 400000,
      chordCount: jobData.chords.length,
      sizeReduction: dataSize < 200000 ? 'Excellent' : dataSize < 300000 ? 'Good' : 'Acceptable'
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

async function testPdfGeneration() {
  try {
    const { testChordChangesToPdf } = require('./test-chord-changes-to-pdf.cjs');
    
    const result = await testChordChangesToPdf();
    
    return {
      success: result.success,
      chordsInPdf: result.chordsInPdf || 0,
      pdfPath: result.pdfPath || null,
      error: result.error || null
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

function analyzeDataReduction(results) {
  const chordResult = results.chordChangeDetection;
  const lambdaResult = results.lambdaCompatibility;
  
  if (!chordResult?.success || !lambdaResult?.success) {
    return {
      success: false,
      error: 'Cannot analyze data reduction - prerequisite tests failed'
    };
  }
  
  const originalSize = chordResult.originalSize;
  const finalSize = lambdaResult.dataSize;
  const overallReduction = ((originalSize - finalSize) / originalSize * 100).toFixed(1);
  
  return {
    success: true,
    originalSize: originalSize,
    finalSize: finalSize,
    overallReduction: parseFloat(overallReduction),
    sizeCategory: finalSize < 100000 ? 'Excellent' : finalSize < 200000 ? 'Good' : 'Acceptable',
    dynamoDbCompatible: finalSize < 400000
  };
}

function generateTestReport(results) {
  return {
    testSuite: 'Complete Chord Change Detection System',
    timestamp: new Date().toISOString(),
    summary: {
      totalTests: Object.keys(results).length,
      passed: Object.values(results).filter(r => r?.success).length,
      failed: Object.values(results).filter(r => !r?.success).length,
      overallSuccess: Object.values(results).every(r => r?.success)
    },
    results: results,
    recommendations: generateRecommendations(results),
    nextSteps: [
      'Deploy updated Lambda functions',
      'Test with real audio files in AWS environment',
      'Monitor DynamoDB storage usage',
      'Verify PDF generation quality',
      'Update frontend to handle chord change data structure'
    ]
  };
}

function generateRecommendations(results) {
  const recommendations = [];
  
  if (!results.localAnalyzer?.success) {
    recommendations.push('Fix local analyzer issues before deployment');
  }
  
  if (!results.chordChangeDetection?.success) {
    recommendations.push('Debug chord change detection algorithm');
  }
  
  if (!results.lambdaCompatibility?.success) {
    recommendations.push('Review Lambda function compatibility');
  }
  
  if (!results.pdfGeneration?.success) {
    recommendations.push('Fix PDF generation with chord changes');
  }
  
  if (results.dataReduction?.overallReduction < 50) {
    recommendations.push('Consider additional data optimization techniques');
  }
  
  if (recommendations.length === 0) {
    recommendations.push('System is ready for production deployment');
    recommendations.push('Monitor performance in production environment');
    recommendations.push('Consider implementing real-time chord analysis');
  }
  
  return recommendations;
}

// Run the complete test suite
if (require.main === module) {
  testCompleteChordChangeSystem()
    .then(result => {
      console.log('\n🎯 FINAL RESULT:');
      if (result.success) {
        console.log('🎉 COMPLETE CHORD CHANGE DETECTION SYSTEM: READY FOR PRODUCTION');
      } else {
        console.log('❌ SYSTEM NOT READY - ISSUES FOUND');
        if (result.error) {
          console.log('Error:', result.error);
        }
      }
    })
    .catch(error => {
      console.error('❌ Test suite failed:', error.message);
    });
}

module.exports = { testCompleteChordChangeSystem };
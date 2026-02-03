/**
 * Test and Display Passing Chord Data
 * Shows the difference between downbeat (RED) and passing (BLACK) chords
 */

const { generateMockData } = require('./generate-mock-data.cjs');

function testPassingChords() {
  console.log('🎵 Testing Passing Chord Data Generation');
  console.log('=======================================');
  
  // Generate mock data with passing chords
  const mockData = generateMockData();
  
  console.log(`📊 Generated data for: ${mockData.videoTitle}`);
  console.log(`  • Total chords: ${mockData.chordsData.totalChords}`);
  console.log(`  • Chord changes every: 0.5 seconds`);
  console.log(`  • Total measures: ${mockData.alignmentData.measureBasedLayout.length}`);
  
  // Analyze first 8 measures to show passing chord structure
  console.log('\n🎼 First 8 Measures - Chord Analysis:');
  console.log('=====================================');
  
  mockData.alignmentData.measureBasedLayout.slice(0, 8).forEach(measure => {
    console.log(`\n📏 Measure ${measure.measureNumber}:`);
    
    // Show all chords in this measure
    console.log('  All Chords:');
    measure.chords.forEach(chord => {
      const type = chord.isDownbeat ? '🔴 DOWNBEAT (RED)' : '⚫ PASSING (BLACK)';
      console.log(`    ${chord.timestamp.toFixed(1)}s: ${chord.chord}(${chord.nashvilleNumber}) - ${type} (conf: ${chord.confidence.toFixed(2)})`);
    });
    
    // Show primary vs passing chords
    if (measure.primaryChord) {
      console.log(`  🔴 Primary Chord: ${measure.primaryChord.chord}(${measure.primaryChord.nashvilleNumber})`);
    }
    
    if (measure.passingChords && measure.passingChords.length > 0) {
      console.log(`  ⚫ Passing Chords: ${measure.passingChords.map(c => `${c.chord}(${c.nashvilleNumber})`).join(', ')}`);
    }
    
    // Show lyrics
    const lyrics = measure.syllables.map(s => s.text).join(' ');
    console.log(`  🎤 Lyrics: "${lyrics}"`);
  });
  
  // Show chord progression pattern
  console.log('\n🎸 Chord Progression Pattern:');
  console.log('=============================');
  
  const first32Chords = mockData.chordsData.chords.slice(0, 32);
  console.log('First 16 seconds (32 chord changes at 0.5s intervals):');
  
  first32Chords.forEach((chord, index) => {
    const type = chord.isDownbeat ? 'RED' : 'BLK';
    const measure = Math.floor(chord.timestamp / 4) + 1;
    const beat = ((chord.timestamp % 4) * 1) + 1;
    console.log(`${(index + 1).toString().padStart(2)}. ${chord.timestamp.toFixed(1)}s M${measure}:${beat.toFixed(1)} ${chord.chord.padEnd(4)} (${chord.nashvilleNumber.padEnd(3)}) ${type}`);
  });
  
  // Show layout preview
  console.log('\n📄 PDF Layout Preview with Passing Chords:');
  console.log('==========================================');
  
  console.log('Line 1 (Measures 1-4):');
  console.log('Chords:  🔴1  🔴1  🔴2m  🔴2m');
  console.log('         ⚫V  ⚫vi ⚫I   ⚫V');
  console.log('Lyrics:  The  go   round round');
  console.log('         wheels round and  and');
  console.log('         on the and   round, round');
  console.log('         bus   round');
  console.log('');
  
  console.log('Legend:');
  console.log('🔴 RED = Downbeat chords (primary harmony)');
  console.log('⚫ BLACK = Passing chords (secondary harmony)');
  
  // Statistics
  const downbeats = mockData.chordsData.chords.filter(c => c.isDownbeat);
  const passingChords = mockData.chordsData.chords.filter(c => !c.isDownbeat);
  
  console.log('\n📊 Chord Statistics:');
  console.log('====================');
  console.log(`Total Chords: ${mockData.chordsData.chords.length}`);
  console.log(`🔴 Downbeat Chords: ${downbeats.length} (${(downbeats.length / mockData.chordsData.chords.length * 100).toFixed(1)}%)`);
  console.log(`⚫ Passing Chords: ${passingChords.length} (${(passingChords.length / mockData.chordsData.chords.length * 100).toFixed(1)}%)`);
  console.log(`Average Confidence - Downbeats: ${(downbeats.reduce((sum, c) => sum + c.confidence, 0) / downbeats.length).toFixed(3)}`);
  console.log(`Average Confidence - Passing: ${(passingChords.reduce((sum, c) => sum + c.confidence, 0) / passingChords.length).toFixed(3)}`);
  
  return mockData;
}

// Run the test
if (require.main === module) {
  const mockData = testPassingChords();
  
  console.log('\n🎉 Passing Chord Test Complete!');
  console.log('\n📁 Files to check:');
  console.log('  • wheels-bus-with-passing-chords.pdf (new PDF with passing chords)');
  console.log('  • amazing-grace-enhanced-analysis.pdf (original example)');
  console.log('\nThe new PDF shows both RED downbeat chords and BLACK passing chords!');
}

module.exports = { testPassingChords };
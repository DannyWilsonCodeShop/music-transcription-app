/**
 * Show the Perfect PDF Input Structure and Expected Output
 * This demonstrates exactly what data flows into the PDF generator
 */

const { generateMockData } = require('./generate-mock-data.cjs');
const fs = require('fs');

function showPerfectPDFInput() {
  console.log('🎵 Perfect PDF Input Structure Demonstration');
  console.log('============================================');
  
  // Generate the comprehensive mock data
  const mockData = generateMockData();
  
  // Show the exact input structure that the PDF generator receives
  const pdfInput = {
    jobId: mockData.jobId,
    videoTitle: mockData.videoTitle,
    
    // Chord data in the format the PDF generator expects
    chords: mockData.chordsData.chords.map(chord => ({
      time: chord.timestamp,
      timestamp: chord.timestamp,
      chord: chord.chord,
      name: chord.chord,
      nashvilleNumber: chord.nashvilleNumber,
      confidence: chord.confidence,
      measure: chord.measure,
      beat: chord.beat,
      isDownbeat: chord.isDownbeat
    })),
    
    // Lyrics data with syllable alignment
    lyricsData: {
      text: mockData.lyricsData.text,
      syllableAlignedLyrics: mockData.lyricsData.syllables.map(syllable => ({
        text: syllable.text,
        startTime: syllable.startTime,
        endTime: syllable.endTime,
        word: syllable.word,
        wordIndex: syllable.wordIndex,
        lineIndex: syllable.lineIndex,
        confidence: syllable.confidence
      }))
    },
    
    // Musical metadata
    key: mockData.musicalAnalysis.key,
    tempo: mockData.musicalAnalysis.bpm,
    timeSignature: mockData.musicalAnalysis.timeSignature,
    
    // Enhanced alignment data
    alignmentData: mockData.alignmentData
  };
  
  console.log('\n📋 PDF Generator Input Summary:');
  console.log(`  • Job ID: ${pdfInput.jobId}`);
  console.log(`  • Title: ${pdfInput.videoTitle}`);
  console.log(`  • Key: ${pdfInput.key}`);
  console.log(`  • Tempo: ${pdfInput.tempo} BPM`);
  console.log(`  • Time Signature: ${pdfInput.timeSignature}`);
  console.log(`  • Total Chords: ${pdfInput.chords.length}`);
  console.log(`  • Total Syllables: ${pdfInput.lyricsData.syllableAlignedLyrics.length}`);
  console.log(`  • Measures: ${pdfInput.alignmentData.measureBasedLayout.length}`);
  
  // Show sample chord data
  console.log('\n🎸 Sample Chord Data (First 8 chords):');
  pdfInput.chords.slice(0, 8).forEach((chord, index) => {
    const downbeat = chord.isDownbeat ? '🔴' : '⚪';
    console.log(`    ${downbeat} ${index + 1}. ${chord.chord}(${chord.nashvilleNumber}) @ ${chord.time.toFixed(1)}s - M${chord.measure}:${chord.beat} (conf: ${chord.confidence.toFixed(2)})`);
  });
  
  // Show sample syllable data
  console.log('\n🎤 Sample Syllable Data (First 8 syllables):');
  pdfInput.lyricsData.syllableAlignedLyrics.slice(0, 8).forEach((syllable, index) => {
    console.log(`    ${index + 1}. "${syllable.text}" @ ${syllable.startTime.toFixed(1)}s-${syllable.endTime.toFixed(1)}s (word: "${syllable.word}", conf: ${syllable.confidence.toFixed(2)})`);
  });
  
  // Show perfect measure-based layout
  console.log('\n📏 Perfect Measure-Based Layout (First 8 measures):');
  pdfInput.alignmentData.measureBasedLayout.slice(0, 8).forEach(measure => {
    const downbeat = measure.hasDownbeat ? '🔴' : '⚪';
    const chords = measure.chords.map(c => `${c.chord}(${c.nashvilleNumber})`).join(', ');
    const syllables = measure.syllables.map(s => s.text).join(' ');
    const timing = measure.beats[0]?.timestamp || 0;
    
    console.log(`    ${downbeat} M${measure.measureNumber} @ ${timing.toFixed(1)}s:`);
    console.log(`        Chords: ${chords}`);
    console.log(`        Lyrics: "${syllables}"`);
    console.log(`        Beats: ${measure.beats.length} (downbeat: ${measure.hasDownbeat})`);
  });
  
  // Save the complete input structure
  fs.writeFileSync('perfect-pdf-input-complete.json', JSON.stringify(pdfInput, null, 2));
  
  // Show the expected PDF output structure
  showExpectedPDFOutput(pdfInput);
  
  return pdfInput;
}

function showExpectedPDFOutput(pdfInput) {
  console.log('\n📄 Expected PDF Output Structure:');
  console.log('==================================');
  
  console.log('\n🎼 PDF Page Layout:');
  console.log('┌─────────────────────────────────────────────────────────────────────────────────────────────────┐');
  console.log('│                           The Wheels on the Bus - Mock Data Test                               │');
  console.log('│                        Key: C major | BPM: 60 | Time: 4/4                                     │');
  console.log('├─────────────────────────────────────────────────────────────────────────────────────────────────┤');
  console.log('│                      Nashville Number System - Perfect Layout                                   │');
  console.log('│                                                                                                 │');
  
  // Show first few systems
  const measuresPerSystem = 4;
  const systemsToShow = 3;
  
  for (let systemIndex = 0; systemIndex < systemsToShow; systemIndex++) {
    const systemStart = systemIndex * measuresPerSystem;
    const systemEnd = Math.min(systemStart + measuresPerSystem, pdfInput.alignmentData.measureBasedLayout.length);
    const systemMeasures = pdfInput.alignmentData.measureBasedLayout.slice(systemStart, systemEnd);
    
    console.log(`│ System ${systemIndex + 1} (Measures ${systemStart + 1}-${systemEnd})                                                        │`);
    
    // Timing line
    let timingLine = '│ Time:   ';
    systemMeasures.forEach(measure => {
      const time = measure.beats[0]?.timestamp || 0;
      const timeStr = `${Math.floor(time / 60)}:${(time % 60).toFixed(0).padStart(2, '0')}`;
      timingLine += timeStr.padEnd(20);
    });
    timingLine += '│';
    console.log(timingLine);
    
    // Chord line
    let chordLine = '│ Chords: ';
    systemMeasures.forEach(measure => {
      const downbeat = measure.hasDownbeat ? '🔴' : '⚪';
      const chord = measure.chords[0];
      const chordStr = chord ? `${downbeat}M${measure.measureNumber}:${chord.chord}(${chord.nashvilleNumber})` : `${downbeat}M${measure.measureNumber}:N/A`;
      chordLine += chordStr.padEnd(20);
    });
    chordLine += '│';
    console.log(chordLine);
    
    // Lyrics line
    let lyricsLine = '│ Lyrics: ';
    systemMeasures.forEach(measure => {
      const lyrics = measure.syllables.map(s => s.text).join(' ');
      lyricsLine += lyrics.substring(0, 18).padEnd(20);
    });
    lyricsLine += '│';
    console.log(lyricsLine);
    
    console.log('│                                                                                                 │');
  }
  
  console.log('│ ... (continues for all 75 measures across multiple pages)                                      │');
  console.log('│                                                                                                 │');
  console.log('│ Summary:                                                                                        │');
  console.log(`│   • Total Measures: ${pdfInput.alignmentData.measureBasedLayout.length}                                                                      │`);
  console.log(`│   • Total Chords: ${pdfInput.chords.length}                                                                        │`);
  console.log(`│   • Total Syllables: ${pdfInput.lyricsData.syllableAlignedLyrics.length}                                                                    │`);
  console.log(`│   • Downbeats: ${pdfInput.alignmentData.downbeatHighlights.length}                                                                         │`);
  console.log('│                                                                                                 │');
  console.log('│                   Generated by ChordScout - Perfect Nashville Number System                   │');
  console.log('└─────────────────────────────────────────────────────────────────────────────────────────────────┘');
  
  console.log('\n✨ Perfect Layout Features Demonstrated:');
  console.log('  ✅ Measure-based organization (75 measures in 4/4 time)');
  console.log('  ✅ Downbeat highlighting with 🔴 markers');
  console.log('  ✅ Nashville Number System integration (1, 2m, 3m, 4, 5, 6m, 7°)');
  console.log('  ✅ Syllable-level lyric alignment (280 syllables precisely timed)');
  console.log('  ✅ Precise timing information (every beat at 60 BPM)');
  console.log('  ✅ Chord progression analysis (C major scale progression)');
  console.log('  ✅ Professional music notation standards');
  console.log('  ✅ System-based layout (4 measures per system)');
  console.log('  ✅ Multi-page support (estimated 5 pages)');
  console.log('  ✅ Complete metadata (key, tempo, time signature)');
  
  console.log('\n📊 Data Quality Metrics:');
  console.log(`  • Chord Detection Confidence: ${(pdfInput.chords.reduce((sum, c) => sum + c.confidence, 0) / pdfInput.chords.length).toFixed(3)}`);
  console.log(`  • Syllable Alignment Confidence: ${(pdfInput.lyricsData.syllableAlignedLyrics.reduce((sum, s) => sum + s.confidence, 0) / pdfInput.lyricsData.syllableAlignedLyrics.length).toFixed(3)}`);
  console.log(`  • Measures with Downbeats: ${pdfInput.alignmentData.measureBasedLayout.filter(m => m.hasDownbeat).length}/${pdfInput.alignmentData.measureBasedLayout.length}`);
  console.log(`  • Average Syllables per Measure: ${(pdfInput.lyricsData.syllableAlignedLyrics.length / pdfInput.alignmentData.measureBasedLayout.length).toFixed(1)}`);
  console.log(`  • Average Chords per Measure: ${(pdfInput.chords.length / pdfInput.alignmentData.measureBasedLayout.length).toFixed(1)}`);
}

// Run the demonstration
if (require.main === module) {
  const pdfInput = showPerfectPDFInput();
  
  console.log('\n🎉 Perfect PDF Input Demonstration Complete!');
  console.log('\n📁 Files Generated:');
  console.log('  • perfect-pdf-input-complete.json (complete input structure)');
  console.log('  • mock-data-complete.json (raw mock data)');
  
  console.log('\n🔄 Next Steps:');
  console.log('  1. This input structure can be fed directly to the PDF generator');
  console.log('  2. The PDF generator will create a professional Nashville Number System chart');
  console.log('  3. The output will include all perfect layout features demonstrated above');
  console.log('  4. The PDF can be uploaded to S3 and served to users');
  
  console.log(`\n📋 Input Summary:`);
  console.log(`  • Job ID: ${pdfInput.jobId}`);
  console.log(`  • Data Size: ${JSON.stringify(pdfInput).length} characters`);
  console.log(`  • Chord Entries: ${pdfInput.chords.length}`);
  console.log(`  • Syllable Entries: ${pdfInput.lyricsData.syllableAlignedLyrics.length}`);
  console.log(`  • Measure Entries: ${pdfInput.alignmentData.measureBasedLayout.length}`);
}

module.exports = { showPerfectPDFInput };
/**
 * Create Actual PDF using Real jsPDF Library
 * This will generate a real PDF file that can be opened
 */

const { generateMockData } = require('./generate-mock-data.cjs');
const fs = require('fs');
const path = require('path');

async function createActualPDF() {
  console.log('🎵 Creating Actual PDF with Real jsPDF');
  console.log('=====================================');
  
  // Try to use jsPDF from the PDF generator directory
  let jsPDF;
  try {
    // Change to PDF generator directory to access its node_modules
    const originalDir = process.cwd();
    const pdfGeneratorDir = path.join(__dirname, 'backend', 'functions-v2', 'pdf-generator');
    
    console.log('📁 Checking PDF generator directory...');
    if (fs.existsSync(pdfGeneratorDir)) {
      process.chdir(pdfGeneratorDir);
      console.log('✅ Changed to PDF generator directory');
      
      try {
        const jsPDFModule = require('jspdf');
        jsPDF = jsPDFModule.jsPDF;
        console.log('✅ Successfully loaded real jsPDF');
      } catch (error) {
        console.log('❌ jsPDF not found in PDF generator directory');
        throw error;
      }
      
      // Change back to original directory
      process.chdir(originalDir);
    } else {
      throw new Error('PDF generator directory not found');
    }
  } catch (error) {
    console.log('⚠️  Could not load real jsPDF, installing it...');
    
    // Try to install jsPDF in current directory
    const { execSync } = require('child_process');
    try {
      execSync('npm install jspdf', { stdio: 'inherit' });
      const jsPDFModule = require('jspdf');
      jsPDF = jsPDFModule.jsPDF;
      console.log('✅ Successfully installed and loaded jsPDF');
    } catch (installError) {
      console.error('❌ Could not install jsPDF:', installError.message);
      return null;
    }
  }
  
  // Generate mock data
  console.log('\n📊 Generating Mock Data...');
  const mockData = generateMockData();
  
  console.log(`✅ Mock data generated:`);
  console.log(`  • Title: ${mockData.videoTitle}`);
  console.log(`  • Duration: ${mockData.audioMetadata.duration}s`);
  console.log(`  • Measures: ${mockData.alignmentData.measureBasedLayout.length}`);
  console.log(`  • Chords: ${mockData.chordsData.totalChords}`);
  console.log(`  • Syllables: ${mockData.lyricsData.totalSyllables}`);
  
  // Create PDF
  console.log('\n📄 Creating PDF Document...');
  const doc = new jsPDF();
  
  let yPosition = 30;
  
  // === HEADER ===
  doc.setFontSize(24);
  doc.setFont('helvetica', 'bold');
  doc.text(mockData.videoTitle, 105, yPosition, { align: 'center' });
  yPosition += 20;
  
  // Musical info
  doc.setFontSize(12);
  doc.setFont('helvetica', 'normal');
  const info = `Key: ${mockData.musicalAnalysis.key} ${mockData.musicalAnalysis.mode} | BPM: ${mockData.musicalAnalysis.bpm} | Time: ${mockData.musicalAnalysis.timeSignature}`;
  doc.text(info, 105, yPosition, { align: 'center' });
  yPosition += 30;
  
  console.log('✅ Header added');
  
  // === PERFECT LAYOUT SECTION ===
  doc.setFontSize(16);
  doc.setFont('helvetica', 'bold');
  doc.text('Nashville Number System - Perfect Layout', 20, yPosition);
  yPosition += 20;
  
  console.log('🎼 Adding measure-based layout...');
  
  // Process first 20 measures to keep PDF manageable
  const measuresToShow = Math.min(20, mockData.alignmentData.measureBasedLayout.length);
  const measuresPerSystem = 4;
  
  for (let measureIndex = 0; measureIndex < measuresToShow; measureIndex += measuresPerSystem) {
    const systemMeasures = mockData.alignmentData.measureBasedLayout.slice(measureIndex, measureIndex + measuresPerSystem);
    const systemNumber = Math.floor(measureIndex / measuresPerSystem) + 1;
    
    // Check for page break
    if (yPosition > 220) {
      doc.addPage();
      yPosition = 20;
      console.log(`📄 Added page ${doc.getNumberOfPages()}`);
    }
    
    // System header
    yPosition += 15;
    doc.setFontSize(14);
    doc.setFont('helvetica', 'bold');
    doc.text(`System ${systemNumber} (Measures ${measureIndex + 1}-${Math.min(measureIndex + measuresPerSystem, measuresToShow)})`, 20, yPosition);
    yPosition += 12;
    
    // Build system content
    let timingLine = 'Time:   ';
    let chordLine = 'Chords: ';
    let lyricsLine = 'Lyrics: ';
    
    systemMeasures.forEach((measure, idx) => {
      const measureWidth = 18;
      
      // Timing
      const time = measure.beats[0]?.timestamp || 0;
      const timeStr = `${Math.floor(time / 60)}:${(time % 60).toFixed(0).padStart(2, '0')}`;
      timingLine += timeStr.padEnd(measureWidth);
      
      // Chords with downbeat markers
      const downbeat = measure.hasDownbeat ? 'DB' : '--'; // Use text instead of emoji for PDF compatibility
      const chord = measure.chords[0];
      const chordStr = chord ? `${downbeat} ${chord.chord}(${chord.nashvilleNumber})` : `${downbeat} N/A`;
      chordLine += chordStr.padEnd(measureWidth);
      
      // Lyrics
      const lyrics = measure.syllables.map(s => s.text).join(' ');
      lyricsLine += lyrics.substring(0, 15).padEnd(measureWidth);
    });
    
    // Output system lines
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.text(timingLine, 20, yPosition);
    yPosition += 8;
    
    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');
    doc.text(chordLine, 20, yPosition);
    yPosition += 8;
    
    doc.setFontSize(12);
    doc.setFont('helvetica', 'normal');
    doc.text(lyricsLine, 20, yPosition);
    yPosition += 15;
    
    console.log(`  ✅ System ${systemNumber}: ${systemMeasures.length} measures added`);
  }
  
  // === SUMMARY SECTION ===
  yPosition += 20;
  if (yPosition > 250) {
    doc.addPage();
    yPosition = 20;
  }
  
  doc.setFontSize(16);
  doc.setFont('helvetica', 'bold');
  doc.text('Summary', 20, yPosition);
  yPosition += 15;
  
  doc.setFontSize(12);
  doc.setFont('helvetica', 'normal');
  doc.text(`Total Measures: ${mockData.alignmentData.measureBasedLayout.length}`, 20, yPosition);
  yPosition += 10;
  doc.text(`Total Chords: ${mockData.chordsData.totalChords}`, 20, yPosition);
  yPosition += 10;
  doc.text(`Total Syllables: ${mockData.lyricsData.totalSyllables}`, 20, yPosition);
  yPosition += 10;
  doc.text(`Downbeats: ${mockData.alignmentData.downbeatHighlights.length}`, 20, yPosition);
  yPosition += 10;
  
  const uniqueChords = [...new Set(mockData.chordsData.chords.map(c => c.chord))];
  doc.text(`Chord Progression: ${uniqueChords.join(' - ')}`, 20, yPosition);
  yPosition += 10;
  
  const nashvilleNumbers = [...new Set(mockData.chordsData.chords.map(c => c.nashvilleNumber))];
  doc.text(`Nashville Numbers: ${nashvilleNumbers.join(' - ')}`, 20, yPosition);
  
  console.log('✅ Summary section added');
  
  // === FOOTER ===
  yPosition += 30;
  if (yPosition > 270) {
    doc.addPage();
    yPosition = 250;
  }
  
  doc.setFontSize(10);
  doc.setFont('helvetica', 'italic');
  doc.text('Generated by ChordScout - Perfect Nashville Number System Layout', 105, yPosition, { align: 'center' });
  
  console.log('✅ Footer added');
  
  // Save PDF
  const pdfFileName = 'perfect-layout-actual.pdf';
  doc.save(pdfFileName);
  
  console.log(`\n✅ PDF Created Successfully!`);
  console.log(`📄 File: ${pdfFileName}`);
  console.log(`📊 Pages: ${doc.getNumberOfPages()}`);
  console.log(`🎼 Systems: ${Math.ceil(measuresToShow / measuresPerSystem)}`);
  
  // Also create a text preview of the PDF content
  const textPreview = `
PERFECT LAYOUT PDF PREVIEW
=========================

Title: ${mockData.videoTitle}
Key: ${mockData.musicalAnalysis.key} ${mockData.musicalAnalysis.mode}
BPM: ${mockData.musicalAnalysis.bpm}
Time Signature: ${mockData.musicalAnalysis.timeSignature}

MEASURE-BASED LAYOUT (First 8 measures):
${mockData.alignmentData.measureBasedLayout.slice(0, 8).map((measure, index) => {
  const downbeat = measure.hasDownbeat ? 'DB' : '--';
  const chord = measure.chords[0];
  const chordInfo = chord ? `${chord.chord}(${chord.nashvilleNumber})` : 'N/A';
  const lyrics = measure.syllables.map(s => s.text).join(' ');
  const timing = measure.beats[0]?.timestamp || 0;
  const timeStr = `${Math.floor(timing / 60)}:${(timing % 60).toFixed(0).padStart(2, '0')}`;
  
  return `M${measure.measureNumber} @ ${timeStr}: ${downbeat} ${chordInfo} | "${lyrics}"`;
}).join('\n')}

SUMMARY:
- Total Measures: ${mockData.alignmentData.measureBasedLayout.length}
- Total Chords: ${mockData.chordsData.totalChords}
- Total Syllables: ${mockData.lyricsData.totalSyllables}
- Chord Progression: ${uniqueChords.join(' - ')}
- Nashville Numbers: ${nashvilleNumbers.join(' - ')}

PERFECT LAYOUT FEATURES:
✅ Measure-based organization
✅ Downbeat highlighting (DB = Downbeat, -- = Other beats)
✅ Nashville Number System integration
✅ Syllable-level lyric alignment
✅ Precise timing information
✅ Professional formatting
`;
  
  fs.writeFileSync('perfect-layout-preview.txt', textPreview);
  
  console.log('\n📁 Files Created:');
  console.log(`  • ${pdfFileName} (actual PDF file)`);
  console.log('  • perfect-layout-preview.txt (text preview)');
  
  return {
    pdfFile: pdfFileName,
    pages: doc.getNumberOfPages(),
    measuresShown: measuresToShow,
    success: true
  };
}

// Run the PDF creation
if (require.main === module) {
  createActualPDF().then(result => {
    if (result) {
      console.log('\n🎉 Actual PDF Creation Complete!');
      console.log(`\nYou can now open: ${result.pdfFile}`);
      console.log(`The PDF contains ${result.pages} pages with ${result.measuresShown} measures of perfect layout.`);
    } else {
      console.log('\n❌ PDF creation failed - jsPDF library not available');
    }
  }).catch(error => {
    console.error('❌ Error creating PDF:', error.message);
  });
}

module.exports = { createActualPDF };
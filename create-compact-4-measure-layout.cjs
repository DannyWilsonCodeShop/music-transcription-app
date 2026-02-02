/**
 * Compact 4-Measure Layout - Exact Amazing Grace Dimensions
 * Proper measure widths to fit 4 measures per line with minimal spacing
 */

const { generateMockData } = require('./generate-mock-data.cjs');
const fs = require('fs');

async function createCompact4MeasureLayout() {
  console.log('🎵 Creating Compact 4-Measure Layout (Amazing Grace Exact)');
  console.log('=========================================================');
  
  // Load jsPDF
  const { jsPDF } = require('jspdf');
  const doc = new jsPDF();
  
  console.log('📊 Using compact dimensions to fit 4 measures per line');
  
  let yPosition = 30;
  
  // === HEADER ===
  doc.setFontSize(18);
  doc.setFont('helvetica', 'bold');
  doc.text('The Wheels on the Bus', 105, yPosition, { align: 'center' });
  yPosition += 12;
  
  doc.setFontSize(11);
  doc.setFont('helvetica', 'normal');
  doc.text('Key: C major | Tempo: 60 BPM | Meter: 4/4', 105, yPosition, { align: 'center' });
  yPosition += 20;
  
  console.log('✅ Header added');
  
  // === COMPACT 4-MEASURE LINES ===
  const totalLines = 4; // Show 4 lines
  
  // Create compact measure data
  const measureData = createCompactMeasureData();
  
  for (let lineIndex = 0; lineIndex < totalLines; lineIndex++) {
    // Check for page break
    if (yPosition > 230) {
      doc.addPage();
      yPosition = 30;
    }
    
    // Add verse label every 2 lines
    if (lineIndex % 2 === 0) {
      yPosition += 8;
      doc.setFontSize(12);
      doc.setFont('helvetica', 'bold');
      doc.text(`Verse ${Math.floor(lineIndex / 2) + 1}`, 20, yPosition);
      yPosition += 12;
    }
    
    // Get 4 measures for this line
    const lineMeasures = measureData.slice(lineIndex * 4, (lineIndex + 1) * 4);
    
    // Generate compact 4-measure line
    generateCompact4MeasureLine(doc, lineMeasures, yPosition, lineIndex + 1);
    yPosition += 25; // Minimal spacing between lines
    
    console.log(`✅ Line ${lineIndex + 1}: 4 compact measures`);
  }
  
  // Save PDF
  const fileName = 'compact-4-measure-layout.pdf';
  doc.save(fileName);
  
  console.log(`\n✅ Compact 4-Measure Layout Created!`);
  console.log(`📄 File: ${fileName}`);
  
  return { fileName };
}

/**
 * Generate compact 4-measure line that fits on page
 */
function generateCompact4MeasureLine(doc, measures, yPosition, lineNumber) {
  // COMPACT LAYOUT CONSTANTS (matching Amazing Grace)
  const lineStartX = 20;
  const measureWidth = 42; // Much smaller measures to fit 4 per line
  const totalLineWidth = measureWidth * 4; // 168px total (fits in 170px available)
  
  // Y positions - very tight spacing
  const lyricsY = yPosition;
  const numbersY = yPosition + 8; // Only 8px gap
  
  console.log(`  📏 Line ${lineNumber}: 4 measures × ${measureWidth}px = ${totalLineWidth}px total`);
  
  // Draw measure boundaries (light gray)
  doc.setDrawColor(220, 220, 220);
  for (let i = 0; i <= 4; i++) {
    const x = lineStartX + (i * measureWidth);
    doc.line(x, yPosition - 3, x, yPosition + 15);
  }
  
  // Process each measure
  for (let measureIndex = 0; measureIndex < 4; measureIndex++) {
    const measure = measures[measureIndex];
    if (!measure) continue;
    
    const measureStartX = lineStartX + (measureIndex * measureWidth);
    
    console.log(`    🎼 M${measureIndex + 1}: "${measure.syllables.map(s => s.text).join(' ')}" → ${measure.chords.map(c => c.number).join(' ')}`);
    
    // Generate compact measure content
    generateCompactMeasureContent(doc, measure, measureStartX, measureWidth, lyricsY, numbersY);
  }
}

/**
 * Generate compact content for a single measure
 */
function generateCompactMeasureContent(doc, measure, startX, measureWidth, lyricsY, numbersY) {
  const syllables = measure.syllables || [];
  const chords = measure.chords || [];
  const syllableCount = syllables.length;
  
  if (syllableCount === 0) return;
  
  // COMPACT SPACING CALCULATION
  const padding = 2; // Minimal padding
  const availableWidth = measureWidth - (padding * 2);
  const syllableWidth = availableWidth / syllableCount;
  
  // Position each syllable and chord
  syllables.forEach((syllable, index) => {
    const chord = chords[index] || chords[0] || { number: '1' };
    const isDownbeat = index === 0;
    
    // Calculate compact position
    const syllableX = startX + padding + (index * syllableWidth) + (syllableWidth / 2);
    
    // Draw syllable (compact font)
    doc.setFontSize(10); // Smaller font to fit
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(0, 0, 0);
    
    // Truncate long syllables
    let displayText = syllable.text;
    if (displayText.length > 4) {
      displayText = displayText.substring(0, 3) + '-';
    }
    
    doc.text(displayText, syllableX, lyricsY, { align: 'center' });
    
    // Draw chord number (compact)
    doc.setFontSize(10);
    doc.setFont('helvetica', 'bold');
    
    if (isDownbeat) {
      doc.setTextColor(255, 0, 0); // RED for downbeat
    } else {
      doc.setTextColor(0, 0, 0); // BLACK for others
    }
    
    doc.text(chord.number, syllableX, numbersY, { align: 'center' });
  });
  
  // Reset color
  doc.setTextColor(0, 0, 0);
}

/**
 * Create compact measure data that fits well
 */
function createCompactMeasureData() {
  return [
    // Line 1 - Verse 1
    {
      syllables: [{ text: 'The' }, { text: 'wheels' }, { text: 'on' }, { text: 'the' }],
      chords: [{ number: '1' }, { number: '1' }, { number: '1' }, { number: '1' }]
    },
    {
      syllables: [{ text: 'bus' }, { text: 'go' }, { text: 'round' }],
      chords: [{ number: '1' }, { number: '5' }, { number: '5' }]
    },
    {
      syllables: [{ text: 'and' }, { text: 'round,' }],
      chords: [{ number: '6m' }, { number: '6m' }]
    },
    {
      syllables: [{ text: 'round' }, { text: 'and' }, { text: 'round' }],
      chords: [{ number: '4' }, { number: '1' }, { number: '1' }]
    },
    
    // Line 2 - Verse 1 ending
    {
      syllables: [{ text: 'The' }, { text: 'wheels' }, { text: 'on' }, { text: 'the' }],
      chords: [{ number: '1' }, { number: '1' }, { number: '1' }, { number: '1' }]
    },
    {
      syllables: [{ text: 'bus' }, { text: 'go' }, { text: 'round' }],
      chords: [{ number: '1' }, { number: '5' }, { number: '5' }]
    },
    {
      syllables: [{ text: 'and' }, { text: 'round' }],
      chords: [{ number: '6m' }, { number: '4' }]
    },
    {
      syllables: [{ text: 'All' }, { text: 'through' }, { text: 'town' }],
      chords: [{ number: '1' }, { number: '5' }, { number: '1' }]
    },
    
    // Line 3 - Verse 2 (Wipers)
    {
      syllables: [{ text: 'The' }, { text: 'wi-' }, { text: 'pers' }],
      chords: [{ number: '1' }, { number: '1' }, { number: '1' }]
    },
    {
      syllables: [{ text: 'on' }, { text: 'the' }, { text: 'bus' }],
      chords: [{ number: '1' }, { number: '1' }, { number: '1' }]
    },
    {
      syllables: [{ text: 'go' }, { text: 'swish' }],
      chords: [{ number: '5' }, { number: '5' }]
    },
    {
      syllables: [{ text: 'swish' }, { text: 'swish' }],
      chords: [{ number: '6m' }, { number: '4' }]
    },
    
    // Line 4 - Verse 2 ending
    {
      syllables: [{ text: 'Swish' }, { text: 'swish' }, { text: 'swish,' }],
      chords: [{ number: '1' }, { number: '1' }, { number: '1' }]
    },
    {
      syllables: [{ text: 'swish' }, { text: 'swish' }],
      chords: [{ number: '5' }, { number: '5' }]
    },
    {
      syllables: [{ text: 'swish' }, { text: 'All' }],
      chords: [{ number: '6m' }, { number: '4' }]
    },
    {
      syllables: [{ text: 'through' }, { text: 'the' }, { text: 'town' }],
      chords: [{ number: '1' }, { number: '5' }, { number: '1' }]
    }
  ];
}

// Run the compact layout creation
if (require.main === module) {
  createCompact4MeasureLayout().then(result => {
    console.log('\n🎉 Compact 4-Measure Layout Complete!');
    console.log(`\nOpen: ${result.fileName}`);
    console.log('\nCompact Features:');
    console.log('  ✅ 4 full measures per line (42px each = 168px total)');
    console.log('  ✅ Minimal spacing (8px between lyrics and numbers)');
    console.log('  ✅ Compact font (10px) to fit more content');
    console.log('  ✅ Proper measure boundaries');
    console.log('  ✅ RED downbeats, BLACK other beats');
    console.log('  ✅ Fits Amazing Grace page width');
    
    // Open the PDF
    const { exec } = require('child_process');
    exec(`start ${result.fileName}`, (error) => {
      if (error) {
        console.log('📄 PDF created successfully! Please open manually:', result.fileName);
      } else {
        console.log('📄 Compact layout PDF opened automatically!');
      }
    });
    
  }).catch(error => {
    console.error('❌ Error creating compact layout:', error.message);
  });
}

module.exports = { createCompact4MeasureLayout };
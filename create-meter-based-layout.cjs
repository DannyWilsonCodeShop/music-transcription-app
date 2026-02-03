/**
 * Meter-Based Layout - Proper 4/4 Time Signature
 * Each measure has exactly 4 beat positions with chord numbers
 * Syllables positioned according to their rhythmic placement within the 4 beats
 */

const { generateMockData } = require('./generate-mock-data.cjs');
const fs = require('fs');

async function createMeterBasedLayout() {
  console.log('🎵 Creating Meter-Based Layout (4/4 Time - 4 Beats per Measure)');
  console.log('================================================================');
  
  // Load jsPDF
  const { jsPDF } = require('jspdf');
  const doc = new jsPDF();
  
  console.log('📊 Creating proper 4/4 meter layout with 4 beats per measure');
  
  let yPosition = 30;
  
  // === HEADER ===
  doc.setFontSize(18);
  doc.setFont('helvetica', 'bold');
  doc.text('The Wheels on the Bus', 105, yPosition, { align: 'center' });
  yPosition += 12;
  
  doc.setFontSize(11);
  doc.setFont('helvetica', 'normal');
  doc.text('Key: C major | Tempo: 60 BPM | Meter: 4/4 (4 beats per measure)', 105, yPosition, { align: 'center' });
  yPosition += 20;
  
  console.log('✅ Header added');
  
  // === METER-BASED 4-MEASURE LINES ===
  const totalLines = 4;
  
  // Create meter-based measure data (4 beats per measure)
  const measureData = createMeterBasedMeasureData();
  
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
    
    // Generate meter-based 4-measure line
    generateMeterBased4MeasureLine(doc, lineMeasures, yPosition, lineIndex + 1);
    yPosition += 30; // Space between lines
    
    console.log(`✅ Line ${lineIndex + 1}: 4 measures with 4 beats each`);
  }
  
  // === METER EXPLANATION ===
  yPosition += 15;
  if (yPosition > 240) {
    doc.addPage();
    yPosition = 30;
  }
  
  doc.setFontSize(12);
  doc.setFont('helvetica', 'bold');
  doc.text('4/4 Meter Layout:', 20, yPosition);
  yPosition += 12;
  
  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  const explanation = [
    '• Each measure has exactly 4 beat positions',
    '• Beat 1 (downbeat) = RED chord number',
    '• Beats 2, 3, 4 = BLACK chord numbers',
    '• Syllables positioned on their rhythmic beats',
    '• Empty beats show chord continuation',
    '• Measure width = 4 beats × 10px = 40px'
  ];
  
  explanation.forEach(line => {
    doc.text(line, 25, yPosition);
    yPosition += 8;
  });
  
  // Save PDF
  const fileName = 'meter-based-layout.pdf';
  doc.save(fileName);
  
  console.log(`\n✅ Meter-Based Layout Created!`);
  console.log(`📄 File: ${fileName}`);
  
  return { fileName };
}

/**
 * Generate meter-based 4-measure line with 4 beats per measure
 */
function generateMeterBased4MeasureLine(doc, measures, yPosition, lineNumber) {
  // METER-BASED LAYOUT CONSTANTS
  const lineStartX = 20;
  const beatWidth = 10; // Width per beat position
  const measureWidth = beatWidth * 4; // 4 beats per measure = 40px
  const totalLineWidth = measureWidth * 4; // 4 measures = 160px
  
  // Y positions
  const lyricsY = yPosition;
  const numbersY = yPosition + 8; // Tight spacing
  
  console.log(`  📏 Line ${lineNumber}: 4 measures × 4 beats × ${beatWidth}px = ${totalLineWidth}px total`);
  
  // Draw measure boundaries
  doc.setDrawColor(180, 180, 180);
  for (let i = 0; i <= 4; i++) {
    const x = lineStartX + (i * measureWidth);
    doc.line(x, yPosition - 3, x, yPosition + 15);
  }
  
  // Draw beat grid (lighter lines)
  doc.setDrawColor(230, 230, 230);
  for (let measureIndex = 0; measureIndex < 4; measureIndex++) {
    for (let beat = 1; beat <= 3; beat++) { // Don't draw line after beat 4 (that's the measure boundary)
      const x = lineStartX + (measureIndex * measureWidth) + (beat * beatWidth);
      doc.line(x, yPosition - 1, x, yPosition + 12);
    }
  }
  
  // Process each measure with 4 beats
  for (let measureIndex = 0; measureIndex < 4; measureIndex++) {
    const measure = measures[measureIndex];
    if (!measure) continue;
    
    const measureStartX = lineStartX + (measureIndex * measureWidth);
    
    console.log(`    🎼 M${measureIndex + 1}: 4 beats - "${measure.beats.filter(b => b.syllable).map(b => b.syllable).join(' ')}" → ${measure.beats.map(b => b.chord).join(' ')}`);
    
    // Generate 4-beat measure content
    generateMeterBasedMeasureContent(doc, measure, measureStartX, beatWidth, lyricsY, numbersY);
  }
}

/**
 * Generate meter-based content for a single measure (4 beats)
 */
function generateMeterBasedMeasureContent(doc, measure, startX, beatWidth, lyricsY, numbersY) {
  const beats = measure.beats || [];
  
  // Process each of the 4 beats
  for (let beatIndex = 0; beatIndex < 4; beatIndex++) {
    const beat = beats[beatIndex];
    if (!beat) continue;
    
    const beatX = startX + (beatIndex * beatWidth) + (beatWidth / 2);
    const isDownbeat = beatIndex === 0; // Beat 1 is downbeat
    
    // Draw syllable if present on this beat
    if (beat.syllable) {
      doc.setFontSize(10);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(0, 0, 0);
      doc.text(beat.syllable, beatX, lyricsY, { align: 'center' });
    }
    
    // Draw chord number for this beat
    doc.setFontSize(10);
    doc.setFont('helvetica', 'bold');
    
    if (isDownbeat) {
      doc.setTextColor(255, 0, 0); // RED for downbeat
    } else {
      doc.setTextColor(0, 0, 0); // BLACK for other beats
    }
    
    doc.text(beat.chord, beatX, numbersY, { align: 'center' });
  }
  
  // Reset color
  doc.setTextColor(0, 0, 0);
}

/**
 * Create meter-based measure data with exactly 4 beats per measure
 */
function createMeterBasedMeasureData() {
  return [
    // Line 1 - Verse 1
    {
      beats: [
        { chord: '1', syllable: 'The' },      // Beat 1 (downbeat)
        { chord: '1', syllable: 'wheels' },   // Beat 2
        { chord: '1', syllable: 'on' },       // Beat 3
        { chord: '1', syllable: 'the' }       // Beat 4
      ]
    },
    {
      beats: [
        { chord: '1', syllable: 'bus' },      // Beat 1 (downbeat)
        { chord: '1', syllable: 'go' },       // Beat 2
        { chord: '5', syllable: 'round' },    // Beat 3
        { chord: '5', syllable: 'and' }       // Beat 4
      ]
    },
    {
      beats: [
        { chord: '6m', syllable: 'round,' },  // Beat 1 (downbeat)
        { chord: '6m', syllable: 'round' },   // Beat 2
        { chord: '4', syllable: 'and' },      // Beat 3
        { chord: '4', syllable: '' }          // Beat 4 (chord continues)
      ]
    },
    {
      beats: [
        { chord: '1', syllable: 'round' },    // Beat 1 (downbeat)
        { chord: '5', syllable: 'and' },      // Beat 2
        { chord: '1', syllable: 'round' },    // Beat 3
        { chord: '1', syllable: '' }          // Beat 4 (chord continues)
      ]
    },
    
    // Line 2 - Verse 1 ending
    {
      beats: [
        { chord: '1', syllable: 'The' },      // Beat 1 (downbeat)
        { chord: '1', syllable: 'wheels' },   // Beat 2
        { chord: '1', syllable: 'on' },       // Beat 3
        { chord: '1', syllable: 'the' }       // Beat 4
      ]
    },
    {
      beats: [
        { chord: '1', syllable: 'bus' },      // Beat 1 (downbeat)
        { chord: '1', syllable: 'go' },       // Beat 2
        { chord: '5', syllable: 'round' },    // Beat 3
        { chord: '5', syllable: 'and' }       // Beat 4
      ]
    },
    {
      beats: [
        { chord: '6m', syllable: 'round' },   // Beat 1 (downbeat)
        { chord: '6m', syllable: '' },        // Beat 2 (chord continues)
        { chord: '4', syllable: 'All' },      // Beat 3
        { chord: '4', syllable: 'through' }   // Beat 4
      ]
    },
    {
      beats: [
        { chord: '1', syllable: 'the' },      // Beat 1 (downbeat)
        { chord: '5', syllable: 'town' },     // Beat 2
        { chord: '1', syllable: '' },         // Beat 3 (chord continues)
        { chord: '1', syllable: '' }          // Beat 4 (chord continues)
      ]
    },
    
    // Line 3 - Verse 2 (Wipers)
    {
      beats: [
        { chord: '1', syllable: 'The' },      // Beat 1 (downbeat)
        { chord: '1', syllable: 'wi-' },      // Beat 2
        { chord: '1', syllable: 'pers' },     // Beat 3
        { chord: '1', syllable: 'on' }        // Beat 4
      ]
    },
    {
      beats: [
        { chord: '1', syllable: 'the' },      // Beat 1 (downbeat)
        { chord: '1', syllable: 'bus' },      // Beat 2
        { chord: '5', syllable: 'go' },       // Beat 3
        { chord: '5', syllable: 'swish' }     // Beat 4
      ]
    },
    {
      beats: [
        { chord: '6m', syllable: 'swish' },   // Beat 1 (downbeat)
        { chord: '6m', syllable: 'swish,' },  // Beat 2
        { chord: '4', syllable: 'swish' },    // Beat 3
        { chord: '4', syllable: 'swish' }     // Beat 4
      ]
    },
    {
      beats: [
        { chord: '1', syllable: 'swish' },    // Beat 1 (downbeat)
        { chord: '5', syllable: '' },         // Beat 2 (chord continues)
        { chord: '1', syllable: '' },         // Beat 3 (chord continues)
        { chord: '1', syllable: '' }          // Beat 4 (chord continues)
      ]
    },
    
    // Line 4 - Verse 2 ending
    {
      beats: [
        { chord: '1', syllable: 'The' },      // Beat 1 (downbeat)
        { chord: '1', syllable: 'wi-' },      // Beat 2
        { chord: '1', syllable: 'pers' },     // Beat 3
        { chord: '1', syllable: 'on' }        // Beat 4
      ]
    },
    {
      beats: [
        { chord: '1', syllable: 'the' },      // Beat 1 (downbeat)
        { chord: '1', syllable: 'bus' },      // Beat 2
        { chord: '5', syllable: 'go' },       // Beat 3
        { chord: '5', syllable: 'swish' }     // Beat 4
      ]
    },
    {
      beats: [
        { chord: '6m', syllable: 'swish' },   // Beat 1 (downbeat)
        { chord: '6m', syllable: 'swish' },   // Beat 2
        { chord: '4', syllable: 'All' },      // Beat 3
        { chord: '4', syllable: 'through' }   // Beat 4
      ]
    },
    {
      beats: [
        { chord: '1', syllable: 'the' },      // Beat 1 (downbeat)
        { chord: '5', syllable: 'town' },     // Beat 2
        { chord: '1', syllable: '' },         // Beat 3 (chord continues)
        { chord: '1', syllable: '' }          // Beat 4 (chord continues)
      ]
    }
  ];
}

// Run the meter-based layout creation
if (require.main === module) {
  createMeterBasedLayout().then(result => {
    console.log('\n🎉 Meter-Based Layout Complete!');
    console.log(`\nOpen: ${result.fileName}`);
    console.log('\nMeter-Based Features:');
    console.log('  ✅ Exactly 4 beats per measure (4/4 time)');
    console.log('  ✅ 4 chord positions per measure');
    console.log('  ✅ Beat 1 = RED (downbeat)');
    console.log('  ✅ Beats 2,3,4 = BLACK');
    console.log('  ✅ Syllables positioned on rhythmic beats');
    console.log('  ✅ Beat grid shows meter structure');
    console.log('  ✅ Proper Nashville Number System');
    
    // Open the PDF
    const { exec } = require('child_process');
    exec(`start ${result.fileName}`, (error) => {
      if (error) {
        console.log('📄 PDF created successfully! Please open manually:', result.fileName);
      } else {
        console.log('📄 Meter-based layout PDF opened automatically!');
      }
    });
    
  }).catch(error => {
    console.error('❌ Error creating meter-based layout:', error.message);
  });
}

module.exports = { createMeterBasedLayout };
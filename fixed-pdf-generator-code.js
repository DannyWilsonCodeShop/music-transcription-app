
// FIXED PDF GENERATOR - Proper Nashville Number System Format
// Removes table layout, uses clean text-based format like Amazing Grace

function generateProperNashvilleFormat(doc, data, startY) {
  console.log('🎵 Generating PROPER Nashville Number System (no tables)');
  
  doc.setFontSize(16);
  doc.setFont('helvetica', 'bold');
  doc.text('Nashville Number System', 20, startY);
  let yPosition = startY + 25;
  
  // Group chords into measures
  const measures = convertChordsToMeasures(data.chords);
  const measuresPerLine = 4;
  
  for (let lineIndex = 0; lineIndex < Math.ceil(measures.length / measuresPerLine); lineIndex++) {
    // Add phrase label (clean)
    if (lineIndex % 2 === 0) {
      doc.setFontSize(12);
      doc.setFont('helvetica', 'bold');
      doc.text(`Verse ${Math.floor(lineIndex / 2) + 1}:`, 20, yPosition);
      yPosition += 15;
    }
    
    // Get 4 measures for this line
    const lineMeasures = [];
    for (let i = 0; i < measuresPerLine; i++) {
      const measureIndex = lineIndex * measuresPerLine + i;
      if (measureIndex < measures.length) {
        lineMeasures.push(measures[measureIndex]);
      }
    }
    
    // Generate CLEAN line (NO TABLES)
    generateCleanNashvilleLine(doc, lineMeasures, yPosition);
    yPosition += 25;
  }
  
  return yPosition;
}

function generateCleanNashvilleLine(doc, measures, yPosition) {
  // CLEAN TEXT-BASED LAYOUT (like Amazing Grace)
  const startX = 40;
  const numberSpacing = 60;
  
  measures.forEach((measure, index) => {
    if (measure) {
      const x = startX + (index * numberSpacing);
      
      // Main Nashville number (clean, large)
      doc.setFontSize(18);
      doc.setFont('helvetica', 'bold');
      
      if (measure.isDownbeat) {
        doc.setTextColor(200, 0, 0); // Subtle red
      } else {
        doc.setTextColor(0, 0, 0); // Black
      }
      
      doc.text(measure.nashvilleNumber || '1', x, yPosition, { align: 'center' });
      
      // Small measure number (subtle)
      doc.setFontSize(8);
      doc.setTextColor(150, 150, 150);
      doc.text(`${measure.measure}`, x, yPosition + 12, { align: 'center' });
    }
  });
  
  doc.setTextColor(0, 0, 0);
}

// REMOVE ALL TABLE/GRID FUNCTIONS:
// - generateProper4MeasureLine() - REMOVE (uses tables)
// - generateProperMeasureContent() - REMOVE (uses grids)
// - All doc.line() calls - REMOVE (creates visual clutter)
// - All table border drawing - REMOVE (not Nashville format)

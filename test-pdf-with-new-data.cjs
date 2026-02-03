const fs = require('fs');
const { jsPDF } = require('jspdf');

const rawData = JSON.parse(fs.readFileSync('test-job-data-new.json', 'utf8'));

const chordsDataRaw = rawData.Item.chordsData.M;
const chords = chordsDataRaw.chords.L.slice(0, 200).map(c => ({  // Test with first 200 chords
  chord: c.M.chord.S,
  start: parseFloat(c.M.start.N),
  duration: parseFloat(c.M.duration.N),
  confidence: parseFloat(c.M.confidence.N)
}));

const key = chordsDataRaw.key.S;
const tempo = parseFloat(chordsDataRaw.tempo.N);
const timeSignature = chordsDataRaw.timeSignature.S;

console.log('Testing PDF generation with new chord data');
console.log(`Tempo: ${tempo} BPM, Key: ${key}, Chords: ${chords.length}`);

// Calculate measures
const [beatsPerMeasure] = timeSignature.split('/').map(Number);
const secondsPerBeat = 60 / tempo;
const secondsPerMeasure = beatsPerMeasure * secondsPerBeat;

const measureMap = {};
chords.forEach(chord => {
  const measureNum = Math.floor(chord.start / secondsPerMeasure) + 1;
  const timeInMeasure = chord.start % secondsPerMeasure;
  const beatInMeasure = timeInMeasure / secondsPerBeat;
  
  if (!measureMap[measureNum]) {
    measureMap[measureNum] = {
      measureNumber: measureNum,
      chords: []
    };
  }
  
  measureMap[measureNum].chords.push({
    chord: chord.chord,
    beat: beatInMeasure,
    isDownbeat: beatInMeasure < 0.5
  });
});

const measures = Object.keys(measureMap)
  .sort((a, b) => parseInt(a) - parseInt(b))
  .map(m => measureMap[m]);

console.log(`Created ${measures.length} measures`);
console.log(`First measure has ${measures[0].chords.length} chords`);

// Generate PDF
const doc = new jsPDF();

doc.setFontSize(18);
doc.setFont('helvetica', 'bold');
doc.text('Despacito - New Chord Detection Test', 105, 20, { align: 'center' });

doc.setFontSize(12);
doc.setFont('helvetica', 'normal');
doc.text(`Key: ${key} | Tempo: ${tempo} BPM | ${measures.length} measures`, 105, 30, { align: 'center' });

let yPosition = 50;
const columnPositions = [38, 73, 108, 143];
const measuresPerLine = 4;

for (let lineIndex = 0; lineIndex < Math.min(10, Math.ceil(measures.length / measuresPerLine)); lineIndex++) {
  const startIdx = lineIndex * measuresPerLine;
  const lineMeasures = measures.slice(startIdx, startIdx + measuresPerLine);
  
  // Draw measure numbers
  doc.setFontSize(8);
  doc.setTextColor(150, 150, 150);
  lineMeasures.forEach((measure, idx) => {
    doc.text(`M${measure.measureNumber}`, columnPositions[idx], yPosition - 3);
  });
  
  // Draw vertical lines
  doc.setDrawColor(200, 200, 200);
  doc.setLineWidth(0.5);
  for (let i = 1; i < lineMeasures.length && i < 4; i++) {
    const lineX = columnPositions[i] - 5;
    doc.line(lineX, yPosition - 5, lineX, yPosition + 20);
  }
  
  // Draw chords
  lineMeasures.forEach((measure, idx) => {
    const xPosition = columnPositions[idx];
    const measureWidth = 30;
    
    // With 14 chords per measure, we need to be smart about spacing
    // Only show chords that represent changes or are on beats
    const displayChords = [];
    let lastChord = null;
    
    measure.chords.forEach((chordInfo, chordIdx) => {
      // Show first chord, or chord changes, or chords on beats
      const onBeat = Math.abs(chordInfo.beat - Math.round(chordInfo.beat)) < 0.3;
      if (chordIdx === 0 || chordInfo.chord !== lastChord || onBeat) {
        displayChords.push(chordInfo);
        lastChord = chordInfo.chord;
      }
    });
    
    console.log(`M${measure.measureNumber}: ${measure.chords.length} total, ${displayChords.length} displayed`);
    
    displayChords.forEach((chordInfo, chordIdx) => {
      const beatOffset = (chordInfo.beat / 4) * measureWidth;
      const chordX = xPosition + beatOffset;
      
      if (chordIdx === 0) {
        doc.setTextColor(255, 0, 0);
        doc.setFontSize(11);
        doc.setFont('helvetica', 'bold');
      } else {
        doc.setTextColor(0, 0, 0);
        doc.setFontSize(9);
        doc.setFont('helvetica', 'normal');
      }
      
      doc.text(chordInfo.chord, chordX, yPosition);
    });
  });
  
  yPosition += 25;
}

doc.save('test-new-chord-detection-local.pdf');
console.log('\n✅ PDF generated: test-new-chord-detection-local.pdf');

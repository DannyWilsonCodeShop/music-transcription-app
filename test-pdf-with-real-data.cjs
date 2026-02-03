const fs = require('fs');
const { jsPDF } = require('jspdf');

// Load the job data
const rawData = JSON.parse(fs.readFileSync('test-job-data-8474.json', 'utf8'));

// Manually convert DynamoDB data
const chordsData = rawData.Item.chordsData.M;
const chords = chordsData.chords.L.map(c => ({
  chord: c.M.chord.S,
  start: parseFloat(c.M.start.N),
  duration: parseFloat(c.M.duration.N),
  confidence: parseFloat(c.M.confidence.N)
}));

const key = chordsData.key.S;
const tempo = 152; // Despacito tempo
const timeSignature = '4/4';

console.log('\n=== TESTING WITH CORRECT TEMPO ===');
console.log(`Tempo: ${tempo} BPM`);
console.log(`Key: ${key}`);
console.log(`Time Signature: ${timeSignature}`);
console.log(`Total chords: ${chords.length}`);

// Test the convertChordsToMeasures function
function convertChordsToMeasures(chords, timeSignature = '4/4', tempo = 120, key = 'C') {
  if (!chords || chords.length === 0) {
    return [];
  }
  
  console.log(`\n🔄 Converting ${chords.length} chords to measures (tempo: ${tempo} BPM, key: ${key})`);
  
  const keyRoot = key.split(' ')[0];
  const [beatsPerMeasure] = timeSignature.split('/').map(Number);
  const secondsPerBeat = 60 / tempo;
  const secondsPerMeasure = beatsPerMeasure * secondsPerBeat;
  
  console.log(`📏 Measure duration: ${secondsPerMeasure.toFixed(2)}s (${beatsPerMeasure} beats @ ${tempo} BPM)`);
  console.log(`📏 Beat duration: ${secondsPerBeat.toFixed(2)}s`);
  
  const measureMap = {};
  
  chords.forEach((chord, index) => {
    const chordTime = chord.time || chord.timestamp || chord.start || chord.startTime || 0;
    const measureNum = Math.floor(chordTime / secondsPerMeasure) + 1;
    const timeInMeasure = chordTime % secondsPerMeasure;
    const beatInMeasure = timeInMeasure / secondsPerBeat;
    
    if (!measureMap[measureNum]) {
      measureMap[measureNum] = {
        measureNumber: measureNum,
        chords: [],
        startTime: (measureNum - 1) * secondsPerMeasure,
        endTime: measureNum * secondsPerMeasure
      };
    }
    
    measureMap[measureNum].chords.push({
      chord: chord.chord,
      beat: beatInMeasure,
      time: chordTime,
      isDownbeat: beatInMeasure < 0.5
    });
  });
  
  const measures = Object.keys(measureMap)
    .sort((a, b) => parseInt(a) - parseInt(b))
    .map(measureNum => {
      const measure = measureMap[measureNum];
      measure.chords.sort((a, b) => a.beat - b.beat);
      return measure;
    });
  
  console.log(`✅ Created ${measures.length} measures`);
  console.log(`📊 Avg chords per measure: ${(chords.length / measures.length).toFixed(1)}`);
  
  // Show first 10 measures
  console.log('\nFirst 10 measures:');
  measures.slice(0, 10).forEach(m => {
    console.log(`  M${m.measureNumber}: ${m.chords.length} chords - ${m.chords.map(c => `${c.chord}@${c.beat.toFixed(1)}`).join(', ')}`);
  });
  
  return measures;
}

// Manually convert DynamoDB data
const chordsData = rawData.Item.chordsData.M;
const chords = chordsData.chords.L.map(c => ({
  chord: c.M.chord.S,
  start: parseFloat(c.M.start.N),
  duration: parseFloat(c.M.duration.N),
  confidence: parseFloat(c.M.confidence.N)
}));

const key = chordsData.key.S;
const tempo = 152; // Despacito tempo
const timeSignature = '4/4';

console.log('\n=== TESTING WITH CORRECT TEMPO ===');
console.log(`Tempo: ${tempo} BPM`);
console.log(`Key: ${key}`);
console.log(`Time Signature: ${timeSignature}`);
console.log(`Total chords: ${chords.length}`);

const measures = convertChordsToMeasures(chords, timeSignature, tempo, key);

// Now generate a PDF
const { jsPDF } = require('jspdf');

function generateTestPDF(measures, key, tempo) {
  const doc = new jsPDF();
  
  doc.setFontSize(18);
  doc.setFont('helvetica', 'bold');
  doc.text('Despacito - Chord Chart Test', 105, 20, { align: 'center' });
  
  doc.setFontSize(12);
  doc.setFont('helvetica', 'normal');
  doc.text(`Key: ${key} | Tempo: ${tempo} BPM | Time: ${timeSignature}`, 105, 30, { align: 'center' });
  
  let yPosition = 50;
  const columnPositions = [38, 73, 108, 143];
  const measuresPerLine = 4;
  
  for (let lineIndex = 0; lineIndex < Math.min(20, Math.ceil(measures.length / measuresPerLine)); lineIndex++) {
    const startIdx = lineIndex * measuresPerLine;
    const lineMeasures = measures.slice(startIdx, startIdx + measuresPerLine);
    
    // Draw measure numbers
    doc.setFontSize(8);
    doc.setTextColor(150, 150, 150);
    lineMeasures.forEach((measure, idx) => {
      doc.text(`M${measure.measureNumber}`, columnPositions[idx], yPosition - 3);
    });
    
    // Draw vertical lines between measures
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
      
      measure.chords.forEach((chordInfo, chordIdx) => {
        const beatOffset = (chordInfo.beat / 4) * measureWidth;
        const chordX = xPosition + beatOffset;
        
        // First chord RED, others BLACK
        if (chordIdx === 0) {
          doc.setTextColor(255, 0, 0);
          doc.setFontSize(12);
          doc.setFont('helvetica', 'bold');
        } else {
          doc.setTextColor(0, 0, 0);
          doc.setFontSize(10);
          doc.setFont('helvetica', 'normal');
        }
        
        doc.text(chordInfo.chord, chordX, yPosition);
      });
    });
    
    yPosition += 25;
    
    if (yPosition > 250) {
      doc.addPage();
      yPosition = 30;
    }
  }
  
  return doc;
}

const pdf = generateTestPDF(measures, key, tempo);
pdf.save('despacito-tempo-152-test.pdf');
console.log('\n✅ PDF generated: despacito-tempo-152-test.pdf');

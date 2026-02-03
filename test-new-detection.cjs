const fs = require('fs');

const rawData = JSON.parse(fs.readFileSync('test-job-data-new.json', 'utf8'));

const chordsDataRaw = rawData.Item.chordsData.M;
const chords = chordsDataRaw.chords.L.map(c => ({
  chord: c.M.chord.S,
  start: parseFloat(c.M.start.N),
  duration: parseFloat(c.M.duration.N),
  confidence: parseFloat(c.M.confidence.N)
}));

const key = chordsDataRaw.key.S;
const tempo = parseFloat(chordsDataRaw.tempo.N);
const timeSignature = chordsDataRaw.timeSignature.S;

console.log('=== NEW CHORD DETECTION TEST ===');
console.log(`Tempo: ${tempo} BPM (detected)`);
console.log(`Key: ${key}`);
console.log(`Time Signature: ${timeSignature}`);
console.log(`Total chords: ${chords.length}`);

// Calculate measures
const [beatsPerMeasure] = timeSignature.split('/').map(Number);
const secondsPerBeat = 60 / tempo;
const secondsPerMeasure = beatsPerMeasure * secondsPerBeat;

console.log(`\nMeasure duration: ${secondsPerMeasure.toFixed(2)}s (${beatsPerMeasure} beats @ ${tempo} BPM)`);
console.log(`Expected chords per measure: ${(secondsPerMeasure / 0.2).toFixed(1)}`);

// Group by measure
const measureMap = {};
chords.forEach(chord => {
  const measureNum = Math.floor(chord.start / secondsPerMeasure) + 1;
  if (!measureMap[measureNum]) {
    measureMap[measureNum] = [];
  }
  measureMap[measureNum].push(chord);
});

const measures = Object.keys(measureMap).sort((a, b) => parseInt(a) - parseInt(b));
const chordsPerMeasure = measures.map(m => measureMap[m].length);
const avgChordsPerMeasure = chordsPerMeasure.reduce((a, b) => a + b, 0) / chordsPerMeasure.length;

console.log(`\nTotal measures: ${measures.length}`);
console.log(`Avg chords per measure: ${avgChordsPerMeasure.toFixed(1)}`);
console.log(`Min chords per measure: ${Math.min(...chordsPerMeasure)}`);
console.log(`Max chords per measure: ${Math.max(...chordsPerMeasure)}`);

console.log('\nFirst 5 measures:');
measures.slice(0, 5).forEach(m => {
  const measureChords = measureMap[m];
  console.log(`  M${m}: ${measureChords.length} chords - ${measureChords.map(c => c.chord).join(', ')}`);
});

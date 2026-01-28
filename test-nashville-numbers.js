// Test Nashville Number System conversion
// This shows how chords will be converted to numbers in the PDF

function getNashvilleNumber(chord, key) {
  // Nashville Number System mapping
  const majorScale = ['C', 'D', 'E', 'F', 'G', 'A', 'B'];
  const minorScale = ['A', 'B', 'C', 'D', 'E', 'F', 'G'];
  
  // Parse chord to get root note
  let rootNote = chord.replace(/[^A-G#b]/g, '');
  if (rootNote.length > 1 && rootNote[1] === '#') {
    rootNote = rootNote.substring(0, 2);
  } else if (rootNote.length > 1 && rootNote[1] === 'b') {
    rootNote = rootNote.substring(0, 2);
  } else {
    rootNote = rootNote[0];
  }
  
  // Parse key to get tonic
  let keyRoot = key.replace(/[^A-G#b]/g, '');
  if (keyRoot.length > 1 && (keyRoot[1] === '#' || keyRoot[1] === 'b')) {
    keyRoot = keyRoot.substring(0, 2);
  } else {
    keyRoot = keyRoot[0];
  }
  
  // Determine if key is major or minor
  const isMinor = key.toLowerCase().includes('m') || key.toLowerCase().includes('minor');
  
  // Convert notes to semitones for calculation
  const noteToSemitone = {
    'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5,
    'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11
  };
  
  const keySemitone = noteToSemitone[keyRoot] || 0;
  const chordSemitone = noteToSemitone[rootNote] || 0;
  
  // Calculate interval
  let interval = (chordSemitone - keySemitone + 12) % 12;
  
  // Map to Nashville numbers
  const majorNumbers = ['1', 'b2', '2', 'b3', '3', '4', 'b5', '5', 'b6', '6', 'b7', '7'];
  const minorNumbers = ['1', 'b2', 'b3', '3', '4', 'b5', '5', 'b6', '6', 'b7', '7', '7'];
  
  let number = isMinor ? minorNumbers[interval] : majorNumbers[interval];
  
  // Add chord quality indicators
  if (chord.includes('m') && !chord.includes('maj')) {
    // Minor chord - use lowercase if it's not the relative minor
    if (!isMinor || interval !== 0) {
      number = number.toLowerCase();
    }
  }
  
  if (chord.includes('7')) {
    number += '7';
  }
  if (chord.includes('maj7')) {
    number = number.replace('7', 'maj7');
  }
  if (chord.includes('dim')) {
    number += '°';
  }
  if (chord.includes('aug') || chord.includes('+')) {
    number += '+';
  }
  
  return number;
}

// Test examples
console.log('=== NASHVILLE NUMBER SYSTEM EXAMPLES ===\n');

// Hotel California (Bm)
console.log('Hotel California - Key: Bm');
const hotelChords = ['Bm', 'F#', 'A', 'E', 'G', 'D', 'Em', 'F#'];
hotelChords.forEach(chord => {
  console.log(`${chord.padEnd(4)} → ${getNashvilleNumber(chord, 'Bm')}`);
});

console.log('\n' + '='.repeat(40) + '\n');

// Let It Be (C major)
console.log('Let It Be - Key: C');
const letItBeChords = ['C', 'G', 'Am', 'F', 'C', 'G', 'F', 'C'];
letItBeChords.forEach(chord => {
  console.log(`${chord.padEnd(4)} → ${getNashvilleNumber(chord, 'C')}`);
});

console.log('\n' + '='.repeat(40) + '\n');

// Wonderwall (Em)
console.log('Wonderwall - Key: Em');
const wonderwallChords = ['Em7', 'G', 'D', 'C', 'Am', 'C', 'D', 'G'];
wonderwallChords.forEach(chord => {
  console.log(`${chord.padEnd(4)} → ${getNashvilleNumber(chord, 'Em')}`);
});

console.log('\n=== PDF LAYOUT PREVIEW ===');
console.log(`
SONG TITLE
Key: Bm minor

[Verse 1]
On a dark desert highway, cool wind in my hair
Warm smell of colitas, rising up through the air

Staff: ___________________
Chord: Bm    F#    A     E
Number: 1     5     b7    4

Staff: ___________________  
Chord: G     D     Em    F#
Number: b6    b3    4     5

[Chorus]
Welcome to the Hotel California
Such a lovely place...

Staff: ___________________
Chord: Bm    F#    A     E  
Number: 1     5     b7    4
`);
/**
 * ABC Notation Generator
 * Converts chord data to ABC notation format for sheet music rendering
 */

interface Chord {
  name: string;
  timestamp: number;
  duration: number;
  confidence: number;
}

interface ChordData {
  key: string;
  mode: string;
  chords: Chord[];
}

interface ABCOptions {
  title?: string;
  artist?: string;
  tempo?: number;
  timeSignature?: string;
}

/**
 * Generate ABC notation from chord progression
 */
export function generateABCFromChords(
  chordData: ChordData,
  options: ABCOptions = {}
): string {
  const {
    title = 'Untitled',
    artist = 'Unknown Artist',
    tempo = 120,
    timeSignature = '4/4'
  } = options;

  // Parse time signature
  const [beatsPerMeasure] = timeSignature.split('/').map(Number);
  
  // ABC header
  let abc = `X:1\n`;
  abc += `T:${title}\n`;
  if (artist) abc += `C:${artist}\n`;
  abc += `M:${timeSignature}\n`;
  abc += `L:1/4\n`; // Quarter note as base unit
  abc += `Q:1/4=${tempo}\n`;
  abc += `K:${chordData.key}${chordData.mode === 'minor' ? 'm' : ''}\n`;
  abc += `%%staves {1}\n`;
  abc += `V:1 clef=treble\n`;
  
  // Generate chord progression with rhythm
  const chords = chordData.chords;
  let currentBeat = 0;
  let measureContent: string[] = [];
  
  for (let i = 0; i < chords.length; i++) {
    const chord = chords[i];
    const nextChord = chords[i + 1];
    
    // Calculate duration in beats (assuming 4/4 time)
    let durationBeats = chord.duration / (60 / tempo);
    
    // If there's a next chord, use the time difference
    if (nextChord) {
      durationBeats = (nextChord.timestamp - chord.timestamp) / (60 / tempo);
    }
    
    // Round to nearest quarter note
    durationBeats = Math.max(1, Math.round(durationBeats));
    
    // Add chord symbol
    const chordSymbol = `"${chord.name}"`;
    
    // Generate notes (whole notes for chord display)
    let noteLength = '';
    if (durationBeats === 1) noteLength = '';
    else if (durationBeats === 2) noteLength = '2';
    else if (durationBeats === 3) noteLength = '3';
    else if (durationBeats === 4) noteLength = '4';
    else noteLength = '4'; // Default to whole note
    
    // Add to measure
    measureContent.push(`${chordSymbol}z${noteLength}`);
    currentBeat += durationBeats;
    
    // Start new measure when we reach the beat count
    if (currentBeat >= beatsPerMeasure) {
      abc += `|${measureContent.join(' ')}`;
      measureContent = [];
      currentBeat = 0;
    }
  }
  
  // Add remaining content
  if (measureContent.length > 0) {
    abc += `|${measureContent.join(' ')}`;
  }
  
  // Close the tune
  abc += `|]\n`;
  
  return abc;
}

/**
 * Generate ABC notation with melody from MIDI data
 */
export function generateABCFromMIDI(
  midiNotes: Array<{ pitch: number; start: number; duration: number }>,
  chordData: ChordData,
  options: ABCOptions = {}
): string {
  const {
    title = 'Untitled',
    artist = 'Unknown Artist',
    tempo = 120,
    timeSignature = '4/4'
  } = options;

  // ABC header
  let abc = `X:1\n`;
  abc += `T:${title}\n`;
  if (artist) abc += `C:${artist}\n`;
  abc += `M:${timeSignature}\n`;
  abc += `L:1/8\n`; // Eighth note as base unit
  abc += `Q:1/4=${tempo}\n`;
  abc += `K:${chordData.key}${chordData.mode === 'minor' ? 'm' : ''}\n`;
  
  // Convert MIDI notes to ABC notation
  const noteNames = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
  
  // Group notes by time
  const sortedNotes = [...midiNotes].sort((a, b) => a.start - b.start);
  
  let measureContent: string[] = [];
  
  for (const note of sortedNotes) {
    // Find corresponding chord
    const chord = chordData.chords.find(
      c => note.start >= c.timestamp && note.start < c.timestamp + c.duration
    );
    
    // Convert MIDI pitch to ABC note
    const octave = Math.floor(note.pitch / 12) - 1;
    const pitchClass = note.pitch % 12;
    let noteName = noteNames[pitchClass];
    
    // ABC octave notation
    if (octave < 4) {
      noteName = noteName.toUpperCase();
      if (octave < 3) noteName += ','.repeat(3 - octave);
    } else {
      noteName = noteName.toLowerCase();
      if (octave > 4) noteName += "'".repeat(octave - 4);
    }
    
    // Add chord symbol if new chord
    if (chord && note.start === chord.timestamp) {
      measureContent.push(`"${chord.name}"`);
    }
    
    // Add note with duration
    const durationEighths = Math.max(1, Math.round(note.duration * 2));
    measureContent.push(noteName + (durationEighths > 1 ? durationEighths : ''));
  }
  
  abc += `|${measureContent.join(' ')}|]\n`;
  
  return abc;
}

/**
 * Generate simple chord chart (just chords, no rhythm)
 */
export function generateSimpleChordChart(
  chordData: ChordData,
  options: ABCOptions = {}
): string {
  const {
    title = 'Untitled',
    artist = 'Unknown Artist',
  } = options;

  let abc = `X:1\n`;
  abc += `T:${title}\n`;
  if (artist) abc += `C:${artist}\n`;
  abc += `M:4/4\n`;
  abc += `L:1/4\n`;
  abc += `K:${chordData.key}${chordData.mode === 'minor' ? 'm' : ''}\n`;
  abc += `%%staves {1}\n`;
  
  // Simple chord progression - 4 chords per line
  const chords = chordData.chords;
  let line = '|';
  
  for (let i = 0; i < chords.length; i++) {
    line += `"${chords[i].name}"z4`;
    
    if ((i + 1) % 4 === 0) {
      abc += line + '|\n';
      line = '|';
    } else {
      line += '|';
    }
  }
  
  // Add remaining chords
  if (line !== '|') {
    // Pad with empty measures if needed
    const remaining = 4 - (chords.length % 4);
    for (let i = 0; i < remaining; i++) {
      line += 'z4|';
    }
    abc += line + '\n';
  }
  
  return abc;
}

/**
 * Format chord progression as text
 */
export function formatChordProgressionText(chordData: ChordData): string {
  const lines: string[] = [];
  lines.push(`Key: ${chordData.key} ${chordData.mode}`);
  lines.push('');
  
  // Group chords by measures (4 beats each)
  let currentLine: string[] = [];
  
  for (const chord of chordData.chords) {
    currentLine.push(chord.name);
    
    if (currentLine.length >= 4) {
      lines.push(currentLine.join(' - '));
      currentLine = [];
    }
  }
  
  if (currentLine.length > 0) {
    lines.push(currentLine.join(' - '));
  }
  
  return lines.join('\n');
}

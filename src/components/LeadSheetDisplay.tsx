import React from 'react';
import './LeadSheetDisplay.css';

// ============================================================================
// TypeScript Interfaces
// ============================================================================

/**
 * Metadata about the song (key, tempo, time signature)
 */
interface LeadSheetMetadata {
  key: string;
  tempo: number;
  timeSignature: string;
  duration?: number;
}

/**
 * Individual word with timing and position information
 */
interface AlignedWord {
  word: string;
  start: number;
  end: number;
  charPosition: number;
}

/**
 * Chord symbol with position information
 */
interface AlignedChord {
  chord: string;
  timestamp: number;
  wordIndex: number | null;
  charPosition: number;
  measure: number;
  beat: number;
}

/**
 * Single line of lyrics with aligned chords
 */
interface AlignedLine {
  measureStart: number;
  measureEnd: number;
  lyrics: string;
  words: AlignedWord[];
  chords: AlignedChord[];
  isInstrumental: boolean;
}

/**
 * Section of the song (Verse, Chorus, Bridge, etc.)
 */
interface AlignedSection {
  label: string;
  measureStart: number;
  measureEnd: number;
  lines: AlignedLine[];
}

/**
 * Complete aligned lead sheet structure
 */
export interface AlignedLeadSheet {
  metadata: LeadSheetMetadata;
  sections: AlignedSection[];
}

// ============================================================================
// Component Props
// ============================================================================

interface LeadSheetDisplayProps {
  leadSheet: AlignedLeadSheet;
  showMeasureNumbers?: boolean;
  showTimestamps?: boolean;  // Debug mode
}

interface SectionLabelProps {
  label: string;
}

interface LyricsLineProps {
  line: AlignedLine;
  showMeasureNumbers: boolean;
  showTimestamps: boolean;
}

// ============================================================================
// Sub-Components
// ============================================================================

/**
 * SectionLabel Component
 * Displays section headers (Verse 1, Chorus, Bridge, etc.)
 */
const SectionLabel: React.FC<SectionLabelProps> = ({ label }) => {
  return (
    <div className="section-label">
      <h3>{label}</h3>
    </div>
  );
};

/**
 * LyricsLine Component
 * Displays a single line of lyrics with chord symbols positioned above
 */
const LyricsLine: React.FC<LyricsLineProps> = ({ 
  line, 
  showMeasureNumbers, 
  showTimestamps 
}) => {
  // Build chord positioning data
  const chordPositions = line.chords.map(chord => ({
    chord: chord.chord,
    position: chord.charPosition,
    timestamp: chord.timestamp
  }));

  return (
    <div className="lyrics-line">
      {/* Measure numbers in left margin */}
      {showMeasureNumbers && (
        <div className="measure-numbers">
          {line.measureStart === line.measureEnd 
            ? `M${line.measureStart}`
            : `M${line.measureStart}-${line.measureEnd}`
          }
        </div>
      )}
      
      <div className="line-content">
        {/* Chord symbols positioned above lyrics */}
        <div className="chord-line">
          {chordPositions.map((cp, idx) => (
            <span
              key={idx}
              className="chord-symbol"
              style={{ 
                position: 'absolute',
                left: `${cp.position * 0.6}ch`  // Approximate character width
              }}
            >
              {cp.chord}
              {showTimestamps && (
                <span className="timestamp">
                  ({cp.timestamp.toFixed(2)}s)
                </span>
              )}
            </span>
          ))}
        </div>
        
        {/* Lyrics text */}
        <div className="lyrics-text">
          {line.isInstrumental ? (
            <span className="instrumental-marker">[Instrumental]</span>
          ) : (
            line.lyrics
          )}
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// Main Component
// ============================================================================

/**
 * LeadSheetDisplay Component
 * Main component for displaying aligned lead sheets with lyrics and chords
 */
const LeadSheetDisplay: React.FC<LeadSheetDisplayProps> = ({ 
  leadSheet, 
  showMeasureNumbers = true, 
  showTimestamps = false 
}) => {
  return (
    <div className="lead-sheet">
      {/* Metadata header */}
      <div className="lead-sheet-header">
        <div className="metadata-item">
          <span className="metadata-label">Key:</span> {leadSheet.metadata.key}
        </div>
        <div className="metadata-item">
          <span className="metadata-label">Tempo:</span> {leadSheet.metadata.tempo} BPM
        </div>
        <div className="metadata-item">
          <span className="metadata-label">Time:</span> {leadSheet.metadata.timeSignature}
        </div>
      </div>
      
      {/* Sections */}
      <div className="lead-sheet-content">
        {leadSheet.sections.map((section, sectionIdx) => (
          <div key={sectionIdx} className="lead-sheet-section">
            {/* Section label */}
            <SectionLabel label={section.label} />
            
            {/* Lines within section */}
            {section.lines.map((line, lineIdx) => (
              <LyricsLine
                key={lineIdx}
                line={line}
                showMeasureNumbers={showMeasureNumbers}
                showTimestamps={showTimestamps}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
};

export default LeadSheetDisplay;

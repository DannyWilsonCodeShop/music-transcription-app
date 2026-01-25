import { useEffect, useRef, useState } from 'react';
import abcjs from 'abcjs';
import { generateSimpleChordChart, formatChordProgressionText } from '../utils/abcGenerator';

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
  chordProgressionText?: string;
}

interface SheetMusicViewerProps {
  chordData: ChordData;
  title: string;
  artist?: string;
  showPlayback?: boolean;
}

export default function SheetMusicViewer({
  chordData,
  title,
  artist,
  showPlayback = true
}: SheetMusicViewerProps) {
  const notationRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLDivElement>(null);
  const [abcNotation, setAbcNotation] = useState('');
  const synthControlRef = useRef<any>(null);

  useEffect(() => {
    if (!chordData || !chordData.chords || chordData.chords.length === 0) {
      return;
    }

    try {
      // Generate ABC notation
      const abc = generateSimpleChordChart(chordData, { title, artist });
      setAbcNotation(abc);

      // Render sheet music
      if (notationRef.current) {
        abcjs.renderAbc(notationRef.current, abc, {
          responsive: 'resize',
          staffwidth: 600,
          scale: 1.0,
          add_classes: true,
        });
      }

      // Setup audio playback
      if (showPlayback && audioRef.current) {
        synthControlRef.current = new abcjs.synth.SynthController();
        synthControlRef.current.load('#audio-controls', null, {
          displayLoop: true,
          displayRestart: true,
          displayPlay: true,
          displayProgress: true,
          displayWarp: true,
        });

        const visualObj = abcjs.renderAbc('*', abc)[0];
        
        synthControlRef.current.setTune(visualObj, false, {
          program: 0, // Acoustic Grand Piano
          chordsOff: false,
        }).then(() => {
          console.log('Audio loaded successfully');
        }).catch((error: any) => {
          console.error('Error loading audio:', error);
        });
      }
    } catch (error) {
      console.error('Error rendering sheet music:', error);
    }

    return () => {
      if (synthControlRef.current) {
        synthControlRef.current.pause();
      }
    };
  }, [chordData, title, artist, showPlayback]);

  const handleDownloadABC = () => {
    const blob = new Blob([abcNotation], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title.replace(/[^a-z0-9]/gi, '_')}.abc`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleDownloadMIDI = () => {
    if (!synthControlRef.current) return;
    
    try {
      const visualObj = abcjs.renderAbc('*', abcNotation)[0];
      const midi = abcjs.synth.getMidiFile(visualObj, {
        chordsOff: false,
        program: 0,
      });
      
      const blob = new Blob([midi], { type: 'audio/midi' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${title.replace(/[^a-z0-9]/gi, '_')}.mid`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error generating MIDI:', error);
    }
  };

  if (!chordData || !chordData.chords || chordData.chords.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>No chord data available</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xl font-bold text-gray-900">{title}</h3>
          {artist && <p className="text-sm text-gray-600">{artist}</p>}
          <p className="text-sm text-gray-500 mt-1">
            Key: {chordData.key} {chordData.mode} • {chordData.chords.length} chords
          </p>
        </div>
        
        <div className="flex gap-2">
          <button
            onClick={handleDownloadABC}
            className="px-3 py-2 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            title="Download ABC notation"
          >
            📄 ABC
          </button>
          <button
            onClick={handleDownloadMIDI}
            className="px-3 py-2 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            title="Download MIDI file"
          >
            🎹 MIDI
          </button>
        </div>
      </div>

      {/* Sheet Music Display */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 overflow-x-auto">
        <div ref={notationRef} className="min-h-[200px]" />
      </div>

      {/* Audio Controls */}
      {showPlayback && (
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl border border-blue-200 p-4">
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium text-gray-700">🎵 Playback:</span>
            <div id="audio-controls" ref={audioRef} className="flex-1" />
          </div>
        </div>
      )}

      {/* Chord Progression Text */}
      <div className="bg-gray-50 rounded-xl border border-gray-200 p-4">
        <h4 className="text-sm font-semibold text-gray-900 mb-3">Chord Progression</h4>
        <pre className="text-sm text-gray-700 font-mono whitespace-pre-wrap">
          {chordData.chordProgressionText || formatChordProgressionText(chordData)}
        </pre>
      </div>

      {/* Chord Timeline */}
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <h4 className="text-sm font-semibold text-gray-900 mb-3">Chord Timeline</h4>
        <div className="space-y-2">
          {chordData.chords.map((chord, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="flex items-center gap-4">
                <span className="text-xs text-gray-500 font-mono w-16">
                  {Math.floor(chord.timestamp / 60)}:{String(Math.floor(chord.timestamp % 60)).padStart(2, '0')}
                </span>
                <span className="text-lg font-bold text-secondary">{chord.name}</span>
                <span className="text-xs text-gray-500">
                  {chord.duration.toFixed(1)}s
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-24 bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-secondary h-2 rounded-full"
                    style={{ width: `${chord.confidence * 100}%` }}
                  />
                </div>
                <span className="text-xs text-gray-500 w-12 text-right">
                  {(chord.confidence * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

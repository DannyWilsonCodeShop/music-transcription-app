import { useState } from 'react';

interface BassNNSDisplayProps {
  bassData: {
    key: string;
    mode: string;
    relativeMajor: string;
    confidence: number;
    tempo: number;
    timeSignature: string;
    totalNotes: number;
    totalMeasures: number;
    duration: number;
    measures: Array<{
      measure: number;
      start: number;
      end: number;
      nns_display: string;
      notes_display: string;
      beat_grid: Array<{
        beat: number;
        nns: string;
        note_name: string;
        has_note: boolean;
      }>;
    }>;
  };
  pdfUrl?: string;
}

export function BassNNSDisplay({ bassData, pdfUrl }: BassNNSDisplayProps) {
  const [showNoteNames, setShowNoteNames] = useState(false);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${String(secs).padStart(2, '0')}`;
  };

  return (
    <div style={{
      background: 'linear-gradient(135deg, #1f2937 0%, #111827 100%)',
      borderRadius: '24px',
      padding: '32px',
      boxShadow: '0 20px 60px rgba(0, 0, 0, 0.5)',
      border: '1px solid rgba(255, 255, 255, 0.1)',
      maxWidth: '1200px',
      margin: '0 auto'
    }}>
      {/* Header */}
      <div style={{ marginBottom: '32px', textAlign: 'center' }}>
        <h2 style={{
          fontSize: '28px',
          fontWeight: '700',
          color: '#ffffff',
          marginBottom: '16px',
          background: 'linear-gradient(135deg, #a78bfa 0%, #818cf8 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent'
        }}>
          🎸 Bass Line - Nashville Number System
        </h2>

        {/* Metadata */}
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          gap: '24px',
          flexWrap: 'wrap',
          marginBottom: '16px'
        }}>
          <div style={{
            padding: '8px 16px',
            background: 'rgba(147, 51, 234, 0.2)',
            borderRadius: '12px',
            border: '1px solid rgba(147, 51, 234, 0.3)'
          }}>
            <span style={{ fontSize: '14px', color: 'rgba(255, 255, 255, 0.7)' }}>Key: </span>
            <span style={{ fontSize: '16px', fontWeight: '600', color: '#ffffff' }}>
              {bassData.key} {bassData.mode}
            </span>
            {bassData.relativeMajor && bassData.mode === 'minor' && (
              <span style={{ fontSize: '12px', color: '#a78bfa', marginLeft: '8px' }}>
                (Relative: {bassData.relativeMajor})
              </span>
            )}
          </div>

          <div style={{
            padding: '8px 16px',
            background: 'rgba(99, 102, 241, 0.2)',
            borderRadius: '12px',
            border: '1px solid rgba(99, 102, 241, 0.3)'
          }}>
            <span style={{ fontSize: '14px', color: 'rgba(255, 255, 255, 0.7)' }}>Tempo: </span>
            <span style={{ fontSize: '16px', fontWeight: '600', color: '#ffffff' }}>
              {Math.round(bassData.tempo)} BPM
            </span>
          </div>

          <div style={{
            padding: '8px 16px',
            background: 'rgba(79, 70, 229, 0.2)',
            borderRadius: '12px',
            border: '1px solid rgba(79, 70, 229, 0.3)'
          }}>
            <span style={{ fontSize: '14px', color: 'rgba(255, 255, 255, 0.7)' }}>Time: </span>
            <span style={{ fontSize: '16px', fontWeight: '600', color: '#ffffff' }}>
              {bassData.timeSignature}
            </span>
          </div>
        </div>

        {/* Stats */}
        <div style={{
          fontSize: '14px',
          color: 'rgba(255, 255, 255, 0.6)',
          marginBottom: '8px'
        }}>
          {bassData.totalMeasures} measures • {bassData.totalNotes} note attacks • {formatTime(bassData.duration)} duration
        </div>

        {/* Confidence */}
        {bassData.confidence && (
          <div style={{
            fontSize: '12px',
            color: 'rgba(255, 255, 255, 0.5)',
            fontStyle: 'italic'
          }}>
            Key detection confidence: {(bassData.confidence * 100).toFixed(0)}%
          </div>
        )}
      </div>

      {/* Toggle Note Names */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '24px',
        padding: '16px',
        background: 'rgba(255, 255, 255, 0.03)',
        borderRadius: '12px',
        border: '1px solid rgba(255, 255, 255, 0.1)'
      }}>
        <div>
          <div style={{ fontSize: '14px', fontWeight: '600', color: '#ffffff', marginBottom: '4px' }}>
            Legend
          </div>
          <div style={{ fontSize: '12px', color: 'rgba(255, 255, 255, 0.6)' }}>
            "-" indicates beats without new note attacks
          </div>
        </div>

        <label style={{
          display: 'flex',
          alignItems: 'center',
          cursor: 'pointer',
          gap: '8px'
        }}>
          <input
            type="checkbox"
            checked={showNoteNames}
            onChange={(e) => setShowNoteNames(e.target.checked)}
            style={{
              width: '18px',
              height: '18px',
              cursor: 'pointer'
            }}
          />
          <span style={{ fontSize: '14px', color: 'rgba(255, 255, 255, 0.8)' }}>
            Show note names
          </span>
        </label>
      </div>

      {/* Measures Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
        gap: '16px',
        marginBottom: '24px'
      }}>
        {bassData.measures.map((measure) => (
          <div
            key={measure.measure}
            style={{
              padding: '16px',
              background: 'rgba(255, 255, 255, 0.05)',
              borderRadius: '12px',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.08)';
              e.currentTarget.style.borderColor = 'rgba(147, 51, 234, 0.5)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
              e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.1)';
            }}
          >
            {/* Measure Number */}
            <div style={{
              fontSize: '12px',
              fontWeight: '600',
              color: 'rgba(255, 255, 255, 0.5)',
              marginBottom: '8px'
            }}>
              Measure {measure.measure}
            </div>

            {/* NNS Display */}
            <div style={{
              fontFamily: 'monospace',
              fontSize: '18px',
              fontWeight: '700',
              color: '#818cf8',
              marginBottom: '4px',
              letterSpacing: '2px'
            }}>
              | {measure.nns_display} |
            </div>

            {/* Note Names (if enabled) */}
            {showNoteNames && (
              <div style={{
                fontFamily: 'monospace',
                fontSize: '12px',
                color: 'rgba(255, 255, 255, 0.5)',
                letterSpacing: '1px'
              }}>
                ({measure.notes_display})
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Download PDF Button */}
      {pdfUrl && (
        <div style={{ textAlign: 'center', marginTop: '32px' }}>
          <a
            href={pdfUrl}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: 'inline-block',
              padding: '14px 32px',
              background: 'linear-gradient(135deg, #9333ea 0%, #6366f1 100%)',
              color: 'white',
              fontWeight: '600',
              borderRadius: '12px',
              textDecoration: 'none',
              fontSize: '16px',
              boxShadow: '0 4px 15px rgba(147, 51, 234, 0.4)',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.boxShadow = '0 6px 20px rgba(147, 51, 234, 0.6)';
              e.currentTarget.style.transform = 'translateY(-2px)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.boxShadow = '0 4px 15px rgba(147, 51, 234, 0.4)';
              e.currentTarget.style.transform = 'translateY(0)';
            }}
          >
            📄 Download NNS Chart PDF
          </a>
        </div>
      )}
    </div>
  );
}

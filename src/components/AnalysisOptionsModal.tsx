import { useState } from 'react';

interface AnalysisOptionsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (options: AnalysisOptions) => void;
  filename: string;
}

export interface AnalysisOptions {
  musicPart: 'bass';  // Only bass is available for now
  includeLyrics: boolean;
  includeKey: boolean;
  includeTempo: boolean;
  includeTimeSignature: boolean;
}

export function AnalysisOptionsModal({ isOpen, onClose, onConfirm, filename }: AnalysisOptionsModalProps) {
  const [musicPart] = useState<'bass'>('bass');  // Fixed to bass only
  const [includeLyrics] = useState(false);  // Not available yet
  const [includeKey, setIncludeKey] = useState(true);
  const [includeTempo, setIncludeTempo] = useState(true);
  const [includeTimeSignature, setIncludeTimeSignature] = useState(true);

  if (!isOpen) return null;

  const handleConfirm = () => {
    onConfirm({
      musicPart,
      includeLyrics,
      includeKey,
      includeTempo,
      includeTimeSignature,
    });
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.7)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '20px'
    }}>
      <div style={{
        background: 'linear-gradient(135deg, #1f2937 0%, #111827 100%)',
        borderRadius: '24px',
        padding: '32px',
        maxWidth: '500px',
        width: '100%',
        boxShadow: '0 20px 60px rgba(0, 0, 0, 0.5), inset 0 0 0 1px rgba(255, 255, 255, 0.1)',
        border: '1px solid rgba(255, 255, 255, 0.1)'
      }}>
        {/* Header */}
        <div style={{ marginBottom: '24px' }}>
          <h2 style={{
            fontSize: '24px',
            fontWeight: '700',
            color: '#ffffff',
            marginBottom: '8px',
            background: 'linear-gradient(135deg, #a78bfa 0%, #818cf8 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent'
          }}>
            Analysis Options
          </h2>
          <p style={{
            fontSize: '14px',
            color: 'rgba(255, 255, 255, 0.6)',
            marginBottom: '4px'
          }}>
            {filename}
          </p>
        </div>

        {/* Question 1: Which music part? */}
        <div style={{ marginBottom: '24px' }}>
          <label style={{
            display: 'block',
            fontSize: '16px',
            fontWeight: '600',
            color: 'rgba(255, 255, 255, 0.9)',
            marginBottom: '12px'
          }}>
            Analysis Type
          </label>

          {/* Bass Option - Only option available */}
          <div
            style={{
              padding: '14px 16px',
              background: 'linear-gradient(135deg, rgba(147, 51, 234, 0.2) 0%, rgba(99, 102, 241, 0.2) 100%)',
              borderRadius: '12px',
              border: '2px solid rgba(147, 51, 234, 0.5)',
              marginBottom: '10px',
              display: 'flex',
              alignItems: 'center'
            }}
          >
            <div style={{
              width: '20px',
              height: '20px',
              borderRadius: '50%',
              border: '2px solid #9333ea',
              marginRight: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0
            }}>
              <div style={{
                width: '10px',
                height: '10px',
                borderRadius: '50%',
                background: '#9333ea'
              }} />
            </div>
            <div style={{ flex: 1 }}>
              <span style={{
                fontSize: '15px',
                fontWeight: '600',
                color: '#ffffff'
              }}>
                🎸 Bass Line
              </span>
              <span style={{
                marginLeft: '8px',
                fontSize: '12px',
                color: '#a78bfa',
                fontWeight: '500'
              }}>
                (Nashville Numbers)
              </span>
            </div>
          </div>
        </div>

        {/* Additional Options */}
        <div style={{
          marginBottom: '24px',
          padding: '16px',
          background: 'rgba(255, 255, 255, 0.03)',
          borderRadius: '12px',
          border: '1px solid rgba(255, 255, 255, 0.1)'
        }}>
          <div style={{
            fontSize: '14px',
            fontWeight: '600',
            color: 'rgba(255, 255, 255, 0.9)',
            marginBottom: '12px'
          }}>
            Include in analysis:
          </div>

          {/* Key Detection */}
          <label style={{
            display: 'flex',
            alignItems: 'center',
            marginBottom: '8px',
            cursor: 'pointer'
          }}>
            <input
              type="checkbox"
              checked={includeKey}
              onChange={(e) => setIncludeKey(e.target.checked)}
              style={{
                width: '18px',
                height: '18px',
                marginRight: '10px',
                cursor: 'pointer'
              }}
            />
            <span style={{ fontSize: '14px', color: 'rgba(255, 255, 255, 0.8)' }}>
              Key Detection
            </span>
          </label>

          {/* Tempo Detection */}
          <label style={{
            display: 'flex',
            alignItems: 'center',
            marginBottom: '8px',
            cursor: 'pointer'
          }}>
            <input
              type="checkbox"
              checked={includeTempo}
              onChange={(e) => setIncludeTempo(e.target.checked)}
              style={{
                width: '18px',
                height: '18px',
                marginRight: '10px',
                cursor: 'pointer'
              }}
            />
            <span style={{ fontSize: '14px', color: 'rgba(255, 255, 255, 0.8)' }}>
              Tempo (BPM)
            </span>
          </label>

          {/* Time Signature */}
          <label style={{
            display: 'flex',
            alignItems: 'center',
            cursor: 'pointer'
          }}>
            <input
              type="checkbox"
              checked={includeTimeSignature}
              onChange={(e) => setIncludeTimeSignature(e.target.checked)}
              style={{
                width: '18px',
                height: '18px',
                marginRight: '10px',
                cursor: 'pointer'
              }}
            />
            <span style={{ fontSize: '14px', color: 'rgba(255, 255, 255, 0.8)' }}>
              Time Signature
            </span>
          </label>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            onClick={onClose}
            style={{
              flex: 1,
              padding: '12px 24px',
              background: 'rgba(255, 255, 255, 0.1)',
              backdropFilter: 'blur(10px)',
              color: 'rgba(255, 255, 255, 0.9)',
              fontWeight: '500',
              borderRadius: '12px',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              cursor: 'pointer',
              fontSize: '15px',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.15)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)';
            }}
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            style={{
              flex: 1,
              padding: '12px 24px',
              background: 'linear-gradient(135deg, #9333ea 0%, #6366f1 100%)',
              color: 'white',
              fontWeight: '600',
              borderRadius: '12px',
              border: 'none',
              cursor: 'pointer',
              fontSize: '15px',
              boxShadow: '0 4px 15px rgba(147, 51, 234, 0.4)',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.boxShadow = '0 6px 20px rgba(147, 51, 234, 0.6)';
              e.currentTarget.style.transform = 'translateY(-1px)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.boxShadow = '0 4px 15px rgba(147, 51, 234, 0.4)';
              e.currentTarget.style.transform = 'translateY(0)';
            }}
          >
            Start Analysis
          </button>
        </div>
      </div>
    </div>
  );
}

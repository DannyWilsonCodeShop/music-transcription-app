import { useState } from 'react';

interface AnalysisOptionsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (options: AnalysisOptions) => void;
  filename: string;
}

export interface AnalysisOptions {
  musicPart: 'bass';  // Will be determined after stem separation
  includeLyrics: boolean;
  includeKey: boolean;
  includeTempo: boolean;
  includeTimeSignature: boolean;
}

export function AnalysisOptionsModal({ isOpen, onClose, onConfirm, filename }: AnalysisOptionsModalProps) {
  const [musicPart] = useState<'bass'>('bass');  // Placeholder - actual selection happens later
  const [includeLyrics] = useState(false);  // Not available yet
  const [includeKey] = useState(true);  // Always included
  const [includeTempo] = useState(true);  // Always included
  const [includeTimeSignature] = useState(true);  // Always included

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
            Ready to Analyze
          </h2>
          <p style={{
            fontSize: '14px',
            color: 'rgba(255, 255, 255, 0.6)',
            marginBottom: '4px'
          }}>
            {filename}
          </p>
        </div>

        {/* Info Box */}
        <div style={{
          marginBottom: '24px',
          padding: '16px',
          background: 'rgba(147, 51, 234, 0.1)',
          borderRadius: '12px',
          border: '1px solid rgba(147, 51, 234, 0.3)'
        }}>
          <div style={{
            fontSize: '14px',
            color: 'rgba(255, 255, 255, 0.9)',
            marginBottom: '8px',
            fontWeight: '500'
          }}>
            📊 What happens next:
          </div>
          <ul style={{
            fontSize: '13px',
            color: 'rgba(255, 255, 255, 0.7)',
            lineHeight: '1.6',
            margin: 0,
            paddingLeft: '20px'
          }}>
            <li>Audio will be analyzed for tempo, key, and time signature</li>
            <li>Stems will be separated (bass, piano, guitar, etc.)</li>
            <li>You'll choose which instruments to transcribe</li>
            <li>Nashville Number System chart will be generated</li>
          </ul>
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

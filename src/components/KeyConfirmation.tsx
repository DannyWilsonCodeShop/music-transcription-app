import React, { useState } from 'react';
import { Check, X, Music2 } from 'lucide-react';
import { confirmKey } from '../services/transcriptionService';

interface KeyConfirmationProps {
  jobId: string;
  detectedKey: string;
  keyConfidence: number;
  onKeyConfirmed: (key: string) => void;
  onCancel: () => void;
}

export const KeyConfirmation: React.FC<KeyConfirmationProps> = ({
  jobId,
  detectedKey,
  keyConfidence,
  onKeyConfirmed,
  onCancel,
}) => {
  const [selectedKey, setSelectedKey] = useState<string>(detectedKey);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // All 24 possible keys (12 major, 12 minor)
  const allKeys = [
    'C major', 'G major', 'D major', 'A major', 'E major', 'B major',
    'F# major', 'Db major', 'Ab major', 'Eb major', 'Bb major', 'F major',
    'A minor', 'E minor', 'B minor', 'F# minor', 'C# minor', 'G# minor',
    'Eb minor', 'Bb minor', 'F minor', 'C minor', 'G minor', 'D minor'
  ];

  const getConfidenceLevel = (confidence: number): { label: string; color: string } => {
    if (confidence >= 0.8) return { label: 'High', color: '#10b981' };
    if (confidence >= 0.5) return { label: 'Medium', color: '#f59e0b' };
    return { label: 'Low', color: '#ef4444' };
  };

  const confidenceInfo = getConfidenceLevel(keyConfidence);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setError(null);
    
    try {
      await confirmKey(jobId, selectedKey);
      onKeyConfirmed(selectedKey);
    } catch (err) {
      console.error('Failed to confirm key:', err);
      setError(err instanceof Error ? err.message : 'Failed to confirm key');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 p-6">
        {/* Header */}
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Confirm Musical Key
          </h2>
          <p className="text-gray-600">
            Verify the detected key or select a different one for accurate Nashville Number notation
          </p>
        </div>

        {/* Detected Key Display */}
        <div className="mb-6 p-6 bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg border border-blue-200">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-blue-600 rounded-full">
              <Music2 className="w-8 h-8 text-white" />
            </div>
            <div className="flex-1">
              <div className="text-sm text-gray-600 mb-1">Detected Key</div>
              <div className="text-3xl font-bold text-gray-900">{detectedKey}</div>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-600 mb-1">Confidence</div>
              <div className="flex items-center gap-2">
                <div className="text-2xl font-bold" style={{ color: confidenceInfo.color }}>
                  {(keyConfidence * 100).toFixed(0)}%
                </div>
                <span 
                  className="px-2 py-1 rounded text-xs font-semibold text-white"
                  style={{ backgroundColor: confidenceInfo.color }}
                >
                  {confidenceInfo.label}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Key Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Is this correct? Or select a different key:
          </label>
          <select
            value={selectedKey}
            onChange={(e) => setSelectedKey(e.target.value)}
            disabled={isSubmitting}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {allKeys.map((key) => (
              <option key={key} value={key}>
                {key}
              </option>
            ))}
          </select>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {/* Info Box */}
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h3 className="font-semibold text-blue-900 mb-2">Why does this matter?</h3>
          <p className="text-sm text-blue-800">
            The key determines how chords are converted to Nashville Numbers. For example, 
            in C major, a C chord is "1" and G is "5". Selecting the correct key ensures 
            accurate number notation on your chart.
          </p>
        </div>

        {/* Timeout Notice */}
        <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-800">
            ⏱️ Auto-confirms detected key in 5 minutes if no selection made
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end gap-3">
          <button
            onClick={onCancel}
            disabled={isSubmitting}
            className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <X className="w-4 h-4" />
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Check className="w-4 h-4" />
            {isSubmitting ? 'Confirming...' : 'Confirm Key'}
          </button>
        </div>
      </div>
    </div>
  );
};

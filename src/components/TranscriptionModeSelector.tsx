import React, { useState } from 'react';
import { Check, X, Music, Piano, Guitar, Disc } from 'lucide-react';
import { confirmTranscriptionMode } from '../services/transcriptionService';

interface TranscriptionModeSelectorProps {
  jobId: string;
  onModeSelected: (mode: string) => void;
  onCancel: () => void;
}

export const TranscriptionModeSelector: React.FC<TranscriptionModeSelectorProps> = ({
  jobId,
  onModeSelected,
  onCancel,
}) => {
  const [selectedMode, setSelectedMode] = useState<'bass-only' | 'bass+piano' | 'bass+guitar' | 'all'>('bass-only');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const modes = [
    {
      value: 'bass-only' as const,
      label: 'Bass Only',
      description: 'Fastest processing (~3 min)',
      icon: Music,
      color: '#3b82f6',
    },
    {
      value: 'bass+piano' as const,
      label: 'Bass + Piano',
      description: 'Enhanced chord detection (~5 min)',
      icon: Piano,
      color: '#8b5cf6',
    },
    {
      value: 'bass+guitar' as const,
      label: 'Bass + Guitar',
      description: 'Full harmonic context (~5 min)',
      icon: Guitar,
      color: '#ec4899',
    },
    {
      value: 'all' as const,
      label: 'All Instruments',
      description: 'Complete transcription (~8 min)',
      icon: Disc,
      color: '#f59e0b',
    },
  ];

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setError(null);
    
    try {
      await confirmTranscriptionMode(jobId, selectedMode);
      onModeSelected(selectedMode);
    } catch (err) {
      console.error('Failed to confirm mode:', err);
      setError(err instanceof Error ? err.message : 'Failed to confirm mode');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full mx-4 p-6">
        {/* Header */}
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Select Transcription Mode
          </h2>
          <p className="text-gray-600">
            Choose which instruments to transcribe for enhanced accuracy
          </p>
        </div>

        {/* Mode Options */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {modes.map((mode) => {
            const Icon = mode.icon;
            const isSelected = selectedMode === mode.value;
            
            return (
              <button
                key={mode.value}
                onClick={() => setSelectedMode(mode.value)}
                disabled={isSubmitting}
                className={`
                  p-4 rounded-lg border-2 transition-all text-left
                  ${isSelected 
                    ? 'border-blue-500 bg-blue-50 shadow-md' 
                    : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm'
                  }
                  ${isSubmitting ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                `}
                style={{
                  borderColor: isSelected ? mode.color : undefined,
                  backgroundColor: isSelected ? `${mode.color}10` : undefined,
                }}
              >
                <div className="flex items-start gap-3">
                  <div 
                    className="p-2 rounded-lg"
                    style={{ 
                      backgroundColor: isSelected ? mode.color : '#f3f4f6',
                      color: isSelected ? 'white' : '#6b7280'
                    }}
                  >
                    <Icon className="w-6 h-6" />
                  </div>
                  <div className="flex-1">
                    <div className="font-semibold text-gray-900 mb-1">
                      {mode.label}
                    </div>
                    <div className="text-sm text-gray-600">
                      {mode.description}
                    </div>
                  </div>
                  {isSelected && (
                    <div 
                      className="w-6 h-6 rounded-full flex items-center justify-center"
                      style={{ backgroundColor: mode.color }}
                    >
                      <Check className="w-4 h-4 text-white" />
                    </div>
                  )}
                </div>
              </button>
            );
          })}
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {/* Timeout Notice */}
        <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-800">
            ⏱️ Auto-selects "Bass Only" in 5 minutes if no selection made
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
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Check className="w-4 h-4" />
            {isSubmitting ? 'Confirming...' : 'Confirm Selection'}
          </button>
        </div>
      </div>
    </div>
  );
};

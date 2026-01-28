import { useEffect, useState } from 'react';
import { TranscriptionJob } from '../services/transcriptionService';

interface TranscriptionProgressBarProps {
  job: TranscriptionJob;
}

export default function TranscriptionProgressBar({ job }: TranscriptionProgressBarProps) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const startTime = new Date(job.createdAt).getTime();
    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, [job.createdAt]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const progress = job.progress || 0;
  const isComplete = job.status === 'COMPLETE';
  const isFailed = job.status === 'FAILED';

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-4">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-lg font-semibold text-gray-800">{job.title}</h3>
        <span className="text-sm text-gray-500">{formatTime(elapsed)}</span>
      </div>

      {/* Progress Bar */}
      <div className="relative w-full h-3 bg-blue-100 rounded-full overflow-hidden mb-3">
        <div
          className={`absolute top-0 left-0 h-full transition-all duration-500 ease-out ${
            isFailed
              ? 'bg-red-500'
              : isComplete
              ? 'bg-green-500'
              : 'bg-gradient-to-r from-secondary to-tertiary'
          }`}
          style={{ width: `${progress}%` }}
        >
          {progress > 0 && (
            <div className="absolute inset-0 bg-white/20 animate-pulse" />
          )}
        </div>
      </div>

      {/* Status and Step */}
      <div className="flex justify-between items-center text-sm">
        <div className="flex items-center space-x-2">
          {(job.status === 'DOWNLOADING' || job.status === 'TRANSCRIBING' || job.status === 'DETECTING_CHORDS' || job.status === 'GENERATING_PDF') && (
            <div className="w-2 h-2 bg-secondary rounded-full animate-pulse" />
          )}
          <span className={`font-medium ${
            isFailed ? 'text-red-600' : isComplete ? 'text-green-600' : 'text-secondary'
          }`}>
            {job.currentStep || job.status}
          </span>
        </div>
        <span className="text-gray-600">{progress}%</span>
      </div>

      {/* Error Message */}
      {isFailed && job.error && (
        <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
          <strong>Error:</strong> {job.error}
        </div>
      )}

      {/* Debug Info */}
      {!isComplete && !isFailed && (
        <div className="mt-3 p-2 bg-blue-50 rounded text-xs text-gray-500 font-mono">
          <div>Job ID: {job.id}</div>
          <div>Status: {job.status}</div>
          {job.updatedAt && (
            <div>Last Update: {new Date(job.updatedAt).toLocaleTimeString()}</div>
          )}
        </div>
      )}
    </div>
  );
}

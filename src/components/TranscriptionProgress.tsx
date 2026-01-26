import { useState, useEffect } from 'react';
import { getJobStatus, TranscriptionJob } from '../services/transcriptionService';

interface TranscriptionProgressProps {
  jobId: string;
  onComplete: (job: TranscriptionJob) => void;
}

export default function TranscriptionProgress({ jobId, onComplete }: TranscriptionProgressProps) {
  const [job, setJob] = useState<TranscriptionJob | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;

    const fetchJobStatus = async () => {
      try {
        const data = await getJobStatus(jobId);
        
        if (data) {
          setJob(data);
          setLoading(false);

          if (data.status === 'COMPLETED') {
            clearInterval(interval);
            onComplete(data);
          } else if (data.status === 'FAILED') {
            clearInterval(interval);
            setError(data.error || 'Transcription failed. Please try again.');
          }
        }
      } catch (err) {
        console.error('Error fetching job status:', err);
        setError('Failed to fetch job status');
      }
    };

    // Initial fetch
    fetchJobStatus();

    // Poll every 5 seconds
    interval = setInterval(fetchJobStatus, 5000);

    return () => clearInterval(interval);
  }, [jobId, onComplete]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'PENDING':
        return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'PROCESSING':
        return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'COMPLETED':
        return 'bg-green-100 text-green-700 border-green-200';
      case 'FAILED':
        return 'bg-red-100 text-red-700 border-red-200';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'PENDING':
        return '⏳';
      case 'PROCESSING':
        return '⚙️';
      case 'COMPLETED':
        return '✅';
      case 'FAILED':
        return '❌';
      default:
        return '📝';
    }
  };

  const getProgressPercentage = (status: string) => {
    switch (status) {
      case 'PENDING':
        return 10;
      case 'PROCESSING':
        return 50;
      case 'COMPLETED':
        return 100;
      case 'FAILED':
        return 0;
      default:
        return 0;
    }
  };

  if (loading && !job) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-center space-x-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-secondary"></div>
          <span className="text-gray-600">Loading job status...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 rounded-xl border border-red-200 p-6">
        <div className="flex items-center space-x-3">
          <span className="text-2xl">❌</span>
          <div>
            <h4 className="font-semibold text-red-900">Error</h4>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!job) return null;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-bold text-gray-900">{job.title}</h3>
          {job.youtubeUrl && (
            <p className="text-sm text-gray-600 truncate">{job.youtubeUrl}</p>
          )}
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(job.status)}`}>
          {getStatusIcon(job.status)} {job.status}
        </span>
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${
              job.status === 'COMPLETED' ? 'bg-green-500' :
              job.status === 'PROCESSING' ? 'bg-blue-500 animate-pulse' :
              job.status === 'FAILED' ? 'bg-red-500' :
              'bg-yellow-500'
            }`}
            style={{ width: `${getProgressPercentage(job.status)}%` }}
          ></div>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          {job.status === 'PENDING' && 'Waiting to start...'}
          {job.status === 'PROCESSING' && 'Processing audio and detecting chords...'}
          {job.status === 'COMPLETED' && 'Transcription complete!'}
          {job.status === 'FAILED' && 'Transcription failed'}
        </p>
      </div>

      {/* Processing Steps */}
      {(job.status === 'PROCESSING' || job.status === 'COMPLETED') && (
        <div className="space-y-2 mb-4">
          <div className="flex items-center space-x-3 text-sm">
            <span className="text-green-600">✓</span>
            <span className="text-gray-700">Audio downloaded</span>
          </div>
          <div className="flex items-center space-x-3 text-sm">
            <span className={job.status === 'COMPLETED' ? 'text-green-600' : 'text-blue-600 animate-pulse'}>
              {job.status === 'COMPLETED' ? '✓' : '⚙️'}
            </span>
            <span className="text-gray-700">Transcribing lyrics</span>
          </div>
          <div className="flex items-center space-x-3 text-sm">
            <span className={job.status === 'COMPLETED' ? 'text-green-600' : 'text-blue-600 animate-pulse'}>
              {job.status === 'COMPLETED' ? '✓' : '⚙️'}
            </span>
            <span className="text-gray-700">Detecting chords</span>
          </div>
          {job.status === 'COMPLETED' && (
            <div className="flex items-center space-x-3 text-sm">
              <span className="text-green-600">✓</span>
              <span className="text-gray-700">Generating sheet music</span>
            </div>
          )}
        </div>
      )}

      {/* Metadata */}
      <div className="pt-4 border-t border-gray-200">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>Job ID: {jobId.substring(0, 20)}...</span>
          <span>{new Date(job.createdAt).toLocaleString()}</span>
        </div>
      </div>
    </div>
  );
}

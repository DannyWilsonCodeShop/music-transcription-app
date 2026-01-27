import { useState, useEffect } from 'react';
import { getJobStatus, TranscriptionJob } from '../services/transcriptionService';
import TranscriptionProgressBar from './TranscriptionProgressBar';

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
          }
        }
      } catch (err) {
        console.error('Error fetching job status:', err);
        // Don't set error immediately - job might not exist yet
        if (!loading) {
          setError('Failed to fetch job status');
        }
      }
    };

    // Initial fetch
    fetchJobStatus();

    // Poll every 3 seconds for more responsive updates
    interval = setInterval(fetchJobStatus, 3000);

    return () => clearInterval(interval);
  }, [jobId, onComplete, loading]);

  if (loading && !job) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 mb-4">
        <div className="flex items-center justify-center space-x-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-secondary"></div>
          <span className="text-gray-600">Initializing transcription...</span>
        </div>
      </div>
    );
  }

  if (error && !job) {
    return (
      <div className="bg-red-50 rounded-lg border border-red-200 p-6 mb-4">
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

  return <TranscriptionProgressBar job={job} />;
}

import { useState, useEffect } from 'react';
import { getJobStatus, type TranscriptionJob } from '../services/transcriptionService';

export default function TranscriptionsList() {
  const [jobs, setJobs] = useState<TranscriptionJob[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchJobs = async () => {
    try {
      // Get job IDs from localStorage
      const storedJobIds = localStorage.getItem('chordscout_jobs');
      if (!storedJobIds) {
        setLoading(false);
        return;
      }

      const jobIds: string[] = JSON.parse(storedJobIds);
      
      // Fetch status for each job
      const jobPromises = jobIds.map(id => getJobStatus(id));
      const jobResults = await Promise.all(jobPromises);
      
      // Filter out null results and sort by creation date
      const validJobs = jobResults
        .filter((job): job is TranscriptionJob => job !== null)
        .sort((a, b) => 
          new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
        );
      
      setJobs(validJobs);
    } catch (error) {
      console.error('Error fetching jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'COMPLETE':
        return 'bg-green-100 text-green-700 border-green-200';
      case 'DOWNLOADING':
      case 'TRANSCRIBING':
      case 'DETECTING_CHORDS':
      case 'GENERATING_PDF':
        return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'FAILED':
        return 'bg-red-100 text-red-700 border-red-200';
      default:
        return 'bg-yellow-100 text-yellow-700 border-yellow-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'COMPLETE':
        return '✅';
      case 'DOWNLOADING':
      case 'TRANSCRIBING':
      case 'DETECTING_CHORDS':
      case 'GENERATING_PDF':
        return '⚙️';
      case 'FAILED':
        return '❌';
      default:
        return '⏳';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'PENDING':
        return 'Pending';
      case 'DOWNLOADING':
        return 'Downloading';
      case 'TRANSCRIBING':
        return 'Transcribing';
      case 'DETECTING_CHORDS':
        return 'Detecting Chords';
      case 'GENERATING_PDF':
        return 'Generating PDF';
      case 'COMPLETE':
        return 'Complete';
      case 'FAILED':
        return 'Failed';
      default:
        return status;
    }
  };

  return (
    <div className="bg-gradient-to-br from-white to-blue-50/30 rounded-xl shadow-lg border border-blue-200">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-4 rounded-t-xl border-b border-blue-200">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-[#3f3f3f] flex items-center gap-2">
            🎼 Your Transcriptions
          </h2>
          {jobs.length > 0 && (
            <span className="px-3 py-1 bg-[#0089c6] text-white text-sm rounded-full font-medium">
              {jobs.length}
            </span>
          )}
        </div>
      </div>

      {/* Scrollable Content */}
      <div className="max-h-[600px] overflow-y-auto">
        {loading ? (
          <div className="text-center py-12 px-4">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-[#0089c6]"></div>
            <p className="text-gray-500 mt-2">Loading transcriptions...</p>
          </div>
        ) : jobs.length === 0 ? (
          <div className="text-center py-16 px-4">
            <div className="text-6xl mb-4">🎼</div>
            <p className="text-gray-500 font-medium mb-2">No transcriptions yet</p>
            <p className="text-sm text-gray-400">
              Paste a YouTube link to get started
            </p>
          </div>
        ) : (
          jobs.map((job, index) => (
            <div
              key={job.id}
              className={`border-b border-gray-100 p-4 hover:bg-gray-50/50 transition-colors ${
                index === jobs.length - 1 ? 'border-b-0' : ''
              }`}
            >
              {/* Job Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h3 className="font-semibold text-[#3f3f3f] mb-1">{job.title}</h3>
                  <p className="text-xs text-gray-500">
                    {new Date(job.createdAt).toLocaleString()}
                  </p>
                  {job.youtubeUrl && (
                    <a 
                      href={job.youtubeUrl} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-xs text-blue-600 hover:underline"
                    >
                      🎬 View on YouTube
                    </a>
                  )}
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-semibold border ${getStatusColor(job.status)}`}
                >
                  {getStatusIcon(job.status)} {getStatusText(job.status)}
                </span>
              </div>

              {/* Progress Bar */}
              {job.progress !== undefined && job.status !== 'COMPLETE' && job.status !== 'FAILED' && (
                <div className="mb-3">
                  <div className="flex justify-between text-xs text-gray-600 mb-1">
                    <span>Progress</span>
                    <span>{job.progress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${job.progress}%` }}
                    ></div>
                  </div>
                </div>
              )}

              {/* Completed Job Results */}
              {job.status === 'COMPLETE' && job.pdfUrl && (
                <div className="space-y-2">
                  <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-sm">📄</span>
                      <span className="text-xs font-semibold text-gray-700">PDF Ready!</span>
                    </div>
                    <a
                      href={job.pdfUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block w-full py-2 px-4 bg-gradient-to-r from-blue-500 to-purple-600 text-white text-sm font-medium rounded-lg hover:shadow-md transition-all text-center"
                    >
                      📥 Download PDF
                    </a>
                  </div>
                </div>
              )}

              {/* Processing State */}
              {(job.status === 'DOWNLOADING' || job.status === 'TRANSCRIBING' || job.status === 'DETECTING_CHORDS' || job.status === 'GENERATING_PDF') && (
                <div className="flex items-center gap-2 text-sm text-blue-600 bg-blue-50 p-3 rounded-lg">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                  <span>{getStatusText(job.status)}...</span>
                </div>
              )}

              {/* Failed State */}
              {job.status === 'FAILED' && (
                <div className="p-3 bg-red-50 rounded-lg border border-red-200">
                  <p className="text-xs text-red-600">
                    ⚠️ {job.error || 'Transcription failed. Please try again.'}
                  </p>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

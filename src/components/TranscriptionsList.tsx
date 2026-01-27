import { useState, useEffect } from 'react';
import { generateClient } from 'aws-amplify/data';
import type { Schema } from '../../amplify/data/resource';

const client = generateClient<Schema>();

export default function TranscriptionsList() {
  const [jobs, setJobs] = useState<Array<Schema["TranscriptionJob"]["type"]>>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchJobs = async () => {
    try {
      const { data } = await client.models.TranscriptionJob.list();
      setJobs(data.sort((a, b) => 
        new Date(b.createdAt || 0).getTime() - new Date(a.createdAt || 0).getTime()
      ));
    } catch (error) {
      console.error('Error fetching jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-700 border-green-200';
      case 'processing':
        return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'failed':
        return 'bg-red-100 text-red-700 border-red-200';
      default:
        return 'bg-yellow-100 text-yellow-700 border-yellow-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return '✅';
      case 'processing':
        return '⚙️';
      case 'failed':
        return '❌';
      default:
        return '⏳';
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
              Upload an audio file or YouTube link to get started
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
                    {new Date(job.createdAt || '').toLocaleString()}
                  </p>
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-semibold border ${getStatusColor(
                    job.status || 'pending'
                  )}`}
                >
                  {getStatusIcon(job.status || 'pending')} {job.status?.toUpperCase()}
                </span>
              </div>

              {/* Completed Job Results */}
              {job.status === 'completed' && (
                <div className="space-y-2">
                  {job.lyrics && (
                    <div className="p-3 bg-white rounded-lg border border-blue-100">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm">🎤</span>
                        <span className="text-xs font-semibold text-gray-700">Lyrics</span>
                      </div>
                      <p className="text-xs text-gray-600 line-clamp-2">
                        {typeof job.lyrics === 'string' ? job.lyrics : 'Available'}
                      </p>
                    </div>
                  )}
                  {job.chords && (
                    <div className="p-3 bg-white rounded-lg border border-purple-100">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm">🎸</span>
                        <span className="text-xs font-semibold text-gray-700">Chords</span>
                      </div>
                      <p className="text-xs text-gray-600 line-clamp-2">
                        {typeof job.chords === 'string' ? job.chords : 'Available'}
                      </p>
                    </div>
                  )}
                  <button className="w-full py-2 px-4 bg-gradient-to-r from-blue-500 to-purple-600 text-white text-sm font-medium rounded-lg hover:shadow-md transition-all">
                    View Full Results
                  </button>
                </div>
              )}

              {/* Processing State */}
              {job.status === 'processing' && (
                <div className="flex items-center gap-2 text-sm text-blue-600 bg-blue-50 p-3 rounded-lg">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                  <span>Processing your audio...</span>
                </div>
              )}

              {/* Failed State */}
              {job.status === 'failed' && (
                <div className="p-3 bg-red-50 rounded-lg border border-red-200">
                  <p className="text-xs text-red-600">
                    ⚠️ Transcription failed. Please try again.
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

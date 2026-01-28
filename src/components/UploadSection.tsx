import { useState } from 'react';
import { startTranscription } from '../services/transcriptionService';

export default function UploadSection() {
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleYouTubeSubmit = async () => {
    if (!youtubeUrl) return;
    
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const jobId = await startTranscription(youtubeUrl);
      
      // Store job ID in localStorage
      const storedJobIds = localStorage.getItem('chordscout_jobs');
      const jobIds: string[] = storedJobIds ? JSON.parse(storedJobIds) : [];
      jobIds.unshift(jobId); // Add to beginning
      localStorage.setItem('chordscout_jobs', JSON.stringify(jobIds.slice(0, 50))); // Keep last 50
      
      setYoutubeUrl('');
      setSuccess(`Job created successfully! Job ID: ${jobId}`);
      
      // Refresh the page after 2 seconds to show the new job
      setTimeout(() => {
        window.location.reload();
      }, 2000);
    } catch (error) {
      console.error('Error creating YouTube job:', error);
      setError(error instanceof Error ? error.message : 'Submission failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl shadow-lg border border-blue-200 p-4">
      {/* Header with Avatar */}
      <div className="flex items-center gap-3 mb-4">
        {/* Avatar */}
        <img
          src="https://api.dicebear.com/7.x/avataaars/svg?seed=user"
          alt="User avatar"
          className="w-10 h-10 rounded-full"
        />
        <div className="flex-1">
          <h3 className="font-semibold text-gray-800">Create New Transcription</h3>
          <p className="text-sm text-gray-600">Paste a YouTube URL to get started</p>
        </div>
      </div>

      {/* YouTube Input */}
      <div className="space-y-4">
        <div className="bg-white/80 rounded-xl p-4">
          <input
            type="url"
            placeholder="https://www.youtube.com/watch?v=..."
            value={youtubeUrl}
            onChange={(e) => setYoutubeUrl(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && youtubeUrl && !loading) {
                handleYouTubeSubmit();
              }
            }}
            className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-[#0089c6] focus:outline-none transition-colors bg-white"
          />
          <p className="text-xs text-gray-500 mt-2">
            🎵 Paste a YouTube music video URL to transcribe with high-accuracy AI
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            <p className="text-sm">{error}</p>
          </div>
        )}

        {/* Success Message */}
        {success && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
            <p className="text-sm">{success}</p>
          </div>
        )}

        <button
          onClick={handleYouTubeSubmit}
          disabled={!youtubeUrl || loading}
          className="w-full py-3 px-6 bg-gradient-to-r from-[#0089c6] to-[#0089c6] text-white font-semibold rounded-full hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? '🎵 Creating Job...' : '🎬 Transcribe YouTube Video'}
        </button>
      </div>
    </div>
  );
}

import { useState } from 'react';
import { mockStartTranscription } from '../services/transcriptionService';

interface UploadInterfaceProps {
  onUploadStart: (jobId: string) => void;
}

export default function UploadInterface({ onUploadStart }: UploadInterfaceProps) {
  const [activeTab, setActiveTab] = useState<'file' | 'youtube'>('youtube');
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [artist, setArtist] = useState('');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  const handleFileUpload = async () => {
    if (!file) return;
    
    setUploading(true);
    setError('');
    
    try {
      // TODO: Implement file upload to S3 and transcription
      // For now, show error that file upload is not yet implemented
      setError('File upload coming soon! Please use YouTube URL for now.');
    } catch (err) {
      console.error('Upload error:', err);
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleYouTubeSubmit = async () => {
    if (!youtubeUrl) return;
    
    setUploading(true);
    setError('');
    
    try {
      // TEMPORARY: Using mock function until API proxy is set up
      // TODO: Replace with real startTranscription once Cognito issues are resolved
      const jobId = await mockStartTranscription(
        youtubeUrl,
        title || 'YouTube Video'
      );

      onUploadStart(jobId);
      
      // Reset form
      setYoutubeUrl('');
      setTitle('');
      setArtist('');
    } catch (err) {
      console.error('Transcription error:', err);
      setError(err instanceof Error ? err.message : 'Transcription failed');
    } finally {
      setUploading(false);
    }
  };

  const isYouTubeUrl = (url: string) => {
    return url.includes('youtube.com') || url.includes('youtu.be');
  };

  return (
    <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl shadow-lg border border-blue-200 p-6">
      {/* Header */}
      <div className="mb-6">
        <h3 className="text-xl font-bold text-gray-900 flex items-center">
          <span className="text-2xl mr-3">🎵</span>
          Upload Music for Transcription
        </h3>
        <p className="text-sm text-gray-600 mt-1">
          Upload an audio file or paste a YouTube link to get lyrics, chords, and sheet music
        </p>
      </div>

      {/* Tab Buttons */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setActiveTab('youtube')}
          className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all text-sm flex items-center justify-center gap-2 ${
            activeTab === 'youtube'
              ? 'bg-gradient-to-r from-red-500 to-red-600 text-white shadow-md'
              : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'
          }`}
        >
          <span className="text-lg">▶️</span>
          YouTube Link
        </button>
        <button
          onClick={() => setActiveTab('file')}
          className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all text-sm flex items-center justify-center gap-2 ${
            activeTab === 'file'
              ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-md'
              : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'
          }`}
        >
          <span className="text-lg">📁</span>
          Audio File
        </button>
      </div>

      {/* YouTube Tab */}
      {activeTab === 'youtube' && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              YouTube URL *
            </label>
            <input
              type="url"
              placeholder="https://www.youtube.com/watch?v=..."
              value={youtubeUrl}
              onChange={(e) => setYoutubeUrl(e.target.value)}
              className="w-full px-4 py-3 border-2 border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-300 text-sm bg-white"
            />
            {youtubeUrl && !isYouTubeUrl(youtubeUrl) && (
              <p className="text-xs text-red-600 mt-1">⚠️ Please enter a valid YouTube URL</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Song Title (optional)
              </label>
              <input
                type="text"
                placeholder="Enter song title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full px-4 py-3 border-2 border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-300 text-sm bg-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Artist (optional)
              </label>
              <input
                type="text"
                placeholder="Enter artist name"
                value={artist}
                onChange={(e) => setArtist(e.target.value)}
                className="w-full px-4 py-3 border-2 border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-300 text-sm bg-white"
              />
            </div>
          </div>

          <button
            onClick={handleYouTubeSubmit}
            disabled={!youtubeUrl || !isYouTubeUrl(youtubeUrl) || uploading}
            className="w-full py-3 px-6 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md font-medium text-sm flex items-center justify-center gap-2"
          >
            {uploading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                Processing...
              </>
            ) : (
              <>
                <span>🎼</span>
                Start Transcription
              </>
            )}
          </button>
        </div>
      )}

      {/* File Upload Tab */}
      {activeTab === 'file' && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Audio File *
            </label>
            <div
              className={`border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer ${
                file
                  ? 'border-secondary bg-white'
                  : 'border-gray-300 bg-white hover:border-secondary hover:bg-blue-50'
              }`}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                const files = e.dataTransfer.files;
                if (files.length > 0 && files[0].type.startsWith('audio/')) {
                  setFile(files[0]);
                }
              }}
            >
              <input
                type="file"
                accept="audio/*"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="hidden"
                id="file-upload"
              />
              <label htmlFor="file-upload" className="cursor-pointer block">
                {file ? (
                  <div>
                    <div className="text-5xl mb-3">🎵</div>
                    <div className="font-semibold text-secondary text-base">{file.name}</div>
                    <div className="text-sm text-gray-500 mt-2">
                      {(file.size / 1024 / 1024).toFixed(1)} MB
                    </div>
                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        setFile(null);
                      }}
                      className="mt-3 text-sm text-red-600 hover:text-red-700"
                    >
                      Remove file
                    </button>
                  </div>
                ) : (
                  <div>
                    <div className="text-5xl mb-3">📤</div>
                    <div className="font-semibold text-gray-700 text-base mb-2">
                      Drop audio file here or click to browse
                    </div>
                    <div className="text-sm text-gray-500">
                      Supports: MP3, WAV, M4A, FLAC, OGG, AAC
                    </div>
                    <div className="text-xs text-gray-400 mt-1">
                      Maximum file size: 50MB
                    </div>
                  </div>
                )}
              </label>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Song Title (optional)
              </label>
              <input
                type="text"
                placeholder="Enter song title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full px-4 py-3 border-2 border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-300 text-sm bg-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Artist (optional)
              </label>
              <input
                type="text"
                placeholder="Enter artist name"
                value={artist}
                onChange={(e) => setArtist(e.target.value)}
                className="w-full px-4 py-3 border-2 border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-300 text-sm bg-white"
              />
            </div>
          </div>

          <button
            onClick={handleFileUpload}
            disabled={!file || uploading}
            className="w-full py-3 px-6 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md font-medium text-sm flex items-center justify-center gap-2"
          >
            {uploading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                Uploading...
              </>
            ) : (
              <>
                <span>🎼</span>
                Upload & Transcribe
              </>
            )}
          </button>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-600 flex items-center gap-2">
            <span>⚠️</span>
            {error}
          </p>
        </div>
      )}

      {/* Info Box */}
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h4 className="text-sm font-semibold text-gray-900 mb-2">What you'll get:</h4>
        <ul className="text-sm text-gray-700 space-y-1">
          <li className="flex items-center gap-2">
            <span className="text-green-600">✓</span>
            Complete lyrics transcription
          </li>
          <li className="flex items-center gap-2">
            <span className="text-green-600">✓</span>
            Chord progression with timestamps
          </li>
          <li className="flex items-center gap-2">
            <span className="text-green-600">✓</span>
            Interactive sheet music with playback
          </li>
          <li className="flex items-center gap-2">
            <span className="text-green-600">✓</span>
            Downloadable ABC notation and MIDI files
          </li>
        </ul>
        <p className="text-xs text-gray-500 mt-3">
          ⏱️ Processing time: 2-5 minutes • 🎯 Accuracy: 85%+
        </p>
      </div>
    </div>
  );
}

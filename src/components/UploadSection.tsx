import { useState } from 'react';
import { uploadData } from 'aws-amplify/storage';
import { generateClient } from 'aws-amplify/data';
import type { Schema } from '../../amplify/data/resource';

const client = generateClient<Schema>();

export default function UploadSection() {
  const [file, setFile] = useState<File | null>(null);
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'file' | 'youtube'>('file');

  const handleFileUpload = async () => {
    if (!file) return;
    
    setLoading(true);
    try {
      // Upload file to S3
      const result = await uploadData({
        path: `audio-files/${Date.now()}-${file.name}`,
        data: file
      }).result;

      // Create transcription job
      await client.models.TranscriptionJob.create({
        status: 'pending',
        audioUrl: result.path,
        title: file.name,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      });

      setFile(null);
      alert('File uploaded successfully! Processing will begin shortly.');
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('Upload failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleYouTubeSubmit = async () => {
    if (!youtubeUrl) return;
    
    setLoading(true);
    try {
      await client.models.TranscriptionJob.create({
        status: 'pending',
        youtubeUrl,
        title: 'YouTube Video',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      });

      setYoutubeUrl('');
      alert('YouTube link submitted! Processing will begin shortly.');
    } catch (error) {
      console.error('Error creating YouTube job:', error);
      alert('Submission failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 border border-blue-200">
      <h2 className="text-xl font-semibold text-[#3f3f3f] mb-4">Upload Audio</h2>

      {/* Tabs */}
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setActiveTab('file')}
          className={`flex-1 py-2 px-4 rounded-lg font-medium transition-all ${
            activeTab === 'file'
              ? 'bg-[#00bfc4] text-white shadow-md'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          📁 Upload File
        </button>
        <button
          onClick={() => setActiveTab('youtube')}
          className={`flex-1 py-2 px-4 rounded-lg font-medium transition-all ${
            activeTab === 'youtube'
              ? 'bg-[#00bfc4] text-white shadow-md'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          🎬 YouTube Link
        </button>
      </div>

      {/* File Upload Tab */}
      {activeTab === 'file' && (
        <div className="space-y-4">
          <div
            className={`border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer ${
              file
                ? 'border-[#00bfc4] bg-[#00bfc4]/5'
                : 'border-gray-300 hover:border-[#00bfc4] hover:bg-gray-50'
            }`}
            onDragOver={(e) => {
              e.preventDefault();
              e.currentTarget.classList.add('border-[#00bfc4]', 'bg-[#00bfc4]/5');
            }}
            onDragLeave={(e) => {
              e.preventDefault();
              if (!file) {
                e.currentTarget.classList.remove('border-[#00bfc4]', 'bg-[#00bfc4]/5');
              }
            }}
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
                  <div className="text-4xl mb-2">🎵</div>
                  <div className="font-semibold text-[#00bfc4] mb-1">{file.name}</div>
                  <div className="text-sm text-gray-500">
                    {(file.size / 1024 / 1024).toFixed(1)} MB
                  </div>
                </div>
              ) : (
                <div>
                  <div className="text-4xl mb-2">📤</div>
                  <div className="font-semibold text-gray-700 mb-1">
                    Drop audio file here or click to browse
                  </div>
                  <div className="text-sm text-gray-500">
                    Supports MP3, WAV, M4A, FLAC, OGG (max 50MB)
                  </div>
                </div>
              )}
            </label>
          </div>

          <button
            onClick={handleFileUpload}
            disabled={!file || loading}
            className="w-full py-3 px-6 bg-gradient-to-r from-[#00bfc4] to-[#0089c6] text-white font-semibold rounded-lg hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? '🎵 Processing...' : '🚀 Upload & Transcribe'}
          </button>
        </div>
      )}

      {/* YouTube Tab */}
      {activeTab === 'youtube' && (
        <div className="space-y-4">
          <div>
            <input
              type="url"
              placeholder="https://www.youtube.com/watch?v=..."
              value={youtubeUrl}
              onChange={(e) => setYoutubeUrl(e.target.value)}
              className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-[#00bfc4] focus:outline-none transition-colors"
            />
            <p className="text-xs text-gray-500 mt-2">
              Paste a YouTube music video URL to transcribe
            </p>
          </div>

          <button
            onClick={handleYouTubeSubmit}
            disabled={!youtubeUrl || loading}
            className="w-full py-3 px-6 bg-gradient-to-r from-[#0089c6] to-[#00bfc4] text-white font-semibold rounded-lg hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Processing...' : '🎬 Transcribe YouTube Video'}
          </button>
        </div>
      )}
    </div>
  );
}

import { useState, useEffect } from 'react';
import { Amplify } from 'aws-amplify';
import { generateClient } from 'aws-amplify/data';
import { uploadData } from 'aws-amplify/storage';
import type { Schema } from '../amplify/data/resource';
import outputs from '../amplify_outputs.json';
import DashboardHeader from './components/DashboardHeader';
import { 
  AcademicCapIcon, 
  FireIcon, 
  MusicalNoteIcon
} from '@heroicons/react/24/outline';

Amplify.configure(outputs);

const client = generateClient<Schema>();

// Daily rotating questions for music community
const DAILY_QUESTIONS = [
  "Share a funny moment from your day!",
  "What song are you learning right now?",
  "Drop your best practice tip!",
  "What's your favorite chord progression?",
  "Share a music goal for this week!",
  "What instrument do you want to learn next?",
  "Tell us about your musical inspiration!",
  "What's the hardest song you've mastered?",
  "Share your practice routine!",
  "What's your go-to warm-up exercise?"
];

const getDailyQuestion = (): string => {
  const today = new Date();
  const dayOfYear = Math.floor((today.getTime() - new Date(today.getFullYear(), 0, 0).getTime()) / (1000 * 60 * 60 * 24));
  const questionIndex = dayOfYear % DAILY_QUESTIONS.length;
  return DAILY_QUESTIONS[questionIndex];
};

function App() {
  const [userName] = useState('Danny');
  const [jobs, setJobs] = useState<Array<Schema["TranscriptionJob"]["type"]>>([]);
  const [loading, setLoading] = useState(true);
  const [file, setFile] = useState<File | null>(null);
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [uploading, setUploading] = useState(false);
  const [activeTab, setActiveTab] = useState<'file' | 'youtube'>('file');
  const [includeAllPublic, setIncludeAllPublic] = useState(false);
  const [showUploadSection, setShowUploadSection] = useState(false);
  const [dailyQuestion] = useState(getDailyQuestion());

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchJobs = async () => {
    try {
      const { data } = await client.models.TranscriptionJob.list();
      setJobs(data.sort((a: any, b: any) => 
        new Date(b.createdAt || 0).getTime() - new Date(a.createdAt || 0).getTime()
      ));
    } catch (error) {
      console.error('Error fetching jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async () => {
    if (!file) return;
    setUploading(true);
    try {
      const result = await uploadData({
        path: `audio-files/${Date.now()}-${file.name}`,
        data: file
      }).result;

      await client.models.TranscriptionJob.create({
        status: 'pending',
        audioUrl: result.path,
        title: file.name,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      });

      setFile(null);
      setShowUploadSection(false);
      fetchJobs();
    } catch (error) {
      console.error('Error uploading file:', error);
    } finally {
      setUploading(false);
    }
  };

  const handleYouTubeSubmit = async () => {
    if (!youtubeUrl) return;
    setUploading(true);
    try {
      await client.models.TranscriptionJob.create({
        status: 'pending',
        youtubeUrl,
        title: 'YouTube Video',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      });

      setYoutubeUrl('');
      setShowUploadSection(false);
      fetchJobs();
    } catch (error) {
      console.error('Error creating YouTube job:', error);
    } finally {
      setUploading(false);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const now = new Date();
    const date = new Date(timestamp);
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="min-h-screen bg-background">
      <DashboardHeader userName={userName} />

      <div className="max-w-[1600px] mx-auto px-4 py-6">
        <div className="pb-8">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            
            {/* LEFT COLUMN - Main Content (75% width) */}
            <div className="lg:col-span-3 flex flex-col">
              
              {/* Top Action Bar */}
              <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl shadow-lg border border-blue-200 p-4 mb-6">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold">
                    🎵
                  </div>
                  <button 
                    onClick={() => setShowUploadSection(!showUploadSection)}
                    className="flex-1 px-4 py-3 bg-gradient-to-r from-white to-blue-50 rounded-full text-left text-sm border-2 border-blue-200 hover:from-blue-50 hover:to-purple-50 transition-all"
                  >
                    ✨ {dailyQuestion}
                  </button>
                  <label className="flex items-center space-x-2 text-sm bg-white px-3 py-2 rounded-full border border-blue-200 hover:bg-blue-50 transition-colors cursor-pointer">
                    <input 
                      type="checkbox" 
                      className="w-4 h-4"
                      checked={includeAllPublic}
                      onChange={(e: any) => setIncludeAllPublic(e.target.checked)}
                    />
                    <span className="flex items-center font-medium text-blue-700">
                      <FireIcon className="w-4 h-4 mr-1 text-orange-500" />
                      Explore
                    </span>
                  </label>
                </div>

                {/* Expanded Upload Section */}
                {showUploadSection && (
                  <div className="mt-6 pt-6 border-t border-blue-200">
                    <div className="flex gap-2 mb-6">
                      <button
                        onClick={() => setActiveTab('file')}
                        className={`flex-1 py-2 px-4 rounded-full font-medium transition-all text-sm ${
                          activeTab === 'file'
                            ? 'bg-gradient-to-r from-white to-blue-50 shadow-md text-gray-900'
                            : 'bg-white/50 text-gray-600 hover:bg-white/70'
                        }`}
                      >
                        📁 Upload File
                      </button>
                      <button
                        onClick={() => setActiveTab('youtube')}
                        className={`flex-1 py-2 px-4 rounded-full font-medium transition-all text-sm ${
                          activeTab === 'youtube'
                            ? 'bg-gradient-to-r from-white to-blue-50 shadow-md text-gray-900'
                            : 'bg-white/50 text-gray-600 hover:bg-white/70'
                        }`}
                      >
                        🎬 YouTube Link
                      </button>
                    </div>

                    {activeTab === 'file' && (
                      <div className="space-y-4">
                        <div
                          className={`border-2 border-dashed rounded-xl p-6 text-center transition-all cursor-pointer ${
                            file
                              ? 'border-secondary bg-white/80'
                              : 'border-gray-300 bg-white/50 hover:border-secondary hover:bg-white/70'
                          }`}
                          onDragOver={(e: any) => e.preventDefault()}
                          onDrop={(e: any) => {
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
                            onChange={(e: any) => setFile(e.target.files?.[0] || null)}
                            className="hidden"
                            id="file-upload"
                          />
                          <label htmlFor="file-upload" className="cursor-pointer block">
                            {file ? (
                              <div>
                                <div className="text-3xl mb-2">🎵</div>
                                <div className="font-semibold text-secondary text-sm">{file.name}</div>
                                <div className="text-xs text-gray-500 mt-1">
                                  {(file.size / 1024 / 1024).toFixed(1)} MB
                                </div>
                              </div>
                            ) : (
                              <div>
                                <div className="text-3xl mb-2">📤</div>
                                <div className="font-semibold text-gray-700 text-sm">
                                  Drop audio file or click to browse
                                </div>
                                <div className="text-xs text-gray-500 mt-1">
                                  MP3, WAV, M4A, FLAC, OGG (max 50MB)
                                </div>
                              </div>
                            )}
                          </label>
                        </div>
                        <button
                          onClick={handleFileUpload}
                          disabled={!file || uploading}
                          className="w-full py-2 px-4 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-full hover:from-blue-600 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md font-medium text-sm"
                        >
                          {uploading ? '🎵 Processing...' : 'Upload & Transcribe ✨'}
                        </button>
                      </div>
                    )}

                    {activeTab === 'youtube' && (
                      <div className="space-y-4">
                        <input
                          type="url"
                          placeholder="https://www.youtube.com/watch?v=..."
                          value={youtubeUrl}
                          onChange={(e: any) => setYoutubeUrl(e.target.value)}
                          className="w-full px-4 py-3 border-2 border-blue-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-300 text-sm bg-white shadow-sm"
                        />
                        <button
                          onClick={handleYouTubeSubmit}
                          disabled={!youtubeUrl || uploading}
                          className="w-full py-2 px-4 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-full hover:from-blue-600 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md font-medium text-sm"
                        >
                          {uploading ? 'Processing...' : 'Transcribe YouTube ✨'}
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Explore Mode Banner */}
              {includeAllPublic && (
                <div className="bg-gradient-to-r from-orange-400 via-red-500 to-pink-500 rounded-xl p-4 flex items-center justify-between shadow-lg mb-6">
                  <div className="flex items-center space-x-3 text-white">
                    <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                      <FireIcon className="w-6 h-6" />
                    </div>
                    <div>
                      <p className="font-bold text-lg">🔥 Explore Mode Active</p>
                      <p className="text-sm opacity-90">Discovering amazing music from everyone</p>
                    </div>
                  </div>
                  <button
                    onClick={() => setIncludeAllPublic(false)}
                    className="text-white hover:bg-white/20 rounded-full p-2 transition-colors"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              )}

              {/* Main Content Container */}
              <div className="bg-gradient-to-br from-white to-blue-50/30 rounded-xl shadow-lg border border-blue-200">
                <div className="p-6 border-b border-blue-200 bg-gradient-to-r from-blue-50 to-purple-50">
                  <h3 className="text-lg font-bold text-gray-900 flex items-center">
                    <span className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white mr-3">
                      🎼
                    </span>
                    Your Transcriptions
                  </h3>
                  <p className="text-sm text-gray-600 ml-11">Track your music transcription progress</p>
                </div>

                <div className="max-h-[600px] overflow-y-auto">
                  {loading ? (
                    <div className="p-8 text-center">
                      <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-secondary"></div>
                      <p className="text-gray-500 mt-4 text-sm">Loading transcriptions...</p>
                    </div>
                  ) : jobs.length === 0 ? (
                    <div className="p-8 text-center">
                      <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <MusicalNoteIcon className="w-8 h-8 text-gray-400" />
                      </div>
                      <h3 className="text-base font-semibold text-gray-900 mb-2">No Transcriptions Yet</h3>
                      <p className="text-sm text-gray-600">Upload an audio file or YouTube link to get started.</p>
                    </div>
                  ) : (
                    jobs.map((job: any, index: number) => (
                      <TranscriptionItem
                        key={job.id}
                        job={job}
                        formatTimestamp={formatTimestamp}
                        isLast={index === jobs.length - 1}
                      />
                    ))
                  )}
                </div>
              </div>
            </div>

            {/* RIGHT COLUMN - Sidebar (25% width) */}
            <div className="space-y-4">
              
              {/* Widget 1 - Ripped Songs */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-base font-bold text-gray-900">🎵 Ripped Songs</h3>
                  <button className="text-xs text-blue-600 hover:text-blue-700 font-medium">View All</button>
                </div>
                <div className="space-y-3">
                  {[
                    { name: 'Hotel California', key: 'Bm', hasLyrics: true, hasPiano: true, hasGuitar: true, date: '2 days ago' },
                    { name: 'Wonderwall', key: 'Em', hasLyrics: true, hasGuitar: true, date: '3 days ago' },
                    { name: 'Let It Be', key: 'C', hasLyrics: true, hasPiano: true, hasGuitar: true, date: '5 days ago' },
                  ].map((song, idx) => (
                    <div key={idx} className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h4 className="font-medium text-sm text-gray-900">{song.name}</h4>
                          <p className="text-xs text-gray-500">{song.date}</p>
                        </div>
                        <span className="px-2 py-1 bg-secondary text-white text-xs rounded-full font-medium">{song.key}</span>
                      </div>
                      <div className="flex gap-1 flex-wrap">
                        {song.hasLyrics && <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded">📝 Lyrics</span>}
                        {song.hasPiano && <span className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded">🎹 Piano</span>}
                        {song.hasGuitar && <span className="px-2 py-0.5 bg-orange-100 text-orange-700 text-xs rounded">🎸 Guitar</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Widget 2 - Backing Tracks */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-base font-bold text-gray-900">🎼 Backing Tracks</h3>
                  <button className="text-xs text-blue-600 hover:text-blue-700 font-medium">View All</button>
                </div>
                <div className="space-y-3">
                  {[
                    { name: 'Blues in A', genre: 'Blues', key: 'A', instruments: ['Drums', 'Bass'], color: 'bg-blue-500' },
                    { name: 'Jazz Swing', genre: 'Jazz', key: 'Bb', instruments: ['Drums', 'Piano'], color: 'bg-purple-500' },
                    { name: 'Rock Ballad', genre: 'Rock', key: 'G', instruments: ['Drums', 'Bass'], color: 'bg-red-500' },
                  ].map((track, idx) => (
                    <div key={idx} className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <div className={`w-2 h-2 rounded-full ${track.color}`}></div>
                            <h4 className="font-medium text-sm text-gray-900">{track.name}</h4>
                          </div>
                          <p className="text-xs text-gray-500">{track.genre}</p>
                        </div>
                        <span className="px-2 py-1 bg-secondary text-white text-xs rounded-full font-medium">{track.key}</span>
                      </div>
                      <div className="flex gap-1 flex-wrap">
                        {track.instruments.map((inst, i) => (
                          <span key={i} className="px-2 py-0.5 bg-gray-200 text-gray-700 text-xs rounded">{inst}</span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Widget 3 - Study Modules */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
                <h3 className="text-base font-bold text-gray-900 mb-4">Study Modules</h3>
                <div className="text-center py-6">
                  <AcademicCapIcon className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                  <p className="text-sm text-gray-500">Coming Soon</p>
                </div>
              </div>

            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Transcription Item Component
const TranscriptionItem: React.FC<{
  job: any;
  formatTimestamp: (timestamp: string) => string;
  isLast: boolean;
}> = ({ job, formatTimestamp, isLast }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-700 border-green-200';
      case 'processing': return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'failed': return 'bg-red-100 text-red-700 border-red-200';
      default: return 'bg-yellow-100 text-yellow-700 border-yellow-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return '✅';
      case 'processing': return '⚙️';
      case 'failed': return '❌';
      default: return '⏳';
    }
  };

  return (
    <div className={`${!isLast ? 'border-b border-gray-100' : ''} p-6 hover:bg-gray-50/50 transition-colors`}>
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="font-semibold text-sm text-gray-900 mb-1">{job.title}</h3>
          <p className="text-xs text-gray-500">{formatTimestamp(job.createdAt || '')}</p>
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getStatusColor(job.status || 'pending')}`}>
          {getStatusIcon(job.status || 'pending')} {job.status?.toUpperCase()}
        </span>
      </div>

      {job.status === 'completed' && (job.lyrics || job.chords) && (
        <div className="space-y-3 mt-4">
          {job.lyrics && (
            <div className="p-4 bg-white rounded-lg border border-blue-100">
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
            <div className="p-4 bg-white rounded-lg border border-purple-100">
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

      {job.status === 'processing' && (
        <div className="flex items-center gap-2 text-sm text-blue-600 bg-blue-50 p-4 rounded-lg mt-4">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
          <span>Processing your audio...</span>
        </div>
      )}

      {job.status === 'failed' && (
        <div className="p-4 bg-red-50 rounded-lg border border-red-200 mt-4">
          <p className="text-xs text-red-600">⚠️ Transcription failed. Please try again.</p>
        </div>
      )}
    </div>
  );
};

export default App;

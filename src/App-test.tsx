import { useState, useEffect } from 'react';
import { Amplify } from 'aws-amplify';
import { generateClient } from 'aws-amplify/data';
import type { Schema } from '../amplify/data/resource';
import outputs from '../amplify_outputs.json';
import SheetMusicModal from './components/SheetMusicModal';
import UploadInterface from './components/UploadInterface';
import TranscriptionProgress from './components/TranscriptionProgress';

// Configure Amplify
Amplify.configure(outputs);

const client = generateClient<Schema>();

// Mock chord data for testing
const mockChordData = {
  key: 'C',
  mode: 'major',
  chords: [
    { name: 'C', timestamp: 0, duration: 4, confidence: 0.92 },
    { name: 'Am', timestamp: 4, duration: 4, confidence: 0.88 },
    { name: 'F', timestamp: 8, duration: 4, confidence: 0.91 },
    { name: 'G', timestamp: 12, duration: 4, confidence: 0.94 },
    { name: 'C', timestamp: 16, duration: 4, confidence: 0.90 },
    { name: 'Em', timestamp: 20, duration: 4, confidence: 0.85 },
    { name: 'Am', timestamp: 24, duration: 4, confidence: 0.89 },
    { name: 'G', timestamp: 28, duration: 4, confidence: 0.93 },
  ],
  chordProgressionText: 'Key: C major\n\nC - Am - F - G\nC - Em - Am - G'
};

function App() {
  const [showSheetMusic, setShowSheetMusic] = useState(false);
  const [selectedSong, setSelectedSong] = useState<any>(null);
  const [activeJobs, setActiveJobs] = useState<string[]>([]);
  const [completedJobs, setCompletedJobs] = useState<any[]>([]);
  const [showUpload, setShowUpload] = useState(true);

  // Load completed transcriptions on mount
  useEffect(() => {
    loadCompletedTranscriptions();
  }, []);

  const loadCompletedTranscriptions = async () => {
    try {
      const { data } = await client.models.TranscriptionJob.list({
        filter: { status: { eq: 'completed' } }
      });
      if (data) {
        setCompletedJobs(data);
      }
    } catch (error) {
      console.error('Error loading transcriptions:', error);
    }
  };

  const handleUploadStart = (jobId: string) => {
    setActiveJobs(prev => [...prev, jobId]);
    setShowUpload(false);
  };

  const handleJobComplete = (job: any) => {
    setActiveJobs(prev => prev.filter(id => id !== job.id));
    setCompletedJobs(prev => [job, ...prev]);
  };

  const handleViewSheetMusic = (song: any) => {
    setSelectedSong(song);
    setShowSheetMusic(true);
  };

  return (
    <>
      <div className="min-h-screen bg-background flex">
      
      {/* LEFT SIDEBAR - Full Height Navigation */}
      <aside className="w-64 bg-primary text-white flex-shrink-0 flex flex-col">
        {/* Logo Section */}
        <div className="p-6 border-b border-gray-700">
          <img 
            src="/Chord Scout Logo 2.png" 
            alt="ChordScout Logo" 
            className="w-full h-auto"
          />
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          <div className="mb-6">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2 px-3">Main</h3>
            <a href="#" className="flex items-center space-x-3 px-3 py-2.5 rounded-lg bg-secondary text-white font-medium text-sm">
              <span className="text-lg">🏠</span>
              <span>Dashboard</span>
            </a>
            <a href="#" className="flex items-center space-x-3 px-3 py-2.5 rounded-lg hover:bg-gray-700 text-gray-300 hover:text-white text-sm transition-colors">
              <span className="text-lg">🎵</span>
              <span>My Songs</span>
            </a>
            <a href="#" className="flex items-center space-x-3 px-3 py-2.5 rounded-lg hover:bg-gray-700 text-gray-300 hover:text-white text-sm transition-colors">
              <span className="text-lg">🎼</span>
              <span>Transcriptions</span>
            </a>
          </div>

          <div className="mb-6">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2 px-3">Practice</h3>
            <a href="#" className="flex items-center space-x-3 px-3 py-2.5 rounded-lg hover:bg-gray-700 text-gray-300 hover:text-white text-sm transition-colors">
              <span className="text-lg">🎸</span>
              <span>Practice Mode</span>
            </a>
            <a href="#" className="flex items-center space-x-3 px-3 py-2.5 rounded-lg hover:bg-gray-700 text-gray-300 hover:text-white text-sm transition-colors">
              <span className="text-lg">🎹</span>
              <span>Backing Tracks</span>
            </a>
            <a href="#" className="flex items-center space-x-3 px-3 py-2.5 rounded-lg hover:bg-gray-700 text-gray-300 hover:text-white text-sm transition-colors">
              <span className="text-lg">📚</span>
              <span>Library</span>
            </a>
          </div>

          <div>
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2 px-3">Account</h3>
            <a href="#" className="flex items-center space-x-3 px-3 py-2.5 rounded-lg hover:bg-gray-700 text-gray-300 hover:text-white text-sm transition-colors">
              <span className="text-lg">⚙️</span>
              <span>Settings</span>
            </a>
            <a href="#" className="flex items-center space-x-3 px-3 py-2.5 rounded-lg hover:bg-gray-700 text-gray-300 hover:text-white text-sm transition-colors">
              <span className="text-lg">❓</span>
              <span>Help & Support</span>
            </a>
          </div>
        </nav>
      </aside>

      {/* MAIN CONTENT AREA */}
      <div className="flex-1 flex flex-col min-h-screen">
        {/* Top Header Bar */}
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Good evening, Danny! 👋</h1>
              <p className="text-sm text-gray-600">Ready to continue your learning journey?</p>
            </div>
            <div className="flex items-center space-x-4">
              <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                <span className="text-xl">🔔</span>
              </button>
              <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                <span className="text-xl">💬</span>
              </button>
              {/* User Profile */}
              <div className="flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors">
                <img
                  src="https://api.dicebear.com/7.x/avataaars/svg?seed=Danny"
                  alt="User avatar"
                  className="w-10 h-10 rounded-full ring-2 ring-secondary"
                />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">Danny Wilson</p>
                  <p className="text-xs text-gray-600 truncate">danny@example.com</p>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-[1600px] mx-auto px-6 py-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              
              {/* MIDDLE COLUMN - Main Content (2/3 width) */}
              <div className="lg:col-span-2 flex flex-col space-y-6">
                
                {/* Upload Interface */}
                {showUpload ? (
                  <UploadInterface onUploadStart={handleUploadStart} />
                ) : (
                  <button
                    onClick={() => setShowUpload(true)}
                    className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl shadow-lg border border-blue-200 p-4 hover:from-blue-100 hover:to-purple-100 transition-all"
                  >
                    <div className="flex items-center justify-center space-x-3">
                      <span className="text-2xl">➕</span>
                      <span className="font-semibold text-gray-900">Upload New Song</span>
                    </div>
                  </button>
                )}

                {/* Active Jobs Progress */}
                {activeJobs.length > 0 && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-bold text-gray-900 flex items-center">
                      <span className="text-2xl mr-2">⚙️</span>
                      Processing ({activeJobs.length})
                    </h3>
                    {activeJobs.map(jobId => (
                      <TranscriptionProgress
                        key={jobId}
                        jobId={jobId}
                        onComplete={handleJobComplete}
                      />
                    ))}
                  </div>
                )}

                {/* Completed Transcriptions */}
                <div className="bg-gradient-to-br from-white to-blue-50/30 rounded-xl shadow-lg border border-blue-200">
                  <div className="p-6 border-b border-blue-200 bg-gradient-to-r from-blue-50 to-purple-50">
                    <h3 className="text-lg font-bold text-gray-900 flex items-center">
                      <span className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white mr-3">
                        🎼
                      </span>
                      Your Transcriptions
                    </h3>
                    <p className="text-sm text-gray-600 ml-11">
                      {completedJobs.length > 0 
                        ? `${completedJobs.length} song${completedJobs.length > 1 ? 's' : ''} transcribed`
                        : 'Track your music transcription progress'
                      }
                    </p>
                  </div>

                  <div className="max-h-[600px] overflow-y-auto">
                    {completedJobs.length === 0 ? (
                      <div className="p-8 text-center">
                        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                          🎵
                        </div>
                        <h3 className="text-base font-semibold text-gray-900 mb-2">No Transcriptions Yet</h3>
                        <p className="text-sm text-gray-600 mb-4">Upload an audio file or YouTube link to get started.</p>
                        
                        {/* Demo Button */}
                        <button
                          onClick={() => handleViewSheetMusic({
                            title: 'Demo Song - I-V-vi-IV Progression',
                            artist: 'ChordScout Demo',
                            chordData: mockChordData
                          })}
                          className="px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:shadow-md transition-all text-sm font-medium"
                        >
                          🎼 View Demo Sheet Music
                        </button>
                      </div>
                    ) : (
                      <div className="p-4 space-y-3">
                        {completedJobs.map((job) => (
                          <div
                            key={job.id}
                            className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-all cursor-pointer"
                            onClick={() => handleViewSheetMusic({
                              title: job.title,
                              artist: job.artist,
                              chordData: job.chords
                            })}
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <h4 className="font-semibold text-gray-900">{job.title}</h4>
                                <p className="text-sm text-gray-600">{job.artist}</p>
                                <div className="flex items-center gap-2 mt-2">
                                  <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full font-medium">
                                    ✓ Completed
                                  </span>
                                  {job.chords?.key && (
                                    <span className="px-2 py-1 bg-secondary text-white text-xs rounded-full font-medium">
                                      Key: {job.chords.key}
                                    </span>
                                  )}
                                </div>
                              </div>
                              <button className="px-3 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:shadow-md transition-all text-sm font-medium">
                                View 🎼
                              </button>
                            </div>
                            <div className="mt-3 pt-3 border-t border-gray-200 text-xs text-gray-500">
                              {new Date(job.createdAt).toLocaleDateString()} • {new Date(job.createdAt).toLocaleTimeString()}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* RIGHT SIDEBAR - Widgets (1/3 width) */}
              <div className="space-y-4">
                
                {/* Widget 1 - Ripped Songs */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-base font-bold text-gray-900">🎵 Ripped Songs</h3>
                    <button className="text-xs text-blue-600 hover:text-blue-700 font-medium">View All</button>
                  </div>
                  <div className="space-y-3">
                    {[
                      { name: 'Hotel California', artist: 'Eagles', key: 'Bm', date: '2 days ago', image: 'https://picsum.photos/seed/hotel/80/80' },
                      { name: 'Wonderwall', artist: 'Oasis', key: 'Em', date: '3 days ago', image: 'https://picsum.photos/seed/wonder/80/80' },
                      { name: 'Let It Be', artist: 'The Beatles', key: 'C', date: '5 days ago', image: 'https://picsum.photos/seed/letit/80/80' },
                    ].map((song, idx) => (
                      <div key={idx} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer">
                        <img 
                          src={song.image} 
                          alt={song.name}
                          className="w-16 h-16 rounded-lg object-cover flex-shrink-0 shadow-sm"
                        />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between mb-1">
                            <div className="flex-1 min-w-0">
                              <h4 className="font-semibold text-sm text-gray-900 truncate">{song.name}</h4>
                              <p className="text-xs text-gray-500 truncate">{song.artist}</p>
                            </div>
                            <span className="ml-2 px-2 py-0.5 bg-secondary text-white text-xs rounded-full font-medium flex-shrink-0">{song.key}</span>
                          </div>
                          <div className="flex gap-1 flex-wrap mt-2">
                            <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded">📝</span>
                            <span className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded">🎹</span>
                            <span className="px-2 py-0.5 bg-orange-100 text-orange-700 text-xs rounded">🎸</span>
                          </div>
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
                      { name: 'Blues in A', genre: 'Blues', key: 'A', color: 'bg-blue-500', image: 'https://picsum.photos/seed/blues/80/80' },
                      { name: 'Jazz Swing', genre: 'Jazz', key: 'Bb', color: 'bg-purple-500', image: 'https://picsum.photos/seed/jazz/80/80' },
                      { name: 'Rock Ballad', genre: 'Rock', key: 'G', color: 'bg-red-500', image: 'https://picsum.photos/seed/rock/80/80' },
                    ].map((track, idx) => (
                      <div key={idx} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer">
                        <div className="relative flex-shrink-0">
                          <img 
                            src={track.image} 
                            alt={track.name}
                            className="w-16 h-16 rounded-lg object-cover shadow-sm"
                          />
                          <div className={`absolute -top-1 -right-1 w-4 h-4 rounded-full ${track.color} border-2 border-white`}></div>
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between mb-1">
                            <div className="flex-1 min-w-0">
                              <h4 className="font-semibold text-sm text-gray-900 truncate">{track.name}</h4>
                              <p className="text-xs text-gray-500 truncate">{track.genre}</p>
                            </div>
                            <span className="ml-2 px-2 py-0.5 bg-secondary text-white text-xs rounded-full font-medium flex-shrink-0">{track.key}</span>
                          </div>
                          <div className="flex gap-1 flex-wrap mt-2">
                            <span className="px-2 py-0.5 bg-gray-200 text-gray-700 text-xs rounded">🥁 Drums</span>
                            <span className="px-2 py-0.5 bg-gray-200 text-gray-700 text-xs rounded">🎸 Bass</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Widget 3 - Study Modules */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
                  <h3 className="text-base font-bold text-gray-900 mb-4">📚 Study Modules</h3>
                  <div className="text-center py-6">
                    <div className="text-4xl mb-2">🎓</div>
                    <p className="text-sm text-gray-500 font-medium">Coming Soon</p>
                    <p className="text-xs text-gray-400 mt-1">Interactive lessons & tutorials</p>
                  </div>
                </div>

              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    {/* Sheet Music Modal */}
    {showSheetMusic && selectedSong && (
      <SheetMusicModal
        isOpen={showSheetMusic}
        onClose={() => setShowSheetMusic(false)}
        chordData={selectedSong.chordData}
        title={selectedSong.title}
        artist={selectedSong.artist}
      />
    )}
    </>
  );
}

export default App;

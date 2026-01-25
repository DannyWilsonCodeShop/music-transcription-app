import { useState } from 'react';
import { Amplify } from 'aws-amplify';
import outputs from '../amplify_outputs.json';
import DashboardHeader from './components/DashboardHeader';
import UploadInterface from './components/UploadInterface';
import TranscriptionProgress from './components/TranscriptionProgress';
import { TranscriptionJob } from './services/transcriptionService';

Amplify.configure(outputs);

function App() {
  const [userName] = useState('Danny');
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [completedJobs, setCompletedJobs] = useState<TranscriptionJob[]>([]);

  const handleUploadStart = (jobId: string) => {
    setActiveJobId(jobId);
  };

  const handleJobComplete = (job: TranscriptionJob) => {
    setCompletedJobs(prev => [job, ...prev]);
    setActiveJobId(null);
  };

  return (
    <div className="min-h-screen bg-background">
      <DashboardHeader userName={userName} />

      <div className="max-w-[1600px] mx-auto px-4 py-6">
        <div className="pb-8">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            
            {/* LEFT COLUMN - Main Content (75% width) */}
            <div className="lg:col-span-3 flex flex-col space-y-6">
              
              {/* Upload Interface */}
              <UploadInterface onUploadStart={handleUploadStart} />

              {/* Active Job Progress */}
              {activeJobId && (
                <TranscriptionProgress 
                  jobId={activeJobId} 
                  onComplete={handleJobComplete}
                />
              )}

              {/* Completed Jobs */}
              {completedJobs.length > 0 && (
                <div className="space-y-4">
                  <h2 className="text-xl font-bold text-gray-900">Recent Transcriptions</h2>
                  {completedJobs.map(job => (
                    <div key={job.id} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                      <div className="flex items-start justify-between mb-4">
                        <div>
                          <h3 className="text-lg font-bold text-gray-900">{job.title}</h3>
                          <p className="text-sm text-gray-600">{new Date(job.createdAt).toLocaleString()}</p>
                        </div>
                        <span className="px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700 border border-green-200">
                          ✅ COMPLETED
                        </span>
                      </div>
                      
                      {job.lyrics && (
                        <div className="mb-4">
                          <h4 className="font-semibold text-gray-900 mb-2">Lyrics</h4>
                          <div className="bg-gray-50 rounded-lg p-4 max-h-40 overflow-y-auto">
                            <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans">{job.lyrics}</pre>
                          </div>
                        </div>
                      )}

                      {job.chords && (
                        <div className="mb-4">
                          <h4 className="font-semibold text-gray-900 mb-2">Chords</h4>
                          <div className="bg-gray-50 rounded-lg p-4">
                            <p className="text-sm text-gray-700 mb-2">
                              Key: <span className="font-medium">{job.chords.key} {job.chords.mode}</span>
                            </p>
                            <div className="flex flex-wrap gap-2">
                              {job.chords.chords?.map((chord: any, idx: number) => (
                                <span 
                                  key={idx}
                                  className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium"
                                >
                                  {chord.name}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>
                      )}

                      {job.sheetMusicUrl && (
                        <div>
                          <a 
                            href={job.sheetMusicUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                          >
                            <span>🎼</span>
                            View Sheet Music
                          </a>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* RIGHT COLUMN - Sidebar (25% width) */}
            <div className="space-y-4 h-[calc(100vh-200px)] overflow-y-auto">
              
              {/* Widget 1 - Ripped Songs */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-base font-bold text-gray-900">🎵 Ripped Songs</h3>
                  <button className="text-xs text-blue-600 hover:text-blue-700 font-medium">View All</button>
                </div>
                <div className="space-y-3 max-h-40 overflow-y-auto">
                  {[
                    { name: 'Hotel California', key: 'Bm', hasLyrics: true, hasPiano: true, hasGuitar: true, date: '2 days ago' },
                    { name: 'Wonderwall', key: 'Em', hasLyrics: true, hasGuitar: true, date: '3 days ago' },
                    { name: 'Let It Be', key: 'C', hasLyrics: true, hasPiano: true, hasGuitar: true, date: '5 days ago' },
                    { name: 'Stairway to Heaven', key: 'Am', hasLyrics: true, hasPiano: true, hasGuitar: true, date: '1 week ago' },
                    { name: 'Bohemian Rhapsody', key: 'Bb', hasLyrics: true, hasPiano: true, date: '1 week ago' },
                    { name: 'Sweet Child O Mine', key: 'D', hasLyrics: true, hasGuitar: true, date: '2 weeks ago' },
                  ].map((song, idx) => (
                    <div key={idx} className="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer">
                      <div className="flex items-start justify-between mb-2">
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
                <div className="space-y-3 max-h-40 overflow-y-auto">
                  {[
                    { name: 'Blues in A', genre: 'Blues', key: 'A', instruments: ['Drums', 'Bass'], color: 'bg-blue-500' },
                    { name: 'Jazz Swing', genre: 'Jazz', key: 'Bb', instruments: ['Drums', 'Piano'], color: 'bg-purple-500' },
                    { name: 'Rock Ballad', genre: 'Rock', key: 'G', instruments: ['Drums', 'Bass'], color: 'bg-red-500' },
                    { name: 'Funk Groove', genre: 'Funk', key: 'E', instruments: ['Drums', 'Bass', 'Keys'], color: 'bg-green-500' },
                    { name: 'Country Waltz', genre: 'Country', key: 'D', instruments: ['Drums', 'Bass'], color: 'bg-yellow-500' },
                    { name: 'Latin Bossa', genre: 'Latin', key: 'Fm', instruments: ['Drums', 'Guitar'], color: 'bg-pink-500' },
                  ].map((track, idx) => (
                    <div key={idx} className="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer">
                      <div className="flex items-start justify-between mb-2">
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
                <h3 className="text-base font-bold text-gray-900 mb-4">📚 Study Modules</h3>
                <div className="space-y-3 max-h-40 overflow-y-auto">
                  {[
                    { title: 'Chord Progressions', progress: 75, lessons: 12, completed: 9 },
                    { title: 'Scale Theory', progress: 45, lessons: 8, completed: 4 },
                    { title: 'Rhythm Patterns', progress: 90, lessons: 15, completed: 14 },
                    { title: 'Song Structure', progress: 30, lessons: 10, completed: 3 },
                    { title: 'Ear Training', progress: 60, lessons: 20, completed: 12 },
                  ].map((module, idx) => (
                    <div key={idx} className="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <h4 className="font-medium text-sm text-gray-900">{module.title}</h4>
                          <p className="text-xs text-gray-500">{module.completed}/{module.lessons} lessons</p>
                        </div>
                        <span className="text-xs font-medium text-blue-600">{module.progress}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-500 h-2 rounded-full transition-all" 
                          style={{ width: `${module.progress}%` }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;

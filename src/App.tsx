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
    <div className="min-h-screen bg-white">
      <DashboardHeader userName={userName} />

      <div className="max-w-[1600px] mx-auto px-4 py-4">
        <div className="pb-6">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            
            {/* LEFT COLUMN - Main Content (75% width) - Light grey background */}
            <div className="lg:col-span-3 flex flex-col space-y-6 bg-background rounded-xl p-6">
              
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
                  <h2 className="text-xl font-bold text-primary">Recent Transcriptions</h2>
                  {completedJobs.map(job => (
                    <div key={job.id} className="bg-white rounded-xl shadow-sm border border-neutral/20 p-6 relative overflow-hidden">
                      {/* Gradient accent */}
                      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-secondary to-tertiary"></div>
                      
                      <div className="flex items-start justify-between mb-4">
                        <div>
                          <h3 className="text-lg font-bold text-primary">{job.title}</h3>
                          <p className="text-sm text-neutral">{new Date(job.createdAt).toLocaleString()}</p>
                        </div>
                        <span className="px-3 py-1 rounded-full text-xs font-medium bg-gradient-to-r from-secondary/10 to-tertiary/10 text-secondary border border-secondary/30">
                          ✅ COMPLETED
                        </span>
                      </div>
                      
                      {job.lyrics && (
                        <div className="mb-4">
                          <h4 className="font-semibold text-primary mb-2">Lyrics</h4>
                          <div className="bg-background rounded-lg p-4 max-h-40 overflow-y-auto">
                            <pre className="text-sm text-neutral whitespace-pre-wrap font-sans">{job.lyrics}</pre>
                          </div>
                        </div>
                      )}

                      {job.chords && (
                        <div className="mb-4">
                          <h4 className="font-semibold text-primary mb-2">Chords</h4>
                          <div className="bg-background rounded-lg p-4">
                            <p className="text-sm text-neutral mb-2">
                              Key: <span className="font-medium">{job.chords.key} {job.chords.mode}</span>
                            </p>
                            <div className="flex flex-wrap gap-2">
                              {job.chords.chords?.map((chord: any, idx: number) => (
                                <span 
                                  key={idx}
                                  className="px-3 py-1 bg-gradient-to-r from-secondary/10 to-tertiary/10 text-secondary rounded-full text-sm font-medium"
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
                            className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-tertiary to-secondary text-white rounded-lg hover:from-secondary hover:to-tertiary transition-colors text-sm font-medium shadow-md"
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
              <div className="bg-white rounded-xl shadow-sm border border-neutral/20 p-4 relative overflow-hidden">
                <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-secondary to-tertiary"></div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-base font-bold text-primary">🎵 Ripped Songs</h3>
                  <button className="text-xs text-tertiary hover:text-secondary font-medium transition-colors">View All</button>
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
                    <div key={idx} className="p-3 bg-background rounded-lg hover:bg-neutral/10 transition-colors cursor-pointer">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <h4 className="font-medium text-sm text-primary">{song.name}</h4>
                          <p className="text-xs text-neutral">{song.date}</p>
                        </div>
                        <span className="px-2 py-1 bg-secondary text-white text-xs rounded-full font-medium">{song.key}</span>
                      </div>
                      <div className="flex gap-1 flex-wrap">
                        {song.hasLyrics && <span className="px-2 py-0.5 bg-tertiary/10 text-tertiary text-xs rounded">📝 Lyrics</span>}
                        {song.hasPiano && <span className="px-2 py-0.5 bg-accent/20 text-primary text-xs rounded">🎹 Piano</span>}
                        {song.hasGuitar && <span className="px-2 py-0.5 bg-secondary/10 text-secondary text-xs rounded">🎸 Guitar</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Widget 2 - Backing Tracks */}
              <div className="bg-white rounded-xl shadow-sm border border-neutral/20 p-4 relative overflow-hidden">
                <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-tertiary to-secondary"></div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-base font-bold text-primary">🎼 Backing Tracks</h3>
                  <button className="text-xs text-tertiary hover:text-secondary font-medium transition-colors">View All</button>
                </div>
                <div className="space-y-3 max-h-40 overflow-y-auto">
                  {[
                    { name: 'Blues in A', genre: 'Blues', key: 'A', instruments: ['Drums', 'Bass'], color: 'bg-tertiary' },
                    { name: 'Jazz Swing', genre: 'Jazz', key: 'Bb', instruments: ['Drums', 'Piano'], color: 'bg-purple-500' },
                    { name: 'Rock Ballad', genre: 'Rock', key: 'G', instruments: ['Drums', 'Bass'], color: 'bg-red-500' },
                    { name: 'Funk Groove', genre: 'Funk', key: 'E', instruments: ['Drums', 'Bass', 'Keys'], color: 'bg-green-500' },
                    { name: 'Country Waltz', genre: 'Country', key: 'D', instruments: ['Drums', 'Bass'], color: 'bg-yellow-500' },
                    { name: 'Latin Bossa', genre: 'Latin', key: 'Fm', instruments: ['Drums', 'Guitar'], color: 'bg-pink-500' },
                  ].map((track, idx) => (
                    <div key={idx} className="p-3 bg-background rounded-lg hover:bg-neutral/10 transition-colors cursor-pointer">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <div className={`w-2 h-2 rounded-full ${track.color}`}></div>
                            <h4 className="font-medium text-sm text-primary">{track.name}</h4>
                          </div>
                          <p className="text-xs text-neutral">{track.genre}</p>
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
              <div className="bg-white rounded-xl shadow-sm border border-neutral/20 p-4 relative overflow-hidden">
                <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-secondary via-tertiary to-secondary"></div>
                <h3 className="text-base font-bold text-primary mb-4">📚 Study Modules</h3>
                <div className="space-y-3 max-h-40 overflow-y-auto">
                  {[
                    { title: 'Chord Progressions', progress: 75, lessons: 12, completed: 9 },
                    { title: 'Scale Theory', progress: 45, lessons: 8, completed: 4 },
                    { title: 'Rhythm Patterns', progress: 90, lessons: 15, completed: 14 },
                    { title: 'Song Structure', progress: 30, lessons: 10, completed: 3 },
                    { title: 'Ear Training', progress: 60, lessons: 20, completed: 12 },
                  ].map((module, idx) => (
                    <div key={idx} className="p-3 bg-background rounded-lg hover:bg-neutral/10 transition-colors cursor-pointer">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <h4 className="font-medium text-sm text-primary">{module.title}</h4>
                          <p className="text-xs text-neutral">{module.completed}/{module.lessons} lessons</p>
                        </div>
                        <span className="text-xs font-medium text-tertiary">{module.progress}%</span>
                      </div>
                      <div className="w-full bg-background rounded-full h-2">
                        <div 
                          className="bg-gradient-to-r from-secondary to-tertiary h-2 rounded-full transition-all" 
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

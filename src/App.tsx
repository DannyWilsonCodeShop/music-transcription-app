import { useState } from 'react';
import { Amplify } from 'aws-amplify';
import outputs from '../amplify_outputs.json';
import DashboardHeader from './components/DashboardHeader';

Amplify.configure(outputs);

function App() {
  const [userName] = useState('Danny');

  return (
    <div className="min-h-screen bg-background">
      <DashboardHeader userName={userName} />

      <div className="max-w-[1600px] mx-auto px-4 py-6">
        <div className="pb-8">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            
            {/* LEFT COLUMN - Logo Section (75% width) */}
            <div className="lg:col-span-3 flex flex-col">
              
              {/* Logo Display */}
              <div className="bg-red-100 border-4 border-red-500 rounded-xl shadow-lg p-8 mb-6 text-center">
                <div className="bg-yellow-200 p-4 mb-4">
                  <p className="text-black font-bold">LOGO SHOULD BE HERE</p>
                </div>
                <img 
                  src="/Chord Scout Logo 1.png" 
                  alt="ChordScout Logo" 
                  className="h-48 w-auto mx-auto border-4 border-green-500"
                  onError={(e) => {
                    console.log('PNG logo failed to load, trying fallback');
                    console.error('Logo load error:', e);
                    e.currentTarget.src = '/chord-scout-logo.png';
                  }}
                  onLoad={(e) => {
                    console.log('Logo loaded successfully!');
                    const img = e.target as HTMLImageElement;
                    console.log('Logo dimensions:', img.naturalWidth, 'x', img.naturalHeight);
                  }}
                />
                <div className="bg-blue-200 p-2 mt-4">
                  <p className="text-black text-sm">Logo container end</p>
                </div>
              </div>
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

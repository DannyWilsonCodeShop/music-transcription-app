import { useState } from 'react';

const mockData = {
  title: "Wonderwall - Oasis",
  key: "G Major",
  tempo: "87 BPM",
  chords: ["Em7", "G", "D", "C", "Am", "C", "D", "G"],
  lyrics: [
    { time: "0:12", text: "Today is gonna be the day that they're gonna throw it back to you", chords: ["Em7", "G", "D", "C"] },
    { time: "0:19", text: "By now you should've somehow realized what you gotta do", chords: ["Am", "C", "D", "G"] },
    { time: "0:26", text: "I don't believe that anybody feels the way I do about you now", chords: ["Em7", "G", "D", "C", "Am", "C", "D"] }
  ],
  nashvilleNumbers: "6m - 1 - 5 - 4 - 2m - 4 - 5 - 1"
};

function App() {
  const [input, setInput] = useState('');
  const [inputType, setInputType] = useState<'url' | 'file'>('url');
  const [showResults, setShowResults] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      setShowResults(true);
    }, 2000);
  };

  const handleReset = () => {
    setShowResults(false);
    setInput('');
    setInputType('url');
  };

  if (showResults) {
    return (
      <div className="h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 overflow-hidden">
        {/* Header */}
        <header className="bg-white/10 backdrop-blur-sm border-b border-white/20">
          <div className="px-6 py-3 flex items-center justify-between">
            <img 
              src="/Chord Scout Logo 5.png" 
              alt="Chord Scout" 
              className="h-8 w-auto"
            />
            <button
              onClick={handleReset}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition-colors"
            >
              New Transcription
            </button>
          </div>
        </header>

        {/* 3-Column Layout */}
        <div className="grid grid-cols-12 h-[calc(100vh-50px)]">
          {/* Left Column */}
          <div className="col-span-2 bg-white/5 border-r border-white/10">
            {/* Left sidebar content can go here */}
          </div>

          {/* Middle Column - Results */}
          <div className="col-span-8 p-3 overflow-y-auto">
            <div className="max-w-4xl mx-auto">
              <div className="mb-4">
                <h1 className="text-xl font-bold text-white mb-1">Transcription Results</h1>
                <p className="text-gray-400 text-sm">Your music has been analyzed</p>
              </div>

              {/* Results Grid */}
              <div className="grid gap-3">
                {/* Song Info */}
                <div className="bg-white/5 border border-white/10 rounded-lg p-3">
                  <h2 className="text-lg font-bold text-white mb-2">{mockData.title}</h2>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="bg-white/5 rounded-lg p-2">
                      <p className="text-gray-400 text-xs">Key</p>
                      <p className="text-white font-semibold text-sm">{mockData.key}</p>
                    </div>
                    <div className="bg-white/5 rounded-lg p-2">
                      <p className="text-gray-400 text-xs">Tempo</p>
                      <p className="text-white font-semibold text-sm">{mockData.tempo}</p>
                    </div>
                  </div>
                </div>

                {/* Chords */}
                <div className="bg-white/5 border border-white/10 rounded-lg p-3">
                  <h3 className="text-sm font-semibold text-white mb-2">Chord Progression</h3>
                  <div className="flex flex-wrap gap-2">
                    {mockData.chords.map((chord, index) => (
                      <span key={index} className="bg-blue-600/20 border border-blue-500/30 text-blue-300 px-2 py-1 rounded text-xs font-mono font-semibold">
                        {chord}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Nashville Numbers */}
                <div className="bg-white/5 border border-white/10 rounded-lg p-3">
                  <h3 className="text-sm font-semibold text-white mb-2">Nashville Number System</h3>
                  <div className="bg-white/5 rounded-lg p-2">
                    <p className="text-green-300 font-mono text-sm">{mockData.nashvilleNumbers}</p>
                  </div>
                </div>

                {/* Lyrics with Chords */}
                <div className="bg-white/5 border border-white/10 rounded-lg p-3">
                  <h3 className="text-sm font-semibold text-white mb-2">Lyrics & Timing</h3>
                  <div className="space-y-2">
                    {mockData.lyrics.map((line, index) => (
                      <div key={index} className="bg-white/5 rounded-lg p-2 border-l-2 border-blue-500">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="bg-blue-600/20 text-blue-300 px-1 py-0.5 rounded text-xs font-mono">
                            {line.time}
                          </span>
                          <div className="flex gap-1">
                            {line.chords.map((chord, chordIndex) => (
                              <span key={chordIndex} className="bg-gray-700/50 text-gray-300 px-1 py-0.5 rounded text-xs font-mono">
                                {chord}
                              </span>
                            ))}
                          </div>
                        </div>
                        <p className="text-gray-300 text-xs">{line.text}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column */}
          <div className="col-span-2 bg-white/5 border-l border-white/10">
            {/* Right sidebar content can go here */}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 overflow-hidden">
      {/* Header */}
      <header className="bg-white/10 backdrop-blur-sm border-b border-white/20">
        <div className="px-6 py-3">
          <img 
            src="/Chord Scout Logo 5.png" 
            alt="Chord Scout" 
            className="h-8 w-auto"
          />
        </div>
      </header>

      {/* 3-Column Layout */}
      <div className="grid grid-cols-12 h-[calc(100vh-50px)]">
        {/* Left Column */}
        <div className="col-span-2 bg-white/5 border-r border-white/10">
          {/* Left sidebar content can go here */}
        </div>

        {/* Middle Column - Main Card */}
        <div className="col-span-8 flex items-center justify-center p-6">
          <div className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl p-8 w-full max-w-lg shadow-2xl">
            {/* Header */}
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-white mb-3">Chord Scout</h1>
              <p className="text-gray-300 text-lg">Transform any song into chords and lyrics</p>
            </div>

            {/* Input Type Selector */}
            <div className="mb-6">
              <p className="text-gray-200 font-medium mb-3">Choose your input method:</p>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setInputType('url')}
                  className={`p-4 rounded-xl border-2 transition-all ${
                    inputType === 'url'
                      ? 'border-blue-500 bg-blue-500/20 text-blue-200'
                      : 'border-white/30 bg-white/10 text-gray-300 hover:border-white/50'
                  }`}
                >
                  <div className="text-center">
                    <div className="text-2xl mb-2">🔗</div>
                    <div className="font-medium">YouTube URL</div>
                    <div className="text-xs opacity-75">Paste a link</div>
                  </div>
                </button>
                <button
                  type="button"
                  onClick={() => setInputType('file')}
                  className={`p-4 rounded-xl border-2 transition-all ${
                    inputType === 'file'
                      ? 'border-blue-500 bg-blue-500/20 text-blue-200'
                      : 'border-white/30 bg-white/10 text-gray-300 hover:border-white/50'
                  }`}
                >
                  <div className="text-center">
                    <div className="text-2xl mb-2">🎵</div>
                    <div className="font-medium">Audio File</div>
                    <div className="text-xs opacity-75">Upload MP3/WAV</div>
                  </div>
                </button>
              </div>
            </div>

            {/* Input Form */}
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block text-gray-200 font-medium mb-3">
                  {inputType === 'url' ? 'YouTube URL' : 'Audio File Path'}
                </label>
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder={
                    inputType === 'url' 
                      ? 'https://www.youtube.com/watch?v=...' 
                      : 'Select or drag an audio file'
                  }
                  className="w-full px-4 py-4 bg-white/10 border border-white/30 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:bg-white/20 transition-all"
                  disabled={isLoading}
                />
              </div>

              <button
                type="submit"
                disabled={!input.trim() || isLoading}
                className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:from-gray-700 disabled:to-gray-700 text-white font-semibold py-4 px-6 rounded-xl transition-all duration-200 disabled:cursor-not-allowed shadow-lg"
              >
                {isLoading ? (
                  <div className="flex items-center justify-center gap-3">
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                    Processing...
                  </div>
                ) : (
                  'Start Transcription'
                )}
              </button>
            </form>

            {/* Features */}
            <div className="mt-8 pt-6 border-t border-white/20">
              <p className="text-gray-300 text-sm text-center mb-4">What you'll get:</p>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex items-center gap-2 text-gray-200">
                  <span className="text-green-400">✓</span>
                  Chord progressions
                </div>
                <div className="flex items-center gap-2 text-gray-200">
                  <span className="text-green-400">✓</span>
                  Nashville numbers
                </div>
                <div className="flex items-center gap-2 text-gray-200">
                  <span className="text-green-400">✓</span>
                  Timed lyrics
                </div>
                <div className="flex items-center gap-2 text-gray-200">
                  <span className="text-green-400">✓</span>
                  Key & tempo
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div className="col-span-2 bg-white/5 border-l border-white/10">
          {/* Right sidebar content can go here */}
        </div>
      </div>
    </div>
  );
}

export default App;
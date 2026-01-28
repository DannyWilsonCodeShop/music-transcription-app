import React, { useState } from 'react';
import { ArrowUpTrayIcon, MusicalNoteIcon, DocumentArrowDownIcon, EyeIcon } from '@heroicons/react/24/outline';

interface MockResult {
  id: string;
  title: string;
  status: 'processing' | 'completed';
  progress: number;
  lyrics?: string;
  chords?: {
    key: string;
    mode: string;
    chords: Array<{ name: string; start: number; end: number; }>;
  };
  pdfUrl?: string;
  createdAt: string;
}

function App() {
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [results, setResults] = useState<MockResult[]>([]);

  const generateMockResult = (input: string | File): MockResult => {
    const titles = [
      "Hotel California - Eagles",
      "Wonderwall - Oasis", 
      "Let It Be - The Beatles",
      "Stairway to Heaven - Led Zeppelin",
      "Sweet Child O' Mine - Guns N' Roses"
    ];
    
    const keys = ['Am', 'G', 'C', 'D', 'Em', 'F', 'Bm'];
    const modes = ['major', 'minor'];
    
    const title = typeof input === 'string' 
      ? titles[Math.floor(Math.random() * titles.length)]
      : `${(input as File).name.replace(/\.[^/.]+$/, "")} - Audio Upload`;
    
    const key = keys[Math.floor(Math.random() * keys.length)];
    const mode = modes[Math.floor(Math.random() * modes.length)];
    
    return {
      id: Date.now().toString(),
      title,
      status: 'processing',
      progress: 0,
      createdAt: new Date().toISOString(),
      lyrics: `[Verse 1]
On a dark desert highway, cool wind in my hair
Warm smell of colitas, rising up through the air
Up ahead in the distance, I saw a shimmering light
My head grew heavy and my sight grew dim
I had to stop for the night

[Chorus]
Welcome to the Hotel California
Such a lovely place (Such a lovely place)
Such a lovely face
Plenty of room at the Hotel California
Any time of year (Any time of year)
You can find it here

[Verse 2]
Her mind is Tiffany-twisted, she got the Mercedes bends
She got a lot of pretty, pretty boys she calls friends
How they dance in the courtyard, sweet summer sweat
Some dance to remember, some dance to forget`,
      chords: {
        key,
        mode,
        chords: [
          { name: 'Bm', start: 0, end: 4 },
          { name: 'F#', start: 4, end: 8 },
          { name: 'A', start: 8, end: 12 },
          { name: 'E', start: 12, end: 16 },
          { name: 'G', start: 16, end: 20 },
          { name: 'D', start: 20, end: 24 },
          { name: 'Em', start: 24, end: 28 },
          { name: 'F#', start: 28, end: 32 }
        ]
      }
    };
  };

  const simulateProcessing = async (result: MockResult) => {
    // Simulate processing stages
    const stages = [
      { status: 'processing', progress: 20, delay: 1000 },
      { status: 'processing', progress: 45, delay: 1500 },
      { status: 'processing', progress: 70, delay: 1200 },
      { status: 'processing', progress: 90, delay: 800 },
      { status: 'completed', progress: 100, delay: 500 }
    ];

    for (const stage of stages) {
      await new Promise(resolve => setTimeout(resolve, stage.delay));
      
      setResults(prev => prev.map(r => 
        r.id === result.id 
          ? { 
              ...r, 
              status: stage.status as 'processing' | 'completed',
              progress: stage.progress,
              ...(stage.status === 'completed' ? { 
                pdfUrl: `https://chord-scout-pdfs.s3.amazonaws.com/pdfs/${result.id}.pdf` 
              } : {})
            }
          : r
      ));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!youtubeUrl && !audioFile) return;

    setIsSubmitting(true);
    
    try {
      const input = youtubeUrl || audioFile!;
      const mockResult = generateMockResult(input);
      
      // Add to results immediately
      setResults(prev => [mockResult, ...prev]);
      
      // Start processing simulation
      simulateProcessing(mockResult);
      
      // Reset form
      setYoutubeUrl('');
      setAudioFile(null);
      
    } catch (error) {
      console.error('Error processing:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-black flex flex-col items-center">
      {/* Logo */}
      <div className="pt-12 pb-16">
        <img 
          src="/Chord Scout Logo 5.png" 
          alt="Chord Scout" 
          className="h-24 w-auto"
        />
      </div>
      
      {/* Upload Interface */}
      <div className="w-full max-w-4xl px-6">
        <div className="bg-gray-900 border border-gray-700 rounded-lg p-8 shadow-2xl mb-8">
          <h2 className="text-2xl font-bold text-white mb-8 text-center flex items-center justify-center">
            <MusicalNoteIcon className="w-6 h-6 mr-2 text-gray-400" />
            Upload Music
          </h2>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* YouTube URL Input */}
            <div>
              <label htmlFor="youtube-url" className="block text-sm font-medium text-gray-300 mb-2">
                YouTube URL
              </label>
              <input
                id="youtube-url"
                type="url"
                value={youtubeUrl}
                onChange={(e) => setYoutubeUrl(e.target.value)}
                placeholder="https://www.youtube.com/watch?v=..."
                className="w-full px-4 py-3 bg-black border border-gray-600 rounded-md text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500"
                disabled={!!audioFile}
              />
            </div>

            {/* Divider */}
            <div className="text-center">
              <span className="text-gray-500 font-medium bg-gray-900 px-4">OR</span>
              <div className="border-t border-gray-700 -mt-3"></div>
            </div>

            {/* Audio File Upload */}
            <div>
              <label htmlFor="audio-file" className="block text-sm font-medium text-gray-300 mb-2">
                Upload Audio File
              </label>
              <div className="border-2 border-dashed border-gray-600 rounded-lg p-8 text-center hover:border-gray-500 transition-colors bg-gray-800">
                <ArrowUpTrayIcon className="w-10 h-10 text-gray-500 mx-auto mb-3" />
                <input
                  id="audio-file"
                  type="file"
                  accept="audio/*"
                  onChange={(e) => setAudioFile(e.target.files?.[0] || null)}
                  className="hidden"
                  disabled={!!youtubeUrl}
                />
                <label
                  htmlFor="audio-file"
                  className="cursor-pointer text-gray-300 hover:text-white font-medium block"
                >
                  {audioFile ? (
                    <span className="text-gray-300">{audioFile.name}</span>
                  ) : (
                    <>
                      <span className="text-gray-300">Choose audio file</span>
                      <br />
                      <span className="text-sm text-gray-500">or drag and drop</span>
                    </>
                  )}
                </label>
                <p className="text-xs text-gray-500 mt-2">MP3, WAV, M4A up to 100MB</p>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={(!youtubeUrl && !audioFile) || isSubmitting}
              className="w-full bg-gray-800 border border-gray-600 text-white py-4 px-6 rounded-md hover:bg-gray-700 hover:border-gray-500 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 focus:ring-offset-black disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors"
            >
              {isSubmitting ? 'Processing...' : 'Start Transcription'}
            </button>
          </form>
        </div>

        {/* Results */}
        {results.length > 0 && (
          <div className="space-y-6">
            <h3 className="text-xl font-bold text-white mb-4">Recent Transcriptions</h3>
            {results.map((result) => (
              <div key={result.id} className="bg-gray-900 border border-gray-700 rounded-lg p-6 shadow-xl">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h4 className="text-lg font-bold text-white">{result.title}</h4>
                    <p className="text-sm text-gray-400">{new Date(result.createdAt).toLocaleString()}</p>
                  </div>
                  <div className="flex items-center space-x-2">
                    {result.status === 'processing' ? (
                      <div className="flex items-center text-yellow-400">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-400 mr-2"></div>
                        <span className="text-sm">Processing...</span>
                      </div>
                    ) : (
                      <div className="flex items-center text-green-400">
                        <div className="rounded-full h-4 w-4 bg-green-400 mr-2"></div>
                        <span className="text-sm">Complete</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="mb-4">
                  <div className="flex justify-between text-sm text-gray-400 mb-1">
                    <span>Progress</span>
                    <span>{result.progress}%</span>
                  </div>
                  <div className="w-full bg-gray-800 rounded-full h-2">
                    <div 
                      className="bg-gradient-to-r from-gray-500 to-gray-400 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${result.progress}%` }}
                    ></div>
                  </div>
                </div>

                {result.status === 'completed' && (
                  <>
                    {/* Key Information */}
                    {result.chords && (
                      <div className="mb-4">
                        <h5 className="text-sm font-semibold text-gray-300 mb-2">Key & Chords</h5>
                        <div className="flex items-center space-x-4 mb-2">
                          <span className="px-3 py-1 bg-gray-800 border border-gray-600 rounded-full text-sm text-white">
                            Key: {result.chords.key} {result.chords.mode}
                          </span>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {result.chords.chords.map((chord, idx) => (
                            <span 
                              key={idx}
                              className="px-2 py-1 bg-gray-800 border border-gray-600 text-gray-300 rounded text-sm"
                            >
                              {chord.name}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Lyrics Preview */}
                    {result.lyrics && (
                      <div className="mb-4">
                        <h5 className="text-sm font-semibold text-gray-300 mb-2">Lyrics Preview</h5>
                        <div className="bg-gray-800 border border-gray-600 rounded-lg p-4 max-h-32 overflow-y-auto">
                          <pre className="text-sm text-gray-300 whitespace-pre-wrap font-mono">
                            {result.lyrics.split('\n').slice(0, 8).join('\n')}
                            {result.lyrics.split('\n').length > 8 && '\n...'}
                          </pre>
                        </div>
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex space-x-3">
                      <button className="flex items-center px-4 py-2 bg-gray-800 border border-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors">
                        <EyeIcon className="w-4 h-4 mr-2" />
                        View Full Lyrics
                      </button>
                      {result.pdfUrl && (
                        <a
                          href={result.pdfUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center px-4 py-2 bg-gray-700 border border-gray-500 text-white rounded-md hover:bg-gray-600 transition-colors"
                        >
                          <DocumentArrowDownIcon className="w-4 h-4 mr-2" />
                          Download PDF
                        </a>
                      )}
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
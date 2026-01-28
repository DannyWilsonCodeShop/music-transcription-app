import React, { useState } from 'react';
import { ArrowUpTrayIcon, MusicalNoteIcon } from '@heroicons/react/24/outline';

function App() {
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [audioFile, setAudioFile] = useState<File | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!youtubeUrl && !audioFile) return;
    
    // TODO: Handle upload
    console.log('Upload:', { youtubeUrl, audioFile: audioFile?.name });
  };

  return (
    <div className="min-h-screen bg-black flex flex-col items-center justify-center px-6">
      {/* Logo */}
      <div className="mb-12">
        <img 
          src="/Chord Scout Logo 5.png" 
          alt="Chord Scout" 
          className="h-16 w-auto opacity-90"
        />
      </div>
      
      {/* Upload Interface */}
      <div className="w-full max-w-md">
        <div className="bg-gray-900 border border-gray-600 rounded-xl p-8 shadow-2xl">
          <div className="text-center mb-8">
            <MusicalNoteIcon className="w-8 h-8 text-gray-400 mx-auto mb-3" />
            <h1 className="text-xl font-semibold text-white">Upload Music</h1>
            <p className="text-sm text-gray-400 mt-2">Get chords and lyrics from any song</p>
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* YouTube URL */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                YouTube URL
              </label>
              <input
                type="url"
                value={youtubeUrl}
                onChange={(e) => setYoutubeUrl(e.target.value)}
                placeholder="https://www.youtube.com/watch?v=..."
                className="w-full px-4 py-3 bg-black border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:border-gray-400 transition-colors"
                disabled={!!audioFile}
              />
            </div>

            {/* Divider */}
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-700"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-4 bg-gray-900 text-gray-500 font-medium">OR</span>
              </div>
            </div>

            {/* Audio File Upload */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Upload Audio File
              </label>
              <div className="border-2 border-dashed border-gray-600 rounded-lg p-6 text-center hover:border-gray-500 transition-colors bg-gray-800/50">
                <ArrowUpTrayIcon className="w-8 h-8 text-gray-500 mx-auto mb-3" />
                <input
                  type="file"
                  accept="audio/*"
                  onChange={(e) => setAudioFile(e.target.files?.[0] || null)}
                  className="hidden"
                  id="audio-upload"
                  disabled={!!youtubeUrl}
                />
                <label
                  htmlFor="audio-upload"
                  className="cursor-pointer text-gray-300 hover:text-white transition-colors"
                >
                  {audioFile ? (
                    <span className="font-medium">{audioFile.name}</span>
                  ) : (
                    <>
                      <span className="font-medium">Choose audio file</span>
                      <p className="text-xs text-gray-500 mt-1">MP3, WAV, M4A up to 100MB</p>
                    </>
                  )}
                </label>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={!youtubeUrl && !audioFile}
              className="w-full bg-gradient-to-r from-gray-700 to-gray-600 hover:from-gray-600 hover:to-gray-500 disabled:from-gray-800 disabled:to-gray-800 text-white font-medium py-3 px-6 rounded-lg border border-gray-500 hover:border-gray-400 disabled:border-gray-700 disabled:text-gray-500 transition-all duration-200 disabled:cursor-not-allowed"
            >
              Start Transcription
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default App;
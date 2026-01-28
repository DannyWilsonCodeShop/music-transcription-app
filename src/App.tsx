import React, { useState } from 'react';
import { ArrowUpTrayIcon, MusicalNoteIcon } from '@heroicons/react/24/outline';

function App() {
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!youtubeUrl && !audioFile) return;

    setIsSubmitting(true);
    
    try {
      // TODO: Process the upload
      console.log('Processing:', { youtubeUrl, audioFile: audioFile?.name });
      
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
          src="/Chord Scout Logo 4.png" 
          alt="Chord Scout" 
          className="h-24 w-auto"
        />
      </div>
      
      {/* Upload Interface */}
      <div className="w-full max-w-md px-6">
        <div className="bg-gray-900 border border-gray-700 rounded-lg p-8 shadow-2xl">
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
      </div>
    </div>
  );
}

export default App;
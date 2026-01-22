import React, { useState } from 'react';
import { Amplify } from 'aws-amplify';
import FileUpload from './components/FileUpload';
import YouTubeInput from './components/YouTubeInput';
import JobStatus from './components/JobStatus';
import './App.css';

// Amplify configuration will be auto-generated after amplify init
// import awsconfig from './aws-exports';
// Amplify.configure(awsconfig);

function App() {
  const [activeTab, setActiveTab] = useState('upload');
  const [currentJobId, setCurrentJobId] = useState(null);

  return (
    <div className="App">
      <header className="App-header">
        <h1>🎵 Music Transcription</h1>
        <p>Extract lyrics and chords from any song using AI</p>
      </header>

      <div className="container">
        <div className="tabs">
          <button 
            className={`tab ${activeTab === 'upload' ? 'active' : ''}`}
            onClick={() => setActiveTab('upload')}
          >
            📁 Upload File
          </button>
          <button 
            className={`tab ${activeTab === 'youtube' ? 'active' : ''}`}
            onClick={() => setActiveTab('youtube')}
          >
            🎬 YouTube Link
          </button>
        </div>

        <div className="content">
          {activeTab === 'upload' && (
            <FileUpload onJobCreated={setCurrentJobId} />
          )}
          {activeTab === 'youtube' && (
            <YouTubeInput onJobCreated={setCurrentJobId} />
          )}
          
          {currentJobId && (
            <JobStatus jobId={currentJobId} />
          )}
        </div>
      </div>

      <footer className="App-footer">
        <p>Powered by OpenAI Whisper & AWS</p>
      </footer>
    </div>
  );
}

export default App;

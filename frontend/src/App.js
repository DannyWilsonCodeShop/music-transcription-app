import React, { useState } from 'react';
import { Amplify } from 'aws-amplify';
import FileUpload from './components/FileUpload';
import JobStatus from './components/JobStatus';
import './App.css';

// Amplify configuration will be auto-generated after amplify init
// import awsconfig from './aws-exports';
// Amplify.configure(awsconfig);

function App() {
  const [currentJobId, setCurrentJobId] = useState(null);

  return (
    <div className="App">
      <header className="App-header">
        <h1>🎵 Music Transcription</h1>
        <p>Extract chords and lyrics from your audio files using AI</p>
      </header>

      <div className="container">
        <div className="content">
          <FileUpload onJobCreated={setCurrentJobId} />
          
          {currentJobId && (
            <JobStatus jobId={currentJobId} />
          )}
        </div>
      </div>

      <footer className="App-footer">
        <p>Powered by Enhanced Chord Detection & AWS</p>
      </footer>
    </div>
  );
}

export default App;

import { useState } from 'react';
import { Amplify } from 'aws-amplify';
import outputs from '../amplify_outputs.json';
import UploadSection from './components/UploadSection';
import TranscriptionOptions from './components/TranscriptionOptions';
import TranscriptionsList from './components/TranscriptionsList';
import RippedSongsWidget from './components/RippedSongsWidget';
import BackingTracksWidget from './components/BackingTracksWidget';
import StudyModulesWidget from './components/StudyModulesWidget';
import DashboardHeader from './components/DashboardHeader';

Amplify.configure(outputs);

function App() {
  const [userName] = useState('Danny');

  return (
    <div className="min-h-screen bg-[#e5e5e5]">
      {/* Header */}
      <DashboardHeader userName={userName} />

      {/* Main Content - 4 Column Grid */}
      <div className="max-w-[1600px] mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left Column - Upload & Transcriptions (3/4 width) */}
          <div className="lg:col-span-3 space-y-6">
            {/* Upload Section */}
            <UploadSection />

            {/* Transcription Options */}
            <TranscriptionOptions />

            {/* Transcriptions List */}
            <TranscriptionsList />
          </div>

          {/* Right Sidebar (1/4 width) */}
          <div className="lg:col-span-1 space-y-4">
            <RippedSongsWidget />
            <BackingTracksWidget />
            <StudyModulesWidget />
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;

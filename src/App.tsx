import { useState, useEffect } from 'react';
import { Amplify } from 'aws-amplify';
import { generateClient } from 'aws-amplify/data';
import { uploadData } from 'aws-amplify/storage';
import type { Schema } from '../amplify/data/resource';
import outputs from '../amplify_outputs.json';

Amplify.configure(outputs);

const client = generateClient<Schema>();

function App() {
  const [jobs, setJobs] = useState<Array<Schema["TranscriptionJob"]["type"]>>([]);
  const [file, setFile] = useState<File | null>(null);
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    try {
      const { data } = await client.models.TranscriptionJob.list();
      setJobs(data);
    } catch (error) {
      console.error('Error fetching jobs:', error);
    }
  };

  const handleFileUpload = async () => {
    if (!file) return;
    
    setLoading(true);
    try {
      // Upload file to S3
      const result = await uploadData({
        key: `audio-files/${Date.now()}-${file.name}`,
        data: file,
      }).result;

      // Create transcription job
      await client.models.TranscriptionJob.create({
        status: 'pending',
        audioUrl: result.key,
        title: file.name,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      });

      setFile(null);
      fetchJobs();
    } catch (error) {
      console.error('Error uploading file:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleYouTubeSubmit = async () => {
    if (!youtubeUrl) return;
    
    setLoading(true);
    try {
      await client.models.TranscriptionJob.create({
        status: 'pending',
        youtubeUrl,
        title: 'YouTube Video',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      });

      setYoutubeUrl('');
      fetchJobs();
    } catch (error) {
      console.error('Error creating YouTube job:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h1>🎵 Music Transcription App</h1>
      <p>AI-powered lyrics and chord transcription from audio files or YouTube links</p>

      <div style={{ marginBottom: '30px', padding: '20px', border: '1px solid #ddd', borderRadius: '8px' }}>
        <h3>Upload Audio File</h3>
        <input
          type="file"
          accept="audio/*"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          style={{ marginBottom: '10px', display: 'block' }}
        />
        <button 
          onClick={handleFileUpload} 
          disabled={!file || loading}
          style={{ padding: '10px 20px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px' }}
        >
          {loading ? 'Uploading...' : 'Upload & Transcribe'}
        </button>
      </div>

      <div style={{ marginBottom: '30px', padding: '20px', border: '1px solid #ddd', borderRadius: '8px' }}>
        <h3>YouTube URL</h3>
        <input
          type="url"
          placeholder="https://www.youtube.com/watch?v=..."
          value={youtubeUrl}
          onChange={(e) => setYoutubeUrl(e.target.value)}
          style={{ width: '100%', padding: '8px', marginBottom: '10px' }}
        />
        <button 
          onClick={handleYouTubeSubmit} 
          disabled={!youtubeUrl || loading}
          style={{ padding: '10px 20px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '4px' }}
        >
          {loading ? 'Processing...' : 'Transcribe from YouTube'}
        </button>
      </div>

      <div>
        <h3>Transcription Jobs</h3>
        {jobs.length === 0 ? (
          <p>No transcription jobs yet. Upload an audio file or paste a YouTube URL to get started!</p>
        ) : (
          <div>
            {jobs.map((job) => (
              <div key={job.id} style={{ padding: '15px', border: '1px solid #eee', borderRadius: '8px', marginBottom: '10px' }}>
                <h4>{job.title}</h4>
                <p><strong>Status:</strong> <span style={{ 
                  color: job.status === 'completed' ? 'green' : job.status === 'failed' ? 'red' : 'orange' 
                }}>{job.status}</span></p>
                {job.lyrics && (
                  <div>
                    <h5>Lyrics:</h5>
                    <pre style={{ whiteSpace: 'pre-wrap', backgroundColor: '#f8f9fa', padding: '10px', borderRadius: '4px' }}>
                      {job.lyrics}
                    </pre>
                  </div>
                )}
                {job.chords && (
                  <div>
                    <h5>Chords:</h5>
                    <pre style={{ whiteSpace: 'pre-wrap', backgroundColor: '#f8f9fa', padding: '10px', borderRadius: '4px' }}>
                      {JSON.stringify(job.chords, null, 2)}
                    </pre>
                  </div>
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
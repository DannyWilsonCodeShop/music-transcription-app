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
        path: `audio-files/${Date.now()}-${file.name}`,
        data: file,
        options: {
          accessLevel: 'guest'
        }
      }).result;

      // Create transcription job
      await client.models.TranscriptionJob.create({
        status: 'pending',
        audioUrl: result.path,
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

  const styles = {
    container: {
      minHeight: '100vh',
      backgroundColor: '#e5e5e5',
      fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "SF Pro Display", Roboto, "IBM Plex Sans", sans-serif',
      color: '#3f3f3f',
      lineHeight: '1.6'
    },
    header: {
      backgroundColor: '#3f3f3f',
      color: 'white',
      padding: '2rem 0',
      textAlign: 'center' as const,
      marginBottom: '3rem'
    },
    title: {
      fontSize: '2.5rem',
      fontWeight: '600',
      margin: '0 0 0.5rem 0',
      letterSpacing: '-0.02em'
    },
    subtitle: {
      fontSize: '1.1rem',
      opacity: '0.9',
      fontWeight: '400',
      margin: '0'
    },
    main: {
      maxWidth: '900px',
      margin: '0 auto',
      padding: '0 1.5rem 3rem'
    },
    card: {
      backgroundColor: 'white',
      borderRadius: '16px',
      padding: '2rem',
      marginBottom: '2rem',
      boxShadow: '0 4px 20px rgba(63, 63, 63, 0.08)',
      border: '1px solid rgba(0, 191, 196, 0.1)'
    },
    cardTitle: {
      fontSize: '1.25rem',
      fontWeight: '600',
      margin: '0 0 1.5rem 0',
      color: '#3f3f3f'
    },
    input: {
      width: '100%',
      padding: '0.875rem 1rem',
      border: '2px solid #e5e5e5',
      borderRadius: '12px',
      fontSize: '1rem',
      fontFamily: 'inherit',
      transition: 'all 0.2s ease',
      marginBottom: '1rem',
      backgroundColor: 'white'
    },
    inputFocus: {
      borderColor: '#00bfc4',
      outline: 'none',
      boxShadow: '0 0 0 3px rgba(0, 191, 196, 0.1)'
    },
    fileInput: {
      width: '100%',
      padding: '1rem',
      border: '2px dashed #00bfc4',
      borderRadius: '12px',
      backgroundColor: 'rgba(0, 191, 196, 0.02)',
      textAlign: 'center' as const,
      cursor: 'pointer',
      transition: 'all 0.2s ease',
      marginBottom: '1rem'
    },
    button: {
      backgroundColor: '#00bfc4',
      color: 'white',
      border: 'none',
      borderRadius: '12px',
      padding: '0.875rem 1.5rem',
      fontSize: '1rem',
      fontWeight: '500',
      cursor: 'pointer',
      transition: 'all 0.2s ease',
      fontFamily: 'inherit'
    },
    buttonSecondary: {
      backgroundColor: '#0089c6',
      color: 'white',
      border: 'none',
      borderRadius: '12px',
      padding: '0.875rem 1.5rem',
      fontSize: '1rem',
      fontWeight: '500',
      cursor: 'pointer',
      transition: 'all 0.2s ease',
      fontFamily: 'inherit'
    },
    buttonDisabled: {
      backgroundColor: '#9e9e9e',
      cursor: 'not-allowed',
      opacity: '0.7'
    },
    jobCard: {
      backgroundColor: 'white',
      border: '1px solid #e5e5e5',
      borderRadius: '12px',
      padding: '1.5rem',
      marginBottom: '1rem',
      transition: 'all 0.2s ease'
    },
    jobTitle: {
      fontSize: '1.1rem',
      fontWeight: '600',
      margin: '0 0 0.5rem 0',
      color: '#3f3f3f'
    },
    statusBadge: {
      display: 'inline-block',
      padding: '0.25rem 0.75rem',
      borderRadius: '20px',
      fontSize: '0.875rem',
      fontWeight: '500',
      textTransform: 'capitalize' as const
    },
    statusCompleted: {
      backgroundColor: 'rgba(0, 191, 196, 0.1)',
      color: '#00bfc4'
    },
    statusPending: {
      backgroundColor: 'rgba(255, 230, 0, 0.2)',
      color: '#3f3f3f'
    },
    statusFailed: {
      backgroundColor: 'rgba(255, 0, 0, 0.1)',
      color: '#d32f2f'
    },
    resultSection: {
      marginTop: '1rem',
      padding: '1rem',
      backgroundColor: '#e5e5e5',
      borderRadius: '8px',
      fontSize: '0.95rem'
    },
    emptyState: {
      textAlign: 'center' as const,
      padding: '3rem 1rem',
      color: '#9e9e9e'
    }
  };

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>🎵 ChordScout</h1>
        <p style={styles.subtitle}>AI-powered music transcription for lyrics and chords</p>
      </header>

      <main style={styles.main}>
        <div style={styles.card}>
          <h2 style={styles.cardTitle}>Upload Audio File</h2>
          <form onSubmit={(e) => { e.preventDefault(); handleFileUpload(); }}>
            <div 
              style={{
                ...styles.fileInput,
                ...(file ? { borderColor: '#00bfc4', backgroundColor: 'rgba(0, 191, 196, 0.05)' } : {})
              }}
              onDragOver={(e) => {
                e.preventDefault();
                e.currentTarget.style.borderColor = '#00bfc4';
                e.currentTarget.style.backgroundColor = 'rgba(0, 191, 196, 0.05)';
              }}
              onDragLeave={(e) => {
                e.preventDefault();
                e.currentTarget.style.borderColor = '#00bfc4';
                e.currentTarget.style.backgroundColor = 'rgba(0, 191, 196, 0.02)';
              }}
              onDrop={(e) => {
                e.preventDefault();
                const files = e.dataTransfer.files;
                if (files.length > 0 && files[0].type.startsWith('audio/')) {
                  setFile(files[0]);
                }
                e.currentTarget.style.borderColor = '#00bfc4';
                e.currentTarget.style.backgroundColor = 'rgba(0, 191, 196, 0.02)';
              }}
            >
              <input
                type="file"
                accept="audio/*"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                style={{ display: 'none' }}
                id="file-upload"
                name="audioFile"
                aria-label="Upload audio file for transcription"
              />
              <label htmlFor="file-upload" style={{ cursor: 'pointer', display: 'block' }}>
                {file ? (
                  <div>
                    <div style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>🎵</div>
                    <div style={{ fontWeight: '500', color: '#00bfc4' }}>{file.name}</div>
                    <div style={{ fontSize: '0.875rem', color: '#9e9e9e', marginTop: '0.25rem' }}>
                      {(file.size / 1024 / 1024).toFixed(1)} MB • Click to change
                    </div>
                  </div>
                ) : (
                  <div>
                    <div style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>📤</div>
                    <div style={{ fontWeight: '500' }}>Drop your audio file here</div>
                    <div style={{ fontSize: '0.875rem', color: '#9e9e9e', marginTop: '0.25rem' }}>
                      Supports MP3, WAV, M4A, and more
                    </div>
                  </div>
                )}
              </label>
            </div>
            <button 
              type="submit"
              disabled={!file || loading}
              style={{
                ...styles.button,
                ...((!file || loading) ? styles.buttonDisabled : {}),
                ...(loading ? { className: 'loading' } : {})
              }}
            >
              {loading ? '🎵 Processing...' : '🚀 Transcribe Audio'}
            </button>
          </form>
        </div>

        <div style={styles.card}>
          <h2 style={styles.cardTitle}>YouTube Video</h2>
          <form onSubmit={(e) => { e.preventDefault(); handleYouTubeSubmit(); }}>
            <input
              type="url"
              placeholder="Paste YouTube URL here..."
              value={youtubeUrl}
              onChange={(e) => setYoutubeUrl(e.target.value)}
              style={styles.input}
              id="youtube-url"
              name="youtubeUrl"
              aria-label="YouTube video URL for transcription"
              autoComplete="url"
            />
            <button 
              type="submit"
              disabled={!youtubeUrl || loading}
              style={{
                ...styles.buttonSecondary,
                ...((!youtubeUrl || loading) ? styles.buttonDisabled : {})
              }}
            >
              {loading ? 'Processing...' : 'Transcribe from YouTube'}
            </button>
          </form>
        </div>

        <div style={styles.card}>
          <h2 style={styles.cardTitle}>Your Transcriptions</h2>
          {jobs.length === 0 ? (
            <div style={styles.emptyState}>
              <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🎼</div>
              <p>No transcriptions yet</p>
              <p style={{ fontSize: '0.875rem' }}>Upload an audio file or YouTube link to get started</p>
            </div>
          ) : (
            <div>
              {jobs.map((job) => (
                <div key={job.id} style={styles.jobCard}>
                  <h3 style={styles.jobTitle}>{job.title}</h3>
                  <div style={{ marginBottom: '1rem' }}>
                    <span 
                      style={{
                        ...styles.statusBadge,
                        ...(job.status === 'completed' ? styles.statusCompleted :
                            job.status === 'failed' ? styles.statusFailed : 
                            styles.statusPending)
                      }}
                    >
                      {job.status}
                    </span>
                  </div>
                  
                  {job.lyrics && (
                    <div style={styles.resultSection}>
                      <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '1rem', fontWeight: '600' }}>Lyrics</h4>
                      <div style={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: '0.9rem' }}>
                        {job.lyrics}
                      </div>
                    </div>
                  )}
                  
                  {job.chords && (
                    <div style={styles.resultSection}>
                      <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '1rem', fontWeight: '600' }}>Chords</h4>
                      <div style={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: '0.9rem' }}>
                        {typeof job.chords === 'string' ? job.chords : JSON.stringify(job.chords, null, 2)}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
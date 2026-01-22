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
        data: file
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
      height: '100vh',
      backgroundColor: '#e5e5e5',
      fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "SF Pro Display", Roboto, "IBM Plex Sans", sans-serif',
      color: '#3f3f3f',
      lineHeight: '1.4',
      overflow: 'hidden'
    },
    header: {
      backgroundColor: '#3f3f3f',
      color: 'white',
      padding: '1rem 0',
      textAlign: 'center' as const,
      marginBottom: '1rem'
    },
    title: {
      fontSize: '1.8rem',
      fontWeight: '600',
      margin: '0 0 0.25rem 0',
      letterSpacing: '-0.02em'
    },
    subtitle: {
      fontSize: '0.9rem',
      opacity: '0.9',
      fontWeight: '400',
      margin: '0'
    },
    main: {
      height: 'calc(100vh - 120px)',
      padding: '0 1rem',
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gridTemplateRows: 'auto 1fr',
      gap: '1rem',
      overflow: 'hidden'
    },
    leftColumn: {
      display: 'flex',
      flexDirection: 'column' as const,
      gap: '1rem'
    },
    rightColumn: {
      display: 'flex',
      flexDirection: 'column' as const,
      gap: '1rem',
      gridRow: '1 / -1'
    },
    card: {
      backgroundColor: 'white',
      borderRadius: '12px',
      padding: '1rem',
      boxShadow: '0 2px 10px rgba(63, 63, 63, 0.08)',
      border: '1px solid rgba(0, 191, 196, 0.1)',
      overflow: 'hidden'
    },
    compactCard: {
      backgroundColor: 'white',
      borderRadius: '12px',
      padding: '0.75rem',
      boxShadow: '0 2px 10px rgba(63, 63, 63, 0.08)',
      border: '1px solid rgba(0, 191, 196, 0.1)',
      flex: '1',
      overflow: 'hidden'
    },
    cardTitle: {
      fontSize: '1rem',
      fontWeight: '600',
      margin: '0 0 0.75rem 0',
      color: '#3f3f3f'
    },
    compactTitle: {
      fontSize: '0.9rem',
      fontWeight: '600',
      margin: '0 0 0.5rem 0',
      color: '#3f3f3f'
    },
    input: {
      width: '100%',
      padding: '0.5rem 0.75rem',
      border: '2px solid #e5e5e5',
      borderRadius: '8px',
      fontSize: '0.9rem',
      fontFamily: 'inherit',
      transition: 'all 0.2s ease',
      marginBottom: '0.5rem',
      backgroundColor: 'white',
      boxSizing: 'border-box' as const
    },
    fileInput: {
      width: '100%',
      padding: '0.75rem',
      border: '2px dashed #00bfc4',
      borderRadius: '8px',
      backgroundColor: 'rgba(0, 191, 196, 0.02)',
      textAlign: 'center' as const,
      cursor: 'pointer',
      transition: 'all 0.2s ease',
      marginBottom: '0.5rem'
    },
    button: {
      backgroundColor: '#00bfc4',
      color: 'white',
      border: 'none',
      borderRadius: '8px',
      padding: '0.5rem 1rem',
      fontSize: '0.9rem',
      fontWeight: '500',
      cursor: 'pointer',
      transition: 'all 0.2s ease',
      fontFamily: 'inherit',
      width: '100%'
    },
    buttonSecondary: {
      backgroundColor: '#0089c6',
      color: 'white',
      border: 'none',
      borderRadius: '8px',
      padding: '0.5rem 1rem',
      fontSize: '0.9rem',
      fontWeight: '500',
      cursor: 'pointer',
      transition: 'all 0.2s ease',
      fontFamily: 'inherit',
      width: '100%'
    },
    buttonDisabled: {
      backgroundColor: '#9e9e9e',
      cursor: 'not-allowed',
      opacity: '0.7'
    },
    transcriptionsCard: {
      gridColumn: '1 / -1',
      maxHeight: '200px',
      overflow: 'auto'
    },
    jobCard: {
      backgroundColor: '#f8f9fa',
      border: '1px solid #e5e5e5',
      borderRadius: '8px',
      padding: '0.75rem',
      marginBottom: '0.5rem',
      fontSize: '0.85rem'
    },
    jobTitle: {
      fontSize: '0.9rem',
      fontWeight: '600',
      margin: '0 0 0.25rem 0',
      color: '#3f3f3f'
    },
    statusBadge: {
      display: 'inline-block',
      padding: '0.125rem 0.5rem',
      borderRadius: '12px',
      fontSize: '0.75rem',
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
    emptyState: {
      textAlign: 'center' as const,
      padding: '1rem',
      color: '#9e9e9e',
      fontSize: '0.85rem'
    },
    featuresGrid: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: '0.5rem',
      height: '100%',
      overflow: 'auto'
    },
    featureSection: {
      marginBottom: '1rem'
    },
    sectionTitle: {
      fontSize: '0.85rem',
      fontWeight: '600',
      margin: '0 0 0.5rem 0',
      color: '#3f3f3f',
      borderBottom: '2px solid #00bfc4',
      paddingBottom: '0.25rem'
    },
    featureGrid: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr 1fr',
      gap: '0.5rem',
      marginBottom: '0.75rem'
    },
    featureCard: {
      backgroundColor: '#f8f9fa',
      borderRadius: '8px',
      padding: '0.75rem',
      textAlign: 'center' as const,
      border: '1px solid rgba(158, 158, 158, 0.2)',
      transition: 'all 0.2s ease'
    },
    featureIcon: {
      fontSize: '1.5rem',
      marginBottom: '0.25rem',
      display: 'block'
    },
    featureTitle: {
      fontSize: '0.75rem',
      fontWeight: '600',
      margin: '0 0 0.25rem 0',
      color: '#3f3f3f',
      lineHeight: '1.2'
    },
    featureDescription: {
      fontSize: '0.65rem',
      color: '#9e9e9e',
      margin: '0 0 0.5rem 0',
      lineHeight: '1.2'
    },
    comingSoonBadge: {
      display: 'inline-block',
      backgroundColor: '#ffe600',
      color: '#3f3f3f',
      padding: '0.125rem 0.375rem',
      borderRadius: '10px',
      fontSize: '0.6rem',
      fontWeight: '600',
      textTransform: 'uppercase' as const,
      letterSpacing: '0.3px'
    }
  };

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>🎵 ChordScout</h1>
        <p style={styles.subtitle}>AI-powered music transcription for lyrics and chords</p>
      </header>

      <main style={styles.main}>
        {/* Left Column - Upload & YouTube */}
        <div style={styles.leftColumn}>
          <div style={styles.compactCard}>
            <h2 style={styles.compactTitle}>Upload Audio File</h2>
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
                      <div style={{ fontSize: '1.2rem', marginBottom: '0.25rem' }}>🎵</div>
                      <div style={{ fontWeight: '500', color: '#00bfc4', fontSize: '0.8rem' }}>{file.name}</div>
                      <div style={{ fontSize: '0.7rem', color: '#9e9e9e', marginTop: '0.125rem' }}>
                        {(file.size / 1024 / 1024).toFixed(1)} MB
                      </div>
                    </div>
                  ) : (
                    <div>
                      <div style={{ fontSize: '1.2rem', marginBottom: '0.25rem' }}>📤</div>
                      <div style={{ fontWeight: '500', fontSize: '0.8rem' }}>Drop audio file</div>
                      <div style={{ fontSize: '0.7rem', color: '#9e9e9e', marginTop: '0.125rem' }}>
                        MP3, WAV, M4A
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
                  ...((!file || loading) ? styles.buttonDisabled : {})
                }}
              >
                {loading ? '🎵 Processing...' : '🚀 Transcribe'}
              </button>
            </form>
          </div>

          <div style={styles.compactCard}>
            <h2 style={styles.compactTitle}>YouTube Video</h2>
            <form onSubmit={(e) => { e.preventDefault(); handleYouTubeSubmit(); }}>
              <input
                type="url"
                placeholder="Paste YouTube URL..."
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
                {loading ? 'Processing...' : 'Transcribe YouTube'}
              </button>
            </form>
          </div>
        </div>

        {/* Right Column - Features */}
        <div style={styles.rightColumn}>
          <div style={styles.compactCard}>
            <h2 style={styles.compactTitle}>🚀 Coming Soon Features</h2>
            <div style={styles.featuresGrid}>
              <div>
                <div style={styles.sectionTitle}>🎸 Transcription & Analysis</div>
                <div style={styles.featureGrid}>
                  <div style={styles.featureCard}>
                    <div style={styles.featureIcon}>🎵</div>
                    <h3 style={styles.featureTitle}>Transcribe Chords</h3>
                    <p style={styles.featureDescription}>AI chord detection</p>
                    <div style={styles.comingSoonBadge}>Soon</div>
                  </div>
                  <div style={styles.featureCard}>
                    <div style={styles.featureIcon}>🎤</div>
                    <h3 style={styles.featureTitle}>Transcribe Lyrics</h3>
                    <p style={styles.featureDescription}>Lyric transcription</p>
                    <div style={styles.comingSoonBadge}>Soon</div>
                  </div>
                  <div style={styles.featureCard}>
                    <div style={styles.featureIcon}>🔄</div>
                    <h3 style={styles.featureTitle}>Transpose</h3>
                    <p style={styles.featureDescription}>Change key instantly</p>
                    <div style={styles.comingSoonBadge}>Soon</div>
                  </div>
                </div>

                <div style={styles.sectionTitle}>📚 Learning & Training</div>
                <div style={styles.featureGrid}>
                  <div style={styles.featureCard}>
                    <div style={styles.featureIcon}>🔢</div>
                    <h3 style={styles.featureTitle}>Nashville Numbers</h3>
                    <p style={styles.featureDescription}>Pro chord notation</p>
                    <div style={styles.comingSoonBadge}>Soon</div>
                  </div>
                  <div style={styles.featureCard}>
                    <div style={styles.featureIcon}>🎓</div>
                    <h3 style={styles.featureTitle}>Theory Lessons</h3>
                    <p style={styles.featureDescription}>Interactive learning</p>
                    <div style={styles.comingSoonBadge}>Soon</div>
                  </div>
                  <div style={styles.featureCard}>
                    <div style={styles.featureIcon}>📊</div>
                    <h3 style={styles.featureTitle}>Chord Charts</h3>
                    <p style={styles.featureDescription}>Visual fingerings</p>
                    <div style={styles.comingSoonBadge}>Soon</div>
                  </div>
                </div>
              </div>

              <div>
                <div style={styles.sectionTitle}>🎶 Practice & Performance</div>
                <div style={styles.featureGrid}>
                  <div style={styles.featureCard}>
                    <div style={styles.featureIcon}>🎼</div>
                    <h3 style={styles.featureTitle}>Backing Tracks</h3>
                    <p style={styles.featureDescription}>Practice tracks</p>
                    <div style={styles.comingSoonBadge}>Soon</div>
                  </div>
                  <div style={styles.featureCard}>
                    <div style={styles.featureIcon}>📖</div>
                    <h3 style={styles.featureTitle}>Song Database</h3>
                    <p style={styles.featureDescription}>Searchable library</p>
                    <div style={styles.comingSoonBadge}>Soon</div>
                  </div>
                </div>

                <div style={styles.sectionTitle}>👥 Community</div>
                <div style={styles.featureGrid}>
                  <div style={styles.featureCard}>
                    <div style={styles.featureIcon}>🤝</div>
                    <h3 style={styles.featureTitle}>Connect</h3>
                    <p style={styles.featureDescription}>Find musicians</p>
                    <div style={styles.comingSoonBadge}>Soon</div>
                  </div>
                  <div style={styles.featureCard}>
                    <div style={styles.featureIcon}>📹</div>
                    <h3 style={styles.featureTitle}>Share Music</h3>
                    <p style={styles.featureDescription}>Upload videos</p>
                    <div style={styles.comingSoonBadge}>Soon</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Transcriptions - Full Width Bottom */}
        <div style={{...styles.card, ...styles.transcriptionsCard}}>
          <h2 style={styles.cardTitle}>Your Transcriptions</h2>
          {jobs.length === 0 ? (
            <div style={styles.emptyState}>
              <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🎼</div>
              <p>No transcriptions yet - Upload an audio file or YouTube link to get started</p>
            </div>
          ) : (
            <div>
              {jobs.map((job) => (
                <div key={job.id} style={styles.jobCard}>
                  <h3 style={styles.jobTitle}>{job.title}</h3>
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
                  {job.lyrics && (
                    <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: '#666' }}>
                      Lyrics: {job.lyrics.substring(0, 100)}...
                    </div>
                  )}
                  {job.chords && (
                    <div style={{ marginTop: '0.25rem', fontSize: '0.8rem', color: '#666' }}>
                      Chords: {typeof job.chords === 'string' ? job.chords.substring(0, 50) : 'Available'}...
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
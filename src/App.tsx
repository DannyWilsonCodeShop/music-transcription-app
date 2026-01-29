import { useState, useEffect } from 'react';
import { startTranscription, getJobStatus, TranscriptionJob } from './services/transcriptionService';

function App() {
  const [url, setUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [job, setJob] = useState<TranscriptionJob | null>(null);

  useEffect(() => {
    if (!jobId) return;
    const pollInterval = setInterval(async () => {
      const status = await getJobStatus(jobId);
      if (status) {
        setJob(status);
        if (status.status === 'COMPLETE' || status.status === 'FAILED') {
          clearInterval(pollInterval);
          setIsLoading(false);
        }
      }
    }, 2000);
    return () => clearInterval(pollInterval);
  }, [jobId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    setIsLoading(true);
    try {
      const newJobId = await startTranscription(url);
      setJobId(newJobId);
    } catch (error) {
      console.error('Failed:', error);
      setIsLoading(false);
      alert('Failed to start transcription.');
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #1f2937 0%, #111827 50%, #0f172a 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }}>
      <div style={{ width: '100%', maxWidth: '800px' }}>
        
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '48px' }}>
          <h1 style={{
            fontSize: '48px',
            fontWeight: 'bold',
            background: 'linear-gradient(to right, #9333ea, #2563eb)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            marginBottom: '12px'
          }}>
            Music Transcription App
          </h1>
          <p style={{ color: '#9ca3af', fontSize: '18px' }}>
            Transform any YouTube video into chords and lyrics
          </p>
        </div>

        {/* Search Bar */}
        <form onSubmit={handleSubmit}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            backgroundColor: 'white',
            borderRadius: '16px',
            boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
            border: '1px solid #e5e7eb',
            overflow: 'hidden',
            transition: 'box-shadow 0.3s'
          }}>
            
            {/* Sparkle Icon */}
            <div style={{ paddingLeft: '20px', paddingRight: '12px' }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="#9333ea">
                <path d="M12 2L9.19 8.63L2 9.24l5.46 4.73L5.82 21L12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2z"/>
              </svg>
            </div>

            {/* Input */}
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Paste YouTube URL here..."
              disabled={isLoading}
              style={{
                flex: 1,
                padding: '20px 0',
                fontSize: '16px',
                border: 'none',
                outline: 'none',
                color: '#1f2937',
                backgroundColor: 'transparent'
              }}
            />

            {/* Button */}
            <button
              type="submit"
              disabled={!url.trim() || isLoading}
              style={{
                margin: '8px',
                padding: '12px 24px',
                background: 'linear-gradient(to right, #9333ea, #2563eb)',
                color: 'white',
                fontWeight: '500',
                borderRadius: '12px',
                border: 'none',
                cursor: url.trim() && !isLoading ? 'pointer' : 'not-allowed',
                opacity: !url.trim() || isLoading ? 0.5 : 1,
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                transition: 'all 0.2s'
              }}
            >
              {isLoading ? 'Processing...' : 'Start'}
              {!isLoading && (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M13 7l5 5m0 0l-5 5m5-5H6"/>
                </svg>
              )}
            </button>
          </div>
        </form>

        {/* Progress */}
        {isLoading && job && (
          <div style={{
            marginTop: '24px',
            padding: '24px',
            backgroundColor: 'white',
            borderRadius: '16px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
            border: '1px solid #e5e7eb'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
              <span style={{ color: '#374151', fontWeight: '500' }}>{job.currentStep || 'Processing...'}</span>
              <span style={{ color: '#9333ea', fontWeight: '600' }}>{job.progress || 0}%</span>
            </div>
            <div style={{
              width: '100%',
              height: '10px',
              backgroundColor: '#e5e7eb',
              borderRadius: '999px',
              overflow: 'hidden'
            }}>
              <div style={{
                height: '100%',
                background: 'linear-gradient(to right, #9333ea, #2563eb)',
                borderRadius: '999px',
                width: `${job.progress || 0}%`,
                transition: 'width 0.5s'
              }}/>
            </div>
          </div>
        )}

        {/* Results */}
        {job?.status === 'COMPLETE' && (
          <div style={{
            marginTop: '24px',
            padding: '24px',
            background: 'linear-gradient(to right, #f0fdf4, #dcfce7)',
            borderRadius: '16px',
            border: '1px solid #86efac'
          }}>
            <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#166534', marginBottom: '8px' }}>
              ✓ Transcription Complete!
            </h2>
            <p style={{ color: '#15803d', marginBottom: '16px' }}>{job.title}</p>
            {job.pdfUrl && (
              <a 
                href={job.pdfUrl}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  display: 'inline-block',
                  padding: '10px 20px',
                  backgroundColor: '#16a34a',
                  color: 'white',
                  borderRadius: '8px',
                  textDecoration: 'none',
                  fontWeight: '500'
                }}
              >
                Download PDF
              </a>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;

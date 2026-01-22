import React, { useEffect, useState } from 'react';
import { API } from 'aws-amplify';
import './JobStatus.css';

function JobStatus({ jobId }) {
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let interval;

    const fetchJobStatus = async () => {
      try {
        const response = await API.get('transcriptionAPI', `/transcribe/job/${jobId}`);
        setJob(response);
        setLoading(false);
        setError(null);

        // Stop polling if job is completed or failed
        if (response.status === 'completed' || response.status === 'failed') {
          clearInterval(interval);
        }
      } catch (err) {
        console.error('Error fetching job status:', err);
        setError(err.message || 'Failed to fetch job status');
        setLoading(false);
      }
    };

    fetchJobStatus();
    interval = setInterval(fetchJobStatus, 3000); // Poll every 3 seconds

    return () => clearInterval(interval);
  }, [jobId]);

  if (loading) {
    return (
      <div className="job-status">
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading job status...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="job-status">
        <div className="error">
          <p>⚠️ {error}</p>
        </div>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="job-status">
        <div className="error">
          <p>Job not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="job-status">
      <h2>Transcription Status</h2>
      
      <div className={`status-badge ${job.status}`}>
        {job.status === 'pending' && '⏳ PENDING'}
        {job.status === 'processing' && '⚙️ PROCESSING'}
        {job.status === 'completed' && '✅ COMPLETED'}
        {job.status === 'failed' && '❌ FAILED'}
      </div>

      {job.status === 'processing' && (
        <div className="processing">
          <div className="spinner"></div>
          <p>Processing your audio... This may take a few minutes.</p>
        </div>
      )}

      {job.status === 'completed' && job.lyrics && job.chords && (
        <div className="results">
          <div className="lyrics-section">
            <h3>📝 Lyrics</h3>
            <div className="lyrics-content">
              {job.lyrics.text || 'No lyrics detected'}
            </div>
          </div>

          <div className="chords-section">
            <h3>🎸 Chord Progression</h3>
            <div className="chords-content">
              {job.chords && job.chords.length > 0 ? (
                job.chords.map((chord, idx) => (
                  <div key={idx} className="chord-item">
                    <span className="chord-name">{chord.name}</span>
                    <span className="chord-time">{chord.timestamp}s</span>
                  </div>
                ))
              ) : (
                <p>No chords detected</p>
              )}
            </div>
          </div>

          <button className="download-btn">
            💾 Download Results
          </button>
        </div>
      )}

      {job.status === 'failed' && (
        <div className="error">
          <p>Transcription failed: {job.errorMessage || 'Unknown error'}</p>
          <button onClick={() => window.location.reload()} className="retry-btn">
            🔄 Try Again
          </button>
        </div>
      )}
    </div>
  );
}

export default JobStatus;

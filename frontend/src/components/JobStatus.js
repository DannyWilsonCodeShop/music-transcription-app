import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './JobStatus.css';

// API endpoint from the new pipeline
const API_ENDPOINT = process.env.REACT_APP_API_ENDPOINT || 'https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com';

function JobStatus({ jobId }) {
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let interval;

    const fetchJobStatus = async () => {
      try {
        const response = await axios.get(`${API_ENDPOINT}/jobs/${jobId}`);
        setJob(response.data);
        setLoading(false);
        setError(null);

        // Stop polling if job is completed or failed
        if (response.data.status === 'COMPLETED' || response.data.status === 'FAILED') {
          clearInterval(interval);
        }
      } catch (err) {
        console.error('Error fetching job status:', err);
        setError(err.response?.data?.error || err.message || 'Failed to fetch job status');
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

  const status = job.status?.toLowerCase() || 'pending';
  const progress = job.progress || 0;

  return (
    <div className="job-status">
      <h2>Transcription Status</h2>
      
      <div className={`status-badge ${status}`}>
        {status === 'uploading' && '⏳ UPLOADING'}
        {status === 'processing' && '⚙️ PROCESSING'}
        {status === 'completed' && '✅ COMPLETED'}
        {status === 'failed' && '❌ FAILED'}
      </div>

      {progress > 0 && progress < 100 && (
        <div className="progress-section">
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress}%` }} />
          </div>
          <p>{progress}% complete</p>
        </div>
      )}

      {status === 'processing' && (
        <div className="processing">
          <div className="spinner"></div>
          <p>Processing your audio... This may take a few minutes.</p>
          <p className="processing-note">
            We're analyzing the audio with enhanced chord detection (84 templates) 
            and bass-weighted key detection for professional accuracy.
          </p>
        </div>
      )}

      {status === 'completed' && job.chordsData && (
        <div className="results">
          <div className="song-info">
            <h3>🎵 Song Information</h3>
            <div className="info-grid">
              <div className="info-item">
                <span className="label">Key:</span>
                <span className="value">{job.chordsData.key} {job.chordsData.mode}</span>
              </div>
              <div className="info-item">
                <span className="label">Tempo:</span>
                <span className="value">{job.chordsData.tempo} BPM</span>
              </div>
              <div className="info-item">
                <span className="label">Time Signature:</span>
                <span className="value">{job.chordsData.timeSignature}</span>
              </div>
              <div className="info-item">
                <span className="label">Duration:</span>
                <span className="value">{job.chordsData.duration}s</span>
              </div>
              <div className="info-item">
                <span className="label">Total Chords:</span>
                <span className="value">{job.chordsData.totalChords}</span>
              </div>
              <div className="info-item">
                <span className="label">Model:</span>
                <span className="value">{job.chordsData.model}</span>
              </div>
            </div>
          </div>

          <div className="chords-section">
            <h3>🎸 Chord Progression</h3>
            <div className="chords-content">
              {job.chordsData.chords && job.chordsData.chords.length > 0 ? (
                job.chordsData.chords.map((chord, idx) => (
                  <div key={idx} className="chord-item">
                    <span className="chord-name">{chord.chord}</span>
                    <span className="chord-time">{chord.start}s - {chord.end}s</span>
                    <span className="chord-confidence">({(chord.confidence * 100).toFixed(0)}%)</span>
                  </div>
                ))
              ) : (
                <p>No chords detected</p>
              )}
            </div>
          </div>

          {job.chordsData.songStructure && job.chordsData.songStructure.length > 0 && (
            <div className="structure-section">
              <h3>🎼 Song Structure</h3>
              <div className="structure-content">
                {job.chordsData.songStructure.map((section, idx) => (
                  <div key={idx} className="structure-item">
                    <span className="section-label">{section.label}</span>
                    <span className="section-time">
                      {section.start ? `${section.start}s - ${section.end}s` : 
                       `Measures ${section.measureStart}-${section.measureEnd}`}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <button className="download-btn" onClick={() => alert('PDF download coming soon!')}>
            💾 Download Chord Sheet (PDF)
          </button>
        </div>
      )}

      {status === 'failed' && (
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

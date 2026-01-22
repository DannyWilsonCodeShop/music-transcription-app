import React, { useState } from 'react';
import { API } from 'aws-amplify';
import './YouTubeInput.css';

function YouTubeInput({ onJobCreated }) {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!url) return;

    setLoading(true);
    setError(null);

    try {
      const response = await API.post('transcriptionAPI', '/transcribe/youtube', {
        body: {
          youtubeUrl: url,
          userId: 'guest' // Replace with actual user ID from Cognito
        }
      });

      onJobCreated(response.jobId);
      setUrl('');
      
    } catch (err) {
      console.error('Error:', err);
      setError(err.message || 'Failed to process YouTube link. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="youtube-input">
      <form onSubmit={handleSubmit}>
        <div className="input-group">
          <div className="input-icon">🎬</div>
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://www.youtube.com/watch?v=..."
            required
            disabled={loading}
            className="youtube-url-input"
          />
        </div>
        <button 
          type="submit" 
          disabled={loading || !url}
          className="submit-button"
        >
          {loading ? (
            <>
              <span className="button-spinner"></span>
              Processing...
            </>
          ) : (
            <>
              🎵 Transcribe
            </>
          )}
        </button>
      </form>
      <p className="hint">Paste a YouTube music video URL to extract lyrics and chords</p>
      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}
    </div>
  );
}

export default YouTubeInput;

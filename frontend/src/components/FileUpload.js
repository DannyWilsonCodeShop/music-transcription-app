import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import './FileUpload.css';

// API endpoint from the new pipeline
const API_ENDPOINT = process.env.REACT_APP_API_ENDPOINT || 'https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com';

function FileUpload({ onJobCreated }) {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);

  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setUploading(true);
    setProgress(0);
    setError(null);

    try {
      // Request upload URL from new API
      const response = await axios.post(`${API_ENDPOINT}/upload`, {
        filename: file.name,
        contentType: file.type,
        userId: 'guest'
      });

      const { jobId, uploadUrl } = response.data;

      // Upload file to S3 using presigned URL
      await axios.put(uploadUrl, file, {
        headers: {
          'Content-Type': file.type
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setProgress(percentCompleted);
        }
      });

      onJobCreated(jobId);
      setUploading(false);
      
    } catch (err) {
      console.error('Upload error:', err);
      setError(err.response?.data?.error || err.message || 'Upload failed. Please try again.');
      setUploading(false);
    }
  }, [onJobCreated]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/*': ['.mp3', '.wav', '.m4a', '.flac', '.ogg']
    },
    maxSize: 50 * 1024 * 1024, // 50MB
    multiple: false,
    disabled: uploading
  });

  return (
    <div className="file-upload">
      <div 
        {...getRootProps()} 
        className={`dropzone ${isDragActive ? 'active' : ''} ${uploading ? 'uploading' : ''}`}
      >
        <input {...getInputProps()} />
        {uploading ? (
          <div className="upload-progress">
            <div className="spinner"></div>
            <p>Uploading... {progress}%</p>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress}%` }} />
            </div>
          </div>
        ) : (
          <div className="dropzone-content">
            <div className="upload-icon">📁</div>
            <p className="dropzone-text">
              {isDragActive 
                ? 'Drop your audio file here' 
                : 'Drag & drop an audio file here, or click to select'}
            </p>
            <p className="file-types">Supported: MP3, WAV, M4A, FLAC, OGG (max 50MB)</p>
          </div>
        )}
      </div>
      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}
    </div>
  );
}

export default FileUpload;

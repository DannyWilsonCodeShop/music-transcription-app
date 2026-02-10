import { useState, useEffect, useCallback } from 'react';
import { getJobStatus, TranscriptionJob } from './services/transcriptionService';
import axios from 'axios';

const API_ENDPOINT = 'https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com';

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [jobId, setJobId] = useState<string | null>(null);
  const [job, setJob] = useState<TranscriptionJob | null>(null);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) return;
    const pollInterval = setInterval(async () => {
      const status = await getJobStatus(jobId);
      if (status) {
        setJob(status);
        if (status.status === 'COMPLETED') {
          clearInterval(pollInterval);
          setIsUploading(false);
          if (status.pdfUrl) {
            setPdfUrl(status.pdfUrl);
          }
        } else if (status.status === 'FAILED') {
          clearInterval(pollInterval);
          setIsUploading(false);
        }
      }
    }, 2000);
    return () => clearInterval(pollInterval);
  }, [jobId]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type.startsWith('audio/')) {
      setFile(droppedFile);
    } else {
      setError('Please drop an audio file (MP3, WAV, M4A, FLAC, OGG)');
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    
    setIsUploading(true);
    setError(null);
    setJob(null);
    setPdfUrl(null);
    setUploadProgress(0);
    
    try {
      console.log('Requesting upload URL for:', file.name, file.type);
      
      // Request upload URL
      const response = await axios.post(`${API_ENDPOINT}/upload`, {
        filename: file.name,
        contentType: file.type || 'audio/mpeg',
        userId: 'guest'
      });

      console.log('Upload URL response:', response.data);
      const { jobId: newJobId, uploadUrl } = response.data;
      setJobId(newJobId);

      console.log('Uploading file to S3...');
      // Upload file to S3 - presigned URL no longer requires specific Content-Type
      await axios.put(uploadUrl, file, {
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / (progressEvent.total || 1)
          );
          console.log('Upload progress:', percentCompleted + '%');
          setUploadProgress(percentCompleted);
        }
      });

      console.log('Upload complete!');
      setUploadProgress(100);
      
    } catch (error: any) {
      console.error('Upload failed:', error);
      console.error('Error response:', error.response?.data);
      setIsUploading(false);
      const errorMsg = error.response?.data?.error || error.message || 'Upload failed. Please try again.';
      setError(errorMsg);
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
          <h1 className="Cipher" style={{
            fontSize: '24px',
            fontWeight: 'bold',
            color: '#00ffff',
            textShadow: '0 0 10px #00ffff, 0 0 20px #00ffff, 0 0 30px #00ffff',
            marginBottom: '16px',
            letterSpacing: '2px'
          }}>
            Cipher
          </h1>
          <h1 style={{
            fontSize: '42px',
            fontWeight: '700',
            background: 'linear-gradient(135deg, #a78bfa 0%, #818cf8 50%, #6366f1 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            marginBottom: '12px',
            letterSpacing: '-0.5px',
            fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
            position: 'relative' as const,
            textShadow: '0 0 40px rgba(139, 92, 246, 0.3)',
            filter: 'drop-shadow(0 4px 12px rgba(99, 102, 241, 0.2))'
          }}>
            Music Transcription App
          </h1>
          <p style={{ color: '#9ca3af', fontSize: '18px' }}>
            Upload your audio file to extract chords and lyrics
          </p>
        </div>

        {/* File Upload Area */}
        {!jobId && (
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            style={{
              padding: '32px',
              backgroundColor: isDragging ? '#f3f4f6' : 'white',
              borderRadius: '16px',
              boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
              border: isDragging ? '2px dashed #9333ea' : '2px dashed #e5e7eb',
              textAlign: 'center',
              cursor: 'pointer',
              transition: 'all 0.3s'
            }}
            onClick={() => document.getElementById('fileInput')?.click()}
          >
            <input
              id="fileInput"
              type="file"
              accept="audio/*"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />
            
            {!file ? (
              <>
                <div style={{ fontSize: '48px', marginBottom: '12px' }}>📁</div>
                <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#1f2937', marginBottom: '6px' }}>
                  {isDragging ? 'Drop your file here' : 'Drag & drop your audio file'}
                </h3>
                <p style={{ color: '#6b7280', marginBottom: '12px', fontSize: '14px' }}>
                  or click to browse
                </p>
                <p style={{ color: '#9ca3af', fontSize: '13px' }}>
                  Supported: MP3, WAV, M4A, FLAC, OGG (max 50MB)
                </p>
              </>
            ) : (
              <>
                <div style={{ fontSize: '48px', marginBottom: '12px' }}>🎵</div>
                <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#1f2937', marginBottom: '6px' }}>
                  {file.name}
                </h3>
                <p style={{ color: '#6b7280', marginBottom: '12px', fontSize: '14px' }}>
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
                <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleUpload();
                    }}
                    disabled={isUploading}
                    style={{
                      padding: '12px 32px',
                      background: 'linear-gradient(to right, #9333ea, #2563eb)',
                      color: 'white',
                      fontWeight: '600',
                      borderRadius: '12px',
                      border: 'none',
                      cursor: isUploading ? 'not-allowed' : 'pointer',
                      opacity: isUploading ? 0.5 : 1,
                      fontSize: '16px'
                    }}
                  >
                    {isUploading ? 'Uploading...' : 'Upload & Process'}
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setFile(null);
                    }}
                    disabled={isUploading}
                    style={{
                      padding: '12px 24px',
                      backgroundColor: '#e5e7eb',
                      color: '#374151',
                      fontWeight: '500',
                      borderRadius: '12px',
                      border: 'none',
                      cursor: isUploading ? 'not-allowed' : 'pointer',
                      opacity: isUploading ? 0.5 : 1
                    }}
                  >
                    Cancel
                  </button>
                </div>
              </>
            )}
          </div>
        )}

        {/* Upload Progress */}
        {isUploading && uploadProgress < 100 && (
          <div style={{
            marginTop: '24px',
            padding: '24px',
            backgroundColor: 'white',
            borderRadius: '16px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
            border: '1px solid #e5e7eb'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
              <span style={{ color: '#374151', fontWeight: '500' }}>Uploading...</span>
              <span style={{ color: '#9333ea', fontWeight: '600' }}>{uploadProgress}%</span>
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
                width: `${uploadProgress}%`,
                transition: 'width 0.3s'
              }}/>
            </div>
          </div>
        )}

        {/* Processing Progress */}
        {isUploading && job && uploadProgress === 100 && (
          <div style={{
            marginTop: '24px',
            padding: '24px',
            backgroundColor: 'white',
            borderRadius: '16px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
            border: '1px solid #e5e7eb'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
              <span style={{ color: '#374151', fontWeight: '500' }}>
                {job.status === 'PROCESSING' ? 'Analyzing audio...' : 'Processing...'}
              </span>
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
            <p style={{ marginTop: '12px', fontSize: '14px', color: '#6b7280' }}>
              Enhanced chord detection with 84 templates and bass-weighted key detection
            </p>
          </div>
        )}

        {/* Error */}
        {error && (
          <div style={{
            marginTop: '24px',
            padding: '24px',
            background: 'linear-gradient(to right, #fef2f2, #fee2e2)',
            borderRadius: '16px',
            border: '1px solid #fca5a5'
          }}>
            <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#991b1b', marginBottom: '8px' }}>
              ❌ Error
            </h2>
            <p style={{ color: '#dc2626', marginBottom: '16px' }}>{error}</p>
            <button
              onClick={() => {
                setError(null);
                setFile(null);
                setJobId(null);
              }}
              style={{
                padding: '10px 20px',
                backgroundColor: '#dc2626',
                color: 'white',
                borderRadius: '8px',
                border: 'none',
                cursor: 'pointer',
                fontWeight: '500'
              }}
            >
              Try Again
            </button>
          </div>
        )}

        {/* Job Failed */}
        {job?.status === 'FAILED' && (
          <div style={{
            marginTop: '24px',
            padding: '24px',
            background: 'linear-gradient(to right, #fef2f2, #fee2e2)',
            borderRadius: '16px',
            border: '1px solid #fca5a5'
          }}>
            <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#991b1b', marginBottom: '8px' }}>
              ❌ Transcription Failed
            </h2>
            <p style={{ color: '#dc2626', marginBottom: '8px' }}>{job.errorMessage || 'An unknown error occurred'}</p>
            <button
              onClick={() => {
                setJob(null);
                setJobId(null);
                setError(null);
                setIsUploading(false);
                setFile(null);
              }}
              style={{
                padding: '10px 20px',
                backgroundColor: '#dc2626',
                color: 'white',
                borderRadius: '8px',
                border: 'none',
                cursor: 'pointer',
                fontWeight: '500'
              }}
            >
              Try Again
            </button>
          </div>
        )}

        {/* Results */}
        {job?.status === 'COMPLETED' && job.chordsData && (
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
            
            {/* Chord Data Display */}
            {job.chordsData && (
              <div style={{ marginTop: '24px' }}>
                {/* Key and Tempo */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: '16px',
                  marginBottom: '24px'
                }}>
                  <div style={{
                    padding: '16px',
                    backgroundColor: 'white',
                    borderRadius: '12px',
                    border: '1px solid #d1fae5'
                  }}>
                    <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '4px' }}>Key</div>
                    <div style={{ fontSize: '24px', fontWeight: '700', color: '#166534' }}>
                      {job.chordsData.key} {job.chordsData.mode}
                    </div>
                    <div style={{ fontSize: '12px', color: '#9ca3af' }}>
                      Confidence: {(job.chordsData.keyConfidence * 100).toFixed(0)}%
                    </div>
                  </div>
                  
                  <div style={{
                    padding: '16px',
                    backgroundColor: 'white',
                    borderRadius: '12px',
                    border: '1px solid #d1fae5'
                  }}>
                    <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '4px' }}>Tempo</div>
                    <div style={{ fontSize: '24px', fontWeight: '700', color: '#166534' }}>
                      {job.chordsData.tempo} BPM
                    </div>
                    <div style={{ fontSize: '12px', color: '#9ca3af' }}>
                      {job.chordsData.timeSignature}
                    </div>
                  </div>
                  
                  <div style={{
                    padding: '16px',
                    backgroundColor: 'white',
                    borderRadius: '12px',
                    border: '1px solid #d1fae5'
                  }}>
                    <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '4px' }}>Duration</div>
                    <div style={{ fontSize: '24px', fontWeight: '700', color: '#166534' }}>
                      {Math.floor(job.chordsData.duration / 60)}:{String(Math.floor(job.chordsData.duration % 60)).padStart(2, '0')}
                    </div>
                    <div style={{ fontSize: '12px', color: '#9ca3af' }}>
                      {job.chordsData.totalChords} chords
                    </div>
                  </div>
                </div>

                {/* Song Structure (MSAF Results) */}
                {job.chordsData.songStructure && job.chordsData.songStructure.length > 0 && (
                  <div style={{
                    marginBottom: '24px',
                    padding: '20px',
                    backgroundColor: 'white',
                    borderRadius: '12px',
                    border: '1px solid #d1fae5'
                  }}>
                    <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#166534', marginBottom: '16px' }}>
                      🎵 Song Structure
                    </h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      {job.chordsData.songStructure.map((section: any, idx: number) => (
                        <div key={idx} style={{
                          padding: '12px 16px',
                          backgroundColor: '#f9fafb',
                          borderRadius: '8px',
                          border: '1px solid #e5e7eb',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center'
                        }}>
                          <div>
                            <span style={{ 
                              fontSize: '16px', 
                              fontWeight: '600', 
                              color: '#1f2937',
                              marginRight: '12px'
                            }}>
                              {section.label}
                            </span>
                            <span style={{ fontSize: '14px', color: '#6b7280' }}>
                              {section.start?.toFixed(1)}s - {section.end?.toFixed(1)}s
                            </span>
                          </div>
                          <div style={{ fontSize: '14px', color: '#9ca3af' }}>
                            {section.duration?.toFixed(1)}s
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Pattern Analysis (Nashville Numbers) */}
                {job.chordsData.patternAnalysis && job.chordsData.patternAnalysis.length > 0 && (
                  <div style={{
                    marginBottom: '24px',
                    padding: '20px',
                    backgroundColor: 'white',
                    borderRadius: '12px',
                    border: '1px solid #d1fae5'
                  }}>
                    <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#166534', marginBottom: '16px' }}>
                      📊 Repeating Patterns
                    </h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                      {job.chordsData.patternAnalysis.slice(0, 5).map((pattern: any, idx: number) => (
                        <div key={idx} style={{
                          padding: '16px',
                          backgroundColor: '#f9fafb',
                          borderRadius: '8px',
                          border: '1px solid #e5e7eb'
                        }}>
                          <div style={{ 
                            fontSize: '14px', 
                            fontWeight: '600', 
                            color: '#6b7280',
                            marginBottom: '8px'
                          }}>
                            Pattern {pattern.patternNumber}
                          </div>
                          <div style={{ 
                            fontSize: '18px', 
                            fontWeight: '600', 
                            color: '#1f2937',
                            marginBottom: '4px',
                            fontFamily: 'monospace'
                          }}>
                            {pattern.progression.join(' → ')}
                          </div>
                          <div style={{ 
                            fontSize: '16px', 
                            color: '#9333ea',
                            marginBottom: '8px',
                            fontFamily: 'monospace',
                            fontStyle: 'italic'
                          }}>
                            ({pattern.nashvilleProgression?.join(' → ') || 'N/A'})
                          </div>
                          <div style={{ fontSize: '14px', color: '#6b7280' }}>
                            {pattern.length} chords • Repeats {pattern.occurrences} times
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* First 20 Chords */}
                {job.chordsData.chords && job.chordsData.chords.length > 0 && (
                  <div style={{
                    marginBottom: '24px',
                    padding: '20px',
                    backgroundColor: 'white',
                    borderRadius: '12px',
                    border: '1px solid #d1fae5'
                  }}>
                    <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#166534', marginBottom: '16px' }}>
                      🎸 Chord Progression (First 20)
                    </h3>
                    <div style={{ 
                      display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fill, minmax(100px, 1fr))',
                      gap: '8px'
                    }}>
                      {job.chordsData.chords.slice(0, 20).map((chord: any, idx: number) => (
                        <div key={idx} style={{
                          padding: '12px',
                          backgroundColor: '#f9fafb',
                          borderRadius: '8px',
                          border: '1px solid #e5e7eb',
                          textAlign: 'center'
                        }}>
                          <div style={{ 
                            fontSize: '18px', 
                            fontWeight: '700', 
                            color: '#1f2937',
                            marginBottom: '4px'
                          }}>
                            {chord.chord}
                          </div>
                          <div style={{ fontSize: '12px', color: '#9ca3af' }}>
                            {chord.start?.toFixed(1)}s
                          </div>
                        </div>
                      ))}
                    </div>
                    {job.chordsData.chords.length > 20 && (
                      <div style={{ 
                        marginTop: '12px', 
                        fontSize: '14px', 
                        color: '#6b7280',
                        textAlign: 'center'
                      }}>
                        ... and {job.chordsData.chords.length - 20} more chords
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
            
            {pdfUrl && (
              <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
                <a 
                  href={pdfUrl}
                  download={`${job.title || 'transcription'}.pdf`}
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
                <a 
                  href={pdfUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: 'inline-block',
                    padding: '10px 20px',
                    backgroundColor: '#2563eb',
                    color: 'white',
                    borderRadius: '8px',
                    textDecoration: 'none',
                    fontWeight: '500'
                  }}
                >
                  View PDF
                </a>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;

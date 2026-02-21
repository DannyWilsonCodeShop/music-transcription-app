import { useState, useEffect, useCallback } from 'react';
import { getJobStatus, TranscriptionJob } from './services/transcriptionService';
import { DownbeatConfirmation } from './components/DownbeatConfirmation';
import axios from 'axios';

const API_ENDPOINT = 'https://l43ftjo75d.execute-api.us-east-1.amazonaws.com';
const UPLOAD_API_ENDPOINT = 'https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com';

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [jobId, setJobId] = useState<string | null>(null);
  const [job, setJob] = useState<TranscriptionJob | null>(null);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showDownbeatConfirmation, setShowDownbeatConfirmation] = useState(false);
  const [downbeatData, setDownbeatData] = useState<any>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

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

  const handleDownbeatConfirm = async (downbeat: number, timeSignature: string) => {
    if (!jobId) return;
    
    try {
      console.log('Confirming downbeat:', downbeat, timeSignature);
      await axios.post(`${API_ENDPOINT}/api/confirm-downbeat`, {
        jobId,
        downbeat,
        timeSignature
      });
      
      setShowDownbeatConfirmation(false);
      console.log('Downbeat confirmed, chord detection will start automatically');
    } catch (error: any) {
      console.error('Failed to confirm downbeat:', error);
      setError('Failed to confirm downbeat. Please try again.');
    }
  };

  const handleDownbeatCancel = () => {
    setShowDownbeatConfirmation(false);
    // Continue with auto-detected downbeat
    console.log('User cancelled downbeat confirmation, using auto-detected value');
  };

  const pollForDownbeatResults = async (jobId: string): Promise<any> => {
    const maxAttempts = 60; // 60 seconds
    const pollInterval = 1000; // 1 second
    
    for (let i = 0; i < maxAttempts; i++) {
      try {
        const status = await getJobStatus(jobId);
        
        if (status.downbeatData && status.downbeatStatus === 'COMPLETED') {
          return status.downbeatData;
        }
        
        if (status.downbeatStatus === 'FAILED') {
          throw new Error('Downbeat detection failed');
        }
        
        // Wait before next poll
        await new Promise(resolve => setTimeout(resolve, pollInterval));
      } catch (error) {
        console.error('Error polling for downbeat:', error);
        throw error;
      }
    }
    
    throw new Error('Downbeat detection timed out');
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
      const response = await axios.post(`${UPLOAD_API_ENDPOINT}/upload`, {
        filename: file.name,
        contentType: file.type || 'audio/mpeg',
        userId: 'guest'
      });

      console.log('Upload URL response:', response.data);
      const { jobId: newJobId, uploadUrl } = response.data;
      setJobId(newJobId);

      console.log('Uploading file to S3...');
      
      // Simulate progress for UX (actual upload happens in background)
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 95) {
            clearInterval(progressInterval);
            return 95;
          }
          return prev + 5;
        });
      }, 100);

      try {
        // Upload to S3 with explicit Content-Type header to match presigned URL
        const contentType = file.type || 'audio/mpeg';
        
        const response = await fetch(uploadUrl, {
          method: 'PUT',
          headers: {
            'Content-Type': contentType
          },
          body: file
        });

        clearInterval(progressInterval);

        if (!response.ok) {
          const errorText = await response.text();
          console.error('S3 upload failed:', response.status, errorText);
          throw new Error(`Upload failed: ${errorText || response.statusText}`);
        }

        console.log('Upload complete!');
        setUploadProgress(100);
      } catch (error) {
        clearInterval(progressInterval);
        throw error;
      }

      console.log('Upload complete!');
      setUploadProgress(100);
      
      // Detect downbeat after upload
      console.log('Detecting downbeat...');
      try {
        const downbeatResponse = await axios.post(`${API_ENDPOINT}/api/detect-downbeat`, {
          jobId: newJobId,
          bucket: 'chordscout-audio-dev-090130568474',
          key: `uploads/${newJobId}/${file.name}`
        });
        
        console.log('Downbeat detection started (async):', downbeatResponse.data);
        
        // Poll for downbeat results
        console.log('Polling for downbeat results...');
        const downbeatData = await pollForDownbeatResults(newJobId);
        
        if (downbeatData) {
          console.log('Downbeat detection complete:', downbeatData);
          
          // Store audio URL for playback in confirmation modal
          setAudioUrl(uploadUrl.split('?')[0]); // Remove query params to get clean URL
          
          setDownbeatData({
            downbeat: downbeatData.detectedDownbeat,
            tempo: downbeatData.tempo,
            timeSignature: downbeatData.timeSignature,
            beatTimes: downbeatData.beatTimes,
            confidence: downbeatData.confidence
          });
          
          setShowDownbeatConfirmation(true);
        }
      } catch (downbeatError: any) {
        console.error('Downbeat detection failed:', downbeatError);
        // Continue without downbeat confirmation (fallback to auto-detection)
        console.log('Continuing without downbeat confirmation');
      }
      
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
              background: isDragging 
                ? 'linear-gradient(135deg, rgba(147, 51, 234, 0.15) 0%, rgba(99, 102, 241, 0.15) 100%)'
                : 'rgba(255, 255, 255, 0.05)',
              backdropFilter: 'blur(10px)',
              borderRadius: '20px',
              boxShadow: isDragging 
                ? '0 8px 32px rgba(147, 51, 234, 0.3), inset 0 0 0 1px rgba(147, 51, 234, 0.3)'
                : '0 8px 32px rgba(0, 0, 0, 0.3), inset 0 0 0 1px rgba(255, 255, 255, 0.1)',
              border: isDragging ? '2px dashed rgba(147, 51, 234, 0.5)' : '2px dashed rgba(255, 255, 255, 0.1)',
              textAlign: 'center',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              position: 'relative' as const,
              overflow: 'hidden'
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
                <div style={{ 
                  fontSize: '48px', 
                  marginBottom: '12px',
                  filter: 'drop-shadow(0 0 20px rgba(147, 51, 234, 0.3))'
                }}>
                  📁
                </div>
                <h3 style={{ 
                  fontSize: '18px', 
                  fontWeight: '600', 
                  color: '#ffffff', 
                  marginBottom: '6px',
                  textShadow: '0 2px 10px rgba(0, 0, 0, 0.3)'
                }}>
                  {isDragging ? 'Drop your file here' : 'Drag & drop your audio file'}
                </h3>
                <p style={{ 
                  color: 'rgba(255, 255, 255, 0.7)', 
                  marginBottom: '12px', 
                  fontSize: '14px' 
                }}>
                  or click to browse
                </p>
                <p style={{ 
                  color: 'rgba(255, 255, 255, 0.5)', 
                  fontSize: '13px' 
                }}>
                  Supported: MP3, WAV, M4A, FLAC, OGG (max 50MB)
                </p>
              </>
            ) : (
              <>
                <div style={{ 
                  fontSize: '48px', 
                  marginBottom: '12px',
                  filter: 'drop-shadow(0 0 20px rgba(99, 102, 241, 0.5))'
                }}>
                  🎵
                </div>
                <h3 style={{ 
                  fontSize: '18px', 
                  fontWeight: '600', 
                  color: '#ffffff', 
                  marginBottom: '6px',
                  textShadow: '0 2px 10px rgba(0, 0, 0, 0.3)'
                }}>
                  {file.name}
                </h3>
                <p style={{ 
                  color: 'rgba(255, 255, 255, 0.7)', 
                  marginBottom: '12px', 
                  fontSize: '14px' 
                }}>
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
                      background: 'linear-gradient(135deg, #9333ea 0%, #6366f1 100%)',
                      color: 'white',
                      fontWeight: '600',
                      borderRadius: '12px',
                      border: 'none',
                      cursor: isUploading ? 'not-allowed' : 'pointer',
                      opacity: isUploading ? 0.5 : 1,
                      fontSize: '16px',
                      boxShadow: '0 4px 15px rgba(147, 51, 234, 0.4)',
                      transition: 'all 0.3s ease',
                      transform: isUploading ? 'scale(0.98)' : 'scale(1)'
                    }}
                    onMouseEnter={(e) => {
                      if (!isUploading) {
                        e.currentTarget.style.boxShadow = '0 6px 20px rgba(147, 51, 234, 0.6)';
                        e.currentTarget.style.transform = 'scale(1.02)';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isUploading) {
                        e.currentTarget.style.boxShadow = '0 4px 15px rgba(147, 51, 234, 0.4)';
                        e.currentTarget.style.transform = 'scale(1)';
                      }
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
                      background: 'rgba(255, 255, 255, 0.1)',
                      backdropFilter: 'blur(10px)',
                      color: 'rgba(255, 255, 255, 0.9)',
                      fontWeight: '500',
                      borderRadius: '12px',
                      border: '1px solid rgba(255, 255, 255, 0.2)',
                      cursor: isUploading ? 'not-allowed' : 'pointer',
                      opacity: isUploading ? 0.5 : 1,
                      transition: 'all 0.3s ease'
                    }}
                    onMouseEnter={(e) => {
                      if (!isUploading) {
                        e.currentTarget.style.background = 'rgba(255, 255, 255, 0.15)';
                        e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.3)';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isUploading) {
                        e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)';
                        e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.2)';
                      }
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
            background: 'rgba(255, 255, 255, 0.05)',
            backdropFilter: 'blur(10px)',
            borderRadius: '20px',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3), inset 0 0 0 1px rgba(255, 255, 255, 0.1)',
            border: '1px solid rgba(255, 255, 255, 0.1)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
              <span style={{ color: 'rgba(255, 255, 255, 0.9)', fontWeight: '500' }}>Uploading...</span>
              <span style={{ 
                color: '#a78bfa', 
                fontWeight: '600',
                textShadow: '0 0 10px rgba(167, 139, 250, 0.5)'
              }}>
                {uploadProgress}%
              </span>
            </div>
            <div style={{
              width: '100%',
              height: '10px',
              background: 'rgba(255, 255, 255, 0.1)',
              borderRadius: '999px',
              overflow: 'hidden',
              boxShadow: 'inset 0 2px 4px rgba(0, 0, 0, 0.3)'
            }}>
              <div style={{
                height: '100%',
                background: 'linear-gradient(90deg, #9333ea 0%, #6366f1 50%, #8b5cf6 100%)',
                borderRadius: '999px',
                width: `${uploadProgress}%`,
                transition: 'width 0.3s ease',
                boxShadow: '0 0 10px rgba(147, 51, 234, 0.5)',
                position: 'relative' as const
              }}/>
            </div>
          </div>
        )}

        {/* Processing Progress */}
        {isUploading && job && uploadProgress === 100 && (
          <div style={{
            marginTop: '24px',
            padding: '24px',
            background: 'rgba(255, 255, 255, 0.05)',
            backdropFilter: 'blur(10px)',
            borderRadius: '20px',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3), inset 0 0 0 1px rgba(255, 255, 255, 0.1)',
            border: '1px solid rgba(255, 255, 255, 0.1)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
              <span style={{ color: 'rgba(255, 255, 255, 0.9)', fontWeight: '500' }}>
                {job.status === 'PROCESSING' ? 'Analyzing audio...' : 'Processing...'}
              </span>
              <span style={{ 
                color: '#a78bfa', 
                fontWeight: '600',
                textShadow: '0 0 10px rgba(167, 139, 250, 0.5)'
              }}>
                {job.progress || 0}%
              </span>
            </div>
            <div style={{
              width: '100%',
              height: '10px',
              background: 'rgba(255, 255, 255, 0.1)',
              borderRadius: '999px',
              overflow: 'hidden',
              boxShadow: 'inset 0 2px 4px rgba(0, 0, 0, 0.3)'
            }}>
              <div style={{
                height: '100%',
                background: 'linear-gradient(90deg, #9333ea 0%, #6366f1 50%, #8b5cf6 100%)',
                borderRadius: '999px',
                width: `${job.progress || 0}%`,
                transition: 'width 0.5s ease',
                boxShadow: '0 0 10px rgba(147, 51, 234, 0.5)'
              }}/>
            </div>
            <p style={{ 
              marginTop: '12px', 
              fontSize: '14px', 
              color: 'rgba(255, 255, 255, 0.6)',
              textAlign: 'center'
            }}>
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
            
            {/* Process Another File Button - Top */}
            <button
              onClick={() => {
                setFile(null);
                setJobId(null);
                setJob(null);
                setError(null);
                setIsUploading(false);
                setPdfUrl(null);
                setUploadProgress(0);
                setShowDownbeatConfirmation(false);
                setDownbeatData(null);
                setAudioUrl(null);
              }}
              style={{
                marginBottom: '24px',
                padding: '12px 24px',
                background: 'linear-gradient(135deg, #9333ea 0%, #6366f1 100%)',
                color: 'white',
                fontWeight: '600',
                borderRadius: '12px',
                border: 'none',
                cursor: 'pointer',
                fontSize: '16px',
                boxShadow: '0 4px 15px rgba(147, 51, 234, 0.4)',
                transition: 'all 0.3s ease',
                width: '100%'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.boxShadow = '0 6px 20px rgba(147, 51, 234, 0.6)';
                e.currentTarget.style.transform = 'scale(1.02)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.boxShadow = '0 4px 15px rgba(147, 51, 234, 0.4)';
                e.currentTarget.style.transform = 'scale(1)';
              }}
            >
              ← Process Another File
            </button>
            
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
                      Confidence: {(parseFloat(job.chordsData.keyConfidence) * 100).toFixed(0)}%
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
                              {parseFloat(section.start || 0).toFixed(1)}s - {parseFloat(section.end || 0).toFixed(1)}s
                            </span>
                          </div>
                          <div style={{ fontSize: '14px', color: '#9ca3af' }}>
                            {parseFloat(section.duration || 0).toFixed(1)}s
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

                {/* Section-Based Chord Sheet */}
                {job.chordsData.chords && job.chordsData.chords.length > 0 && (
                  <div style={{
                    marginBottom: '24px',
                    padding: '20px',
                    backgroundColor: 'white',
                    borderRadius: '12px',
                    border: '1px solid #d1fae5'
                  }}>
                    <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#166534', marginBottom: '16px' }}>
                      🎸 Chord Sheet
                    </h3>
                    {(() => {
                      // Group chords by song sections
                      const sections = job.chordsData.songStructure || [];
                      const chords = job.chordsData.chords;
                      
                      if (sections.length === 0) {
                        // No sections detected, display all chords in one section
                        const chordLines = [];
                        for (let i = 0; i < chords.length; i += 16) {
                          chordLines.push(chords.slice(i, i + 16));
                        }
                        
                        return (
                          <div style={{ marginBottom: '20px' }}>
                            <div style={{
                              fontSize: '16px',
                              fontWeight: '600',
                              color: '#166534',
                              marginBottom: '12px',
                              textTransform: 'uppercase',
                              letterSpacing: '0.5px'
                            }}>
                              Full Song
                            </div>
                            {chordLines.map((line, lineIdx) => (
                              <div key={lineIdx} style={{
                                display: 'flex',
                                gap: '4px',
                                marginBottom: '8px',
                                fontFamily: 'monospace',
                                fontSize: '16px',
                                flexWrap: 'wrap'
                              }}>
                                {line.map((chord: any, chordIdx: number) => (
                                  <span key={chordIdx}>
                                    <span style={{
                                      padding: '4px 8px',
                                      backgroundColor: '#f9fafb',
                                      borderRadius: '4px',
                                      border: '1px solid #e5e7eb',
                                      fontWeight: '600',
                                      color: '#1f2937'
                                    }}>
                                      {chord.chord}
                                    </span>
                                    {chordIdx < line.length - 1 && chordIdx % 4 === 3 && (
                                      <span style={{ margin: '0 8px', color: '#9ca3af' }}>|</span>
                                    )}
                                  </span>
                                ))}
                              </div>
                            ))}
                          </div>
                        );
                      }
                      
                      // Group chords by sections
                      return sections.map((section: any, sectionIdx: number) => {
                        const sectionStart = parseFloat(section.start || 0);
                        const sectionEnd = parseFloat(section.end || 0);
                        
                        // Find chords within this section's time range
                        const sectionChords = chords.filter((chord: any) => {
                          const chordTime = parseFloat(chord.start || 0);
                          return chordTime >= sectionStart && chordTime < sectionEnd;
                        });
                        
                        if (sectionChords.length === 0) return null;
                        
                        // Split into lines of up to 16 chords
                        const chordLines = [];
                        for (let i = 0; i < sectionChords.length; i += 16) {
                          chordLines.push(sectionChords.slice(i, i + 16));
                        }
                        
                        return (
                          <div key={sectionIdx} style={{ marginBottom: '20px' }}>
                            <div style={{
                              fontSize: '16px',
                              fontWeight: '600',
                              color: '#166534',
                              marginBottom: '8px',
                              textTransform: 'uppercase',
                              letterSpacing: '0.5px'
                            }}>
                              {section.label} ({parseFloat(section.start || 0).toFixed(1)}s - {parseFloat(section.end || 0).toFixed(1)}s)
                            </div>
                            {chordLines.map((line, lineIdx) => (
                              <div key={lineIdx} style={{
                                display: 'flex',
                                gap: '4px',
                                marginBottom: '8px',
                                fontFamily: 'monospace',
                                fontSize: '16px',
                                flexWrap: 'wrap'
                              }}>
                                {line.map((chord: any, chordIdx: number) => (
                                  <span key={chordIdx}>
                                    <span style={{
                                      padding: '4px 8px',
                                      backgroundColor: '#f9fafb',
                                      borderRadius: '4px',
                                      border: '1px solid #e5e7eb',
                                      fontWeight: '600',
                                      color: '#1f2937'
                                    }}>
                                      {chord.chord}
                                    </span>
                                    {chordIdx < line.length - 1 && chordIdx % 4 === 3 && (
                                      <span style={{ margin: '0 8px', color: '#9ca3af' }}>|</span>
                                    )}
                                  </span>
                                ))}
                              </div>
                            ))}
                          </div>
                        );
                      });
                    })()}
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
      
      {/* Downbeat Confirmation Modal */}
      {showDownbeatConfirmation && downbeatData && audioUrl && (
        <DownbeatConfirmation
          audioUrl={audioUrl}
          detectedDownbeat={downbeatData.downbeat}
          detectedTempo={downbeatData.tempo}
          detectedTimeSignature={downbeatData.timeSignature}
          beatTimes={downbeatData.beatTimes}
          onConfirm={handleDownbeatConfirm}
          onCancel={handleDownbeatCancel}
        />
      )}
    </div>
  );
}

export default App;

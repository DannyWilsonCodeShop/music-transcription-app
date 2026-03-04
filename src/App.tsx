import { useState, useEffect, useCallback } from 'react';
import { getJobStatus, TranscriptionJob } from './services/transcriptionService';
import { DownbeatConfirmation } from './components/DownbeatConfirmation';
import { AnalysisOptionsModal, AnalysisOptions } from './components/AnalysisOptionsModal';
import LeadSheetDisplay from './components/LeadSheetDisplay';
import { BassNNSDisplay } from './components/BassNNSDisplay';
import axios from 'axios';

const API_ENDPOINT = 'https://l43ftjo75d.execute-api.us-east-1.amazonaws.com/dev';
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
  const [processingStartTime, setProcessingStartTime] = useState<number | null>(null);
  const [elapsedTime, setElapsedTime] = useState<number>(0);
  const [showDebugMode, setShowDebugMode] = useState(false);
  const [showAnalysisModal, setShowAnalysisModal] = useState(false);
  const [analysisOptions, setAnalysisOptions] = useState<AnalysisOptions | null>(null);

  // Timer effect - updates every second while processing
  useEffect(() => {
    if (!processingStartTime || job?.status === 'COMPLETED' || job?.status === 'FAILED') {
      return;
    }

    const interval = setInterval(() => {
      setElapsedTime(Math.floor((Date.now() - processingStartTime) / 1000));
    }, 1000);

    return () => clearInterval(interval);
  }, [processingStartTime, job?.status]);

  useEffect(() => {
    if (!jobId) {
      console.log('Polling effect: No jobId, skipping');
      return;
    }
    
    console.log('Starting polling for jobId:', jobId);
    let consecutiveErrors = 0;
    const MAX_ERRORS = 5;
    const POLL_TIMEOUT = 10 * 60 * 1000; // 10 minutes
    const startTime = Date.now();
    
    const pollInterval = setInterval(async () => {
      const elapsed = Date.now() - startTime;
      console.log(`Polling attempt for ${jobId} (elapsed: ${Math.floor(elapsed/1000)}s)`);
      
      // Check if we've exceeded the timeout
      if (elapsed > POLL_TIMEOUT) {
        clearInterval(pollInterval);
        setError('Processing timeout. The job may still be running. Please refresh to check status.');
        console.error('Polling timeout exceeded');
        return;
      }
      
      try {
        console.log('Calling getJobStatus...');
        const status = await getJobStatus(jobId);
        console.log('Poll result:', { 
          hasStatus: !!status, 
          status: status?.status, 
          progress: status?.progress,
          jobId, 
          consecutiveErrors 
        });
        
        if (status) {
          consecutiveErrors = 0; // Reset error counter on success
          setJob(status);
          console.log('Job status updated:', status.status, status.progress, status.statusMessage);
          
          if (status.status === 'COMPLETED') {
            console.log('Job completed!');
            clearInterval(pollInterval);
            setIsUploading(false);
            if (status.pdfUrl) {
              setPdfUrl(status.pdfUrl);
            }
          } else if (status.status === 'FAILED') {
            console.error('Job failed:', status.errorMessage);
            clearInterval(pollInterval);
            setIsUploading(false);
            setError(status.errorMessage || 'Processing failed');
          }
        } else {
          // getJobStatus returned null (network error or 404)
          consecutiveErrors++;
          console.warn(`Failed to get job status (${consecutiveErrors}/${MAX_ERRORS}) - returned null`);
          
          if (consecutiveErrors >= MAX_ERRORS) {
            clearInterval(pollInterval);
            setError('Lost connection to server. The job may still be running. Please refresh to check status.');
          }
        }
      } catch (error) {
        consecutiveErrors++;
        console.error(`Error polling job status (${consecutiveErrors}/${MAX_ERRORS}):`, error);
        
        if (consecutiveErrors >= MAX_ERRORS) {
          clearInterval(pollInterval);
          setError('Connection error. The job may still be running. Please refresh to check status.');
        }
      }
    }, 2000);
    
    return () => {
      console.log('Cleaning up polling interval for jobId:', jobId);
      clearInterval(pollInterval);
    };
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
      setShowAnalysisModal(true); // Show modal after file selection
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
    const maxAttempts = 180; // 180 seconds (3 minutes)
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

  const handleAnalysisConfirm = (options: AnalysisOptions) => {
    setAnalysisOptions(options);
    setShowAnalysisModal(false);
    // Automatically start upload after options are selected
    handleUpload(options);
  };

  const handleAnalysisCancel = () => {
    setShowAnalysisModal(false);
    setFile(null); // Clear file selection if user cancels
  };

  const handleUpload = async (options?: AnalysisOptions) => {
    if (!file) return;
    
    const uploadOptions = options || analysisOptions;
    if (!uploadOptions) {
      console.error('No analysis options provided');
      return;
    }
    
    setIsUploading(true);
    setError(null);
    setJob(null);
    setPdfUrl(null);
    setUploadProgress(0);
    setProcessingStartTime(Date.now());
    setElapsedTime(0);
    
    try {
      console.log('Requesting upload URL for:', file.name, file.type);
      
      // Request upload URL with analysis options
      const response = await axios.post(`${UPLOAD_API_ENDPOINT}/upload`, {
        filename: file.name,
        contentType: file.type || 'audio/mpeg',
        userId: 'guest',
        analysisOptions: uploadOptions // Include analysis options
      }, {
        timeout: 120000 // 2 minutes timeout for upload URL request
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
      
      // Keep isUploading true so progress bar continues to show during processing
      console.log('Starting chord detection...');
      
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
      {/* Analysis Options Modal */}
      <AnalysisOptionsModal
        isOpen={showAnalysisModal}
        onClose={handleAnalysisCancel}
        onConfirm={handleAnalysisConfirm}
        filename={file?.name || ''}
      />

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
        {!jobId && !showAnalysisModal && (
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

        {/* Processing Progress - Show whenever we have a jobId and upload is complete, until job is done */}
        {jobId && uploadProgress === 100 && (!job || (job.status !== 'COMPLETED' && job.status !== 'FAILED')) && (
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
                {job?.statusMessage || 'Initializing processing...'}
              </span>
              <span style={{ 
                color: '#a78bfa', 
                fontWeight: '600',
                textShadow: '0 0 10px rgba(167, 139, 250, 0.5)'
              }}>
                {job?.progress || 0}%
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
                width: `${job?.progress || 0}%`,
                transition: 'width 0.5s ease',
                boxShadow: '0 0 10px rgba(147, 51, 234, 0.5)'
              }}/>
            </div>
            <div style={{ 
              marginTop: '12px', 
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <p style={{ 
                fontSize: '14px', 
                color: 'rgba(255, 255, 255, 0.6)',
              }}>
                {job?.statusMessage || 'Waiting for job to start...'}
              </p>
              <div style={{
                fontSize: '16px',
                fontWeight: '600',
                color: '#00ffff',
                textShadow: '0 0 10px rgba(0, 255, 255, 0.5)',
                fontFamily: 'monospace',
                padding: '4px 12px',
                background: 'rgba(0, 255, 255, 0.1)',
                borderRadius: '8px',
                border: '1px solid rgba(0, 255, 255, 0.3)'
              }}>
                ⏱️ {Math.floor(elapsedTime / 60)}:{String(elapsedTime % 60).padStart(2, '0')}
              </div>
            </div>
            {!job && (
              <div style={{ 
                marginTop: '12px',
                color: 'rgba(255, 255, 255, 0.5)', 
                fontSize: '12px',
                fontFamily: 'monospace'
              }}>
                Job ID: {jobId}
              </div>
            )}
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
                setProcessingStartTime(null);
                setElapsedTime(0);
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
                setProcessingStartTime(null);
                setElapsedTime(0);
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
        {job?.status === 'COMPLETED' && (job.chordsData || job.bassData) && (
          <div style={{
            marginTop: '24px',
            padding: '24px',
            background: 'linear-gradient(to right, #f0fdf4, #dcfce7)',
            borderRadius: '16px',
            border: '1px solid #86efac'
          }}>
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
                setProcessingStartTime(null);
                setElapsedTime(0);
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
            
            {/* Song Metadata - only show if chordsData exists */}
            {job.chordsData && (
            <div style={{
              marginBottom: '24px',
              padding: '20px',
              backgroundColor: 'white',
              borderRadius: '12px',
              border: '1px solid #d1fae5'
            }}>
              <h2 style={{ 
                fontSize: '24px', 
                fontWeight: '700', 
                color: '#166534', 
                marginBottom: '16px',
                borderBottom: '2px solid #d1fae5',
                paddingBottom: '12px'
              }}>
                {job.filename || job.title}
              </h2>
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                gap: '16px'
              }}>
                <div>
                  <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Key</div>
                  <div style={{ fontSize: '20px', fontWeight: '600', color: '#166534' }}>
                    {job.chordsData.key}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Tempo</div>
                  <div style={{ fontSize: '20px', fontWeight: '600', color: '#166534' }}>
                    {job.chordsData.tempo} BPM
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Time Signature</div>
                  <div style={{ fontSize: '20px', fontWeight: '600', color: '#166534' }}>
                    {job.chordsData.timeSignature}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Duration</div>
                  <div style={{ fontSize: '20px', fontWeight: '600', color: '#166534' }}>
                    {Math.floor(job.chordsData.duration / 60)}:{String(Math.floor(job.chordsData.duration % 60)).padStart(2, '0')}
                  </div>
                </div>
                {elapsedTime > 0 && (
                  <div>
                    <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Processing Time</div>
                    <div style={{ fontSize: '20px', fontWeight: '600', color: '#166534' }}>
                      {Math.floor(elapsedTime / 60)}:{String(elapsedTime % 60).padStart(2, '0')}
                    </div>
                  </div>
                )}
              </div>
            </div>
            )}

            {/* Lyrics Section */}
            {job.chordsData && job.chordsData.lyrics && job.chordsData.lyrics.text && (
              <div style={{
                marginBottom: '24px',
                padding: '20px',
                backgroundColor: 'white',
                borderRadius: '12px',
                border: '1px solid #d1fae5'
              }}>
                <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#166534', marginBottom: '16px' }}>
                  🎤 Lyrics
                </h3>
                <div style={{
                  fontSize: '14px',
                  lineHeight: '1.8',
                  color: '#1f2937',
                  whiteSpace: 'pre-wrap',
                  fontFamily: 'Georgia, serif'
                }}>
                  {job.chordsData.lyrics.text}
                </div>
                <div style={{
                  marginTop: '12px',
                  fontSize: '12px',
                  color: '#6b7280',
                  fontStyle: 'italic'
                }}>
                  Language: {job.chordsData.lyrics.language || 'unknown'} • 
                  Words: {job.chordsData.lyrics.words?.length || 0}
                </div>
              </div>
            )}

            {/* Bass NNS Display (if bassData exists) */}
            {job.bassData && (
              <div style={{ marginBottom: '24px' }}>
                <BassNNSDisplay 
                  bassData={job.bassData}
                  pdfUrl={pdfUrl || undefined}
                />
              </div>
            )}

            {/* Lead Sheet Display (if leadSheet data exists) or Chord-Only Display */}
            {job.chordsData?.leadSheet ? (
              <div style={{
                marginBottom: '24px',
                padding: '20px',
                backgroundColor: 'white',
                borderRadius: '12px',
                border: '1px solid #d1fae5'
              }}>
                <div style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  alignItems: 'center',
                  marginBottom: '16px'
                }}>
                  <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#166534', margin: 0 }}>
                    🎼 Lead Sheet
                  </h3>
                  <button
                    onClick={() => setShowDebugMode(!showDebugMode)}
                    style={{
                      padding: '6px 12px',
                      fontSize: '12px',
                      backgroundColor: showDebugMode ? '#9333ea' : '#e5e7eb',
                      color: showDebugMode ? 'white' : '#6b7280',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontWeight: '500',
                      transition: 'all 0.2s ease'
                    }}
                  >
                    {showDebugMode ? '🐛 Debug ON' : '🐛 Debug OFF'}
                  </button>
                </div>
                <LeadSheetDisplay 
                  leadSheet={job.chordsData.leadSheet}
                  showMeasureNumbers={true}
                  showTimestamps={showDebugMode}
                />
              </div>
            ) : (
              /* Fallback to chord-only display if no lead sheet */
              job.chordsData?.chords && job.chordsData.chords.length > 0 ? (
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
                  // Debug logging
                  console.log('Rendering chord sheet with data:', {
                    chordsCount: job.chordsData.chords.length,
                    sectionsCount: job.chordsData.songStructure?.length || 0,
                    firstChord: job.chordsData.chords[0],
                    sections: job.chordsData.songStructure,
                    allKeys: Object.keys(job.chordsData)
                  });
                  
                  // Helper function to calculate Nashville Number
                  const getNashvilleNumber = (chordName: string, key: string) => {
                    const noteNames = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
                    const flatToSharp: any = {'Db': 'C#', 'Eb': 'D#', 'Gb': 'F#', 'Ab': 'G#', 'Bb': 'A#'};
                    
                    // Extract root from chord
                    let root = chordName[0];
                    if (chordName.length > 1 && (chordName[1] === '#' || chordName[1] === 'b')) {
                      root = chordName.substring(0, 2);
                    }
                    
                    // Normalize to sharp
                    if (root in flatToSharp) root = flatToSharp[root];
                    
                    // Extract key root (handle "E Minor / G Major" format)
                    let keyRoot = key.split(' ')[0];
                    if (keyRoot in flatToSharp) keyRoot = flatToSharp[keyRoot];
                    
                    try {
                      const rootIdx = noteNames.indexOf(root);
                      const keyIdx = noteNames.indexOf(keyRoot);
                      if (rootIdx === -1 || keyIdx === -1) return '';
                      
                      const degree = ((rootIdx - keyIdx + 12) % 12) + 1;
                      const degreeMap: any = {1: '1', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '1', 9: '2', 10: '3', 11: '4', 12: '5'};
                      let nns = degreeMap[degree] || '';
                      
                      // Add quality suffix
                      if (chordName.toLowerCase().includes('m') && !chordName.toLowerCase().includes('maj')) {
                        nns += 'm';
                      }
                      
                      return nns;
                    } catch {
                      return '';
                    }
                  };
                  
                  // Group chords by song sections
                  const sections = job.chordsData.songStructure || [];
                  const chords = job.chordsData.chords;
                  const key = job.chordsData.key;
                  
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
                                  display: 'inline-flex',
                                  flexDirection: 'column',
                                  alignItems: 'center',
                                  padding: '4px 8px',
                                  backgroundColor: '#f9fafb',
                                  borderRadius: '4px',
                                  border: '1px solid #e5e7eb'
                                }}>
                                  <span style={{
                                    fontWeight: '600',
                                    color: '#1f2937'
                                  }}>
                                    {chord.chord}
                                  </span>
                                  <span style={{
                                    fontSize: '11px',
                                    color: '#9333ea',
                                    fontStyle: 'italic',
                                    marginTop: '2px'
                                  }}>
                                    ({getNashvilleNumber(chord.chord, key)})
                                  </span>
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
                    // Handle both property names: start/end or startTime/endTime
                    const sectionStart = parseFloat(section.start || section.startTime || 0);
                    const sectionEnd = parseFloat(section.end || section.endTime || (sectionIdx < sections.length - 1 ? sections[sectionIdx + 1].startTime : 999999));
                    
                    console.log(`Section ${sectionIdx} (${section.label}): ${sectionStart}s - ${sectionEnd}s`);
                    
                    // Find chords within this section's time range
                    const sectionChords = chords.filter((chord: any) => {
                      const chordTime = parseFloat(chord.start || 0);
                      return chordTime >= sectionStart && chordTime < sectionEnd;
                    });
                    
                    console.log(`  Found ${sectionChords.length} chords in this section`);
                    
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
                          {section.label}
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
                                  display: 'inline-flex',
                                  flexDirection: 'column',
                                  alignItems: 'center',
                                  padding: '4px 8px',
                                  backgroundColor: '#f9fafb',
                                  borderRadius: '4px',
                                  border: '1px solid #e5e7eb'
                                }}>
                                  <span style={{
                                    fontWeight: '600',
                                    color: '#1f2937'
                                  }}>
                                    {chord.chord}
                                  </span>
                                  <span style={{
                                    fontSize: '11px',
                                    color: '#9333ea',
                                    fontStyle: 'italic',
                                    marginTop: '2px'
                                  }}>
                                    ({getNashvilleNumber(chord.chord, key)})
                                  </span>
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
            ) : (
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
                <p style={{ color: '#6b7280' }}>
                  No chords detected. Debug: {JSON.stringify({
                    hasChordsData: !!job.chordsData,
                    hasChords: !!job.chordsData?.chords,
                    chordsLength: job.chordsData?.chords?.length || 0
                  })}
                </p>
              </div>
            )
            )}
            
            {pdfUrl && (
              <div style={{ display: 'flex', gap: '12px' }}>
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

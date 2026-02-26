/**
 * Example: Integrating Downbeat Confirmation into Upload Workflow
 * 
 * This file shows how to integrate the DownbeatConfirmation component
 * into your existing upload page/component.
 */

import React, { useState } from 'react';
import { DownbeatConfirmation } from './components/DownbeatConfirmation';
import { requestUploadUrl, getJobStatus } from './services/transcriptionService';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 
                     'https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com';

interface DownbeatData {
  audioUrl: string;
  downbeat: number;
  tempo: number;
  timeSignature: string;
  beatTimes: number[];
}

export function UploadPageWithDownbeatConfirmation() {
  const [isUploading, setIsUploading] = useState(false);
  const [showDownbeatConfirmation, setShowDownbeatConfirmation] = useState(false);
  const [downbeatData, setDownbeatData] = useState<DownbeatData | null>(null);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  /**
   * Step 1: Handle file upload
   */
  const handleFileUpload = async (file: File) => {
    try {
      setIsUploading(true);
      setError(null);
      setUploadProgress(10);

      // Request upload URL
      const { jobId, uploadUrl } = await requestUploadUrl(
        file.name,
        file.type,
        'guest' // or actual user ID
      );

      setCurrentJobId(jobId);
      setUploadProgress(20);

      // Upload file to S3
      await uploadFileToS3(uploadUrl, file, (progress) => {
        setUploadProgress(20 + progress * 0.3); // 20-50%
      });

      setUploadProgress(50);

      // Step 2: Detect downbeat
      await detectDownbeat(jobId, file.name);

    } catch (err) {
      console.error('Upload error:', err);
      setError(err instanceof Error ? err.message : 'Upload failed');
      setIsUploading(false);
    }
  };

  /**
   * Step 2: Detect downbeat
   */
  const detectDownbeat = async (jobId: string, filename: string) => {
    try {
      setUploadProgress(60);

      const response = await fetch(`${API_BASE_URL}/api/detect-downbeat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          jobId,
          // The Lambda will get bucket/key from the job in DynamoDB
          // Or you can pass them explicitly:
          // bucket: 'your-bucket-name',
          // key: `uploads/${jobId}/${filename}`
        }),
      });

      if (!response.ok) {
        throw new Error('Downbeat detection failed');
      }

      const data = await response.json();
      setUploadProgress(80);

      // Generate presigned URL for audio playback (if needed)
      // Or use the original upload URL if it's still valid
      const audioUrl = await getPresignedAudioUrl(jobId, filename);

      // Step 3: Show confirmation modal
      setDownbeatData({
        audioUrl,
        downbeat: data.detectedDownbeat,
        tempo: data.tempo,
        timeSignature: data.timeSignature,
        beatTimes: data.beatTimes,
      });

      setIsUploading(false);
      setUploadProgress(100);
      setShowDownbeatConfirmation(true);

    } catch (err) {
      console.error('Downbeat detection error:', err);
      setError(err instanceof Error ? err.message : 'Downbeat detection failed');
      setIsUploading(false);
    }
  };

  /**
   * Step 3: User confirms downbeat
   */
  const handleDownbeatConfirm = async (downbeat: number, timeSignature: string) => {
    try {
      if (!currentJobId) return;

      // Save confirmed values and trigger chord detection
      const response = await fetch(`${API_BASE_URL}/api/confirm-downbeat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          jobId: currentJobId,
          downbeat,
          timeSignature,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to confirm downbeat');
      }

      // Close modal
      setShowDownbeatConfirmation(false);
      setDownbeatData(null);

      // Step 4: Start polling for job status
      startPollingJobStatus(currentJobId);

    } catch (err) {
      console.error('Confirm downbeat error:', err);
      setError(err instanceof Error ? err.message : 'Failed to confirm downbeat');
    }
  };

  /**
   * User cancels downbeat confirmation
   */
  const handleDownbeatCancel = () => {
    setShowDownbeatConfirmation(false);
    setDownbeatData(null);
    setCurrentJobId(null);
    setError('Downbeat confirmation cancelled');
  };

  /**
   * Step 4: Poll for job status
   */
  const startPollingJobStatus = (jobId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const job = await getJobStatus(jobId);
        
        if (!job) {
          console.log('Job not found, continuing to poll...');
          return;
        }

        console.log('Job status:', job.status, job.progress);

        if (job.status === 'COMPLETED') {
          clearInterval(pollInterval);
          // Navigate to results page or show results
          console.log('Job completed!', job);
          // window.location.href = `/results/${jobId}`;
        } else if (job.status === 'FAILED') {
          clearInterval(pollInterval);
          setError(job.errorMessage || 'Processing failed');
        }
      } catch (err) {
        console.error('Polling error:', err);
        // Continue polling on error
      }
    }, 2000); // Poll every 2 seconds

    // Stop polling after 5 minutes
    setTimeout(() => {
      clearInterval(pollInterval);
    }, 5 * 60 * 1000);
  };

  /**
   * Helper: Upload file to S3 with progress
   */
  const uploadFileToS3 = async (
    uploadUrl: string,
    file: File,
    onProgress: (progress: number) => void
  ): Promise<void> => {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const progress = e.loaded / e.total;
          onProgress(progress);
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve();
        } else {
          reject(new Error(`Upload failed with status ${xhr.status}`));
        }
      });

      xhr.addEventListener('error', () => {
        reject(new Error('Upload failed'));
      });

      xhr.open('PUT', uploadUrl);
      xhr.setRequestHeader('Content-Type', file.type);
      xhr.send(file);
    });
  };

  /**
   * Helper: Get presigned URL for audio playback
   */
  const getPresignedAudioUrl = async (jobId: string, filename: string): Promise<string> => {
    // Option 1: Request presigned URL from backend
    const response = await fetch(`${API_BASE_URL}/api/get-audio-url/${jobId}`);
    const data = await response.json();
    return data.audioUrl;

    // Option 2: If you have the bucket/key, generate it client-side
    // (requires AWS SDK and credentials)
    // return generatePresignedUrl(bucket, key);

    // Option 3: Use public URL if bucket is public
    // return `https://your-bucket.s3.amazonaws.com/uploads/${jobId}/${filename}`;
  };

  return (
    <div className="upload-page">
      <h1>Upload Audio for Transcription</h1>

      {/* File Upload UI */}
      <div className="upload-area">
        <input
          type="file"
          accept="audio/*"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFileUpload(file);
          }}
          disabled={isUploading}
        />

        {isUploading && (
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${uploadProgress}%` }}
            />
            <span>{uploadProgress}%</span>
          </div>
        )}

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}
      </div>

      {/* Downbeat Confirmation Modal */}
      {showDownbeatConfirmation && downbeatData && (
        <DownbeatConfirmation
          audioUrl={downbeatData.audioUrl}
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

/**
 * Alternative: Simpler integration without downbeat confirmation
 * (for testing or if you want to skip the confirmation step)
 */
export function UploadPageWithoutDownbeatConfirmation() {
  const handleFileUpload = async (file: File) => {
    // 1. Upload file
    const { jobId, uploadUrl } = await requestUploadUrl(file.name, file.type);
    await uploadToS3(uploadUrl, file);

    // 2. Skip downbeat detection, go straight to chord detection
    // The backend will auto-detect downbeat without user confirmation
    await fetch(`${API_BASE_URL}/api/start-chord-detection`, {
      method: 'POST',
      body: JSON.stringify({ jobId }),
    });

    // 3. Poll for results
    // ...
  };

  return <div>{/* Upload UI */}</div>;
}

/**
 * Alternative: Optional downbeat confirmation
 * (show confirmation only if confidence is low)
 */
export function UploadPageWithOptionalConfirmation() {
  const handleFileUpload = async (file: File) => {
    // 1. Upload file
    const { jobId, uploadUrl } = await requestUploadUrl(file.name, file.type);
    await uploadToS3(uploadUrl, file);

    // 2. Detect downbeat
    const response = await fetch(`${API_BASE_URL}/api/detect-downbeat`, {
      method: 'POST',
      body: JSON.stringify({ jobId }),
    });
    const data = await response.json();

    // 3. Show confirmation only if confidence is low
    if (data.confidence < 0.5) {
      // Show confirmation modal
      setShowDownbeatConfirmation(true);
    } else {
      // Auto-confirm and proceed
      await fetch(`${API_BASE_URL}/api/confirm-downbeat`, {
        method: 'POST',
        body: JSON.stringify({
          jobId,
          downbeat: data.detectedDownbeat,
          timeSignature: data.timeSignature,
        }),
      });
    }
  };

  return <div>{/* Upload UI */}</div>;
}

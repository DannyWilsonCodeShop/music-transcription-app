// API Configuration - File Upload Pipeline
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 
                     'https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com';

// Import lead sheet types from LeadSheetDisplay component
import type { AlignedLeadSheet } from '../components/LeadSheetDisplay';

export interface TranscriptionJob {
  id: string;
  filename?: string;
  title: string;
  status: 'PENDING' | 'UPLOADING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  currentStep?: string;
  progress?: number;
  statusMessage?: string;
  createdAt: string;
  updatedAt?: string;
  completedAt?: string;
  chordsData?: {
    key: string;
    mode: string;
    keyConfidence: number;
    tempo: number;
    timeSignature: string;
    duration: number;
    totalChords: number;
    chords: Array<{
      chord: string;
      start: number;
      end: number;
      duration: number;
      confidence: number;
    }>;
    songStructure?: Array<{
      label: string;
      start: number;
      end: number;
      duration: number;
      measureStart?: number;
      measureEnd?: number;
      patternCount?: number;
    }>;
    patternAnalysis?: Array<{
      patternNumber: number;
      progression: string[];
      nashvilleProgression: string[];
      length: number;
      occurrences: number;
      positions: number[];
    }>;
    leadSheet?: AlignedLeadSheet;
    model?: string;
  };
  pdfUrl?: string;
  errorMessage?: string;
}

/**
 * Request upload URL for file upload
 */
export async function requestUploadUrl(
  filename: string,
  contentType: string,
  userId: string = 'guest'
): Promise<{ jobId: string; uploadUrl: string }> {
  try {
    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        filename,
        contentType,
        userId,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to request upload URL');
    }

    const data = await response.json();
    console.log('Upload URL received:', data);
    return data;
  } catch (error) {
    console.error('Error requesting upload URL:', error);
    throw new Error('Failed to request upload URL. Please try again.');
  }
}

/**
 * Get the status of a transcription job via File Upload Pipeline API
 */
export async function getJobStatus(jobId: string): Promise<TranscriptionJob | null> {
  console.log(`[transcriptionService] getJobStatus called for jobId: ${jobId}`);
  try {
    const url = `${API_BASE_URL}/jobs/${jobId}`;
    console.log(`[transcriptionService] Fetching: ${url}`);
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    console.log(`[transcriptionService] Response status: ${response.status}`);

    if (response.status === 404) {
      console.log('[transcriptionService] Job not found (404)');
      return null;
    }

    if (!response.ok) {
      const error = await response.json();
      console.error('[transcriptionService] Error response:', error);
      throw new Error(error.error || 'Failed to get job status');
    }

    const data = await response.json();
    console.log('[transcriptionService] Job data received:', {
      jobId: data.jobId,
      status: data.status,
      progress: data.progress,
      statusMessage: data.statusMessage
    });
    
    // Map backend response to frontend format
    const mappedJob = {
      id: data.jobId,
      filename: data.filename,
      title: data.filename || 'Processing...',
      status: data.status,
      currentStep: getStepDescription(data.status),
      progress: data.progress || 0,
      statusMessage: data.statusMessage,
      createdAt: data.createdAt,
      updatedAt: data.updatedAt,
      completedAt: data.completedAt,
      chordsData: data.chordsData,
      pdfUrl: data.pdfUrl,
      errorMessage: data.errorMessage,
    } as TranscriptionJob;
    
    console.log('[transcriptionService] Mapped job:', {
      id: mappedJob.id,
      status: mappedJob.status,
      progress: mappedJob.progress
    });
    
    return mappedJob;
  } catch (error) {
    console.error('[transcriptionService] Error getting job status:', error);
    // Return null on network errors to allow retry
    if (error instanceof TypeError && error.message === 'Failed to fetch') {
      console.log('[transcriptionService] Network error, will retry...');
      return null;
    }
    return null;
  }
}

/**
 * Get user-friendly step description
 */
function getStepDescription(status: string): string {
  switch (status) {
    case 'PENDING':
      return 'Initializing...';
    case 'UPLOADING':
      return 'Uploading file...';
    case 'PROCESSING':
      return 'Analyzing audio with enhanced chord detection...';
    case 'COMPLETED':
      return 'Complete!';
    case 'FAILED':
      return 'Failed';
    default:
      return 'Processing...';
  }
}

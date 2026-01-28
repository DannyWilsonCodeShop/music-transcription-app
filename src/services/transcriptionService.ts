// API Configuration - ChordScout V2 with Deepgram + ECS
const API_BASE_URL = 'https://l43ftjo75d.execute-api.us-east-1.amazonaws.com/dev';

export interface TranscriptionJob {
  id: string;
  youtubeUrl?: string;
  title: string;
  status: 'PENDING' | 'DOWNLOADING' | 'TRANSCRIBING' | 'DETECTING_CHORDS' | 'GENERATING_PDF' | 'COMPLETE' | 'FAILED';
  currentStep?: string;
  progress?: number;
  createdAt: string;
  updatedAt?: string;
  completedAt?: string;
  lyrics?: string;
  chords?: any;
  pdfUrl?: string;
  sheetMusicUrl?: string;
  error?: string;
}

/**
 * Start a new transcription job via ChordScout V2 API
 */
export async function startTranscription(
  youtubeUrl: string
): Promise<string> {
  try {
    const response = await fetch(`${API_BASE_URL}/jobs`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        youtubeUrl,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to start transcription');
    }

    const data = await response.json();
    console.log('Transcription started successfully:', data);
    return data.jobId;
  } catch (error) {
    console.error('Error starting transcription:', error);
    throw new Error('Failed to start transcription. Please try again.');
  }
}

/**
 * Get the status of a transcription job via ChordScout V2 API
 */
export async function getJobStatus(jobId: string): Promise<TranscriptionJob | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (response.status === 404) {
      return null;
    }

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to get job status');
    }

    const data = await response.json();
    
    // Map backend response to frontend format
    return {
      id: data.jobId,
      youtubeUrl: data.youtubeUrl,
      title: data.videoTitle || 'Processing...',
      status: mapBackendStatus(data.status),
      progress: data.progress || 0,
      createdAt: data.createdAt,
      updatedAt: data.updatedAt,
      completedAt: data.completedAt,
      pdfUrl: data.pdfUrl,
      sheetMusicUrl: data.pdfUrl, // Use PDF URL as sheet music
      error: data.error,
    } as TranscriptionJob;
  } catch (error) {
    console.error('Error getting job status:', error);
    return null;
  }
}

/**
 * Map backend status to frontend status
 */
function mapBackendStatus(backendStatus: string): TranscriptionJob['status'] {
  switch (backendStatus) {
    case 'PENDING':
      return 'PENDING';
    case 'DOWNLOADING':
    case 'DOWNLOADED':
      return 'DOWNLOADING';
    case 'TRANSCRIBING':
    case 'TRANSCRIBED':
      return 'TRANSCRIBING';
    case 'DETECTING_CHORDS':
      return 'DETECTING_CHORDS';
    case 'GENERATING_PDF':
      return 'GENERATING_PDF';
    case 'COMPLETE':
      return 'COMPLETE';
    case 'FAILED':
      return 'FAILED';
    default:
      return 'PENDING';
  }
}


/**
 * Mock function for testing without AWS credentials
 */
export async function mockStartTranscription(
  youtubeUrl: string,
  title: string
): Promise<string> {
  const jobId = `mock-job-${Date.now()}`;
  console.log('Mock transcription started:', { jobId, youtubeUrl, title });
  
  // Simulate async operation
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  return jobId;
}

/**
 * Mock function for testing
 */
export async function mockGetJobStatus(jobId: string): Promise<TranscriptionJob> {
  // Simulate different stages
  const elapsed = Date.now() - parseInt(jobId.split('-')[2] || '0');
  
  let status: TranscriptionJob['status'] = 'PENDING';
  if (elapsed > 5000) status = 'DOWNLOADING';
  if (elapsed > 15000) status = 'COMPLETE';
  
  return {
    id: jobId,
    title: 'Test Song',
    status,
    createdAt: new Date().toISOString(),
    lyrics: status === 'COMPLETE' ? 'Never gonna give you up\nNever gonna let you down' : undefined,
    chords: status === 'COMPLETE' ? {
      key: 'C',
      mode: 'major',
      chords: [
        { name: 'C', timestamp: 0, duration: 2, confidence: 0.9 },
        { name: 'G', timestamp: 2, duration: 2, confidence: 0.85 },
        { name: 'Am', timestamp: 4, duration: 2, confidence: 0.88 },
        { name: 'F', timestamp: 6, duration: 2, confidence: 0.92 },
      ]
    } : undefined,
  };
}

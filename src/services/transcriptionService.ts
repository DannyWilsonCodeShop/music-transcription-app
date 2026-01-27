// API Configuration
const API_BASE_URL = 'https://rzx9drt3z1.execute-api.us-east-1.amazonaws.com/prod';

export interface TranscriptionJob {
  id: string;
  youtubeUrl?: string;
  title: string;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  currentStep?: string;
  progress?: number;
  createdAt: string;
  updatedAt?: string;
  lyrics?: string;
  chords?: any;
  sheetMusicUrl?: string;
  error?: string;
}

/**
 * Start a new transcription job via API proxy
 */
export async function startTranscription(
  youtubeUrl: string,
  title: string
): Promise<string> {
  try {
    const response = await fetch(`${API_BASE_URL}/transcription/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        youtubeUrl,
        title,
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
 * Get the status of a transcription job via API proxy
 */
export async function getJobStatus(jobId: string): Promise<TranscriptionJob | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/transcription/status/${jobId}`, {
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
    return data as TranscriptionJob;
  } catch (error) {
    console.error('Error getting job status:', error);
    return null;
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
  if (elapsed > 5000) status = 'PROCESSING';
  if (elapsed > 15000) status = 'COMPLETED';
  
  return {
    id: jobId,
    title: 'Test Song',
    status,
    createdAt: new Date().toISOString(),
    lyrics: status === 'COMPLETED' ? 'Never gonna give you up\nNever gonna let you down' : undefined,
    chords: status === 'COMPLETED' ? {
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

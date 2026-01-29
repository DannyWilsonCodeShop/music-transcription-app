// API Configuration - Music Transcription App V2 with Deepgram + ECS
const API_BASE_URL = 'https://l43ftjo75d.execute-api.us-east-1.amazonaws.com/dev';

// TEMPORARY: Enable mock mode while fixing YouTube download
const USE_MOCK_DATA = true;

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
 * Start a new transcription job via Music Transcription App V2 API
 */
export async function startTranscription(
  youtubeUrl: string
): Promise<string> {
  // TEMPORARY: Use mock data while fixing YouTube download
  if (USE_MOCK_DATA) {
    console.log('🎭 MOCK MODE: Using mock transcription');
    return mockStartTranscription(youtubeUrl, 'Mock Video');
  }

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
 * Get the status of a transcription job via Music Transcription App V2 API
 */
export async function getJobStatus(jobId: string): Promise<TranscriptionJob | null> {
  // TEMPORARY: Use mock data while fixing YouTube download
  if (USE_MOCK_DATA) {
    console.log('🎭 MOCK MODE: Using mock job status');
    return mockGetJobStatus(jobId);
  }

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
  console.log('🎭 Mock transcription started:', { jobId, youtubeUrl, title });
  
  // Simulate async operation
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  return jobId;
}

/**
 * Mock function for testing - simulates realistic workflow
 */
export async function mockGetJobStatus(jobId: string): Promise<TranscriptionJob> {
  // Simulate different stages based on elapsed time
  const elapsed = Date.now() - parseInt(jobId.split('-')[2] || '0');
  
  let status: TranscriptionJob['status'] = 'PENDING';
  let progress = 0;
  let currentStep = 'Initializing...';
  
  if (elapsed > 2000) {
    status = 'DOWNLOADING';
    progress = 15;
    currentStep = 'Downloading audio from YouTube...';
  }
  if (elapsed > 5000) {
    status = 'TRANSCRIBING';
    progress = 45;
    currentStep = 'Transcribing lyrics with Deepgram Nova-3...';
  }
  if (elapsed > 10000) {
    status = 'DETECTING_CHORDS';
    progress = 75;
    currentStep = 'Detecting chords with AI model...';
  }
  if (elapsed > 15000) {
    status = 'GENERATING_PDF';
    progress = 90;
    currentStep = 'Generating PDF with chords and lyrics...';
  }
  if (elapsed > 18000) {
    status = 'COMPLETE';
    progress = 100;
    currentStep = 'Complete!';
  }
  
  const job: TranscriptionJob = {
    id: jobId,
    title: 'Rick Astley - Never Gonna Give You Up',
    status,
    progress,
    currentStep,
    createdAt: new Date(Date.now() - elapsed).toISOString(),
    updatedAt: new Date().toISOString(),
  };
  
  // Add completion data when done
  if (status === 'COMPLETE') {
    job.completedAt = new Date().toISOString();
    job.lyrics = `[Verse 1]
We're no strangers to love
You know the rules and so do I
A full commitment's what I'm thinking of
You wouldn't get this from any other guy

[Pre-Chorus]
I just wanna tell you how I'm feeling
Gotta make you understand

[Chorus]
Never gonna give you up
Never gonna let you down
Never gonna run around and desert you
Never gonna make you cry
Never gonna say goodbye
Never gonna tell a lie and hurt you`;
    
    job.chords = {
      key: 'F',
      mode: 'major',
      chords: [
        { name: 'F', timestamp: 0, duration: 4, confidence: 0.92 },
        { name: 'G', timestamp: 4, duration: 4, confidence: 0.89 },
        { name: 'Am', timestamp: 8, duration: 4, confidence: 0.91 },
        { name: 'F', timestamp: 12, duration: 4, confidence: 0.93 },
        { name: 'G', timestamp: 16, duration: 4, confidence: 0.88 },
        { name: 'C', timestamp: 20, duration: 4, confidence: 0.90 },
        { name: 'G', timestamp: 24, duration: 4, confidence: 0.87 },
        { name: 'Am', timestamp: 28, duration: 4, confidence: 0.92 },
      ]
    };
    
    // Mock PDF URL (will show download button)
    job.pdfUrl = 'https://example.com/mock-pdf.pdf';
    job.sheetMusicUrl = 'https://example.com/mock-pdf.pdf';
  }
  
  return job;
}

// Local Enhanced Music Transcription Server
// Runs the complete enhanced system locally for development and testing

const express = require('express');
const cors = require('cors');
const { v4: uuidv4 } = require('uuid');
const fs = require('fs-extra');
const path = require('path');

// Import enhanced analysis modules
const { analyzeAudioLocally } = require('./modules/enhanced-audio-analyzer');
const { analyzeLyricsLocally } = require('./modules/enhanced-lyrics-analyzer');
const { integrateMusicalDataLocally } = require('./modules/musical-integration-orchestrator');
const { generateEnhancedPDFLocally } = require('./modules/enhanced-pdf-generator');

const app = express();
const PORT = 3001;

// Middleware
app.use(cors());
app.use(express.json());
app.use('/pdfs', express.static(path.join(__dirname, 'generated-pdfs')));

// In-memory job storage for local development
const jobs = new Map();

// Create directories
const ensureDirectories = async () => {
  await fs.ensureDir(path.join(__dirname, 'generated-pdfs'));
  await fs.ensureDir(path.join(__dirname, 'temp-audio'));
  console.log('📁 Local directories created');
};

// API Routes

// Start transcription job
app.post('/jobs', async (req, res) => {
  try {
    const { youtubeUrl } = req.body;
    const jobId = uuidv4();
    
    console.log(`🎵 Starting enhanced local transcription: ${jobId}`);
    console.log(`🔗 YouTube URL: ${youtubeUrl}`);
    
    // Create job record
    const job = {
      jobId,
      youtubeUrl,
      status: 'PENDING',
      progress: 0,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      title: 'Processing...'
    };
    
    jobs.set(jobId, job);
    
    // Start processing asynchronously
    processJobLocally(jobId, youtubeUrl).catch(error => {
      console.error(`❌ Job ${jobId} failed:`, error);
      updateJobStatus(jobId, 'FAILED', 0, error.message);
    });
    
    res.json({ jobId });
  } catch (error) {
    console.error('❌ Error starting job:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get job status
app.get('/jobs/:jobId', (req, res) => {
  const { jobId } = req.params;
  const job = jobs.get(jobId);
  
  if (!job) {
    return res.status(404).json({ error: 'Job not found' });
  }
  
  res.json(job);
});

// Enhanced local processing pipeline
async function processJobLocally(jobId, youtubeUrl) {
  try {
    console.log(`🚀 Starting enhanced local processing for ${jobId}`);
    
    // Step 1: Simulate YouTube download (5-15%)
    updateJobStatus(jobId, 'DOWNLOADING', 5, 'Downloading audio from YouTube...');
    await simulateDelay(2000);
    
    const mockAudioUrl = 'local://audio/amazing-grace.mp3';
    updateJobStatus(jobId, 'DOWNLOADING', 15, 'Audio download complete');
    
    // Step 2: Enhanced Audio Analysis (15-45%)
    updateJobStatus(jobId, 'ANALYZING_AUDIO', 20, 'Starting enhanced audio analysis...');
    const audioAnalysis = await analyzeAudioLocally(mockAudioUrl, (progress, message) => {
      updateJobStatus(jobId, 'ANALYZING_AUDIO', 20 + (progress * 0.25), message);
    });
    
    // Step 3: Lyrics Transcription (45-55%)
    updateJobStatus(jobId, 'TRANSCRIBING', 45, 'Transcribing lyrics...');
    await simulateDelay(1500);
    const mockLyrics = getMockLyrics();
    updateJobStatus(jobId, 'TRANSCRIBING', 55, 'Lyrics transcription complete');
    
    // Step 4: Enhanced Lyrics Analysis (55-75%)
    updateJobStatus(jobId, 'ANALYZING_LYRICS', 60, 'Starting enhanced lyrics analysis...');
    const lyricsAnalysis = await analyzeLyricsLocally(mockLyrics, audioAnalysis, (progress, message) => {
      updateJobStatus(jobId, 'ANALYZING_LYRICS', 60 + (progress * 0.15), message);
    });
    
    // Step 5: Musical Integration (75-90%)
    updateJobStatus(jobId, 'INTEGRATING', 75, 'Integrating musical analysis...');
    const integratedData = await integrateMusicalDataLocally(audioAnalysis, lyricsAnalysis, (progress, message) => {
      updateJobStatus(jobId, 'INTEGRATING', 75 + (progress * 0.15), message);
    });
    
    // Step 6: Enhanced PDF Generation (90-100%)
    updateJobStatus(jobId, 'GENERATING_PDF', 90, 'Generating enhanced PDF...');
    const pdfResult = await generateEnhancedPDFLocally(integratedData, jobId, (progress, message) => {
      updateJobStatus(jobId, 'GENERATING_PDF', 90 + (progress * 0.10), message);
    });
    
    // Complete the job
    const job = jobs.get(jobId);
    job.status = 'COMPLETE';
    job.progress = 100;
    job.title = 'Amazing Grace';
    job.pdfUrl = `http://localhost:${PORT}/pdfs/${jobId}.pdf`;
    job.completedAt = new Date().toISOString();
    job.updatedAt = new Date().toISOString();
    
    // Store enhanced analysis data
    job.musicalAnalysis = audioAnalysis;
    job.lyricsAnalysis = lyricsAnalysis;
    job.pdfData = integratedData;
    job.qualityMetrics = pdfResult.qualityMetrics;
    
    console.log(`✅ Enhanced local processing complete for ${jobId}`);
    console.log(`📄 PDF available at: ${job.pdfUrl}`);
    
  } catch (error) {
    console.error(`❌ Enhanced processing failed for ${jobId}:`, error);
    updateJobStatus(jobId, 'FAILED', 0, error.message);
  }
}

function updateJobStatus(jobId, status, progress, message) {
  const job = jobs.get(jobId);
  if (job) {
    job.status = status;
    job.progress = progress;
    job.statusMessage = message;
    job.updatedAt = new Date().toISOString();
    console.log(`📊 ${jobId}: ${status} (${progress}%) - ${message}`);
  }
}

function getMockLyrics() {
  return `Amazing Grace, how sweet the sound
That saved a wretch like me
I once was lost, but now am found
Was blind, but now I see

'Twas grace that taught my heart to fear
And grace my fears relieved
How precious did that grace appear
The hour I first believed`;
}

async function simulateDelay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Start server
app.listen(PORT, async () => {
  await ensureDirectories();
  console.log(`🚀 Enhanced Local Music Transcription Server running on http://localhost:${PORT}`);
  console.log(`📊 API Base URL: http://localhost:${PORT}`);
  console.log(`📄 PDFs served from: http://localhost:${PORT}/pdfs/`);
  console.log(`\n🎯 To test the enhanced system:`);
  console.log(`1. Update your frontend to use: http://localhost:${PORT}`);
  console.log(`2. Or test directly: POST http://localhost:${PORT}/jobs`);
  console.log(`3. Monitor progress: GET http://localhost:${PORT}/jobs/{jobId}`);
});

module.exports = app;
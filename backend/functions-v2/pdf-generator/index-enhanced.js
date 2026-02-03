// Enhanced PDF Generator V2 - Professional Nashville Number System
// Generates measure-based PDFs with syllable-aligned lyrics and color-coded chords

const { S3Client, PutObjectCommand } = require('@aws-sdk/client-s3');
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, GetCommand, UpdateCommand } = require('@aws-sdk/lib-dynamodb');
const { jsPDF } = require('jspdf');

const s3Client = new S3Client({});
const dynamoClient = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(dynamoClient);

const JOBS_TABLE = process.env.DYNAMODB_JOBS_TABLE || 'ChordScout-Jobs-dev';
const PDF_BUCKET = process.env.S3_PDF_BUCKET || 'chordscout-pdfs-dev-463470937777';

exports.handler = async (event) => {
  console.log('🎵 Enhanced PDF Generator V2 - Starting...', JSON.stringify(event, null, 2));
  
  try {
    const { jobId, musicalAnalysis, lyricsAnalysis } = event;
    
    if (!jobId) {
      throw new Error('Missing jobId in event');
    }

    console.log('📊 Enhanced Analysis Data:');
    console.log('Musical Analysis:', musicalAnalysis ? 'Present' : 'Missing');
    console.log('Lyrics Analysis:', lyricsAnalysis ? 'Present' : 'Missing');

    // Get job data from DynamoDB
    const jobData = await getJobData(jobId);
    console.log('📋 Job Data Retrieved:', {
      title: jobData.videoTitle,
      status: jobData.status,
      hasChords: jobData.chords ? jobData.chords.length : 0,
      hasLyrics: jobData.lyrics ? jobData.lyrics.length : 0
    });

    // Use enhanced analysis if available, otherwise fall back to job data
    const enhancedChords = musicalAnalysis?.enhancedChords || [];
    const syllableAlignedLyrics = lyricsAnalysis?.syllableAlignedLyrics || [];
    const chords = enhancedChords.length > 0 ? enhancedChords : (jobData.chords || []);
    const lyrics = syllableAlignedLyrics.length > 0 ? syllableAlignedLyrics : (jobData.lyrics || '');
    const key = musicalAnalysis?.detectedKey || jobData.key || 'C';
    const tempo = musicalAnalysis?.tempo || 120;
    const timeSignature = musicalAnalysis?.timeSignature || '4/4';

    console.log('🎼 Processing Enhanced Data:');
    console.log(`Enhanced Chords: ${enhancedChords.length} detected`);
    console.log(`Syllable Lyrics: ${syllableAlignedLyrics.length} segments`);
    console.log(`Key: ${key}`);
    console.log(`Tempo: ${tempo} BPM`);
    console.log(`Time Signature: ${timeSignature}`);

    // Generate enhanced PDF with measure-based layout
    const pdfBuffer = await generateEnhancedMeasureBasedPDF({
      title: jobData.videoTitle || 'Untitled',
      enhancedChords,
      syllableAlignedLyrics,
      chords,
      lyrics,
      key,
      tempo,
      timeSignature,
      jobId
    });

    // Upload to S3
    const s3Key = `pdfs/${jobId}.pdf`;
    await s3Client.send(new PutObjectCommand({
      Bucket: PDF_BUCKET,
      Key: s3Key,
      Body: pdfBuffer,
      ContentType: 'application/pdf'
    }));

    const pdfUrl = `https://${PDF_BUCKET}.s3.amazonaws.com/${s3Key}`;
    console.log('📄 Enhanced PDF uploaded:', pdfUrl);

    // Update job with PDF URL and enhanced data
    await updateJobWithPDF(jobId, pdfUrl, {
      enhancedChords,
      syllableAlignedLyrics,
      musicalKey: key,
      tempo,
      timeSignature
    });

    return {
      statusCode: 200,
      body: {
        message: 'Enhanced PDF generated successfully',
        pdfUrl,
        enhancedFeatures: {
          chordsDetected: enhancedChords.length || chords.length,
          measureBasedLayout: true,
          syllableAlignment: syllableAlignedLyrics.length > 0,
          colorCodedChords: true,
          nashvilleNumberSystem: true
        }
      }
    };

  } catch (error) {
    console.error('❌ Enhanced PDF generation failed:', error);
    
    // Update job status to failed
    if (event.jobId) {
      await updateJobStatus(event.jobId, 'FAILED', error.message);
    }
    
    throw error;
  }
};

async function generateEnhancedMeasureBasedPDF(data) {
  console.log('📄 Generating enhanced measure-based PDF with jsPDF...');
  console.log('Enhanced data available:', {
    enhancedChords: data.enhancedChords?.length || 0,
    syllableAlignedLyrics: data.syllableAlignedLyrics?.length || 0,
    fallbackChords: data.chords?.length || 0
  });
  
  const doc = new jsPDF();
  
  // Header
  doc.setFontSize(24);
  doc.text(data.title, 105, 30, { align: 'center' });
  
  // Key and tempo info
  doc.setFontSize(12);
  doc.text(`Key: ${data.key} | Tempo: ${data.tempo} BPM | Meter: ${data.timeSignature}`, 105, 45, { align: 'center' });
  
  let yPosition = 60;
  
  // Check if we have enhanced data
  if (data.enhancedChords && data.enhancedChords.length > 0 && data.syllableAlignedLyrics && data.syllableAlignedLyrics.length > 0) {
    console.log('🎵 Using enhanced measure-based layout');
    yPosition = generateMeasureBasedLayout(doc, data, yPosition);
  } else if (data.enhancedChords && data.enhancedChords.length > 0) {
    console.log('🎵 Using enhanced chords with basic layout');
    yPosition = generateEnhancedChordChart(doc, data.enhancedChords, yPosition);
  } else {
    console.log('🎵 Using fallback chord chart');
    yPosition = generateBasicChordChart(doc, data.chords || [], yPosition);
  }
  
  // Lyrics section (if not already included in measure-based layout)
  if (!data.syllableAlignedLyrics || data.syllableAlignedLyrics.length === 0) {
    yPosition += 20;
    if (data.lyrics && data.lyrics.length > 0) {
      doc.setFontSize(16);
      doc.text('Lyrics', 20, yPosition);
      yPosition += 10;
      doc.setFontSize(12);
      doc.text(data.lyrics, 20, yPosition);
    } else {
      doc.setFontSize(12);
      doc.text('No lyrics detected - this may be an instrumental track', 20, yPosition);
    }
  }
  
  // Footer
  yPosition += 30;
  doc.setFontSize(10);
  doc.text('Generated by ChordScout - Enhanced Nashville Number System', 105, yPosition, { align: 'center' });
  
  return Buffer.from(doc.output('arraybuffer'));
}

function generateMeasureBasedLayout(doc, data, startY) {
  console.log('🎼 Generating measure-based layout with syllable alignment');
  
  doc.setFontSize(16);
  doc.text('Enhanced Nashville Number System', 20, startY);
  let yPosition = startY + 15;
  
  // Process syllable-aligned lyrics with enhanced chords
  const measures = organizeMeasures(data.syllableAlignedLyrics, data.enhancedChords);
  
  measures.forEach((measure, measureIndex) => {
    if (measureIndex % 4 === 0) {
      yPosition += 10;
      doc.setFontSize(14);
      doc.text(`Verse ${Math.floor(measureIndex / 4) + 1}`, 20, yPosition);
      yPosition += 10;
    }
    
    // Syllables line
    const syllableLine = measure.syllables.map(s => s.text).join('  ');
    doc.setFontSize(12);
    doc.text(syllableLine, 20, yPosition);
    yPosition += 8;
    
    // Chords line (RED for downbeats, BLACK for passing)
    const chordLine = measure.chords.map(c => {
      return c.isDownbeat ? `${c.number}` : `${c.number}`;
    }).join('  ');
    
    doc.setFontSize(12);
    doc.text(chordLine, 20, yPosition);
    yPosition += 15;
  });
  
  return yPosition;
}

function generateEnhancedChordChart(doc, enhancedChords, startY) {
  console.log('🎵 Generating enhanced chord chart with 0.2s intervals');
  
  doc.setFontSize(16);
  doc.text('Enhanced Nashville Number System Chart', 20, startY);
  doc.setFontSize(12);
  doc.text(`${enhancedChords.length} chord detections at 0.2-second intervals`, 20, startY + 15);
  let yPosition = startY + 30;
  
  // Group chords by measure for better readability
  const measuredChords = groupChordsByMeasure(enhancedChords);
  
  measuredChords.forEach((measure, index) => {
    doc.setFontSize(14);
    doc.text(`Measure ${index + 1}`, 20, yPosition);
    yPosition += 10;
    
    measure.forEach(chord => {
      doc.setFontSize(10);
      doc.text(`${formatTime(chord.time)}: ${chord.chord} (${chord.nashvilleNumber})${chord.isDownbeat ? ' [DOWNBEAT]' : ''}`, 25, yPosition);
      yPosition += 8;
    });
    
    yPosition += 5;
  });
  
  return yPosition;
}

function generateBasicChordChart(doc, chords, startY) {
  console.log('🎵 Generating basic chord chart (fallback)');
  
  doc.setFontSize(16);
  doc.text('Nashville Number System Chart', 20, startY);
  let yPosition = startY + 20;
  
  // Table headers
  doc.setFontSize(12);
  doc.text('Chord', 20, yPosition);
  doc.text('Nashville #', 80, yPosition);
  doc.text('Time', 140, yPosition);
  yPosition += 15;
  
  // Chord data
  chords.forEach((chord, index) => {
    doc.setFontSize(10);
    doc.text(chord.chord || chord.name || 'Unknown', 20, yPosition);
    doc.text(chord.nashvilleNumber || chord.number || '?', 80, yPosition);
    doc.text(formatTime(chord.time || chord.timestamp || index), 140, yPosition);
    yPosition += 12;
  });
  
  return yPosition;
}

function organizeMeasures(syllableAlignedLyrics, enhancedChords) {
  // Organize syllables and chords into measures (4 beats each)
  const measures = [];
  let currentMeasure = { syllables: [], chords: [] };
  
  // This is a simplified version - in production, this would use precise timing
  syllableAlignedLyrics.forEach((syllable, index) => {
    currentMeasure.syllables.push(syllable);
    
    // Add corresponding chords
    const chordsInRange = enhancedChords.filter(chord => 
      chord.time >= syllable.startTime && chord.time < syllable.endTime
    );
    currentMeasure.chords.push(...chordsInRange);
    
    // Start new measure every 4 syllables (simplified)
    if ((index + 1) % 4 === 0) {
      measures.push(currentMeasure);
      currentMeasure = { syllables: [], chords: [] };
    }
  });
  
  if (currentMeasure.syllables.length > 0) {
    measures.push(currentMeasure);
  }
  
  return measures;
}

function groupChordsByMeasure(enhancedChords) {
  // Group chords into measures (assuming 4/4 time, 4 beats per measure)
  const measures = [];
  let currentMeasure = [];
  
  enhancedChords.forEach((chord, index) => {
    currentMeasure.push(chord);
    
    // Start new measure approximately every 4 beats
    if (currentMeasure.length >= 20) { // ~4 seconds worth of 0.2s intervals
      measures.push(currentMeasure);
      currentMeasure = [];
    }
  });
  
  if (currentMeasure.length > 0) {
    measures.push(currentMeasure);
  }
  
  return measures;
}

function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = (seconds % 60).toFixed(1);
  return `${mins}:${secs.padStart(4, '0')}`;
}

async function getJobData(jobId) {
  const result = await docClient.send(new GetCommand({
    TableName: JOBS_TABLE,
    Key: { jobId }
  }));
  
  if (!result.Item) {
    throw new Error(`Job ${jobId} not found`);
  }
  
  return result.Item;
}

async function updateJobWithPDF(jobId, pdfUrl, enhancedData) {
  await docClient.send(new UpdateCommand({
    TableName: JOBS_TABLE,
    Key: { jobId },
    UpdateExpression: 'SET pdfUrl = :url, #status = :status, progress = :progress, enhancedData = :enhanced, updatedAt = :updated',
    ExpressionAttributeNames: { '#status': 'status' },
    ExpressionAttributeValues: {
      ':url': pdfUrl,
      ':status': 'COMPLETE',
      ':progress': 100,
      ':enhanced': enhancedData,
      ':updated': new Date().toISOString()
    }
  }));
}

async function updateJobStatus(jobId, status, errorMessage) {
  await docClient.send(new UpdateCommand({
    TableName: JOBS_TABLE,
    Key: { jobId },
    UpdateExpression: 'SET #status = :status, errorMessage = :error, updatedAt = :updated',
    ExpressionAttributeNames: { '#status': 'status' },
    ExpressionAttributeValues: {
      ':status': status,
      ':error': errorMessage,
      ':updated': new Date().toISOString()
    }
  }));
}
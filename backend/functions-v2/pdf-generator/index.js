// Enhanced PDF Generator - Working Version with Measure-Based Layout
// Uses enhanced chord and lyrics data to generate professional Nashville Number System PDFs

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
  console.log('🎵 Enhanced PDF Generator - Starting...', JSON.stringify(event, null, 2));
  
  try {
    const { jobId } = event;
    
    if (!jobId) {
      throw new Error('Missing jobId in event');
    }

    // Update status
    await updateJobStatus(jobId, 'GENERATING_PDF', 90);

    // Get job data from DynamoDB
    const jobData = await getJobData(jobId);
    console.log('📋 Job Data Retrieved:', {
      title: jobData.videoTitle || jobData.title,
      status: jobData.status,
      hasChords: jobData.chords ? jobData.chords.length : 0,
      hasLyrics: jobData.lyricsData ? 'Present' : 'Missing',
      hasEnhancedLyrics: jobData.lyricsData?.syllableAlignedLyrics ? jobData.lyricsData.syllableAlignedLyrics.length : 0
    });

    // Extract enhanced data - now using chord changes instead of all detections
    const chords = jobData.chords || [];
    const chordAnalysis = jobData.chordAnalysis || {};
    const chordChanges = chordAnalysis.chordChanges || chords; // Use chord changes if available
    const lyricsData = jobData.lyricsData || {};
    const syllableAlignedLyrics = lyricsData.syllableAlignedLyrics || [];
    const key = jobData.key || 'C';
    const tempo = jobData.tempo || 120;
    const timeSignature = jobData.timeSignature || '4/4';

    console.log('🎼 Processing Data:');
    console.log(`Chord Changes: ${chordChanges.length} detected`);
    console.log(`Syllable Lyrics: ${syllableAlignedLyrics.length} segments`);
    console.log(`Key: ${key}`);
    console.log(`Tempo: ${tempo} BPM`);
    
    if (chordAnalysis.summary) {
      console.log(`📉 Data reduction: ${chordAnalysis.summary.dataReduction}% (${chordAnalysis.summary.originalDetections} → ${chordAnalysis.summary.totalChanges} changes)`);
    }

    // Generate enhanced PDF
    const pdfBuffer = await generateEnhancedPDF({
      title: jobData.videoTitle || jobData.title || 'Untitled',
      chords: chordChanges, // Use chord changes instead of all detections
      syllableAlignedLyrics,
      lyrics: lyricsData.text || '',
      key,
      tempo,
      timeSignature,
      jobId,
      chordAnalysis: chordAnalysis // Pass full analysis for metadata
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

    // Update job as complete
    await docClient.send(new UpdateCommand({
      TableName: JOBS_TABLE,
      Key: { jobId },
      UpdateExpression: 'SET pdfUrl = :url, #status = :status, progress = :progress, completedAt = :completed, updatedAt = :updated',
      ExpressionAttributeNames: { '#status': 'status' },
      ExpressionAttributeValues: {
        ':url': pdfUrl,
        ':status': 'COMPLETE',
        ':progress': 100,
        ':completed': new Date().toISOString(),
        ':updated': new Date().toISOString()
      }
    }));

    return {
      statusCode: 200,
      body: {
        message: 'Enhanced PDF generated successfully',
        pdfUrl,
        enhancedFeatures: {
          chordsDetected: chordChanges.length,
          chordChangesUsed: true,
          dataReduction: chordAnalysis.summary?.dataReduction || 0,
          measureBasedLayout: syllableAlignedLyrics.length > 0,
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
      await updateJobStatus(event.jobId, 'FAILED', 0, error.message);
    }
    
    throw error;
  }
};

async function generateEnhancedPDF(data) {
  console.log('📄 Generating enhanced PDF with jsPDF...');
  console.log('Data available:', {
    chords: data.chords?.length || 0,
    syllableAlignedLyrics: data.syllableAlignedLyrics?.length || 0,
    hasLyrics: data.lyrics?.length || 0
  });
  
  const doc = new jsPDF();
  
  // Header
  doc.setFontSize(24);
  doc.setFont('helvetica', 'bold');
  doc.text(data.title, 105, 30, { align: 'center' });
  
  // Key and tempo info
  doc.setFontSize(12);
  doc.setFont('helvetica', 'normal');
  doc.text(`Key: ${data.key} | Tempo: ${data.tempo} BPM | Meter: ${data.timeSignature}`, 105, 45, { align: 'center' });
  
  let yPosition = 60;
  
  // Check if we have enhanced data for measure-based layout
  if (data.syllableAlignedLyrics && data.syllableAlignedLyrics.length > 0 && data.chords && data.chords.length > 0) {
    console.log('🎵 Using enhanced measure-based layout');
    yPosition = generateMeasureBasedLayout(doc, data, yPosition);
  } else if (data.chords && data.chords.length > 0) {
    console.log('🎵 Using enhanced chord chart');
    yPosition = generateEnhancedChordChart(doc, data.chords, yPosition);
  } else {
    console.log('🎵 No chord data available');
    doc.setFontSize(12);
    doc.text('No chord data detected - this may be an instrumental track', 20, yPosition);
    yPosition += 20;
  }
  
  // Lyrics section (if not already included in measure-based layout)
  if (!data.syllableAlignedLyrics || data.syllableAlignedLyrics.length === 0) {
    yPosition += 20;
    if (data.lyrics && data.lyrics.length > 0) {
      doc.setFontSize(16);
      doc.setFont('helvetica', 'bold');
      doc.text('Lyrics', 20, yPosition);
      yPosition += 10;
      doc.setFontSize(12);
      doc.setFont('helvetica', 'normal');
      
      // Split lyrics into lines that fit on the page
      const lines = doc.splitTextToSize(data.lyrics, 170);
      lines.forEach(line => {
        if (yPosition > 270) { // Start new page if needed
          doc.addPage();
          yPosition = 20;
        }
        doc.text(line, 20, yPosition);
        yPosition += 8;
      });
    } else {
      doc.setFontSize(12);
      doc.text('No lyrics detected - this may be an instrumental track', 20, yPosition);
    }
  }
  
  // Footer
  yPosition += 30;
  if (yPosition > 270) {
    doc.addPage();
    yPosition = 20;
  }
  doc.setFontSize(10);
  doc.setFont('helvetica', 'italic');
  doc.text('Generated by ChordScout - Enhanced Nashville Number System', 105, yPosition, { align: 'center' });
  
  return Buffer.from(doc.output('arraybuffer'));
}

function generateMeasureBasedLayout(doc, data, startY) {
  console.log('🎼 Generating measure-based layout with syllable alignment');
  
  doc.setFontSize(16);
  doc.setFont('helvetica', 'bold');
  doc.text('Enhanced Nashville Number System', 20, startY);
  let yPosition = startY + 15;
  
  // Create measures by grouping syllables and chords
  const measures = createMeasures(data.syllableAlignedLyrics, data.chords);
  
  measures.forEach((measure, measureIndex) => {
    if (yPosition > 250) { // Start new page if needed
      doc.addPage();
      yPosition = 20;
    }
    
    if (measureIndex % 4 === 0) {
      yPosition += 10;
      doc.setFontSize(14);
      doc.setFont('helvetica', 'bold');
      doc.text(`Verse ${Math.floor(measureIndex / 4) + 1}`, 20, yPosition);
      yPosition += 10;
    }
    
    // Syllables line
    if (measure.syllables.length > 0) {
      const syllableLine = measure.syllables.map(s => s.text).join('  ');
      doc.setFontSize(12);
      doc.setFont('helvetica', 'normal');
      doc.text(syllableLine, 20, yPosition);
      yPosition += 8;
    }
    
    // Chords line with Nashville numbers
    if (measure.chords.length > 0) {
      const chordLine = measure.chords.map(c => {
        const nashvilleNumber = convertToNashvilleNumber(c.chord || c.name, data.key);
        return nashvilleNumber;
      }).join('  ');
      
      doc.setFontSize(12);
      doc.setFont('helvetica', 'bold');
      doc.text(chordLine, 20, yPosition);
      yPosition += 15;
    }
  });
  
  return yPosition;
}

function generateEnhancedChordChart(doc, chords, startY) {
  console.log('🎵 Generating PROPER Nashville Number System (no tables)');
  
  doc.setFontSize(16);
  doc.setFont('helvetica', 'bold');
  doc.text('Nashville Number System', 20, startY);
  let yPosition = startY + 25;
  
  // Convert chord changes to measure-based format
  const measures = convertChordsToMeasureFormat(chords);
  
  // Generate clean 4-measure lines (NO TABLES, NO GRIDS)
  const measuresPerLine = 4;
  const totalLines = Math.ceil(measures.length / measuresPerLine);
  
  for (let lineIndex = 0; lineIndex < totalLines; lineIndex++) {
    // Check for page break
    if (yPosition > 220) {
      doc.addPage();
      yPosition = 30;
    }
    
    // Add phrase label (clean, no clutter)
    if (lineIndex % 2 === 0) {
      yPosition += 8;
      doc.setFontSize(12);
      doc.setFont('helvetica', 'bold');
      doc.text(`Verse ${Math.floor(lineIndex / 2) + 1}:`, 20, yPosition);
      yPosition += 15;
    }
    
    // Get 4 measures for this line
    const lineMeasures = [];
    for (let i = 0; i < measuresPerLine; i++) {
      const measureIndex = lineIndex * measuresPerLine + i;
      if (measureIndex < measures.length) {
        lineMeasures.push(measures[measureIndex]);
      }
    }
    
    // Generate CLEAN Nashville line (NO TABLES)
    generateCleanNashvilleLine(doc, lineMeasures, yPosition);
    yPosition += 30; // Clean spacing between lines
    
    console.log(`✅ Line ${lineIndex + 1}: Clean Nashville format (no tables)`);
  }
  
  return yPosition;
}

function generateCleanNashvilleLine(doc, measures, yPosition) {
  // CLEAN TEXT-BASED LAYOUT (like Amazing Grace)
  const startX = 40;
  const numberSpacing = 60; // Clean spacing between numbers
  
  measures.forEach((measure, index) => {
    if (measure && index < 4) { // Only show 4 measures per line
      const x = startX + (index * numberSpacing);
      
      // Get the primary chord for this measure
      const primaryChord = measure.chords && measure.chords.length > 0 ? measure.chords[0] : null;
      const nashvilleNumber = primaryChord?.nashvilleNumber || measure.nashvilleNumber || '1';
      const isDownbeat = primaryChord?.isDownbeat || measure.isDownbeat || (index === 0);
      
      // Main Nashville number (clean, large)
      doc.setFontSize(18);
      doc.setFont('helvetica', 'bold');
      
      // Subtle color coding for downbeats
      if (isDownbeat) {
        doc.setTextColor(200, 0, 0); // Subtle red for downbeats
      } else {
        doc.setTextColor(0, 0, 0); // Black for other chords
      }
      
      doc.text(nashvilleNumber, x, yPosition, { align: 'center' });
      
      // Small measure number below (very subtle)
      doc.setFontSize(8);
      doc.setTextColor(150, 150, 150);
      doc.text(`${measure.measureNumber || index + 1}`, x, yPosition + 12, { align: 'center' });
    }
  });
  
  // Reset color
  doc.setTextColor(0, 0, 0);
}

function convertChordsToMeasureFormat(chords) {
  if (!chords || chords.length === 0) {
    return [];
  }
  
  const measures = [];
  const measureMap = {};
  
  // Group chords by measure
  chords.forEach(chord => {
    const measureNum = chord.measure || Math.floor((chord.time || chord.startTime || 0) / 2) + 1;
    
    if (!measureMap[measureNum]) {
      measureMap[measureNum] = {
        measureNumber: measureNum,
        chords: [],
        nashvilleNumber: null,
        isDownbeat: false
      };
    }
    
    measureMap[measureNum].chords.push(chord);
    
    // Set the primary Nashville number for this measure
    if (chord.isDownbeat || !measureMap[measureNum].nashvilleNumber) {
      measureMap[measureNum].nashvilleNumber = chord.nashvilleNumber || convertChordToNashvilleNumber(chord.chord, 'C');
      measureMap[measureNum].isDownbeat = chord.isDownbeat || false;
    }
  });
  
  // Convert to array format
  Object.keys(measureMap).sort((a, b) => parseInt(a) - parseInt(b)).forEach(measureNum => {
    measures.push(measureMap[measureNum]);
  });
  
  return measures;
}

function convertChordToNashvilleNumber(chordName, keyRoot = 'C') {
  if (!chordName || chordName === 'N') return '1';
  
  const noteToSemitone = {
    'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5,
    'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11
  };

  // Extract root note from chord
  let rootNote = chordName[0];
  if (chordName.length > 1 && (chordName[1] === '#' || chordName[1] === 'b')) {
    rootNote = chordName.substring(0, 2);
  }

  const keySemitone = noteToSemitone[keyRoot] || 0;
  const chordSemitone = noteToSemitone[rootNote] || 0;

  let interval = (chordSemitone - keySemitone + 12) % 12;
  const majorNumbers = ['1', 'b2', '2', 'b3', '3', '4', 'b5', '5', 'b6', '6', 'b7', '7'];
  
  let number = majorNumbers[interval];
  
  // Add chord quality indicators
  if (chordName.toLowerCase().includes('m') && !chordName.toLowerCase().includes('maj')) {
    number += 'm';
  }
  
  return number;
}

function createMeasures(syllableAlignedLyrics, chords) {
  const measures = [];
  let currentMeasure = { syllables: [], chords: [] };
  
  // Group syllables into measures (simplified - 4 syllables per measure)
  syllableAlignedLyrics.forEach((syllable, index) => {
    currentMeasure.syllables.push(syllable);
    
    // Find chords that occur during this syllable
    const chordsInRange = chords.filter(chord => {
      const chordTime = chord.time || chord.timestamp || 0;
      return chordTime >= syllable.startTime && chordTime < syllable.endTime;
    });
    
    currentMeasure.chords.push(...chordsInRange);
    
    // Start new measure every 4 syllables (simplified)
    if ((index + 1) % 4 === 0) {
      measures.push(currentMeasure);
      currentMeasure = { syllables: [], chords: [] };
    }
  });
  
  // Add remaining syllables
  if (currentMeasure.syllables.length > 0) {
    measures.push(currentMeasure);
  }
  
  return measures;
}

function convertToNashvilleNumber(chord, key) {
  // Simple Nashville number conversion
  const keyMap = {
    'C': { 'C': '1', 'Dm': '2m', 'Em': '3m', 'F': '4', 'G': '5', 'Am': '6m', 'Bdim': '7°' },
    'G': { 'G': '1', 'Am': '2m', 'Bm': '3m', 'C': '4', 'D': '5', 'Em': '6m', 'F#dim': '7°' },
    'D': { 'D': '1', 'Em': '2m', 'F#m': '3m', 'G': '4', 'A': '5', 'Bm': '6m', 'C#dim': '7°' },
    'A': { 'A': '1', 'Bm': '2m', 'C#m': '3m', 'D': '4', 'E': '5', 'F#m': '6m', 'G#dim': '7°' },
    'E': { 'E': '1', 'F#m': '2m', 'G#m': '3m', 'A': '4', 'B': '5', 'C#m': '6m', 'D#dim': '7°' },
    'F': { 'F': '1', 'Gm': '2m', 'Am': '3m', 'Bb': '4', 'C': '5', 'Dm': '6m', 'Edim': '7°' }
  };
  
  const numbers = keyMap[key] || keyMap['C'];
  return numbers[chord] || chord;
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

async function updateJobStatus(jobId, status, progress, errorMessage) {
  const updateExpr = errorMessage
    ? 'SET #status = :status, progress = :progress, errorMessage = :error, updatedAt = :updated'
    : 'SET #status = :status, progress = :progress, updatedAt = :updated';
  
  const exprValues = {
    ':status': status,
    ':progress': progress,
    ':updated': new Date().toISOString()
  };
  
  if (errorMessage) {
    exprValues[':error'] = errorMessage;
  }
  
  await docClient.send(new UpdateCommand({
    TableName: JOBS_TABLE,
    Key: { jobId },
    UpdateExpression: updateExpr,
    ExpressionAttributeNames: { '#status': 'status' },
    ExpressionAttributeValues: exprValues
  }));
}
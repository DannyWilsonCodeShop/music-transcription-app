// Lambda: PDF Generator - MVP Version
// Generates simple PDF with lyrics and Nashville Number System chart
// Focus: Lyrics + NNS chart showing only root chord changes

const { S3Client, PutObjectCommand } = require('@aws-sdk/client-s3');
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, GetCommand, UpdateCommand } = require('@aws-sdk/lib-dynamodb');
const { jsPDF } = require('jspdf');

const s3Client = new S3Client({});
const dynamoClient = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(dynamoClient);

const JOBS_TABLE = process.env.DYNAMODB_JOBS_TABLE;
const PDF_BUCKET = process.env.S3_PDF_BUCKET;

exports.handler = async (event) => {
  console.log('Event:', JSON.stringify(event, null, 2));
  
  try {
    const { jobId } = event;
    
    // Update status
    await updateJobStatus(jobId, 'GENERATING_PDF', 90);
    
    // Get job data from DynamoDB
    const getResult = await docClient.send(new GetCommand({
      TableName: JOBS_TABLE,
      Key: { jobId }
    }));
    
    const job = getResult.Item;
    if (!job) {
      throw new Error('Job not found');
    }
    
    const { lyricsData, chordsData, videoTitle } = job;
    
    console.log('Generating MVP PDF...');
    console.log('Video title:', videoTitle);
    console.log('Has lyrics:', !!lyricsData && !!lyricsData.text);
    console.log('Has chords:', !!chordsData && !!chordsData.chords);
    
    // Generate simple PDF with lyrics + NNS chart
    const pdfBuffer = await generateMVPPDF(videoTitle, lyricsData || null, chordsData || null);
    
    // Upload to S3
    const pdfKey = `pdfs/${jobId}.pdf`;
    await s3Client.send(new PutObjectCommand({
      Bucket: PDF_BUCKET,
      Key: pdfKey,
      Body: pdfBuffer,
      ContentType: 'application/pdf',
      Metadata: {
        jobId,
        videoTitle: videoTitle || 'Unknown'
      }
    }));
    
    const pdfUrl = `https://${PDF_BUCKET}.s3.amazonaws.com/${pdfKey}`;
    
    // Update job as complete
    await docClient.send(new UpdateCommand({
      TableName: JOBS_TABLE,
      Key: { jobId },
      UpdateExpression: 'SET pdfS3Key = :key, pdfUrl = :url, #status = :status, progress = :progress, completedAt = :completed, updatedAt = :updated',
      ExpressionAttributeNames: { '#status': 'status' },
      ExpressionAttributeValues: {
        ':key': pdfKey,
        ':url': pdfUrl,
        ':status': 'COMPLETE',
        ':progress': 100,
        ':completed': new Date().toISOString(),
        ':updated': new Date().toISOString()
      }
    }));
    
    console.log('PDF generated successfully:', pdfUrl);
    
    return {
      statusCode: 200,
      body: {
        jobId,
        pdfUrl,
        pdfKey
      }
    };
    
  } catch (error) {
    console.error('Error:', error);
    await updateJobStatus(event.jobId, 'FAILED', 0, error.message);
    
    return {
      statusCode: 500,
      body: { error: error.message }
    };
  }
};

async function generateMVPPDF(title, lyricsData, chordsData) {
  const doc = new jsPDF();
  
  // Title
  doc.setFontSize(20);
  doc.setFont('helvetica', 'bold');
  doc.text(title || 'Untitled', 20, 20);
  
  let yPos = 35;
  const pageHeight = doc.internal.pageSize.height;
  const marginBottom = 20;
  const pageWidth = doc.internal.pageSize.width;
  
  // Key signature (if chords available)
  if (chordsData && chordsData.key) {
    doc.setFontSize(12);
    doc.setFont('helvetica', 'normal');
    doc.text(`Key: ${chordsData.key}`, 20, yPos);
    yPos += 15;
  }
  
  // Nashville Number System Chart - Show only root chord changes
  if (chordsData && chordsData.chords && chordsData.chords.length > 0) {
    doc.setFontSize(14);
    doc.setFont('helvetica', 'bold');
    doc.text('Nashville Number System Chart', 20, yPos);
    yPos += 10;
    
    // Extract root chord changes only
    const rootChordChanges = extractRootChordChanges(chordsData.chords);
    
    console.log(`Root chord changes: ${rootChordChanges.length} (from ${chordsData.chords.length} total chords)`);
    
    // Draw NNS chart
    yPos = drawNNSChart(doc, rootChordChanges, chordsData.key, 20, yPos, pageWidth - 40);
    yPos += 20;
  }
  
  // Lyrics section
  const hasLyrics = lyricsData && lyricsData.text && lyricsData.text.trim().length > 0;
  
  if (hasLyrics) {
    // Add separator
    doc.setLineWidth(0.5);
    doc.line(20, yPos, pageWidth - 20, yPos);
    yPos += 10;
    
    doc.setFontSize(14);
    doc.setFont('helvetica', 'bold');
    doc.text('Lyrics', 20, yPos);
    yPos += 10;
    
    // Format and display lyrics
    doc.setFontSize(11);
    doc.setFont('helvetica', 'normal');
    
    const lyrics = lyricsData.text || '';
    const paragraphs = lyrics.split('\n\n');
    
    for (const paragraph of paragraphs) {
      if (!paragraph.trim()) continue;
      
      // Check if we need a new page
      if (yPos > pageHeight - marginBottom - 30) {
        doc.addPage();
        yPos = 20;
      }
      
      const lines = doc.splitTextToSize(paragraph, pageWidth - 40);
      for (const line of lines) {
        if (yPos > pageHeight - marginBottom - 10) {
          doc.addPage();
          yPos = 20;
        }
        doc.text(line, 20, yPos);
        yPos += 6;
      }
      
      yPos += 8; // Space between paragraphs
    }
  } else {
    // No lyrics available
    doc.setFontSize(12);
    doc.setFont('helvetica', 'italic');
    doc.setTextColor(128, 128, 128);
    doc.text('No lyrics detected - this may be an instrumental track', 20, yPos);
    doc.setTextColor(0, 0, 0);
  }
  
  // Footer
  doc.setFontSize(8);
  doc.setTextColor(128, 128, 128);
  const footerText = 'Generated by ChordScout - Nashville Number System';
  doc.text(footerText, 20, pageHeight - 10);
  
  return Buffer.from(doc.output('arraybuffer'));
}

function extractRootChordChanges(chords) {
  /**
   * Extract only root chord changes (when the bass note/root changes)
   * This filters out chord variations and focuses on fundamental harmonic movement
   */
  if (!chords || chords.length === 0) return [];
  
  const rootChanges = [];
  let previousRoot = null;
  
  for (const chord of chords) {
    const chordName = chord.chord || chord.name;
    if (!chordName || chordName === 'N') continue;
    
    // Extract root note (first 1-2 characters)
    const root = extractRootNote(chordName);
    
    // Only add if root changed
    if (root !== previousRoot) {
      rootChanges.push({
        chord: chordName,
        root: root,
        start: chord.start,
        duration: chord.duration,
        confidence: chord.confidence
      });
      previousRoot = root;
    }
  }
  
  console.log(`Extracted ${rootChanges.length} root changes from ${chords.length} chords`);
  return rootChanges;
}

function extractRootNote(chordName) {
  /**
   * Extract the root note from a chord name
   * Examples: "Cmaj7" -> "C", "F#m" -> "F#", "Bb7" -> "Bb"
   */
  if (!chordName) return '';
  
  // Handle sharp and flat
  if (chordName.length >= 2 && (chordName[1] === '#' || chordName[1] === 'b')) {
    return chordName.substring(0, 2);
  }
  
  // Just the first letter
  return chordName[0];
}

function drawNNSChart(doc, rootChordChanges, key, x, y, width) {
  /**
   * Draw a simple Nashville Number System chart
   * Format: Chord Name | Nashville Number | Time
   */
  const startY = y;
  const rowHeight = 8;
  const colWidths = [60, 60, 50]; // Chord, NNS, Time
  
  // Header
  doc.setFontSize(10);
  doc.setFont('helvetica', 'bold');
  doc.setFillColor(240, 240, 240);
  doc.rect(x, y, width, rowHeight, 'F');
  
  doc.text('Chord', x + 5, y + 6);
  doc.text('Nashville #', x + colWidths[0] + 5, y + 6);
  doc.text('Time', x + colWidths[0] + colWidths[1] + 5, y + 6);
  
  y += rowHeight;
  
  // Draw rows
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(10);
  
  const maxRows = 25; // Limit to prevent overflow
  const displayChords = rootChordChanges.slice(0, maxRows);
  
  for (let i = 0; i < displayChords.length; i++) {
    const chord = displayChords[i];
    
    // Alternate row colors
    if (i % 2 === 0) {
      doc.setFillColor(250, 250, 250);
      doc.rect(x, y, width, rowHeight, 'F');
    }
    
    // Chord name
    doc.setTextColor(0, 100, 200);
    doc.setFont('helvetica', 'bold');
    doc.text(chord.chord, x + 5, y + 6);
    
    // Nashville number
    const nashvilleNumber = getNashvilleNumber(chord.chord, key);
    doc.setTextColor(200, 0, 0);
    doc.setFont('helvetica', 'bold');
    doc.text(nashvilleNumber, x + colWidths[0] + 5, y + 6);
    
    // Time
    doc.setTextColor(0, 0, 0);
    doc.setFont('helvetica', 'normal');
    const timeStr = formatTime(chord.start);
    doc.text(timeStr, x + colWidths[0] + colWidths[1] + 5, y + 6);
    
    y += rowHeight;
  }
  
  // Border
  doc.setDrawColor(200, 200, 200);
  doc.setLineWidth(0.5);
  doc.rect(x, startY, width, (displayChords.length + 1) * rowHeight);
  
  if (rootChordChanges.length > maxRows) {
    y += 5;
    doc.setFontSize(9);
    doc.setTextColor(128, 128, 128);
    doc.text(`... and ${rootChordChanges.length - maxRows} more chord changes`, x + 5, y);
    y += 5;
  }
  
  return y;
}

function formatTime(seconds) {
  /**
   * Format seconds as MM:SS
   */
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function getNashvilleNumber(chord, key) {
  /**
   * Convert chord to Nashville Number System notation
   * Based on the key signature
   */
  
  // Parse chord to get root note
  let rootNote = extractRootNote(chord);
  
  // Parse key to get tonic
  let keyRoot = extractRootNote(key);
  
  // Determine if key is major or minor
  const isMinor = key.toLowerCase().includes('m') || key.toLowerCase().includes('minor');
  
  // Convert notes to semitones for calculation
  const noteToSemitone = {
    'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5,
    'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11
  };
  
  const keySemitone = noteToSemitone[keyRoot] || 0;
  const chordSemitone = noteToSemitone[rootNote] || 0;
  
  // Calculate interval
  let interval = (chordSemitone - keySemitone + 12) % 12;
  
  // Map to Nashville numbers
  const majorNumbers = ['1', 'b2', '2', 'b3', '3', '4', 'b5', '5', 'b6', '6', 'b7', '7'];
  const minorNumbers = ['1', 'b2', 'b3', '3', '4', 'b5', '5', 'b6', '6', 'b7', '7', '7'];
  
  let number = isMinor ? minorNumbers[interval] : majorNumbers[interval];
  
  // Add chord quality indicators
  const chordLower = chord.toLowerCase();
  
  if (chordLower.includes('m') && !chordLower.includes('maj')) {
    // Minor chord
    number += 'm';
  }
  
  if (chordLower.includes('maj7')) {
    number += 'maj7';
  } else if (chordLower.includes('7')) {
    number += '7';
  }
  
  if (chordLower.includes('dim') || chordLower.includes('°')) {
    number += '°';
  }
  if (chordLower.includes('aug') || chordLower.includes('+')) {
    number += '+';
  }
  if (chordLower.includes('sus')) {
    number += 'sus';
  }
  
  return number;
}

async function updateJobStatus(jobId, status, progress, error = null) {
  const updateExpr = error
    ? 'SET #status = :status, progress = :progress, errorMessage = :error, updatedAt = :updated'
    : 'SET #status = :status, progress = :progress, updatedAt = :updated';
  
  const exprValues = {
    ':status': status,
    ':progress': progress,
    ':updated': new Date().toISOString()
  };
  
  if (error) {
    exprValues[':error'] = error;
  }
  
  await docClient.send(new UpdateCommand({
    TableName: JOBS_TABLE,
    Key: { jobId },
    UpdateExpression: updateExpr,
    ExpressionAttributeNames: { '#status': 'status' },
    ExpressionAttributeValues: exprValues
  }));
}

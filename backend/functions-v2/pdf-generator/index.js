// DIAGNOSTIC PDF Generator - Shows only patterns and progressions
// This is a temporary version for debugging chord detection
// Full version backed up as: index-full-version.js.backup

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
  const timestamp = new Date().toISOString();
  console.log('=' .repeat(80));
  console.log(`[${timestamp}] 🎵 DIAGNOSTIC PDF GENERATOR STARTING`);
  console.log('=' .repeat(80));
  console.log('Event:', JSON.stringify(event, null, 2));
  
  try {
    const { jobId } = event;
    
    if (!jobId) {
      console.error('[ERROR] Missing jobId in event');
      throw new Error('Missing jobId in event');
    }

    console.log(`[INFO] Processing job: ${jobId}`);

    // Update status
    console.log('[STEP 1] Updating job status to GENERATING_PDF (90%)');
    await updateJobStatus(jobId, 'GENERATING_PDF', 90);
    console.log('[STEP 1] ✓ Status updated successfully');

    // Get job data from DynamoDB
    console.log('[STEP 2] Fetching job data from DynamoDB');
    const jobData = await getJobData(jobId);
    console.log('[STEP 2] ✓ Job data retrieved successfully');

    // Generate diagnostic PDF
    console.log('[STEP 3] Generating diagnostic PDF');
    const pdfBuffer = await generateDiagnosticPDF(jobData);
    console.log(`[STEP 3] ✓ PDF generated successfully (${pdfBuffer.length} bytes)`);

    // Upload to S3
    console.log('[STEP 4] Uploading PDF to S3');
    const s3Key = `pdfs/${jobId}.pdf`;
    await s3Client.send(new PutObjectCommand({
      Bucket: PDF_BUCKET,
      Key: s3Key,
      Body: pdfBuffer,
      ContentType: 'application/pdf'
    }));

    const pdfUrl = `https://${PDF_BUCKET}.s3.amazonaws.com/${s3Key}`;
    console.log(`[STEP 4] ✓ PDF uploaded to S3: ${pdfUrl}`);

    // Update job as complete
    console.log('[STEP 5] Updating job status to COMPLETE (100%)');
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
    console.log('[STEP 5] ✓ Job marked as COMPLETE');

    console.log('=' .repeat(80));
    console.log('✅ DIAGNOSTIC PDF GENERATION COMPLETED SUCCESSFULLY');
    console.log('=' .repeat(80));

    return {
      statusCode: 200,
      body: {
        message: 'Diagnostic PDF generated successfully',
        pdfUrl,
        mode: 'diagnostic'
      }
    };

  } catch (error) {
    console.error('=' .repeat(80));
    console.error('❌ PDF GENERATION FAILED');
    console.error('=' .repeat(80));
    console.error('Error:', error);
    console.error('Stack:', error.stack);
    
    if (event.jobId) {
      console.log(`[ERROR] Updating job ${event.jobId} to FAILED status`);
      await updateJobStatus(event.jobId, 'FAILED', 0, error.message);
    }
    
    throw error;
  }
};

async function generateDiagnosticPDF(jobData) {
  console.log('📄 Generating diagnostic PDF...');
  
  const doc = new jsPDF();
  const chordsData = jobData.chordsData || {};
  let yPos = 20;

  // Title
  doc.setFontSize(20);
  doc.setFont('helvetica', 'bold');
  doc.text('Pattern Diagnostic Report', 105, yPos, { align: 'center' });
  yPos += 15;

  // Song info
  doc.setFontSize(12);
  doc.setFont('helvetica', 'normal');
  doc.text(`Song: ${jobData.videoTitle || 'Unknown'}`, 20, yPos);
  yPos += 7;
  doc.text(`Key: ${chordsData.key || 'Unknown'} ${chordsData.mode || ''}`, 20, yPos);
  yPos += 7;
  doc.text(`Tempo: ${chordsData.tempo || 'Unknown'} BPM`, 20, yPos);
  yPos += 7;
  doc.text(`Total Chords: ${chordsData.totalChords || 0}`, 20, yPos);
  yPos += 7;
  doc.text(`Duration: ${chordsData.duration || 0}s`, 20, yPos);
  yPos += 15;

  // Separator
  doc.setDrawColor(0, 0, 0);
  doc.line(20, yPos, 190, yPos);
  yPos += 10;

  // Pattern Analysis
  const patternAnalysis = chordsData.patternAnalysis || [];
  
  if (patternAnalysis.length > 0) {
    doc.setFontSize(16);
    doc.setFont('helvetica', 'bold');
    doc.text('DETECTED REPEATING PATTERNS', 20, yPos);
    yPos += 10;

    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.text(`Found ${patternAnalysis.length} repeating patterns`, 20, yPos);
    yPos += 15;

    // Display each pattern
    for (const pattern of patternAnalysis) {
      // Check for page break
      if (yPos > 250) {
        doc.addPage();
        yPos = 20;
      }

      // Pattern header
      doc.setFontSize(14);
      doc.setFont('helvetica', 'bold');
      doc.text(`Pattern ${pattern.patternNumber}`, 20, yPos);
      yPos += 8;

      // Progression (large and clear)
      doc.setFontSize(16);
      doc.setFont('helvetica', 'normal');
      
      // Show both chord names and Nashville numbers
      const chordProgression = pattern.progression.join('  →  ');
      const nashvilleProgression = pattern.nashvilleProgression 
        ? pattern.nashvilleProgression.join('  →  ')
        : 'N/A';
      
      // Chord names
      const chordLines = doc.splitTextToSize(chordProgression, 170);
      chordLines.forEach(line => {
        doc.text(line, 25, yPos);
        yPos += 8;
      });
      
      // Nashville numbers (in parentheses)
      doc.setFontSize(12);
      doc.setFont('helvetica', 'italic');
      const nashvilleLines = doc.splitTextToSize(`(${nashvilleProgression})`, 170);
      nashvilleLines.forEach(line => {
        doc.text(line, 25, yPos);
        yPos += 7;
      });
      yPos += 2;

      // Details
      doc.setFontSize(11);
      doc.setFont('helvetica', 'normal');
      doc.text(`Length: ${pattern.length} chords`, 25, yPos);
      yPos += 6;
      doc.text(`Occurrences: ${pattern.occurrences} times in the song`, 25, yPos);
      yPos += 6;

      // Show where it appears (with timestamps)
      if (chordsData.chords && pattern.positions && pattern.positions.length > 0) {
        const times = pattern.positions
          .filter(pos => pos < chordsData.chords.length)
          .map(pos => {
            const chord = chordsData.chords[pos];
            const time = chord.start || chord.time || 0;
            return `${Math.floor(time / 60)}:${String(Math.floor(time % 60)).padStart(2, '0')}`;
          })
          .slice(0, 10);

        doc.text(`Appears at: ${times.join(', ')}${pattern.positions.length > 10 ? '...' : ''}`, 25, yPos);
        yPos += 6;
      }

      yPos += 10;
    }
  } else {
    doc.setFontSize(14);
    doc.setFont('helvetica', 'bold');
    doc.text('NO REPEATING PATTERNS DETECTED', 20, yPos);
    yPos += 10;

    doc.setFontSize(11);
    doc.setFont('helvetica', 'normal');
    doc.text('This could mean:', 20, yPos);
    yPos += 7;
    doc.text('• The song has no repeating chord progressions', 25, yPos);
    yPos += 6;
    doc.text('• The chord detection is too noisy', 25, yPos);
    yPos += 6;
    doc.text('• The song is through-composed (no verse/chorus structure)', 25, yPos);
    yPos += 15;
  }

  // Add raw chord sequence
  if (yPos > 200) {
    doc.addPage();
    yPos = 20;
  }

  doc.setDrawColor(0, 0, 0);
  doc.line(20, yPos, 190, yPos);
  yPos += 10;

  doc.setFontSize(16);
  doc.setFont('helvetica', 'bold');
  doc.text('RAW CHORD SEQUENCE', 20, yPos);
  yPos += 10;

  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  doc.text('First 50 chords detected:', 20, yPos);
  yPos += 10;

  if (chordsData.chords && chordsData.chords.length > 0) {
    const chordsToShow = chordsData.chords.slice(0, 50);
    
    // Display in compact format: 10 chords per line
    let chordLine = [];
    for (let i = 0; i < chordsToShow.length; i++) {
      const chord = chordsToShow[i];
      const time = (chord.start || chord.time || 0).toFixed(1);
      chordLine.push(`${chord.chord}(${time}s)`);

      if (chordLine.length === 10 || i === chordsToShow.length - 1) {
        if (yPos > 270) {
          doc.addPage();
          yPos = 20;
        }
        doc.text(chordLine.join('  '), 20, yPos);
        yPos += 6;
        chordLine = [];
      }
    }

    if (chordsData.chords.length > 50) {
      yPos += 5;
      doc.text(`... and ${chordsData.chords.length - 50} more chords`, 20, yPos);
    }
  }

  // Footer
  yPos += 15;
  if (yPos > 270) {
    doc.addPage();
    yPos = 20;
  }
  doc.setFontSize(10);
  doc.setFont('helvetica', 'italic');
  doc.text('Generated by ChordScout - Diagnostic Mode', 105, yPos, { align: 'center' });
  
  return Buffer.from(doc.output('arraybuffer'));
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
  console.log(`[DynamoDB] Updating job ${jobId}: status=${status}, progress=${progress}%`);
  
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
    console.log(`[DynamoDB] Error message: ${errorMessage}`);
  }
  
  try {
    await docClient.send(new UpdateCommand({
      TableName: JOBS_TABLE,
      Key: { jobId },
      UpdateExpression: updateExpr,
      ExpressionAttributeNames: { '#status': 'status' },
      ExpressionAttributeValues: exprValues
    }));
    console.log(`[DynamoDB] ✓ Update successful`);
  } catch (error) {
    console.error(`[DynamoDB] ❌ Update failed:`, error);
    throw error;
  }
}

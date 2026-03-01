// Bass NNS PDF Generator
// Generates Nashville Number System chart for bass transcription

const { S3Client, PutObjectCommand } = require('@aws-sdk/client-s3');
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, GetCommand, UpdateCommand } = require('@aws-sdk/lib-dynamodb');
const { jsPDF } = require('jspdf');

const s3Client = new S3Client({});
const dynamoClient = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(dynamoClient);

const JOBS_TABLE = process.env.DYNAMODB_JOBS_TABLE || 'ChordScout-Jobs-V2-dev';
const PDF_BUCKET = process.env.S3_PDF_BUCKET || 'chordscout-pdfs-dev-090130568474';

exports.handler = async (event) => {
  const timestamp = new Date().toISOString();
  console.log('='.repeat(80));
  console.log(`[${timestamp}] 🎸 BASS NNS PDF GENERATOR STARTING`);
  console.log('='.repeat(80));
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
    await updateJobStatus(jobId, 'GENERATING_PDF', 90, 'Generating NNS chart PDF...');
    console.log('[STEP 1] ✓ Status updated successfully');

    // Get job data from DynamoDB
    console.log('[STEP 2] Fetching job data from DynamoDB');
    const jobData = await getJobData(jobId);
    console.log('[STEP 2] ✓ Job data retrieved successfully');

    // Validate bass data exists
    if (!jobData.bassData) {
      throw new Error('No bass transcription data found in job');
    }

    // Generate PDF
    console.log('[STEP 3] Generating Bass NNS PDF');
    const pdfBuffer = await generateBassNNSPDF(jobData);
    console.log(`[STEP 3] ✓ PDF generated successfully (${pdfBuffer.length} bytes)`);

    // Upload to S3
    console.log('[STEP 4] Uploading PDF to S3');
    const s3Key = `pdfs/${jobId}-bass-nns.pdf`;
    await s3Client.send(new PutObjectCommand({
      Bucket: PDF_BUCKET,
      Key: s3Key,
      Body: pdfBuffer,
      ContentType: 'application/pdf'
    }));

    const pdfUrl = `https://${PDF_BUCKET}.s3.amazonaws.com/${s3Key}`;
    console.log(`[STEP 4] ✓ PDF uploaded to S3: ${pdfUrl}`);

    // Update job as complete
    console.log('[STEP 5] Updating job status to COMPLETED (100%)');
    await docClient.send(new UpdateCommand({
      TableName: JOBS_TABLE,
      Key: { jobId },
      UpdateExpression: 'SET pdfUrl = :url, #status = :status, progress = :progress, statusMessage = :statusMessage, completedAt = :completed, updatedAt = :updated',
      ExpressionAttributeNames: { '#status': 'status' },
      ExpressionAttributeValues: {
        ':url': pdfUrl,
        ':status': 'COMPLETED',
        ':progress': 100,
        ':statusMessage': 'Complete! Your bass NNS chart is ready.',
        ':completed': new Date().toISOString(),
        ':updated': new Date().toISOString()
      }
    }));
    console.log('[STEP 5] ✓ Job marked as COMPLETED');

    console.log('='.repeat(80));
    console.log('✅ BASS NNS PDF GENERATION COMPLETED SUCCESSFULLY');
    console.log('='.repeat(80));

    return {
      statusCode: 200,
      body: {
        message: 'Bass NNS PDF generated successfully',
        pdfUrl
      }
    };

  } catch (error) {
    console.error('='.repeat(80));
    console.error('❌ PDF GENERATION FAILED');
    console.error('='.repeat(80));
    console.error('Error:', error);
    console.error('Stack:', error.stack);
    
    if (event.jobId) {
      console.log(`[ERROR] Updating job ${event.jobId} to FAILED status`);
      await updateJobStatus(event.jobId, 'FAILED', 0, error.message);
    }
    
    throw error;
  }
};

async function generateBassNNSPDF(jobData) {
  const doc = new jsPDF();
  const bassData = jobData.bassData;
  let yPos = 20;

  // Title
  doc.setFontSize(20);
  doc.setFont('helvetica', 'bold');
  doc.text('Bass Line - Nashville Number System', 105, yPos, { align: 'center' });
  yPos += 15;

  // Song info
  doc.setFontSize(12);
  doc.setFont('helvetica', 'normal');
  if (jobData.filename) {
    doc.text(`Song: ${jobData.filename}`, 105, yPos, { align: 'center' });
    yPos += 7;
  }

  // Metadata header (key, tempo, time signature)
  const metadataText = [
    `Key: ${bassData.key} ${bassData.mode}`,
    bassData.relativeMajor ? `(Relative Major: ${bassData.relativeMajor})` : null,
    `Tempo: ${Math.round(bassData.tempo)} BPM`,
    `Time: ${bassData.timeSignature}`
  ].filter(Boolean).join('  |  ');
  
  doc.text(metadataText, 105, yPos, { align: 'center' });
  yPos += 10;

  // Confidence indicator
  if (bassData.confidence) {
    doc.setFontSize(10);
    doc.setFont('helvetica', 'italic');
    doc.setTextColor(102, 102, 102);
    doc.text(`Key detection confidence: ${(bassData.confidence * 100).toFixed(0)}%`, 105, yPos, { align: 'center' });
    yPos += 5;
  }

  yPos += 5;

  // Separator
  doc.setDrawColor(0, 0, 0);
  doc.setTextColor(0, 0, 0);
  doc.line(20, yPos, 190, yPos);
  yPos += 10;

  // Legend
  doc.setFontSize(10);
  doc.setFont('helvetica', 'italic');
  doc.setTextColor(102, 102, 102);
  doc.text('Format: | NNS numbers | (note names)', 20, yPos);
  yPos += 5;
  doc.text('"-" indicates beats without new note attacks', 20, yPos);
  yPos += 10;

  // Render measures
  const measures = bassData.measures || [];
  const measuresPerLine = 4; // 4 measures per line
  let measureCount = 0;

  doc.setFontSize(11);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(0, 0, 0);

  for (let i = 0; i < measures.length; i++) {
    const measure = measures[i];
    
    // Check for page break
    if (yPos > 260) {
      doc.addPage();
      yPos = 20;
      
      // Re-add header on new page
      doc.setFontSize(14);
      doc.setFont('helvetica', 'bold');
      doc.text('Bass Line - Nashville Number System (continued)', 105, yPos, { align: 'center' });
      yPos += 15;
    }

    // Start new line every 4 measures
    if (measureCount % measuresPerLine === 0) {
      if (measureCount > 0) {
        yPos += 15; // Space between lines
      }
      
      // Measure numbers line
      doc.setFontSize(9);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(102, 102, 102);
      
      const measureNumbers = [];
      for (let j = 0; j < measuresPerLine && (i + j) < measures.length; j++) {
        measureNumbers.push(`M${measures[i + j].measure}`);
      }
      doc.text(measureNumbers.join('        '), 20, yPos);
      yPos += 5;
    }

    // NNS line
    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(0, 102, 204); // Blue for NNS
    
    const xPos = 20 + (measureCount % measuresPerLine) * 45;
    const nnsDisplay = `| ${measure.nns_display} |`;
    doc.text(nnsDisplay, xPos, yPos);

    // Note names line (below NNS)
    doc.setFontSize(9);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(102, 102, 102); // Gray for note names
    
    const notesDisplay = `(${measure.notes_display})`;
    doc.text(notesDisplay, xPos, yPos + 5);

    measureCount++;

    // Move to next line after 4 measures
    if (measureCount % measuresPerLine === 0) {
      yPos += 10;
    }
  }

  // Summary section
  yPos += 20;
  if (yPos > 250) {
    doc.addPage();
    yPos = 20;
  }

  doc.setDrawColor(0, 0, 0);
  doc.line(20, yPos, 190, yPos);
  yPos += 10;

  doc.setFontSize(14);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(0, 0, 0);
  doc.text('Summary', 20, yPos);
  yPos += 10;

  doc.setFontSize(11);
  doc.setFont('helvetica', 'normal');
  doc.text(`Total Measures: ${bassData.totalMeasures}`, 20, yPos);
  yPos += 7;
  doc.text(`Total Note Attacks: ${bassData.totalNotes}`, 20, yPos);
  yPos += 7;
  doc.text(`Duration: ${Math.round(bassData.duration)}s (${Math.floor(bassData.duration / 60)}:${String(Math.floor(bassData.duration % 60)).padStart(2, '0')})`, 20, yPos);
  yPos += 7;
  doc.text(`Average Notes per Measure: ${(bassData.totalNotes / bassData.totalMeasures).toFixed(1)}`, 20, yPos);

  // Footer
  yPos += 15;
  if (yPos > 270) {
    doc.addPage();
    yPos = 270;
  }
  doc.setFontSize(10);
  doc.setFont('helvetica', 'italic');
  doc.setTextColor(102, 102, 102);
  doc.text('Generated by ChordScout - Bass Transcription', 105, yPos, { align: 'center' });
  
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

async function updateJobStatus(jobId, status, progress, message) {
  console.log(`[DynamoDB] Updating job ${jobId}: status=${status}, progress=${progress}%`);
  
  const updateExpr = 'SET #status = :status, progress = :progress, statusMessage = :message, updatedAt = :updated';
  
  const exprValues = {
    ':status': status,
    ':progress': progress,
    ':message': message || '',
    ':updated': new Date().toISOString()
  };
  
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

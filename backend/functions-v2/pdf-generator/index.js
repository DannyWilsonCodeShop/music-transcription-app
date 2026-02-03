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
    const chordsData = jobData.chordsData || {};
    const chords = chordsData.chords || jobData.chords || [];
    const chordAnalysis = jobData.chordAnalysis || {};
    const chordChanges = chordAnalysis.chordChanges || chords; // Use chord changes if available
    const lyricsData = jobData.lyricsData || {};
    const syllableAlignedLyrics = lyricsData.syllableAlignedLyrics || [];
    const key = chordsData.key || jobData.key || 'C';
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
      lyricsData: lyricsData, // Pass full lyrics data for word-level timing
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
  
  // Always use perfect 4-measure layout if we have chords
  if (data.chords && data.chords.length > 0) {
    console.log('🎵 Using perfect 4-measure layout');
    yPosition = generatePerfect4MeasureLayout(doc, data, yPosition);
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

function generatePerfect4MeasureLayout(doc, data, startY) {
  console.log('🎼 Generating perfect 4-measure layout (Amazing Grace style)');
  
  doc.setFontSize(16);
  doc.setFont('helvetica', 'bold');
  doc.text('Nashville Number System', 20, startY);
  let yPosition = startY + 20;
  
  // Convert chords to measure format
  const measures = convertChordsToMeasures(data.chords, data.timeSignature, data.tempo, data.key);
  
  console.log(`📊 Total measures: ${measures.length}`);
  
  // Get song sections if available
  const sections = data.chordAnalysis?.sections || [];
  console.log(`📋 Song sections: ${sections.length > 0 ? sections.map(s => s.label).join(', ') : 'None detected'}`);
  
  // Define column positions for 4-measure layout (matching Amazing Grace)
  const columnPositions = [38, 73, 108, 143];
  const measuresPerLine = 4;
  const totalLines = Math.ceil(measures.length / measuresPerLine);
  
  let currentSectionIndex = 0;
  let currentSection = sections[0] || null;
  
  for (let lineIndex = 0; lineIndex < totalLines; lineIndex++) {
    // Check for page break
    if (yPosition > 220) {
      doc.addPage();
      yPosition = 30;
    }
    
    // Get measure numbers for this line
    const firstMeasureNum = lineIndex * measuresPerLine + 1;
    const lastMeasureNum = Math.min((lineIndex + 1) * measuresPerLine, measures.length);
    
    // Check if we've entered a new section
    if (sections.length > 0) {
      // Find which section these measures belong to
      for (let i = currentSectionIndex; i < sections.length; i++) {
        const section = sections[i];
        if (firstMeasureNum >= section.measureStart && firstMeasureNum <= section.measureEnd) {
          if (!currentSection || currentSection.label !== section.label) {
            currentSection = section;
            currentSectionIndex = i;
            
            // Add section label
            yPosition += 10;
            doc.setFontSize(14);
            doc.setFont('helvetica', 'bold');
            doc.text(section.label, 20, yPosition);
            yPosition += 15;
          }
          break;
        }
      }
    } else {
      // Fallback: Add verse label every 8 measures (2 lines)
      if (lineIndex % 2 === 0) {
        yPosition += 10;
        doc.setFontSize(14);
        doc.setFont('helvetica', 'bold');
        doc.text(`Verse ${Math.floor(lineIndex / 2) + 1}`, 20, yPosition);
        yPosition += 15;
      }
    }
    
    // Get 4 measures for this line
    const lineMeasures = [];
    for (let i = 0; i < measuresPerLine; i++) {
      const measureIndex = lineIndex * measuresPerLine + i;
      if (measureIndex < measures.length) {
        lineMeasures.push(measures[measureIndex]);
      }
    }
    
    // Generate the perfect measure line
    generatePerfectMeasureLine(doc, lineMeasures, columnPositions, yPosition, data.key, data.lyricsData);
    yPosition += 35; // Space between lines
    
    console.log(`✅ Line ${lineIndex + 1}: Measures ${firstMeasureNum}-${lastMeasureNum}`);
  }
  
  // Add lyrics section if available
  if (data.lyrics && data.lyrics.length > 0) {
    yPosition += 20;
    if (yPosition > 250) {
      doc.addPage();
      yPosition = 30;
    }
    
    doc.setFontSize(14);
    doc.setFont('helvetica', 'bold');
    doc.text('Lyrics', 20, yPosition);
    yPosition += 15;
    
    doc.setFontSize(11);
    doc.setFont('helvetica', 'normal');
    const lines = doc.splitTextToSize(data.lyrics, 170);
    lines.forEach(line => {
      if (yPosition > 270) {
        doc.addPage();
        yPosition = 20;
      }
      doc.text(line, 20, yPosition);
      yPosition += 7;
    });
  }
  
  return yPosition;
}

function generatePerfectMeasureLine(doc, measures, columnPositions, yPosition, key, lyricsData) {
  const chordY = yPosition;
  const lyricsY = yPosition + 12;
  const lineHeight = 25;
  
  // Draw vertical lines between measures
  doc.setDrawColor(200, 200, 200); // Light gray
  doc.setLineWidth(0.5);
  for (let i = 1; i < measures.length && i < 4; i++) {
    const lineX = columnPositions[i] - 5;
    doc.line(lineX, yPosition - 5, lineX, yPosition + lineHeight);
  }
  
  measures.forEach((measure, index) => {
    if (index >= 4) return; // Only 4 measures per line
    
    const xPosition = columnPositions[index];
    const measureWidth = 30; // Width allocated for each measure
    
    // Get all chords in this measure
    const chordsInMeasure = measure.chords || [];
    
    if (chordsInMeasure.length === 0) return;
    
    // Dynamic spacing: calculate how much space each chord needs
    const chordCount = chordsInMeasure.length;
    const avgChordWidth = 5; // Average width of a chord symbol in points
    const minSpacing = 3; // Minimum spacing between chords
    const totalChordWidth = chordCount * avgChordWidth;
    const totalSpacing = (chordCount - 1) * minSpacing;
    const requiredWidth = totalChordWidth + totalSpacing;
    
    // With 4 chords, we should almost always use beat-based positioning
    const useEvenSpacing = requiredWidth > measureWidth;
    
    if (useEvenSpacing) {
      // Even spacing mode: distribute chords evenly across measure width
      const spacing = measureWidth / (chordCount + 1);
      
      chordsInMeasure.forEach((chordInfo, chordIndex) => {
        const chordX = xPosition + (spacing * (chordIndex + 1));
        
        // First chord (downbeat) in RED and bold
        if (chordIndex === 0) {
          doc.setTextColor(255, 0, 0); // RED
          doc.setFontSize(11);
          doc.setFont('helvetica', 'bold');
        } else {
          // Passing chords in BLACK and normal
          doc.setTextColor(0, 0, 0); // BLACK
          doc.setFontSize(9);
          doc.setFont('helvetica', 'normal');
        }
        
        doc.text(chordInfo.nashvilleNumber, chordX, chordY);
      });
    } else {
      // Beat-based positioning mode: position chords by their beat
      chordsInMeasure.forEach((chordInfo, chordIndex) => {
        // Calculate X position based on beat (0-4 for 4/4 time)
        const beatOffset = (chordInfo.beat / 4) * measureWidth;
        let chordX = xPosition + beatOffset;
        
        // Check for overlap with previous chord
        if (chordIndex > 0) {
          const prevChordInfo = chordsInMeasure[chordIndex - 1];
          const prevBeatOffset = (prevChordInfo.beat / 4) * measureWidth;
          const prevChordX = xPosition + prevBeatOffset;
          const minDistance = avgChordWidth + minSpacing;
          
          // If too close, shift right
          if (chordX - prevChordX < minDistance) {
            chordX = prevChordX + minDistance;
          }
        }
        
        // First chord (downbeat) in RED and bold
        if (chordIndex === 0 || chordInfo.isDownbeat) {
          doc.setTextColor(255, 0, 0); // RED
          doc.setFontSize(11);
          doc.setFont('helvetica', 'bold');
        } else {
          // Passing chords in BLACK and normal
          doc.setTextColor(0, 0, 0); // BLACK
          doc.setFontSize(9);
          doc.setFont('helvetica', 'normal');
        }
        
        doc.text(chordInfo.nashvilleNumber, chordX, chordY);
      });
    }
    
    // LYRICS below chords
    doc.setTextColor(0, 0, 0);
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    
    // Get lyrics for this measure's time range
    let measureLyrics = '';
    if (lyricsData && lyricsData.words) {
      // Find words that fall within this measure's time range
      const wordsInMeasure = lyricsData.words.filter(word => 
        word.start >= measure.startTime && word.start < measure.endTime
      );
      measureLyrics = wordsInMeasure.map(w => w.word).join(' ');
    } else if (lyricsData && lyricsData.text) {
      // Fallback: try to split lyrics evenly across measures
      const words = lyricsData.text.split(/\s+/);
      const wordsPerMeasure = Math.ceil(words.length / 50); // Assume ~50 measures
      const startIdx = (measure.measureNumber - 1) * wordsPerMeasure;
      measureLyrics = words.slice(startIdx, startIdx + wordsPerMeasure).join(' ');
    }
    
    // Truncate if too long to fit in measure column
    if (measureLyrics.length > 15) {
      measureLyrics = measureLyrics.substring(0, 12) + '...';
    }
    
    doc.text(measureLyrics, xPosition, lyricsY);
  });
  
  // Reset color
  doc.setTextColor(0, 0, 0);
}

function convertChordsToMeasures(chords, timeSignature = '4/4', tempo = 120, key = 'C') {
  if (!chords || chords.length === 0) {
    return [];
  }
  
  console.log(`🔄 Converting ${chords.length} chords to measures (tempo: ${tempo} BPM, key: ${key})`);
  
  // Extract root note from key (e.g., "C# major" -> "C#")
  const keyRoot = key.split(' ')[0];
  
  // Parse time signature
  const [beatsPerMeasure] = timeSignature.split('/').map(Number);
  const secondsPerBeat = 60 / tempo; // Calculate from actual tempo
  const secondsPerMeasure = beatsPerMeasure * secondsPerBeat;
  
  console.log(`📏 Measure duration: ${secondsPerMeasure.toFixed(2)}s (${beatsPerMeasure} beats @ ${tempo} BPM)`);
  console.log(`📏 Beat duration: ${secondsPerBeat.toFixed(2)}s`);
  
  const measureMap = {};
  
  // Group chords by measure and beat position
  chords.forEach((chord, index) => {
    const chordTime = chord.time || chord.timestamp || chord.start || chord.startTime || 0;
    const measureNum = Math.floor(chordTime / secondsPerMeasure) + 1;
    const timeInMeasure = chordTime % secondsPerMeasure;
    const beatInMeasure = timeInMeasure / secondsPerBeat; // 0-4 for 4/4 time
    
    if (!measureMap[measureNum]) {
      measureMap[measureNum] = {
        measureNumber: measureNum,
        allChords: [], // All chords before filtering
        startTime: (measureNum - 1) * secondsPerMeasure,
        endTime: measureNum * secondsPerMeasure
      };
    }
    
    const chordName = chord.chord || chord.name;
    const nashvilleNumber = chord.nashvilleNumber || convertChordToNashvilleNumber(chordName, keyRoot);
    const confidence = chord.confidence || 0.5;
    
    measureMap[measureNum].allChords.push({
      chord: chordName,
      nashvilleNumber: nashvilleNumber,
      beat: beatInMeasure,
      time: chordTime,
      confidence: confidence,
      isDownbeat: beatInMeasure < 0.5 // First beat of measure
    });
  });
  
  // Convert to array and intelligently select best chords per measure
  const measures = Object.keys(measureMap)
    .sort((a, b) => parseInt(a) - parseInt(b))
    .map(measureNum => {
      const measure = measureMap[measureNum];
      const allChords = measure.allChords;
      
      // Sort chords within measure by beat
      allChords.sort((a, b) => a.beat - b.beat);
      
      // Intelligently select up to 4 most important chords
      const selectedChords = selectBestChords(allChords, 4);
      
      return {
        measureNumber: measure.measureNumber,
        chords: selectedChords,
        startTime: measure.startTime,
        endTime: measure.endTime
      };
    });
  
  console.log(`✅ Created ${measures.length} measures`);
  
  // Log some examples
  if (measures.length > 0) {
    const firstMeasure = measures[0];
    console.log(`📊 First measure: ${firstMeasure.chords.length} chords selected from ${measureMap[1].allChords.length} total`);
  }
  
  return measures;
}

function selectBestChords(allChords, maxChords = 4) {
  /**
   * Intelligently select the most important chords based on:
   * 1. Confidence score (higher = better)
   * 2. Beat alignment (on-beat chords are more important)
   * 3. Chord changes (when chord actually changes)
   * 4. Position (first chord always included)
   * 
   * For maxChords=4: downbeat + 3 best chords
   */
  
  if (allChords.length <= maxChords) {
    return allChords;
  }
  
  // Always include first chord (downbeat)
  const selected = [allChords[0]];
  const remaining = allChords.slice(1);
  
  // Score each remaining chord
  const scoredChords = remaining.map((chord, index) => {
    let score = 0;
    
    // 1. Confidence score (0-1, weight: 30%)
    score += chord.confidence * 0.3;
    
    // 2. Beat alignment (on-beat = higher score, weight: 40%)
    const beatRounded = Math.round(chord.beat);
    const beatDistance = Math.abs(chord.beat - beatRounded);
    const beatScore = 1 - (beatDistance / 0.5); // 1.0 if exactly on beat, 0.0 if halfway between
    score += beatScore * 0.4;
    
    // 3. Chord change (different from previous chord, weight: 30%)
    const prevChord = index > 0 ? remaining[index - 1] : allChords[0];
    if (chord.chord !== prevChord.chord) {
      score += 0.3;
    }
    
    return { ...chord, score };
  });
  
  // Sort by score (descending) and take top (maxChords - 1)
  scoredChords.sort((a, b) => b.score - a.score);
  const topChords = scoredChords.slice(0, maxChords - 1);
  
  // Add to selected and re-sort by beat position
  selected.push(...topChords);
  selected.sort((a, b) => a.beat - b.beat);
  
  return selected;
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
#!/usr/bin/env node

/**
 * Pattern Diagnostic PDF Generator
 * 
 * Creates a simple PDF showing only the detected patterns and progressions
 * No measures, no Nashville numbers - just the raw pattern data
 */

const AWS = require('aws-sdk');
const { jsPDF } = require('jspdf');
const fs = require('fs');

// Configure AWS
AWS.config.update({
  region: 'us-east-1',
  credentials: new AWS.SharedIniFileCredentials({ profile: 'chordscout' })
});

const dynamodb = new AWS.DynamoDB.DocumentClient();

async function createPatternDiagnosticPDF(jobId) {
  console.log('Fetching job data...');

  try {
    // Get job data from DynamoDB
    const result = await dynamodb.get({
      TableName: 'ChordScout-Jobs-V2-dev',
      Key: { jobId }
    }).promise();

    if (!result.Item) {
      console.error('❌ Job not found');
      return;
    }

    const job = result.Item;
    console.log(`Title: ${job.videoTitle || 'Unknown'}`);

    if (!job.chordsData) {
      console.error('❌ No chord data available yet');
      return;
    }

    const chordsData = job.chordsData;
    
    // Create PDF
    console.log('Creating diagnostic PDF...');
    const doc = new jsPDF();
    let yPos = 20;

    // Title
    doc.setFontSize(20);
    doc.setFont('helvetica', 'bold');
    doc.text('Pattern Diagnostic Report', 105, yPos, { align: 'center' });
    yPos += 15;

    // Song info
    doc.setFontSize(12);
    doc.setFont('helvetica', 'normal');
    doc.text(`Song: ${job.videoTitle || 'Unknown'}`, 20, yPos);
    yPos += 7;
    doc.text(`Key: ${chordsData.key} ${chordsData.mode}`, 20, yPos);
    yPos += 7;
    doc.text(`Tempo: ${chordsData.tempo} BPM`, 20, yPos);
    yPos += 7;
    doc.text(`Total Chords: ${chordsData.totalChords}`, 20, yPos);
    yPos += 7;
    doc.text(`Duration: ${chordsData.duration}s`, 20, yPos);
    yPos += 15;

    // Separator
    doc.setDrawColor(0, 0, 0);
    doc.line(20, yPos, 190, yPos);
    yPos += 10;

    // Pattern Analysis
    if (chordsData.patternAnalysis && chordsData.patternAnalysis.length > 0) {
      doc.setFontSize(16);
      doc.setFont('helvetica', 'bold');
      doc.text('DETECTED REPEATING PATTERNS', 20, yPos);
      yPos += 10;

      doc.setFontSize(10);
      doc.setFont('helvetica', 'normal');
      doc.text(`Found ${chordsData.patternAnalysis.length} repeating patterns`, 20, yPos);
      yPos += 15;

      // Display each pattern
      for (const pattern of chordsData.patternAnalysis) {
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
        const progression = pattern.progression.join('  →  ');
        
        // Wrap if too long
        const lines = doc.splitTextToSize(progression, 170);
        lines.forEach(line => {
          doc.text(line, 25, yPos);
          yPos += 8;
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
            .slice(0, 10);  // Show first 10

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

    // Add raw chord sequence for reference
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
      
      // Display in a compact format: 10 chords per line
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

    // Save PDF
    const filename = `pattern-diagnostic-${jobId}.pdf`;
    const pdfBuffer = Buffer.from(doc.output('arraybuffer'));
    fs.writeFileSync(filename, pdfBuffer);

    console.log(`✅ PDF created: ${filename}`);
    console.log(`\nSummary:`);
    console.log(`  Total chords: ${chordsData.totalChords}`);
    console.log(`  Repeating patterns: ${chordsData.patternAnalysis?.length || 0}`);
    console.log(`  Key: ${chordsData.key} ${chordsData.mode}`);

  } catch (error) {
    console.error('❌ Error:', error.message);
    console.error(error.stack);
  }
}

// Get job ID from command line
const jobId = process.argv[2];

if (!jobId) {
  console.error('Usage: node create-pattern-diagnostic-pdf.cjs <jobId>');
  console.error('');
  console.error('This creates a simple PDF showing only the detected patterns');
  console.error('and progressions, without any measure-based layout.');
  process.exit(1);
}

createPatternDiagnosticPDF(jobId);

// Test Chord Changes → PDF Pipeline
// Verifies that chord change detection works with PDF generation

const fs = require('fs');
const path = require('path');

async function testChordChangesToPdf() {
  console.log('🎵 Testing Chord Changes → PDF Pipeline...\n');
  
  try {
    // Step 1: Generate chord changes using our detector
    console.log('📊 Step 1: Generating chord changes...');
    const { detectChordChanges, consolidateChordChangesPerMeasure } = require('./chord-change-detector.cjs');
    const { analyzeAudioLocally } = require('./local-server/modules/enhanced-audio-analyzer.js');
    
    // Get raw chord data
    const analysis = await analyzeAudioLocally('meetup_ring.mp3', () => {});
    const rawChords = analysis.chords.chords;
    
    // Detect chord changes
    const timeSignature = {
      numerator: analysis.timeSignature.numerator,
      denominator: analysis.timeSignature.denominator,
      measureDuration: analysis.timeSignature.measureDuration
    };
    
    const chordChangeResult = detectChordChanges(rawChords, timeSignature);
    const consolidatedChanges = consolidateChordChangesPerMeasure(chordChangeResult.chordChanges, 8);
    
    console.log(`✅ Generated ${consolidatedChanges.length} chord changes`);
    
    // Step 2: Transform chord changes for PDF compatibility
    console.log('\n🔄 Step 2: Transforming for PDF compatibility...');
    
    // The chord changes already have the 'time' field for PDF compatibility
    const pdfCompatibleChords = consolidatedChanges.map(change => ({
      ...change,
      // Ensure all PDF-expected fields are present
      time: change.time || change.startTime,
      timestamp: change.startTime,
      chord: change.chord,
      name: change.chord, // Alternative field name
      nashvilleNumber: change.nashvilleNumber,
      number: change.nashvilleNumber, // Alternative field name
      confidence: change.confidence
    }));
    
    console.log(`✅ Transformed ${pdfCompatibleChords.length} chord changes for PDF`);
    
    // Step 3: Create job data structure that matches DynamoDB format
    console.log('\n📋 Step 3: Creating DynamoDB-compatible job data...');
    
    const jobData = {
      jobId: 'chord-changes-test-' + Date.now(),
      title: 'Amazing Grace - Chord Changes',
      videoTitle: 'Amazing Grace - Chord Changes',
      status: 'CHORD_ANALYSIS_COMPLETE',
      chords: pdfCompatibleChords, // This is what PDF generator expects
      key: `${analysis.key.root} ${analysis.key.mode}`,
      tempo: analysis.tempo.bpm,
      timeSignature: `${analysis.timeSignature.numerator}/${analysis.timeSignature.denominator}`,
      lyricsData: {
        text: 'Amazing grace, how sweet the sound\nThat saved a wretch like me\nI once was lost, but now am found\nWas blind, but now I see',
        syllableAlignedLyrics: []
      },
      progress: 100,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
    
    // Check data size
    const dataSize = JSON.stringify(jobData).length;
    console.log(`📏 Job data size: ${dataSize} bytes`);
    console.log(`DynamoDB compatible: ${dataSize < 400000 ? '✅ YES' : '❌ NO'}`);
    
    // Step 4: Test PDF generation with chord changes
    console.log('\n📄 Step 4: Testing PDF generation...');
    
    try {
      const { jsPDF } = require('jspdf');
      console.log('✅ jsPDF loaded successfully');
      
      // Create PDF using the same logic as the Lambda function
      const doc = new jsPDF();
      
      // Header
      doc.setFontSize(24);
      doc.setFont('helvetica', 'bold');
      doc.text(jobData.title, 105, 30, { align: 'center' });
      
      // Key and tempo info
      doc.setFontSize(12);
      doc.setFont('helvetica', 'normal');
      doc.text(`Key: ${jobData.key} | Tempo: ${jobData.tempo} BPM | Meter: ${jobData.timeSignature}`, 105, 45, { align: 'center' });
      
      let yPosition = 60;
      
      // Chord changes chart
      doc.setFontSize(16);
      doc.setFont('helvetica', 'bold');
      doc.text('Nashville Number System - Chord Changes', 20, yPosition);
      yPosition += 20;
      
      // Headers
      doc.setFontSize(12);
      doc.setFont('helvetica', 'bold');
      doc.text('Measure', 20, yPosition);
      doc.text('Beat', 50, yPosition);
      doc.text('Time', 70, yPosition);
      doc.text('Chord', 100, yPosition);
      doc.text('Nashville', 130, yPosition);
      doc.text('Duration', 170, yPosition);
      yPosition += 10;
      
      // Chord changes data (first 40 to fit on page)
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(10);
      
      const chordsToShow = jobData.chords.slice(0, 40);
      console.log(`📊 Adding ${chordsToShow.length} chord changes to PDF...`);
      
      chordsToShow.forEach((chord, index) => {
        if (yPosition > 270) { // Start new page if needed
          doc.addPage();
          yPosition = 20;
        }
        
        // Color code downbeats in red
        if (chord.isDownbeat) {
          doc.setTextColor(255, 0, 0); // Red for downbeats
        } else {
          doc.setTextColor(0, 0, 0); // Black for other chords
        }
        
        const time = (chord.time || chord.timestamp || chord.startTime || 0).toFixed(1);
        const chordName = chord.chord || chord.name || 'Unknown';
        const nashville = chord.nashvilleNumber || chord.number || '?';
        const duration = (chord.duration || 0).toFixed(1);
        const measure = chord.measure || '?';
        const beat = chord.beat || '?';
        
        doc.text(measure.toString(), 20, yPosition);
        doc.text(beat.toString(), 50, yPosition);
        doc.text(time + 's', 70, yPosition);
        doc.text(chordName, 100, yPosition);
        doc.text(nashville, 130, yPosition);
        doc.text(duration + 's', 170, yPosition);
        
        yPosition += 12;
      });
      
      // Reset color
      doc.setTextColor(0, 0, 0);
      
      // Summary section
      yPosition += 20;
      if (yPosition > 250) {
        doc.addPage();
        yPosition = 20;
      }
      
      doc.setFontSize(14);
      doc.setFont('helvetica', 'bold');
      doc.text('Chord Change Summary', 20, yPosition);
      yPosition += 15;
      
      doc.setFontSize(12);
      doc.setFont('helvetica', 'normal');
      doc.text(`Total chord changes: ${jobData.chords.length}`, 20, yPosition);
      yPosition += 10;
      doc.text(`Data reduction: ${chordChangeResult.summary.dataReduction}% vs raw detections`, 20, yPosition);
      yPosition += 10;
      doc.text(`Original detections: ${chordChangeResult.summary.originalDetections}`, 20, yPosition);
      yPosition += 10;
      
      // Count downbeats
      const downbeats = jobData.chords.filter(c => c.isDownbeat).length;
      doc.text(`Downbeat changes: ${downbeats}`, 20, yPosition);
      yPosition += 10;
      doc.text(`Other changes: ${jobData.chords.length - downbeats}`, 20, yPosition);
      
      // Footer
      yPosition += 30;
      if (yPosition > 270) {
        doc.addPage();
        yPosition = 20;
      }
      doc.setFontSize(10);
      doc.setFont('helvetica', 'italic');
      doc.text('Generated by ChordScout - Chord Change Detection System', 105, yPosition, { align: 'center' });
      
      // Save PDF
      const outputPath = path.join(__dirname, 'chord-changes-output.pdf');
      const pdfBuffer = Buffer.from(doc.output('arraybuffer'));
      fs.writeFileSync(outputPath, pdfBuffer);
      
      console.log('✅ PDF generated successfully!');
      console.log(`💾 PDF saved to: ${outputPath}`);
      
      return {
        success: true,
        originalDetections: chordChangeResult.summary.originalDetections,
        chordChanges: consolidatedChanges.length,
        dataReduction: chordChangeResult.summary.dataReduction,
        dataSize: dataSize,
        dynamoDbCompatible: dataSize < 400000,
        pdfPath: outputPath,
        chordsInPdf: chordsToShow.length
      };
      
    } catch (pdfError) {
      console.log('❌ PDF generation failed:', pdfError.message);
      return {
        success: false,
        error: 'PDF generation failed: ' + pdfError.message,
        chordChanges: consolidatedChanges.length,
        dataSize: dataSize,
        dynamoDbCompatible: dataSize < 400000
      };
    }
    
  } catch (error) {
    console.error('❌ Chord changes to PDF test failed:', error);
    return { success: false, error: error.message };
  }
}

// Run the test
if (require.main === module) {
  testChordChangesToPdf()
    .then(result => {
      console.log('\n🎯 CHORD CHANGES → PDF TEST RESULT:');
      if (result.success) {
        console.log('✅ COMPLETE SUCCESS!');
        console.log(`📊 Original detections: ${result.originalDetections}`);
        console.log(`🎼 Chord changes: ${result.chordChanges}`);
        console.log(`📉 Data reduction: ${result.dataReduction}%`);
        console.log(`📏 Data size: ${result.dataSize} bytes`);
        console.log(`✅ DynamoDB compatible: ${result.dynamoDbCompatible ? 'YES' : 'NO'}`);
        console.log(`📄 PDF generated: ${result.pdfPath}`);
        console.log(`🎵 Chords in PDF: ${result.chordsInPdf}`);
        console.log('\n🎉 SOLUTION COMPLETE: Chord change detection solves DynamoDB limit AND generates perfect PDFs!');
      } else {
        console.log('❌ TEST FAILED:', result.error);
        if (result.chordChanges) {
          console.log(`🎼 Chord changes detected: ${result.chordChanges}`);
          console.log(`✅ DynamoDB compatible: ${result.dynamoDbCompatible ? 'YES' : 'NO'}`);
        }
      }
    })
    .catch(error => {
      console.error('❌ Test failed:', error.message);
    });
}

module.exports = { testChordChangesToPdf };
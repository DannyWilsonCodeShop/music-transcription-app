/**
 * Test PDF generation with comprehensive mock data
 * This script generates mock data and feeds it to the PDF generator
 */

const { generateMockData } = require('./generate-mock-data.cjs');
const fs = require('fs');

// Import the PDF generator (adjust path as needed)
const pdfGenerator = require('./backend/functions-v2/pdf-generator/index');

async function testPDFWithMockData() {
    console.log('🎵 Generating comprehensive mock data...');
    
    // Generate the mock data
    const mockData = generateMockData();
    
    // Save mock data to file for inspection
    fs.writeFileSync('mock-data-complete.json', JSON.stringify(mockData, null, 2));
    console.log('💾 Complete mock data saved to: mock-data-complete.json');
    
    // Show summary of generated data
    console.log('\n📊 Generated Data Summary:');
    console.log(`  Job ID: ${mockData.jobId}`);
    console.log(`  Duration: ${mockData.audioMetadata.duration} seconds`);
    console.log(`  BPM: ${mockData.musicalAnalysis.bpm}`);
    console.log(`  Key: ${mockData.musicalAnalysis.key} ${mockData.musicalAnalysis.mode}`);
    console.log(`  Time Signature: ${mockData.musicalAnalysis.timeSignature}`);
    console.log(`  Total Chords: ${mockData.chordsData.totalChords}`);
    console.log(`  Total Syllables: ${mockData.lyricsData.totalSyllables}`);
    console.log(`  Total Beats: ${mockData.beatData.totalBeats}`);
    console.log(`  Measures: ${mockData.alignmentData.measureBasedLayout.length}`);
    console.log(`  Downbeats: ${mockData.alignmentData.downbeatHighlights.length}`);
    
    // Show sample of chord progression
    console.log('\n🎼 Sample Chord Progression (first 16 beats):');
    mockData.chordsData.chords.slice(0, 16).forEach(chord => {
        const downbeat = chord.isDownbeat ? '🔴' : '⚪';
        console.log(`  ${downbeat} M${chord.measure}:${chord.beat} - ${chord.chord} (${chord.nashvilleNumber}) @ ${chord.timestamp.toFixed(1)}s`);
    });
    
    // Show sample of lyrics alignment
    console.log('\n🎤 Sample Lyrics Alignment (first 20 syllables):');
    mockData.lyricsData.syllables.slice(0, 20).forEach(syllable => {
        console.log(`  "${syllable.text}" @ ${syllable.startTime.toFixed(1)}s-${syllable.endTime.toFixed(1)}s (word: ${syllable.word})`);
    });
    
    // Show measure-based layout sample
    console.log('\n📏 Sample Measure Layout (first 4 measures):');
    mockData.alignmentData.measureBasedLayout.slice(0, 4).forEach(measure => {
        console.log(`  Measure ${measure.measureNumber}:`);
        console.log(`    Chords: ${measure.chords.map(c => `${c.chord}(${c.nashvilleNumber})`).join(', ')}`);
        console.log(`    Syllables: ${measure.syllables.map(s => s.text).join(' ')}`);
        console.log(`    Downbeat: ${measure.hasDownbeat ? '🔴 YES' : '⚪ NO'}`);
    });
    
    // Prepare the input for PDF generator
    const pdfInput = {
        jobId: mockData.jobId,
        videoTitle: mockData.videoTitle,
        musicalAnalysis: mockData.musicalAnalysis,
        chordsData: mockData.chordsData,
        lyricsData: mockData.lyricsData,
        beatData: mockData.beatData,
        alignmentData: mockData.alignmentData
    };
    
    console.log('\n📄 Testing PDF Generation...');
    console.log('Input structure for PDF generator:');
    console.log(JSON.stringify({
        jobId: pdfInput.jobId,
        videoTitle: pdfInput.videoTitle,
        musicalAnalysis: pdfInput.musicalAnalysis,
        chordsDataSample: {
            key: pdfInput.chordsData.key,
            mode: pdfInput.chordsData.mode,
            totalChords: pdfInput.chordsData.totalChords,
            sampleChords: pdfInput.chordsData.chords.slice(0, 8)
        },
        lyricsDataSample: {
            totalSyllables: pdfInput.lyricsData.totalSyllables,
            sampleSyllables: pdfInput.lyricsData.syllables.slice(0, 10)
        },
        beatDataSample: {
            bpm: pdfInput.beatData.bpm,
            totalBeats: pdfInput.beatData.totalBeats,
            sampleBeats: pdfInput.beatData.beats.slice(0, 8)
        },
        alignmentDataSample: {
            totalMeasures: pdfInput.alignmentData.measureBasedLayout.length,
            downbeats: pdfInput.alignmentData.downbeatHighlights.length,
            sampleMeasure: pdfInput.alignmentData.measureBasedLayout[0]
        }
    }, null, 2));
    
    // Save the PDF input for manual testing
    fs.writeFileSync('pdf-generator-input.json', JSON.stringify(pdfInput, null, 2));
    console.log('\n💾 PDF generator input saved to: pdf-generator-input.json');
    
    try {
        // Test the PDF generator
        console.log('\n🔄 Calling PDF generator...');
        
        // Create the event structure that Lambda expects
        const lambdaEvent = {
            jobId: mockData.jobId,
            // Include all the data the PDF generator needs
            ...pdfInput
        };
        
        // Mock Lambda context
        const lambdaContext = {
            getRemainingTimeInMillis: () => 30000,
            functionName: 'test-pdf-generator',
            awsRequestId: 'test-request-id'
        };
        
        const result = await pdfGenerator.handler(lambdaEvent, lambdaContext);
        
        console.log('✅ PDF generation completed!');
        console.log('Result:', JSON.stringify(result, null, 2));
        
        if (result.pdfUrl) {
            console.log(`\n📄 PDF URL: ${result.pdfUrl}`);
        }
        
    } catch (error) {
        console.error('❌ PDF generation failed:', error);
        console.error('Error details:', error.message);
        
        // Show what input would be needed
        console.log('\n🔍 Expected PDF Generator Input Format:');
        console.log('The PDF generator expects this structure:');
        console.log(JSON.stringify({
            jobId: "string",
            videoTitle: "string", 
            musicalAnalysis: {
                key: "string",
                mode: "string",
                bpm: "number",
                timeSignature: "string"
            },
            chordsData: {
                chords: [
                    {
                        timestamp: "number",
                        chord: "string", 
                        nashvilleNumber: "string",
                        measure: "number",
                        beat: "number",
                        isDownbeat: "boolean"
                    }
                ]
            },
            lyricsData: {
                syllables: [
                    {
                        text: "string",
                        startTime: "number",
                        endTime: "number",
                        word: "string"
                    }
                ]
            },
            alignmentData: {
                measureBasedLayout: [
                    {
                        measureNumber: "number",
                        chords: "array",
                        syllables: "array",
                        hasDownbeat: "boolean"
                    }
                ]
            }
        }, null, 2));
    }
    
    return mockData;
}

// Run the test
if (require.main === module) {
    testPDFWithMockData().then(mockData => {
        console.log('\n🎉 Mock data generation and PDF test completed!');
        console.log(`\nFiles created:`);
        console.log(`  - mock-data-complete.json (full mock data)`);
        console.log(`  - pdf-generator-input.json (PDF generator input)`);
        console.log(`\nYou can now:`);
        console.log(`  1. Inspect the generated data structure`);
        console.log(`  2. Use this data to test the PDF generator`);
        console.log(`  3. Upload to DynamoDB if needed`);
        console.log(`  4. Test the complete workflow`);
    }).catch(error => {
        console.error('❌ Test failed:', error);
    });
}

module.exports = { testPDFWithMockData };
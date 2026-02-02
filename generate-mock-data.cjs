/**
 * Generate comprehensive mock data for PDF testing
 * 5 minutes at 60 BPM = 300 beats = 75 measures (4/4 time)
 * Chord changes every 2 measures, cycling through C major scale
 * Lyrics: variations of "The wheels on the bus go round and round"
 */

const AWS = require('aws-sdk');

// Configure AWS (you may need to set your credentials)
const dynamodb = new AWS.DynamoDB.DocumentClient({
    region: 'us-east-1'
});

// C Major scale chords in Nashville Number System
const cMajorChords = [
    { chord: 'C', nashville: '1', roman: 'I' },
    { chord: 'Dm', nashville: '2m', roman: 'ii' },
    { chord: 'Em', nashville: '3m', roman: 'iii' },
    { chord: 'F', nashville: '4', roman: 'IV' },
    { chord: 'G', nashville: '5', roman: 'V' },
    { chord: 'Am', nashville: '6m', roman: 'vi' },
    { chord: 'Bdim', nashville: '7°', roman: 'vii°' }
];

// Lyrics variations
const lyricsVariations = [
    "The wheels on the bus go round and round",
    "Round and round, round and round", 
    "The wheels on the bus go round and round",
    "All through the town",
    "The wipers on the bus go swish swish swish",
    "Swish swish swish, swish swish swish",
    "The wipers on the bus go swish swish swish", 
    "All through the town",
    "The horn on the bus goes beep beep beep",
    "Beep beep beep, beep beep beep",
    "The horn on the bus goes beep beep beep",
    "All through the town",
    "The doors on the bus go open and shut",
    "Open and shut, open and shut",
    "The doors on the bus go open and shut",
    "All through the town"
];

function generateMockData() {
    const jobId = `mock-wheels-bus-${Date.now()}`;
    const bpm = 60;
    const timeSignature = '4/4';
    const key = 'C';
    const totalDurationSeconds = 300; // 5 minutes
    const beatsPerSecond = bpm / 60;
    const totalBeats = totalDurationSeconds * beatsPerSecond;
    const measuresCount = Math.floor(totalBeats / 4); // 4/4 time
    
    console.log(`Generating data for ${totalDurationSeconds}s song:`);
    console.log(`- BPM: ${bpm}`);
    console.log(`- Total beats: ${totalBeats}`);
    console.log(`- Total measures: ${measuresCount}`);
    
    // Generate chord progression (change every 0.5 seconds for passing chords)
    const chordProgression = [];
    const chordChangeInterval = 0.5; // Change every half second
    const totalChordChanges = Math.floor(totalDurationSeconds / chordChangeInterval);
    
    for (let i = 0; i < totalChordChanges; i++) {
        const timestamp = i * chordChangeInterval;
        const measure = Math.floor(timestamp / (4 / beatsPerSecond)) + 1;
        const beatInMeasure = Math.floor((timestamp % (4 / beatsPerSecond)) / (1 / beatsPerSecond)) + 1;
        const isDownbeat = beatInMeasure === 1;
        
        // Create more complex chord progression with passing chords
        let chordIndex;
        if (isDownbeat) {
            // Downbeats get primary chords (cycle through scale)
            chordIndex = Math.floor(measure / 2) % cMajorChords.length;
        } else {
            // Passing chords - use different progression
            const passingChordPatterns = [
                [0, 4, 5, 0], // I - V - vi - I
                [3, 0, 4, 5], // IV - I - V - vi
                [5, 3, 0, 4], // vi - IV - I - V
                [4, 5, 0, 3]  // V - vi - I - IV
            ];
            const patternIndex = Math.floor(i / 8) % passingChordPatterns.length;
            const chordInPattern = (i % 8) % 4;
            chordIndex = passingChordPatterns[patternIndex][chordInPattern];
        }
        
        const currentChord = cMajorChords[chordIndex];
        
        chordProgression.push({
            timestamp: timestamp,
            chord: currentChord.chord,
            nashvilleNumber: currentChord.nashville,
            romanNumeral: currentChord.roman,
            beat: beatInMeasure,
            measure: measure,
            isDownbeat: isDownbeat,
            confidence: isDownbeat ? 0.90 + Math.random() * 0.08 : 0.75 + Math.random() * 0.15 // Higher confidence for downbeats
        });
    }
    
    // Generate lyrics with syllable-level timing
    const lyricsData = [];
    let currentTime = 0;
    let lyricIndex = 0;
    
    while (currentTime < totalDurationSeconds) {
        const line = lyricsVariations[lyricIndex % lyricsVariations.length];
        const words = line.split(' ');
        const lineStartTime = currentTime;
        const lineDuration = 8; // 8 seconds per line (2 measures at 60 BPM)
        const wordDuration = lineDuration / words.length;
        
        words.forEach((word, wordIndex) => {
            const wordStartTime = lineStartTime + (wordIndex * wordDuration);
            const syllables = splitIntoSyllables(word);
            const syllableDuration = wordDuration / syllables.length;
            
            syllables.forEach((syllable, syllableIndex) => {
                const syllableStartTime = wordStartTime + (syllableIndex * syllableDuration);
                
                lyricsData.push({
                    text: syllable,
                    startTime: syllableStartTime,
                    endTime: syllableStartTime + syllableDuration,
                    word: word,
                    wordIndex: wordIndex,
                    lineIndex: lyricIndex,
                    confidence: 0.9 + Math.random() * 0.08 // 0.9-0.98
                });
            });
        });
        
        currentTime += lineDuration;
        lyricIndex++;
    }
    
    // Generate beat grid with downbeat highlighting
    const beatGrid = [];
    for (let i = 0; i < totalBeats; i++) {
        const timestamp = i / beatsPerSecond;
        const measure = Math.floor(i / 4) + 1;
        const beat = (i % 4) + 1;
        const isDownbeat = beat === 1;
        
        beatGrid.push({
            timestamp: timestamp,
            beat: beat,
            measure: measure,
            isDownbeat: isDownbeat,
            strength: isDownbeat ? 1.0 : (beat === 3 ? 0.7 : 0.4) // Strong downbeat, medium beat 3, weak beats 2&4
        });
    }
    
    // Create the complete job data structure
    const jobData = {
        jobId: jobId,
        status: 'COMPLETE',
        videoTitle: 'The Wheels on the Bus - Mock Data Test',
        youtubeUrl: 'https://youtube.com/watch?v=mock-wheels-bus',
        createdAt: new Date().toISOString(),
        completedAt: new Date().toISOString(),
        
        // Audio metadata
        audioMetadata: {
            duration: totalDurationSeconds,
            sampleRate: 44100,
            channels: 2,
            format: 'mp3'
        },
        
        // Musical analysis
        musicalAnalysis: {
            key: key,
            mode: 'major',
            timeSignature: timeSignature,
            bpm: bpm,
            confidence: 0.92
        },
        
        // Chord data
        chordsData: {
            key: key,
            mode: 'major',
            chords: chordProgression,
            totalChords: chordProgression.length
        },
        
        // Lyrics data
        lyricsData: {
            text: lyricsVariations.join('\n'),
            syllables: lyricsData,
            totalSyllables: lyricsData.length,
            language: 'en'
        },
        
        // Beat tracking
        beatData: {
            bpm: bpm,
            timeSignature: timeSignature,
            beats: beatGrid,
            totalBeats: beatGrid.length,
            confidence: 0.88
        },
        
        // Enhanced alignment data
        alignmentData: {
            syllableChordAlignment: alignSyllablesWithChords(lyricsData, chordProgression),
            measureBasedLayout: generateMeasureLayout(lyricsData, chordProgression, beatGrid),
            downbeatHighlights: beatGrid.filter(b => b.isDownbeat)
        }
    };
    
    return jobData;
}

function splitIntoSyllables(word) {
    // Simple syllable splitting - in production, use a proper syllable library
    const syllablePatterns = {
        'wheels': ['wheels'],
        'round': ['round'],
        'and': ['and'],
        'through': ['through'],
        'town': ['town'],
        'wipers': ['wi', 'pers'],
        'swish': ['swish'],
        'beep': ['beep'],
        'horn': ['horn'],
        'goes': ['goes'],
        'doors': ['doors'],
        'open': ['o', 'pen'],
        'shut': ['shut']
    };
    
    return syllablePatterns[word.toLowerCase()] || [word];
}

function alignSyllablesWithChords(lyricsData, chordProgression) {
    return lyricsData.map(syllable => {
        // Find the chord that's active during this syllable
        const activeChord = chordProgression.find(chord => 
            chord.timestamp <= syllable.startTime && 
            chord.timestamp + 1 > syllable.startTime // Assume 1 second chord duration
        );
        
        return {
            ...syllable,
            chord: activeChord ? activeChord.chord : null,
            nashvilleNumber: activeChord ? activeChord.nashvilleNumber : null,
            isOnDownbeat: activeChord ? activeChord.isDownbeat : false
        };
    });
}

function generateMeasureLayout(lyricsData, chordProgression, beatGrid) {
    const measures = [];
    const measuresCount = Math.max(...beatGrid.map(b => b.measure));
    
    for (let measureNum = 1; measureNum <= measuresCount; measureNum++) {
        const measureBeats = beatGrid.filter(b => b.measure === measureNum);
        
        // Get all chords that occur during this measure
        const measureStart = (measureNum - 1) * 4; // 4 seconds per measure at 60 BPM
        const measureEnd = measureNum * 4;
        const measureChords = chordProgression.filter(c => 
            c.timestamp >= measureStart && c.timestamp < measureEnd
        );
        
        // Get syllables for this measure
        const measureSyllables = lyricsData.filter(s => {
            return s.startTime >= measureStart && s.startTime < measureEnd;
        });
        
        // Separate downbeat chords from passing chords
        const downbeatChords = measureChords.filter(c => c.isDownbeat);
        const passingChords = measureChords.filter(c => !c.isDownbeat);
        
        measures.push({
            measureNumber: measureNum,
            beats: measureBeats,
            chords: measureChords, // All chords in measure
            downbeatChords: downbeatChords, // RED chords
            passingChords: passingChords, // BLACK chords
            syllables: measureSyllables,
            hasDownbeat: measureBeats.some(b => b.isDownbeat),
            primaryChord: downbeatChords[0] || measureChords[0] // Main chord for the measure
        });
    }
    
    return measures;
}

// Generate and save the mock data
async function saveMockDataToDynamoDB() {
    const mockData = generateMockData();
    
    const params = {
        TableName: 'TranscriptionJobs-dev', // Adjust table name as needed
        Item: mockData
    };
    
    try {
        await dynamodb.put(params).promise();
        console.log('✅ Mock data saved to DynamoDB successfully!');
        console.log(`Job ID: ${mockData.jobId}`);
        return mockData.jobId;
    } catch (error) {
        console.error('❌ Error saving to DynamoDB:', error);
        // Save to local file as backup
        const fs = require('fs');
        fs.writeFileSync('mock-data-backup.json', JSON.stringify(mockData, null, 2));
        console.log('💾 Mock data saved to local file: mock-data-backup.json');
        return mockData.jobId;
    }
}

// Export for testing
module.exports = {
    generateMockData,
    saveMockDataToDynamoDB
};

// Run if called directly
if (require.main === module) {
    saveMockDataToDynamoDB().then(jobId => {
        console.log(`\n🎵 Mock data generated for job: ${jobId}`);
        console.log('📊 Data includes:');
        console.log('  - 300 seconds (5 minutes) of audio');
        console.log('  - 300 beats at 60 BPM');
        console.log('  - 75 measures in 4/4 time');
        console.log('  - Chord progression through C major scale');
        console.log('  - "Wheels on the Bus" lyrics with syllable timing');
        console.log('  - Downbeat highlighting');
        console.log('  - Complete alignment data');
    });
}
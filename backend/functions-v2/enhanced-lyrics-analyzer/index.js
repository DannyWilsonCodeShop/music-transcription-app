// Enhanced Lyrics Analysis Lambda
// Performs detailed syllable-level lyrics analysis for Nashville Number System
// - Advanced syllable separation with proper hyphenation
// - Beat alignment and downbeat identification
// - Verse/section detection and labeling
// - Pickup note identification

const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, UpdateCommand, GetCommand } = require('@aws-sdk/lib-dynamodb');

const dynamoClient = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(dynamoClient);

const JOBS_TABLE = process.env.DYNAMODB_JOBS_TABLE;

exports.handler = async (event) => {
  console.log('Enhanced Lyrics Analysis Event:', JSON.stringify(event, null, 2));

  try {
    const { jobId, lyricsText } = event;

    // Get musical analysis data from the job
    const job = await getJobData(jobId);
    const musicalAnalysis = job.musicalAnalysis || job.tempoAnalysis;

    if (!musicalAnalysis) {
      throw new Error('Musical analysis data not found. Run audio analysis first.');
    }

    // Update job status
    await updateJobStatus(jobId, 'processing', 30, 'Starting enhanced lyrics analysis');

    console.log('Starting enhanced lyrics analysis for job:', jobId);

    // Step 1: Advanced Syllable Separation (40% progress)
    const syllableAnalysis = await performSyllableSeparation(lyricsText);
    await updateJobStatus(jobId, 'processing', 40, 'Syllable separation complete');

    // Step 2: Beat Alignment (55% progress)
    const beatAlignment = await alignSyllablesToBeats(syllableAnalysis, musicalAnalysis);
    await updateJobStatus(jobId, 'processing', 55, 'Beat alignment complete');

    // Step 3: Downbeat Identification (70% progress)
    const downbeatAnalysis = await identifyDownbeats(beatAlignment, musicalAnalysis);
    await updateJobStatus(jobId, 'processing', 70, 'Downbeat identification complete');

    // Step 4: Verse Detection (85% progress)
    const verseAnalysis = await detectVersesAndSections(downbeatAnalysis, lyricsText);
    await updateJobStatus(jobId, 'processing', 85, 'Verse detection complete');

    // Step 5: Pickup Note Analysis (95% progress)
    const pickupAnalysis = await identifyPickupNotes(verseAnalysis, musicalAnalysis);
    await updateJobStatus(jobId, 'processing', 95, 'Pickup note analysis complete');

    // Combine all lyrics analysis
    const completeLyricsAnalysis = {
      syllables: pickupAnalysis.syllables,
      verses: verseAnalysis.verses,
      sections: verseAnalysis.sections,
      pickupNotes: pickupAnalysis.pickupNotes,
      beatAlignment: beatAlignment,
      processingMetadata: {
        totalSyllables: pickupAnalysis.syllables.length,
        totalVerses: verseAnalysis.verses.length,
        totalPickups: pickupAnalysis.pickupNotes.length,
        analysisVersion: '2.0',
        completedAt: new Date().toISOString()
      }
    };

    // Update job with lyrics analysis
    await updateJobAnalysis(jobId, 'lyricsAnalysis', completeLyricsAnalysis);
    await updateJobStatus(jobId, 'processing', 100, 'Enhanced lyrics analysis complete');

    console.log('Enhanced lyrics analysis completed successfully');

    return {
      statusCode: 200,
      body: {
        jobId,
        lyricsAnalysis: completeLyricsAnalysis,
        message: 'Enhanced lyrics analysis completed'
      }
    };

  } catch (error) {
    console.error('Enhanced lyrics analysis error:', error);
    await updateJobStatus(event.jobId, 'failed', 0, `Lyrics analysis failed: ${error.message}`);

    return {
      statusCode: 500,
      body: { error: error.message }
    };
  }
};

async function performSyllableSeparation(lyricsText) {
  // Advanced syllable separation with proper hyphenation
  console.log('Performing advanced syllable separation...');
  
  try {
    const lines = lyricsText.split('\n').filter(line => line.trim());
    const allSyllables = [];
    let globalSyllableIndex = 0;
    
    for (let lineIndex = 0; lineIndex < lines.length; lineIndex++) {
      const line = lines[lineIndex].trim();
      if (!line) continue;
      
      const words = line.split(/\s+/);
      let wordIndex = 0;
      
      for (const word of words) {
        const syllables = separateWordIntoSyllables(word);
        
        for (let syllableIndex = 0; syllableIndex < syllables.length; syllableIndex++) {
          allSyllables.push({
            text: syllables[syllableIndex],
            originalWord: word,
            lineIndex: lineIndex,
            wordIndex: wordIndex,
            syllableIndex: syllableIndex,
            globalIndex: globalSyllableIndex,
            isLastSyllableInWord: syllableIndex === syllables.length - 1,
            isFirstSyllableInWord: syllableIndex === 0
          });
          globalSyllableIndex++;
        }
        wordIndex++;
      }
    }

    return {
      syllables: allSyllables,
      totalLines: lines.length,
      totalWords: allSyllables.reduce((acc, syl) => syl.isLastSyllableInWord ? acc + 1 : acc, 0),
      totalSyllables: allSyllables.length
    };
  } catch (error) {
    console.error('Syllable separation error:', error);
    throw new Error(`Syllable separation failed: ${error.message}`);
  }
}

function separateWordIntoSyllables(word) {
  // Advanced syllable separation algorithm
  // Handles complex cases like "A-maz-ing", "beau-ti-ful", etc.
  
  if (!word || word.length === 0) return [''];
  
  // Clean the word
  const cleanWord = word.replace(/[^\w']/g, '');
  if (cleanWord.length <= 2) return [word];
  
  // Common syllable patterns for musical words
  const commonSyllables = {
    'amazing': ['A-', 'maz-', 'ing'],
    'grace': ['Grace'],
    'beautiful': ['beau-', 'ti-', 'ful'],
    'wonderful': ['won-', 'der-', 'ful'],
    'hallelujah': ['hal-', 'le-', 'lu-', 'jah'],
    'salvation': ['sal-', 'va-', 'tion'],
    'forever': ['for-', 'ev-', 'er'],
    'together': ['to-', 'geth-', 'er'],
    'remember': ['re-', 'mem-', 'ber'],
    'believe': ['be-', 'lieve'],
    'receive': ['re-', 'ceive'],
    'deliver': ['de-', 'liv-', 'er'],
    'victory': ['vic-', 'to-', 'ry'],
    'glory': ['glo-', 'ry'],
    'holy': ['ho-', 'ly'],
    'mighty': ['migh-', 'ty'],
    'worthy': ['wor-', 'thy']
  };
  
  const lowerWord = cleanWord.toLowerCase();
  if (commonSyllables[lowerWord]) {
    // Preserve original capitalization
    return commonSyllables[lowerWord].map((syllable, index) => {
      if (index === 0 && word[0] === word[0].toUpperCase()) {
        return syllable.charAt(0).toUpperCase() + syllable.slice(1);
      }
      return syllable;
    });
  }
  
  // Advanced syllable detection algorithm
  const syllables = [];
  let currentSyllable = '';
  const vowels = 'aeiouAEIOU';
  let lastWasVowel = false;
  
  for (let i = 0; i < cleanWord.length; i++) {
    const char = cleanWord[i];
    const isVowel = vowels.includes(char);
    
    currentSyllable += char;
    
    // Syllable break conditions
    if (isVowel && !lastWasVowel && currentSyllable.length > 1) {
      // Vowel after consonant - potential syllable break
      if (i < cleanWord.length - 1) {
        syllables.push(currentSyllable.slice(0, -1) + '-');
        currentSyllable = char;
      }
    } else if (!isVowel && lastWasVowel && i < cleanWord.length - 2) {
      // Consonant after vowel - check for double consonants
      const nextChar = cleanWord[i + 1];
      if (!vowels.includes(nextChar)) {
        // Double consonant - split here
        syllables.push(currentSyllable + '-');
        currentSyllable = '';
      }
    }
    
    lastWasVowel = isVowel;
  }
  
  // Add final syllable
  if (currentSyllable) {
    syllables.push(currentSyllable);
  }
  
  // If no syllables were created, return the original word
  if (syllables.length === 0) {
    return [word];
  }
  
  // Ensure we don't have empty syllables
  return syllables.filter(syl => syl.trim().length > 0);
}

async function alignSyllablesToBeats(syllableAnalysis, musicalAnalysis) {
  // Align syllables to musical beats based on tempo and time signature
  console.log('Aligning syllables to musical beats...');
  
  try {
    const { syllables } = syllableAnalysis;
    const tempo = musicalAnalysis.bpm || musicalAnalysis.tempo?.bpm || 120;
    const timeSignature = musicalAnalysis.timeSignature || { numerator: 4, denominator: 4 };
    
    const beatDuration = 60 / tempo; // seconds per beat
    const beatsPerMeasure = timeSignature.numerator || 4;
    
    // Estimate syllable timing based on natural speech rhythm
    const estimatedSyllableDuration = 0.3; // 300ms per syllable average
    const totalEstimatedDuration = syllables.length * estimatedSyllableDuration;
    
    const alignedSyllables = syllables.map((syllable, index) => {
      // Estimate timing for each syllable
      const estimatedStart = index * estimatedSyllableDuration;
      const estimatedEnd = estimatedStart + estimatedSyllableDuration;
      
      // Calculate which beat this syllable falls on
      const beatNumber = Math.floor(estimatedStart / beatDuration);
      const measureNumber = Math.floor(beatNumber / beatsPerMeasure);
      const beatInMeasure = beatNumber % beatsPerMeasure;
      
      return {
        ...syllable,
        start: estimatedStart,
        end: estimatedEnd,
        beatNumber: beatNumber,
        measureNumber: measureNumber,
        beatInMeasure: beatInMeasure,
        isOnBeat: Math.abs((estimatedStart % beatDuration) / beatDuration) < 0.2
      };
    });

    return {
      alignedSyllables: alignedSyllables,
      beatDuration: beatDuration,
      beatsPerMeasure: beatsPerMeasure,
      totalMeasures: Math.ceil(alignedSyllables.length / beatsPerMeasure),
      analysisMetadata: {
        tempo: tempo,
        timeSignature: `${timeSignature.numerator}/${timeSignature.denominator}`,
        estimatedDuration: totalEstimatedDuration
      }
    };
  } catch (error) {
    console.error('Beat alignment error:', error);
    throw new Error(`Beat alignment failed: ${error.message}`);
  }
}

async function identifyDownbeats(beatAlignment, musicalAnalysis) {
  // Identify which syllables fall on downbeats (strong beats)
  console.log('Identifying downbeats...');
  
  try {
    const { alignedSyllables, beatsPerMeasure } = beatAlignment;
    const timeSignature = musicalAnalysis.timeSignature || { numerator: 4 };
    
    // Define strong beats based on time signature
    let strongBeats = [0]; // Beat 1 is always strong
    
    if (timeSignature.numerator === 4) {
      strongBeats = [0, 2]; // Beats 1 and 3 in 4/4
    } else if (timeSignature.numerator === 3) {
      strongBeats = [0]; // Beat 1 in 3/4
    } else if (timeSignature.numerator === 6) {
      strongBeats = [0, 3]; // Beats 1 and 4 in 6/8
    }
    
    const syllablesWithDownbeats = alignedSyllables.map(syllable => {
      const isDownbeat = strongBeats.includes(syllable.beatInMeasure);
      
      return {
        ...syllable,
        isDownbeat: isDownbeat,
        isStrongBeat: isDownbeat,
        isWeakBeat: !isDownbeat,
        downbeatConfidence: isDownbeat ? 0.9 : 0.1
      };
    });

    const downbeats = syllablesWithDownbeats.filter(syl => syl.isDownbeat);
    
    return {
      syllables: syllablesWithDownbeats,
      downbeats: downbeats,
      strongBeats: strongBeats,
      analysisMetadata: {
        totalDownbeats: downbeats.length,
        downbeatPattern: strongBeats,
        timeSignature: `${timeSignature.numerator}/${timeSignature.denominator || 4}`
      }
    };
  } catch (error) {
    console.error('Downbeat identification error:', error);
    throw new Error(`Downbeat identification failed: ${error.message}`);
  }
}

async function detectVersesAndSections(downbeatAnalysis, originalLyrics) {
  // Detect verses, choruses, and other song sections
  console.log('Detecting verses and sections...');
  
  try {
    const { syllables } = downbeatAnalysis;
    const lines = originalLyrics.split('\n').filter(line => line.trim());
    
    const verses = [];
    const sections = [];
    let currentVerse = 1;
    let currentSection = null;
    
    // Group syllables by lines
    const syllablesByLine = {};
    syllables.forEach(syllable => {
      if (!syllablesByLine[syllable.lineIndex]) {
        syllablesByLine[syllable.lineIndex] = [];
      }
      syllablesByLine[syllable.lineIndex].push(syllable);
    });
    
    // Analyze each line for verse/section patterns
    for (let lineIndex = 0; lineIndex < lines.length; lineIndex++) {
      const line = lines[lineIndex].trim();
      const lineSyllables = syllablesByLine[lineIndex] || [];
      
      // Check for section markers
      const sectionType = detectSectionType(line);
      
      if (sectionType || lineIndex === 0) {
        // Start new section
        if (currentSection) {
          sections.push(currentSection);
        }
        
        const label = sectionType || `Verse ${currentVerse}`;
        currentSection = {
          type: sectionType || 'verse',
          label: label,
          startLine: lineIndex,
          startSyllableIndex: lineSyllables[0]?.globalIndex || 0,
          syllables: [...lineSyllables]
        };
        
        if (!sectionType) {
          verses.push({
            number: currentVerse,
            label: `Verse ${currentVerse}`,
            startLine: lineIndex,
            syllables: [...lineSyllables]
          });
          currentVerse++;
        }
      } else if (currentSection) {
        // Add to current section
        currentSection.syllables.push(...lineSyllables);
      }
      
      // Check for verse breaks (empty lines or pattern changes)
      if (lineIndex < lines.length - 1) {
        const nextLine = lines[lineIndex + 1];
        if (!nextLine.trim() || detectSectionType(nextLine)) {
          // End current section
          if (currentSection) {
            currentSection.endLine = lineIndex;
            currentSection.endSyllableIndex = lineSyllables[lineSyllables.length - 1]?.globalIndex || 0;
          }
        }
      }
    }
    
    // Add final section
    if (currentSection) {
      currentSection.endLine = lines.length - 1;
      currentSection.endSyllableIndex = syllables[syllables.length - 1]?.globalIndex || 0;
      sections.push(currentSection);
    }

    return {
      syllables: syllables,
      verses: verses,
      sections: sections,
      analysisMetadata: {
        totalVerses: verses.length,
        totalSections: sections.length,
        sectionTypes: [...new Set(sections.map(s => s.type))]
      }
    };
  } catch (error) {
    console.error('Verse detection error:', error);
    throw new Error(`Verse detection failed: ${error.message}`);
  }
}

function detectSectionType(line) {
  // Detect section markers in lyrics
  const lowerLine = line.toLowerCase().trim();
  
  if (lowerLine.includes('verse')) return 'verse';
  if (lowerLine.includes('chorus')) return 'chorus';
  if (lowerLine.includes('bridge')) return 'bridge';
  if (lowerLine.includes('intro')) return 'intro';
  if (lowerLine.includes('outro')) return 'outro';
  if (lowerLine.includes('refrain')) return 'chorus';
  
  return null;
}

async function identifyPickupNotes(verseAnalysis, musicalAnalysis) {
  // Identify pickup notes (anacrusis) - weak beats that lead into downbeats
  console.log('Identifying pickup notes...');
  
  try {
    const { syllables } = verseAnalysis;
    const pickupNotes = [];
    
    // Look for syllables that come before downbeats
    for (let i = 0; i < syllables.length - 1; i++) {
      const currentSyllable = syllables[i];
      const nextSyllable = syllables[i + 1];
      
      // If current syllable is weak beat and next is downbeat
      if (!currentSyllable.isDownbeat && nextSyllable.isDownbeat) {
        // Check if it's at the beginning of a measure or phrase
        if (currentSyllable.beatInMeasure === 3 || // Last beat of measure
            currentSyllable.isFirstSyllableInWord) {
          
          pickupNotes.push({
            ...currentSyllable,
            isPickup: true,
            leadsToDownbeat: nextSyllable.globalIndex,
            pickupType: currentSyllable.beatInMeasure === 3 ? 'measure_pickup' : 'phrase_pickup'
          });
        }
      }
    }
    
    // Mark pickup notes in syllables array
    const syllablesWithPickups = syllables.map(syllable => {
      const isPickup = pickupNotes.some(pickup => pickup.globalIndex === syllable.globalIndex);
      return {
        ...syllable,
        isPickup: isPickup
      };
    });

    return {
      syllables: syllablesWithPickups,
      pickupNotes: pickupNotes,
      analysisMetadata: {
        totalPickups: pickupNotes.length,
        pickupTypes: [...new Set(pickupNotes.map(p => p.pickupType))]
      }
    };
  } catch (error) {
    console.error('Pickup note identification error:', error);
    throw new Error(`Pickup note identification failed: ${error.message}`);
  }
}

// Helper Functions

async function getJobData(jobId) {
  const result = await docClient.send(new GetCommand({
    TableName: JOBS_TABLE,
    Key: { jobId }
  }));
  
  if (!result.Item) {
    throw new Error('Job not found');
  }
  
  return result.Item;
}

async function updateJobStatus(jobId, status, progress, message = null) {
  const updateExpr = message
    ? 'SET #status = :status, progress = :progress, statusMessage = :message, updatedAt = :updated'
    : 'SET #status = :status, progress = :progress, updatedAt = :updated';

  const exprValues = {
    ':status': status,
    ':progress': progress,
    ':updated': new Date().toISOString()
  };

  if (message) {
    exprValues[':message'] = message;
  }

  await docClient.send(new UpdateCommand({
    TableName: JOBS_TABLE,
    Key: { jobId },
    UpdateExpression: updateExpr,
    ExpressionAttributeNames: { '#status': 'status' },
    ExpressionAttributeValues: exprValues
  }));
}

async function updateJobAnalysis(jobId, analysisField, analysisData) {
  await docClient.send(new UpdateCommand({
    TableName: JOBS_TABLE,
    Key: { jobId },
    UpdateExpression: `SET ${analysisField} = :data, updatedAt = :updated`,
    ExpressionAttributeValues: {
      ':data': analysisData,
      ':updated': new Date().toISOString()
    }
  }));
}
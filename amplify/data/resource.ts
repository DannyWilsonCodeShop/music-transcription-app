import { type ClientSchema, a, defineData } from '@aws-amplify/backend';

/*== ENHANCED MUSIC TRANSCRIPTION SCHEMA =================================
Schema for music transcription jobs with detailed musical analysis
- Tempo and time signature detection
- High-resolution chord analysis (0.2s intervals)
- Syllable-level lyrics with beat alignment
- Nashville Number System data
- Measure-based alignment for perfect PDF output
=========================================================================*/
const schema = a.schema({
  TranscriptionJob: a
    .model({
      id: a.id().required(),
      status: a.enum(['pending', 'processing', 'completed', 'failed']),
      audioUrl: a.string(),
      youtubeUrl: a.string(),
      title: a.string(),
      artist: a.string(),
      userId: a.string(),
      createdAt: a.datetime(),
      updatedAt: a.datetime(),
      
      // Enhanced Musical Analysis Data
      musicalAnalysis: a.json(), // Complete musical analysis object
      
      // Tempo and Timing Analysis
      tempoAnalysis: a.json(), // { bpm, confidence, tempoChanges, beatGrid }
      
      // Time Signature and Measures
      timeSignatureAnalysis: a.json(), // { numerator, denominator, measures, downbeats }
      
      // Key and Harmony Analysis  
      keyAnalysis: a.json(), // { root, mode, confidence, keyChanges }
      
      // High-Resolution Chord Analysis (0.2s intervals)
      chordAnalysis: a.json(), // { interval: 0.2, chords: [...] }
      
      // Syllable-Level Lyrics with Beat Alignment
      lyricsAnalysis: a.json(), // { syllables: [...], verses: [...] }
      
      // Song Structure Analysis
      structureAnalysis: a.json(), // { sections: [...], measures: [...] }
      
      // Nashville Number System Data
      nashvilleNumbers: a.json(), // { downbeats: [...], passingChords: [...] }
      
      // PDF Generation Data (processed and ready)
      pdfData: a.json(), // { measures: [...], layout: {...} }
      
      // Legacy fields (for backward compatibility)
      lyrics: a.string(),
      chords: a.json(),
      
      // Processing metadata
      processingSteps: a.json(), // Track which analysis steps completed
      qualityMetrics: a.json(), // Confidence scores and validation data
    })
    .authorization((allow) => [
      allow.owner(),
      allow.guest().to(['create', 'read'])
    ]),
  
  // Enhanced User model with preferences
  User: a
    .model({
      id: a.id().required(),
      email: a.string(),
      name: a.string(),
      createdAt: a.datetime(),
      
      // User preferences for transcription
      preferences: a.json(), // { defaultKey, preferredTimeSignature, etc. }
    })
    .authorization((allow) => [allow.owner()]),

  // New: Musical Analysis Cache (for performance)
  AnalysisCache: a
    .model({
      id: a.id().required(),
      audioHash: a.string().required(), // Hash of audio file for caching
      analysisType: a.enum(['tempo', 'chords', 'key', 'structure']),
      analysisData: a.json(),
      confidence: a.float(),
      createdAt: a.datetime(),
      expiresAt: a.datetime(),
    })
    .authorization((allow) => [
      allow.guest().to(['create', 'read']),
      allow.authenticated()
    ]),

  // New: Processing Queue for complex analysis
  ProcessingQueue: a
    .model({
      id: a.id().required(),
      jobId: a.string().required(),
      step: a.enum(['audio_analysis', 'lyrics_processing', 'structure_analysis', 'pdf_generation']),
      status: a.enum(['queued', 'processing', 'completed', 'failed']),
      priority: a.integer(),
      attempts: a.integer(),
      errorMessage: a.string(),
      processingData: a.json(),
      createdAt: a.datetime(),
      updatedAt: a.datetime(),
    })
    .authorization((allow) => [
      allow.guest().to(['create', 'read', 'update']),
      allow.authenticated()
    ]),
});

export type Schema = ClientSchema<typeof schema>;

export const data = defineData({
  schema,
  authorizationModes: {
    defaultAuthorizationMode: 'identityPool',
  },
});

/*== STEP 2 ===============================================================
Go to your frontend source code. From your client-side code, generate a
Data client to make CRUDL requests to your table. (THIS SNIPPET WILL ONLY
WORK IN THE FRONTEND CODE FILE.)

Using JavaScript or Next.js React Server Components, Middleware, Server 
Actions or Pages Router? Review how to generate Data clients for those use
cases: https://docs.amplify.aws/gen2/build-a-backend/data/connect-to-API/
=========================================================================*/

/*
"use client"
import { generateClient } from "aws-amplify/data";
import type { Schema } from "@/amplify/data/resource";

const client = generateClient<Schema>() // use this Data client for CRUDL requests
*/

/*== STEP 3 ===============================================================
Fetch records from the database and use them in your frontend component.
(THIS SNIPPET WILL ONLY WORK IN THE FRONTEND CODE FILE.)
=========================================================================*/

/* For example, in a React component, you can use this snippet in your
  function's RETURN statement */
// const { data: todos } = await client.models.Todo.list()

// return <ul>{todos.map(todo => <li key={todo.id}>{todo.content}</li>)}</ul>

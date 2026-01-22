import { defineBackend } from '@aws-amplify/backend';
import { auth } from './auth/resource';
import { data } from './data/resource';
import { storage } from './storage/resource';
import { transcribeAudio } from './functions/transcribe-audio/resource';

/**
 * Music Transcription App Backend
 * Provides AI-powered lyrics and chord transcription from audio files
 */
defineBackend({
  auth,
  data,
  storage,
  transcribeAudio,
});

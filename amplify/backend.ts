import { defineBackend } from '@aws-amplify/backend';
import { auth } from './auth/resource';
import { data } from './data/resource';
import { storage } from './storage/resource';

/**
 * Music Transcription App Backend
 * Provides AI-powered lyrics and chord transcription from audio files
 */
const backend = defineBackend({
  auth,
  data,
  storage,
});

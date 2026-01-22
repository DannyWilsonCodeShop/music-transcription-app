import { defineFunction } from '@aws-amplify/backend';

export const transcribeAudio = defineFunction({
  name: 'transcribe-audio',
  entry: './handler.ts',
  environment: {
    OPENAI_API_KEY_SECRET: 'music-transcription/openai-key',
    YOUTUBE_API_KEY_SECRET: 'music-transcription/youtube-key'
  },
  timeoutSeconds: 300, // 5 minutes for audio processing
  memoryMB: 1024
});
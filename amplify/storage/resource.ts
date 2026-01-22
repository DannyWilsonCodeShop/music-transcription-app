import { defineStorage } from '@aws-amplify/backend';

export const storage = defineStorage({
  name: 'musicTranscriptionStorage',
  access: (allow) => ({
    'audio-files/*': [
      allow.guest.to(['read', 'write']),
      allow.authenticated.to(['read', 'write', 'delete'])
    ],
    'transcriptions/*': [
      allow.guest.to(['read']),
      allow.authenticated.to(['read', 'write', 'delete'])
    ]
  })
});
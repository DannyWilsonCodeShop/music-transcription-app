import { defineFunction } from '@aws-amplify/backend';

export const jobTrigger = defineFunction({
  name: 'job-trigger',
  entry: './handler.ts',
  timeoutSeconds: 60,
  memoryMB: 256
});

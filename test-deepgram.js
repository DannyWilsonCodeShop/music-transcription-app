// Test script for Deepgram API
import dotenv from 'dotenv';
import fetch from 'node-fetch';
import fs from 'fs';

dotenv.config();

const DEEPGRAM_API_KEY = process.env.DEEPGRAM_API_KEY;

if (!DEEPGRAM_API_KEY || DEEPGRAM_API_KEY === 'paste-your-deepgram-key-here') {
  console.error('❌ Please set your DEEPGRAM_API_KEY in the .env file');
  process.exit(1);
}

async function testDeepgram() {
  console.log('🧪 Testing Deepgram API...\n');
  
  try {
    // Test with a simple API call to check authentication
    const response = await fetch('https://api.deepgram.com/v1/projects', {
      method: 'GET',
      headers: {
        'Authorization': `Token ${DEEPGRAM_API_KEY}`
      }
    });

    if (!response.ok) {
      const error = await response.text();
      console.error('❌ API Error:', response.status, error);
      return;
    }

    const data = await response.json();
    console.log('✅ Success! Deepgram API is working');
    console.log('   Projects found:', data.projects?.length || 0);
    
    if (data.projects && data.projects.length > 0) {
      const project = data.projects[0];
      console.log('   Project ID:', project.project_id);
      console.log('   Project Name:', project.name);
    }
    
    console.log('\n💡 Your Deepgram API key is valid and ready to use!');
    
  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

testDeepgram();

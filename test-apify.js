// Test script for Apify YouTube Audio Scraper
import dotenv from 'dotenv';
dotenv.config();

const APIFY_TOKEN = process.env.APIFY_API_TOKEN;

if (!APIFY_TOKEN || APIFY_TOKEN === 'paste-your-new-token-here') {
  console.error('❌ Please set your APIFY_API_TOKEN in the .env file');
  process.exit(1);
}

async function testApify() {
  console.log('🧪 Testing Apify API...\n');
  
  try {
    // Using a simpler YouTube transcript scraper that doesn't need extra API keys
    const response = await fetch('https://api.apify.com/v2/acts/agentx~youtube-transcript/runs', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${APIFY_TOKEN}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        video_url: 'https://www.youtube.com/watch?v=jNQXAC9IVRw' // "Me at the zoo" - first YouTube video
      })
    });

    if (!response.ok) {
      const error = await response.text();
      console.error('❌ API Error:', response.status, error);
      return;
    }

    const data = await response.json();
    console.log('✅ Success! Run started:');
    console.log('   Run ID:', data.data.id);
    console.log('   Status:', data.data.status);
    console.log('   View run:', `https://console.apify.com/actors/runs/${data.data.id}`);
    console.log('\n💡 The scraper is now running. Check the Apify console to see results.');
    
  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

testApify();

// Test the working API endpoint
const API_BASE_URL = 'https://ppq03hif98.execute-api.us-east-1.amazonaws.com/dev';

async function testWorkingAPI() {
  console.log('🧪 Testing Working API Endpoint...');
  console.log('API URL:', API_BASE_URL);
  
  try {
    // Test with a simple YouTube URL
    const testUrl = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'; // Rick Roll for testing
    
    console.log('\n📡 Starting transcription job...');
    const response = await fetch(`${API_BASE_URL}/jobs`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        youtubeUrl: testUrl,
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      console.error('❌ API Error:', response.status, error);
      return;
    }

    const data = await response.json();
    console.log('✅ Job started successfully:', data);
    
    if (data.jobId) {
      console.log('\n🔍 Checking job status...');
      
      // Wait a moment then check status
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const statusResponse = await fetch(`${API_BASE_URL}/jobs/${data.jobId}`);
      if (statusResponse.ok) {
        const statusData = await statusResponse.json();
        console.log('📊 Job status:', statusData);
      }
    }
    
    console.log('\n🎉 API is working correctly!');
    console.log('✅ Ready to enable live mode on dev branch');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  }
}

testWorkingAPI();
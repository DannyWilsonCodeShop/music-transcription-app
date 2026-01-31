// Start Local Enhanced Music Transcription System
// Installs dependencies and starts the local server

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

async function startLocalEnhancedSystem() {
  console.log('🚀 Starting Local Enhanced Music Transcription System...\n');

  try {
    const localServerPath = path.join(__dirname, 'local-server');
    
    // Check if local-server directory exists
    if (!fs.existsSync(localServerPath)) {
      console.error('❌ Local server directory not found!');
      console.log('Please ensure the local-server directory exists with all modules.');
      return;
    }

    console.log('📦 Installing dependencies...');
    
    // Install dependencies
    process.chdir(localServerPath);
    
    try {
      execSync('npm install', { stdio: 'inherit' });
      console.log('✅ Dependencies installed successfully\n');
    } catch (error) {
      console.log('⚠️  npm install failed, trying with --force...');
      execSync('npm install --force', { stdio: 'inherit' });
      console.log('✅ Dependencies installed with --force\n');
    }

    console.log('🎼 Starting Enhanced Local Server...\n');
    console.log('📊 Server Features:');
    console.log('  • 0.2-second chord detection');
    console.log('  • Syllable-level lyrics analysis');
    console.log('  • Downbeat identification');
    console.log('  • Perfect measure-based PDF layout');
    console.log('  • RED/BLACK chord color coding');
    console.log('  • Up to 8 passing chords per measure\n');

    console.log('🔗 API Endpoints:');
    console.log('  • POST http://localhost:3001/jobs - Start transcription');
    console.log('  • GET http://localhost:3001/jobs/{jobId} - Check status');
    console.log('  • GET http://localhost:3001/pdfs/{jobId}.pdf - Download PDF\n');

    console.log('🎯 To use with your frontend:');
    console.log('  1. Update API_BASE_URL to: http://localhost:3001');
    console.log('  2. Or test directly with curl/Postman');
    console.log('  3. Monitor console for detailed progress\n');

    console.log('Starting server...\n');
    
    // Start the server
    execSync('npm start', { stdio: 'inherit' });

  } catch (error) {
    console.error('❌ Failed to start local enhanced system:', error.message);
    console.log('\n🔧 Troubleshooting:');
    console.log('  1. Ensure Node.js is installed (v16+ recommended)');
    console.log('  2. Check if port 3001 is available');
    console.log('  3. Try running: cd local-server && npm install && npm start');
    console.log('  4. Check the local-server/package.json file exists');
  }
}

// Update frontend configuration helper
function updateFrontendConfig() {
  console.log('\n📝 To update your frontend to use the local enhanced system:');
  console.log('\n1. Update src/services/transcriptionService.ts:');
  console.log('   const API_BASE_URL = "http://localhost:3001";');
  console.log('\n2. Or create a .env.local file:');
  console.log('   REACT_APP_API_BASE_URL=http://localhost:3001');
  console.log('\n3. Restart your frontend: npm run dev');
}

if (require.main === module) {
  startLocalEnhancedSystem().then(() => {
    updateFrontendConfig();
  });
}

module.exports = { startLocalEnhancedSystem, updateFrontendConfig };
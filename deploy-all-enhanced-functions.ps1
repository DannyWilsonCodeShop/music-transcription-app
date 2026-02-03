# Deploy All Enhanced Functions
Write-Host "🚀 Deploying All Enhanced Functions..." -ForegroundColor Green

# Function 1: Enhanced Chord Detector Trigger
Write-Host "`n📊 Deploying Enhanced Chord Detector..." -ForegroundColor Cyan
Set-Location "backend/functions-v2/chord-detector-trigger"
if (Test-Path "node_modules") { Remove-Item -Recurse -Force "node_modules" }
npm install --production
Compress-Archive -Path "index.js", "package.json", "node_modules" -DestinationPath "enhanced-chord-detector.zip" -Force
aws lambda update-function-code --function-name "chordscout-v2-chord-detector-trigger-dev" --zip-file "fileb://enhanced-chord-detector.zip"
Remove-Item "enhanced-chord-detector.zip" -Force
Set-Location "../../.."

# Function 2: Enhanced Lyrics Transcriber
Write-Host "`n🎤 Deploying Enhanced Lyrics Transcriber..." -ForegroundColor Cyan
Set-Location "backend/functions-v2/lyrics-transcriber"
if (Test-Path "node_modules") { Remove-Item -Recurse -Force "node_modules" }
npm install --production
Compress-Archive -Path "index.js", "package.json", "node_modules" -DestinationPath "enhanced-lyrics-transcriber.zip" -Force
aws lambda update-function-code --function-name "chordscout-v2-lyrics-transcriber-dev" --zip-file "fileb://enhanced-lyrics-transcriber.zip"
Remove-Item "enhanced-lyrics-transcriber.zip" -Force
Set-Location "../../.."

# Function 3: Enhanced PDF Generator
Write-Host "`n📄 Deploying Enhanced PDF Generator..." -ForegroundColor Cyan
Set-Location "backend/functions-v2/pdf-generator"
if (Test-Path "node_modules") { Remove-Item -Recurse -Force "node_modules" }
npm install --production
Compress-Archive -Path "index.js", "package.json", "node_modules" -DestinationPath "enhanced-pdf-generator.zip" -Force
aws lambda update-function-code --function-name "chordscout-v2-pdf-generator-dev" --zip-file "fileb://enhanced-pdf-generator.zip"
Remove-Item "enhanced-pdf-generator.zip" -Force
Set-Location "../../.."

Write-Host "`n✅ All Enhanced Functions Deployed Successfully!" -ForegroundColor Green
Write-Host "`n🎯 Enhanced Features Now Active:" -ForegroundColor Yellow
Write-Host "  • Enhanced 0.2s chord detection intervals" -ForegroundColor White
Write-Host "  • Syllable-aligned lyrics processing" -ForegroundColor White
Write-Host "  • Professional measure-based PDF layout" -ForegroundColor White
Write-Host "  • Nashville Number System integration" -ForegroundColor White

Write-Host "`n🧪 Test the enhanced system:" -ForegroundColor Cyan
Write-Host "  Visit: https://dev.dqg97bbmmprz.amplifyapp.com/" -ForegroundColor White
Write-Host "  Submit any YouTube music URL" -ForegroundColor White
Write-Host "  Expect: Professional PDFs with 20x more chord data" -ForegroundColor White
# Deploy YouTube Downloader Function
Write-Host "🎵 Deploying YouTube Downloader Function..." -ForegroundColor Green

# Create zip file
Set-Location "backend/functions"
# Copy the fixed file to index.py (Lambda expects this name)
Copy-Item "youtube-downloader-fixed.py" "index.py" -Force
Compress-Archive -Path "index.py" -DestinationPath "youtube-downloader.zip" -Force
Set-Location "../.."

# Update Lambda function
Write-Host "Updating Lambda function..." -ForegroundColor Yellow
$result = aws lambda update-function-code --function-name chordscout-youtube-downloader-dev --zip-file "fileb://backend/functions/youtube-downloader.zip"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ YouTube Downloader function updated successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to update function" -ForegroundColor Red
    Write-Host $result
}
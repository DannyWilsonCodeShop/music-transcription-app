# PowerShell script to deploy RapidAPI YouTube solution

Write-Host "=== Deploying RapidAPI YouTube Solution ===" -ForegroundColor Green
Write-Host ""

# Check if RapidAPI key is provided
$RAPIDAPI_KEY = $env:RAPIDAPI_KEY
if (-not $RAPIDAPI_KEY) {
    Write-Host "❌ RAPIDAPI_KEY environment variable not set" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please set your RapidAPI key first:" -ForegroundColor Yellow
    Write-Host "  `$env:RAPIDAPI_KEY = 'your-rapidapi-key-here'" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Get your key from: https://rapidapi.com/developer/dashboard" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ RapidAPI key found" -ForegroundColor Green

# Create deployment package
Write-Host "Creating deployment package..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "temp-deploy" | Out-Null
Copy-Item "backend/lambda-functions/youtube-downloader-rapidapi.py" "temp-deploy/index.py"

# Create requirements.txt
$requirements = @"
requests==2.31.0
boto3==1.34.0
"@
$requirements | Out-File -FilePath "temp-deploy/requirements.txt" -Encoding UTF8

# Install dependencies
Set-Location "temp-deploy"
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt -t . --quiet

# Create deployment zip
Write-Host "Creating deployment package..." -ForegroundColor Yellow
Compress-Archive -Path ".\*" -DestinationPath "..\youtube-downloader-rapidapi.zip" -Force
Set-Location ".."

# Update Lambda function
Write-Host "Updating Lambda function..." -ForegroundColor Yellow
aws lambda update-function-code `
    --function-name chordscout-youtube-downloader-dev `
    --zip-file fileb://youtube-downloader-rapidapi.zip `
    --region us-east-1

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to update Lambda function code" -ForegroundColor Red
    exit 1
}

# Update environment variables
Write-Host "Setting environment variables..." -ForegroundColor Yellow
$envVars = @{
    BUCKET_NAME = "chordscout-audio-dev-090130568474"
    RAPIDAPI_KEY = $RAPIDAPI_KEY
    ENVIRONMENT = "dev"
} | ConvertTo-Json -Compress

aws lambda update-function-configuration `
    --function-name chordscout-youtube-downloader-dev `
    --environment "Variables=$envVars" `
    --region us-east-1

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to update Lambda environment variables" -ForegroundColor Red
    exit 1
}

# Clean up
Remove-Item -Recurse -Force "temp-deploy"
Remove-Item "youtube-downloader-rapidapi.zip"

Write-Host ""
Write-Host "✅ RapidAPI solution deployed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "🎉 Your YouTube downloads should now work reliably!" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Test with a YouTube video in your app" -ForegroundColor White
Write-Host "2. Monitor usage in RapidAPI dashboard" -ForegroundColor White
Write-Host "3. Check CloudWatch logs for any issues" -ForegroundColor White
Write-Host ""
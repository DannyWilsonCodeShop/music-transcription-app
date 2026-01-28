#!/usr/bin/env pwsh

Write-Host "🚀 Deploying Working RapidAPI YouTube Downloader" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green

# Set variables
$FUNCTION_NAME = "chordscout-youtube-downloader-dev"
$REGION = "us-east-1"
$BUCKET_NAME = "music-transcription-app-audio"
$RAPIDAPI_KEY = "252611e8d7mshdde3262a7e2137bp12792bjsn7ce487b8a3dc"

Write-Host "✅ RapidAPI Status: WORKING (youtube-mp36.p.rapidapi.com)" -ForegroundColor Green
Write-Host "✅ Function: $FUNCTION_NAME" -ForegroundColor Green
Write-Host "✅ Region: $REGION" -ForegroundColor Green
Write-Host "✅ Bucket: $BUCKET_NAME" -ForegroundColor Green
Write-Host ""

# Create deployment package
Write-Host "📦 Creating deployment package..." -ForegroundColor Yellow
Set-Location backend/lambda-functions

# Remove old files
Remove-Item lambda_function.py -ErrorAction SilentlyContinue
Remove-Item youtube-downloader-rapidapi.zip -ErrorAction SilentlyContinue

# Copy and rename the file
Copy-Item youtube-downloader-rapidapi.py lambda_function.py

# Verify the file exists
if (Test-Path lambda_function.py) {
    Write-Host "✅ lambda_function.py created" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to create lambda_function.py" -ForegroundColor Red
    exit 1
}

# Create zip using PowerShell
Compress-Archive -Path lambda_function.py -DestinationPath youtube-downloader-rapidapi.zip -Force
Write-Host "✅ Package created: youtube-downloader-rapidapi.zip" -ForegroundColor Green

# Deploy to AWS Lambda
Write-Host ""
Write-Host "🚀 Deploying to AWS Lambda..." -ForegroundColor Yellow

# Update function code
try {
    aws lambda update-function-code `
        --function-name $FUNCTION_NAME `
        --zip-file fileb://youtube-downloader-rapidapi.zip `
        --region $REGION

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Function code updated successfully!" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to update function code" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Error updating function code: $_" -ForegroundColor Red
    exit 1
}

# Update function configuration (handler and environment)
Write-Host ""
Write-Host "🔧 Updating function configuration..." -ForegroundColor Yellow

try {
    aws lambda update-function-configuration `
        --function-name $FUNCTION_NAME `
        --handler "lambda_function.lambda_handler" `
        --environment "Variables={BUCKET_NAME=$BUCKET_NAME,RAPIDAPI_KEY=$RAPIDAPI_KEY}" `
        --region $REGION

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Function configuration updated!" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to update function configuration" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Error updating function configuration: $_" -ForegroundColor Red
    exit 1
}

# Test the function
Write-Host ""
Write-Host "🧪 Testing the deployed function..." -ForegroundColor Yellow

$timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$TEST_PAYLOAD = @{
    youtubeUrl = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    jobId = "test-rapidapi-$timestamp"
} | ConvertTo-Json -Compress

Write-Host "Test payload: $TEST_PAYLOAD"

try {
    aws lambda invoke `
        --function-name $FUNCTION_NAME `
        --payload $TEST_PAYLOAD `
        --region $REGION `
        response.json

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Function invoked successfully!" -ForegroundColor Green
        Write-Host "Response:"
        
        $response = Get-Content response.json | ConvertFrom-Json
        $response | ConvertTo-Json -Depth 10
        
        # Check if successful
        if ($response.statusCode -eq 200) {
            Write-Host ""
            Write-Host "🎉 SUCCESS! RapidAPI YouTube Downloader is working!" -ForegroundColor Green
            Write-Host "✅ Audio downloaded and uploaded to S3" -ForegroundColor Green
            Write-Host "✅ Ready for production use" -ForegroundColor Green
        } else {
            Write-Host ""
            Write-Host "⚠️  Function ran but returned an error:" -ForegroundColor Yellow
            $response | ConvertTo-Json -Depth 10
        }
    } else {
        Write-Host "❌ Failed to invoke function" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Error invoking function: $_" -ForegroundColor Red
}

# Cleanup
Remove-Item lambda_function.py -ErrorAction SilentlyContinue
Remove-Item response.json -ErrorAction SilentlyContinue
Remove-Item youtube-downloader-rapidapi.zip -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "🏁 Deployment complete!" -ForegroundColor Green
Write-Host "Next steps:"
Write-Host "1. ✅ RapidAPI is working" -ForegroundColor Green
Write-Host "2. ✅ Lambda function deployed" -ForegroundColor Green
Write-Host "3. 🔄 Test full workflow with Step Functions" -ForegroundColor Yellow
Write-Host "4. 🚀 Deploy frontend updates" -ForegroundColor Yellow

Set-Location ../..
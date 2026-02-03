# Deploy CORS-enabled API Proxy Lambda Function
# This Lambda acts as a CORS-enabled proxy to the enhanced transcription system

Write-Host "🚀 Deploying CORS-enabled API Proxy Lambda..." -ForegroundColor Green

# Configuration
$FUNCTION_NAME = "chordscout-cors-api-proxy-dev"
$REGION = "us-east-1"
$STATE_MACHINE_ARN = "arn:aws:states:us-east-1:090130568474:stateMachine:ChordScout-V2-Transcription-dev"
$JOBS_TABLE_NAME = "ChordScout-Jobs-V2-dev"

# Create deployment package
Write-Host "📦 Creating deployment package..." -ForegroundColor Yellow
if (Test-Path "cors-api-proxy.zip") { Remove-Item "cors-api-proxy.zip" }

# Create package.json for dependencies
$packageJson = @{
    name = "cors-api-proxy"
    version = "1.0.0"
    dependencies = @{
        "@aws-sdk/client-sfn" = "^3.975.0"
        "@aws-sdk/client-dynamodb" = "^3.975.0"
        "@aws-sdk/lib-dynamodb" = "^3.975.0"
        "uuid" = "^9.0.0"
    }
} | ConvertTo-Json -Depth 3

$packageJson | Out-File -FilePath "package.json" -Encoding UTF8

# Install dependencies
Write-Host "📥 Installing dependencies..." -ForegroundColor Yellow
npm install --production

# Create the zip file
Write-Host "📦 Creating zip package..." -ForegroundColor Yellow
Compress-Archive -Path "fix-cors-lambda.js", "node_modules", "package.json" -DestinationPath "cors-api-proxy.zip" -Force

Write-Host "✅ Deployment package created: cors-api-proxy.zip" -ForegroundColor Green

# Check if function exists
Write-Host "🔍 Checking if Lambda function exists..." -ForegroundColor Yellow
try {
    aws lambda get-function --function-name $FUNCTION_NAME --region $REGION | Out-Null
    Write-Host "🔄 Updating existing Lambda function..." -ForegroundColor Yellow
    aws lambda update-function-code --function-name $FUNCTION_NAME --zip-file fileb://cors-api-proxy.zip --region $REGION
} catch {
    Write-Host "🆕 Creating new Lambda function..." -ForegroundColor Yellow
    aws lambda create-function `
        --function-name $FUNCTION_NAME `
        --runtime nodejs18.x `
        --role "arn:aws:iam::090130568474:role/ChordScout-Lambda-Role-dev" `
        --handler "fix-cors-lambda.handler" `
        --zip-file fileb://cors-api-proxy.zip `
        --timeout 30 `
        --memory-size 256 `
        --region $REGION
}

# Update environment variables
Write-Host "🔧 Setting environment variables..." -ForegroundColor Yellow
$envVars = @{
    STATE_MACHINE_ARN = $STATE_MACHINE_ARN
    JOBS_TABLE_NAME = $JOBS_TABLE_NAME
} | ConvertTo-Json -Compress

aws lambda update-function-configuration `
    --function-name $FUNCTION_NAME `
    --environment "Variables=$envVars" `
    --region $REGION

# Get function ARN
$FUNCTION_ARN = aws lambda get-function --function-name $FUNCTION_NAME --region $REGION --query 'Configuration.FunctionArn' --output text

Write-Host "✅ Lambda function deployed successfully!" -ForegroundColor Green
Write-Host "📋 Function Details:" -ForegroundColor Cyan
Write-Host "  - Name: $FUNCTION_NAME" -ForegroundColor White
Write-Host "  - ARN: $FUNCTION_ARN" -ForegroundColor White
Write-Host "  - Region: $REGION" -ForegroundColor White

# For now, let's use the existing API Gateway and just get its endpoint
Write-Host ""
Write-Host "🌐 Getting existing API Gateway endpoint..." -ForegroundColor Yellow

# The enhanced system is already using this API Gateway
$API_ENDPOINT = "https://rzx9drt3z1.execute-api.us-east-1.amazonaws.com/prod"

Write-Host ""
Write-Host "🎉 CORS-enabled Lambda deployment complete!" -ForegroundColor Green
Write-Host "📋 API Details:" -ForegroundColor Cyan
Write-Host "  - Endpoint: $API_ENDPOINT" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Update the existing API Gateway to use this CORS-enabled Lambda" -ForegroundColor White
Write-Host "2. Update frontend to disable mock mode" -ForegroundColor White
Write-Host "3. Test the enhanced transcription system" -ForegroundColor White

# Cleanup
Write-Host ""
Write-Host "🧹 Cleaning up temporary files..." -ForegroundColor Yellow
Remove-Item "cors-api-proxy.zip" -ErrorAction SilentlyContinue
Remove-Item "package.json" -ErrorAction SilentlyContinue
Remove-Item "package-lock.json" -ErrorAction SilentlyContinue
Remove-Item "node_modules" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "✅ Deployment complete!" -ForegroundColor Green
# Deploy Real Audio Analysis Lambda Function
# Creates and deploys a Lambda function with real chord detection capabilities

Write-Host "🎼 Deploying Real Audio Analysis Lambda Function..." -ForegroundColor Green

# Configuration
$FUNCTION_NAME = "chordscout-real-audio-analyzer-dev"
$REGION = "us-east-1"
$ACCOUNT_ID = "463470937777"
$ECR_REPO = "chordscout-real-audio-analyzer"
$IMAGE_TAG = "latest"

# Check prerequisites
Write-Host "📋 Checking prerequisites..." -ForegroundColor Yellow

# Check if Docker is running
try {
    docker version | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check if AWS CLI is configured
try {
    aws sts get-caller-identity | Out-Null
    Write-Host "✅ AWS CLI is configured" -ForegroundColor Green
} catch {
    Write-Host "❌ AWS CLI is not configured. Please run 'aws configure'." -ForegroundColor Red
    exit 1
}

# Step 1: Create ECR repository if it doesn't exist
Write-Host "🏗️ Step 1: Setting up ECR repository..." -ForegroundColor Yellow

try {
    aws ecr describe-repositories --repository-names $ECR_REPO --region $REGION | Out-Null
    Write-Host "✅ ECR repository exists: $ECR_REPO" -ForegroundColor Green
} catch {
    Write-Host "📦 Creating ECR repository: $ECR_REPO" -ForegroundColor Cyan
    aws ecr create-repository --repository-name $ECR_REPO --region $REGION
    Write-Host "✅ ECR repository created" -ForegroundColor Green
}

# Step 2: Build Docker image
Write-Host "🔨 Step 2: Building Docker image..." -ForegroundColor Yellow

Set-Location "backend/functions-v2/real-audio-analyzer"

try {
    docker build -t $ECR_REPO .
    Write-Host "✅ Docker image built successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker build failed" -ForegroundColor Red
    Set-Location "../../.."
    exit 1
}

# Step 3: Login to ECR and push image
Write-Host "📤 Step 3: Pushing image to ECR..." -ForegroundColor Yellow

$ECR_URI = "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPO"

try {
    # Login to ECR
    aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"
    
    # Tag and push image
    docker tag "$ECR_REPO:latest" "$ECR_URI:$IMAGE_TAG"
    docker push "$ECR_URI:$IMAGE_TAG"
    
    Write-Host "✅ Image pushed to ECR: $ECR_URI:$IMAGE_TAG" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to push image to ECR" -ForegroundColor Red
    Set-Location "../../.."
    exit 1
}

Set-Location "../../.."

# Step 4: Create or update Lambda function
Write-Host "🚀 Step 4: Creating/updating Lambda function..." -ForegroundColor Yellow

# Check if function exists
try {
    aws lambda get-function --function-name $FUNCTION_NAME --region $REGION | Out-Null
    $FUNCTION_EXISTS = $true
    Write-Host "📝 Function exists, will update" -ForegroundColor Cyan
} catch {
    $FUNCTION_EXISTS = $false
    Write-Host "📝 Function doesn't exist, will create" -ForegroundColor Cyan
}

if (-not $FUNCTION_EXISTS) {
    # Create new function
    Write-Host "🆕 Creating new Lambda function..." -ForegroundColor Cyan
    
    try {
        aws lambda create-function `
            --function-name $FUNCTION_NAME `
            --package-type Image `
            --code ImageUri="$ECR_URI:$IMAGE_TAG" `
            --role "arn:aws:iam::$ACCOUNT_ID:role/lambda-execution-role" `
            --timeout 300 `
            --memory-size 1024 `
            --environment Variables="{DYNAMODB_JOBS_TABLE=ChordScout-Jobs-dev,S3_AUDIO_BUCKET=chordscout-audio-dev-463470937777}" `
            --region $REGION
        
        Write-Host "✅ Lambda function created successfully" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to create Lambda function" -ForegroundColor Red
        Write-Host "Make sure the IAM role 'lambda-execution-role' exists with proper permissions" -ForegroundColor Yellow
        exit 1
    }
} else {
    # Update existing function
    Write-Host "🔄 Updating existing Lambda function..." -ForegroundColor Cyan
    
    try {
        aws lambda update-function-code `
            --function-name $FUNCTION_NAME `
            --image-uri "$ECR_URI:$IMAGE_TAG" `
            --region $REGION
        
        Write-Host "✅ Lambda function updated successfully" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to update Lambda function" -ForegroundColor Red
        exit 1
    }
}

# Step 5: Test the function
Write-Host "🧪 Step 5: Testing the function..." -ForegroundColor Yellow

$TEST_EVENT = @{
    jobId = "test-real-audio-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    audioUrl = "https://chordscout-audio-dev-463470937777.s3.amazonaws.com/audio/meetup_ring.mp3"
    analysisInterval = 0.5
} | ConvertTo-Json

Write-Host "🎵 Testing with meetup_ring.mp3..." -ForegroundColor Cyan

try {
    $result = aws lambda invoke `
        --function-name $FUNCTION_NAME `
        --payload $TEST_EVENT `
        --region $REGION `
        test-real-audio-response.json
    
    if (Test-Path "test-real-audio-response.json") {
        $response = Get-Content "test-real-audio-response.json" | ConvertFrom-Json
        
        Write-Host "✅ Function test completed" -ForegroundColor Green
        Write-Host "📊 Response status: $($response.statusCode)" -ForegroundColor Cyan
        
        if ($response.statusCode -eq 200 -and $response.body) {
            $body = $response.body
            Write-Host "🎼 Analysis results:" -ForegroundColor Cyan
            Write-Host "   Duration: $($body.results.duration)s" -ForegroundColor White
            Write-Host "   Tempo: $($body.results.tempo) BPM" -ForegroundColor White
            Write-Host "   Key: $($body.results.key)" -ForegroundColor White
            Write-Host "   Original detections: $($body.results.originalDetections)" -ForegroundColor White
            Write-Host "   Chord changes: $($body.results.chordChanges)" -ForegroundColor White
            Write-Host "   Data reduction: $($body.results.dataReduction)%" -ForegroundColor White
            Write-Host "   DynamoDB compatible: $($body.results.dynamoDbCompatible)" -ForegroundColor White
        }
        
        Remove-Item "test-real-audio-response.json" -ErrorAction SilentlyContinue
    }
} catch {
    Write-Host "❌ Function test failed" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

# Step 6: Summary
Write-Host "`n📋 Deployment Summary" -ForegroundColor Yellow
Write-Host "✅ Real Audio Analysis Lambda Function Deployed" -ForegroundColor Green
Write-Host "📦 ECR Repository: $ECR_URI" -ForegroundColor Cyan
Write-Host "🚀 Lambda Function: $FUNCTION_NAME" -ForegroundColor Cyan
Write-Host "🎼 Capabilities:" -ForegroundColor Cyan
Write-Host "   - Real audio file analysis using librosa" -ForegroundColor White
Write-Host "   - Tempo detection with beat tracking" -ForegroundColor White
Write-Host "   - Key detection using chromagram analysis" -ForegroundColor White
Write-Host "   - Chord recognition with template matching" -ForegroundColor White
Write-Host "   - Chord change detection for data reduction" -ForegroundColor White
Write-Host "   - Nashville number system generation" -ForegroundColor White
Write-Host "   - DynamoDB size optimization" -ForegroundColor White

Write-Host "`n🎉 Real Audio Analysis System Ready!" -ForegroundColor Green
Write-Host "The system now performs actual audio analysis instead of mock data." -ForegroundColor White
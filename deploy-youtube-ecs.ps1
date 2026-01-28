# Deploy YouTube Downloader ECS Solution
param(
    [string]$StackName = "youtube-downloader-ecs",
    [string]$Region = "us-east-1",
    [string]$VpcId = "",
    [string]$SubnetIds = "",
    [string]$JobsTable = "music-transcription-jobs",
    [string]$S3Bucket = "music-transcription-audio-dev"
)

Write-Host "🚀 Deploying YouTube Downloader ECS Solution" -ForegroundColor Green
Write-Host "Stack: $StackName" -ForegroundColor Yellow
Write-Host "Region: $Region" -ForegroundColor Yellow

# Get AWS Account ID
$AWS_ACCOUNT_ID = aws sts get-caller-identity --query Account --output text
Write-Host "Account: $AWS_ACCOUNT_ID" -ForegroundColor Yellow

# Auto-detect VPC and Subnets if not provided
if (-not $VpcId) {
    Write-Host "🔍 Auto-detecting VPC..." -ForegroundColor Blue
    $VpcId = aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query "Vpcs[0].VpcId" --output text --region $Region
    Write-Host "Found VPC: $VpcId" -ForegroundColor Green
}

if (-not $SubnetIds) {
    Write-Host "🔍 Auto-detecting Subnets..." -ForegroundColor Blue
    $SubnetList = aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VpcId" --query "Subnets[0:2].SubnetId" --output text --region $Region
    $SubnetIds = $SubnetList -replace "`t", ","
    Write-Host "Found Subnets: $SubnetIds" -ForegroundColor Green
}

# Deploy CloudFormation stack
Write-Host "📦 Deploying CloudFormation stack..." -ForegroundColor Blue
$TemplateFile = "backend/infrastructure-v2/youtube-downloader-ecs.yaml"

aws cloudformation deploy `
    --template-file $TemplateFile `
    --stack-name $StackName `
    --parameter-overrides `
        VpcId=$VpcId `
        SubnetIds=$SubnetIds `
        JobsTableName=$JobsTable `
        S3BucketName=$S3Bucket `
    --capabilities CAPABILITY_IAM `
    --region $Region

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ CloudFormation deployment failed" -ForegroundColor Red
    exit 1
}

Write-Host "✅ CloudFormation stack deployed successfully" -ForegroundColor Green

# Get stack outputs
Write-Host "📋 Getting stack outputs..." -ForegroundColor Blue
$ECRRepo = aws cloudformation describe-stacks --stack-name $StackName --query "Stacks[0].Outputs[?OutputKey=='ECRRepositoryURI'].OutputValue" --output text --region $Region
$LambdaArn = aws cloudformation describe-stacks --stack-name $StackName --query "Stacks[0].Outputs[?OutputKey=='LambdaFunctionArn'].OutputValue" --output text --region $Region

Write-Host "ECR Repository: $ECRRepo" -ForegroundColor Cyan
Write-Host "Lambda ARN: $LambdaArn" -ForegroundColor Cyan

# Check if Docker is available
$DockerAvailable = Get-Command docker -ErrorAction SilentlyContinue
if ($DockerAvailable) {
    Write-Host "🐳 Docker found - building and pushing image..." -ForegroundColor Blue
    
    # Build and push Docker image
    Set-Location "backend/functions-v2/youtube-downloader-ecs"
    
    # Login to ECR
    aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$Region.amazonaws.com"
    
    # Build and push
    docker build -t youtube-downloader:latest .
    docker tag youtube-downloader:latest "$ECRRepo:latest"
    docker push "$ECRRepo:latest"
    
    Set-Location "../../.."
    Write-Host "✅ Docker image built and pushed" -ForegroundColor Green
} else {
    Write-Host "⚠️  Docker not found - skipping image build" -ForegroundColor Yellow
    Write-Host "   You'll need to build and push the Docker image manually:" -ForegroundColor Yellow
    Write-Host "   1. Install Docker" -ForegroundColor White
    Write-Host "   2. Run: docker build -t youtube-downloader backend/functions-v2/youtube-downloader-ecs/" -ForegroundColor White
    Write-Host "   3. Run: docker tag youtube-downloader $ECRRepo:latest" -ForegroundColor White
    Write-Host "   4. Run: docker push $ECRRepo:latest" -ForegroundColor White
}

# Update Lambda function code
Write-Host "📦 Updating Lambda function code..." -ForegroundColor Blue
Set-Location "backend/functions-v2/youtube-downloader-trigger"

# Install dependencies and create zip
if (Test-Path "node_modules") { Remove-Item -Recurse -Force "node_modules" }
if (Test-Path "function.zip") { Remove-Item "function.zip" }

npm install --production
Compress-Archive -Path "index.js", "package.json", "node_modules" -DestinationPath "function.zip" -Force

# Update Lambda function
aws lambda update-function-code `
    --function-name youtube-downloader-trigger `
    --zip-file fileb://function.zip `
    --region $Region

Set-Location "../../.."

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Lambda function updated successfully" -ForegroundColor Green
} else {
    Write-Host "⚠️  Lambda function update failed - check if function exists" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 Deployment Summary:" -ForegroundColor Green
Write-Host "✅ CloudFormation stack: $StackName" -ForegroundColor White
Write-Host "✅ ECR Repository: $ECRRepo" -ForegroundColor White
Write-Host "✅ Lambda Function: youtube-downloader-trigger" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
if (-not $DockerAvailable) {
    Write-Host "1. Build and push Docker image (see instructions above)" -ForegroundColor White
}
Write-Host "2. Update Step Function to use new Lambda" -ForegroundColor White
Write-Host "3. Test end-to-end workflow" -ForegroundColor White
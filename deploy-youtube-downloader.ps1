# Build and Deploy YouTube Downloader ECS Solution (PowerShell)
Write-Host "🚀 Building YouTube Downloader ECS Solution..." -ForegroundColor Green

# Set variables
$AWS_REGION = "us-east-1"
$AWS_ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text)
$ECR_REPO = "youtube-downloader"
$IMAGE_TAG = "latest"

Write-Host "AWS Account: $AWS_ACCOUNT_ID" -ForegroundColor Yellow
Write-Host "Region: $AWS_REGION" -ForegroundColor Yellow

# 1. Build and push Docker image
Write-Host "📦 Building Docker image..." -ForegroundColor Blue
Set-Location "backend/functions-v2/youtube-downloader-ecs"

# Create ECR repository if it doesn't exist
try {
    aws ecr describe-repositories --repository-names $ECR_REPO --region $AWS_REGION 2>$null
} catch {
    Write-Host "Creating ECR repository..." -ForegroundColor Yellow
    aws ecr create-repository --repository-name $ECR_REPO --region $AWS_REGION
}

# Get ECR login token
Write-Host "🔐 Logging into ECR..." -ForegroundColor Blue
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

# Build and tag image
Write-Host "🔨 Building Docker image..." -ForegroundColor Blue
docker build -t "${ECR_REPO}:${IMAGE_TAG}" .
docker tag "${ECR_REPO}:${IMAGE_TAG}" "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/${ECR_REPO}:${IMAGE_TAG}"

# Push image
Write-Host "📤 Pushing to ECR..." -ForegroundColor Blue
docker push "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/${ECR_REPO}:${IMAGE_TAG}"

Set-Location "../../.."

# 2. Package Lambda function
Write-Host "📦 Packaging Lambda function..." -ForegroundColor Blue
Set-Location "backend/functions-v2/youtube-downloader-trigger"
npm install
Compress-Archive -Path "index.js", "package.json", "node_modules" -DestinationPath "function.zip" -Force
Set-Location "../../.."

Write-Host "✅ Build complete!" -ForegroundColor Green
Write-Host "🐳 Docker image: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/${ECR_REPO}:${IMAGE_TAG}" -ForegroundColor Cyan
Write-Host "📦 Lambda package: backend/functions-v2/youtube-downloader-trigger/function.zip" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Create ECS task definition" -ForegroundColor White
Write-Host "2. Deploy Lambda function" -ForegroundColor White
Write-Host "3. Update Step Function to use new Lambda" -ForegroundColor White
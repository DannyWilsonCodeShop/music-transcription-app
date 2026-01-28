# Deploy ECS YouTube Downloader
# This script builds and deploys the Docker container to AWS ECS

param(
    [string]$Region = "us-east-1",
    [string]$AccountId = "",
    [string]$ClusterName = "chord-scout-cluster",
    [string]$TaskDefinitionName = "youtube-downloader",
    [string]$ImageName = "chord-scout-youtube-downloader"
)

Write-Host "=== Deploying ECS YouTube Downloader ===" -ForegroundColor Green

# Get AWS Account ID if not provided
if (-not $AccountId) {
    Write-Host "Getting AWS Account ID..." -ForegroundColor Yellow
    $AccountId = (aws sts get-caller-identity --query Account --output text)
    if (-not $AccountId) {
        Write-Error "Failed to get AWS Account ID. Make sure AWS CLI is configured."
        exit 1
    }
}

$ECRRepository = "$AccountId.dkr.ecr.$Region.amazonaws.com/$ImageName"

Write-Host "Account ID: $AccountId" -ForegroundColor Cyan
Write-Host "Region: $Region" -ForegroundColor Cyan
Write-Host "ECR Repository: $ECRRepository" -ForegroundColor Cyan

# Step 1: Create ECR repository if it doesn't exist
Write-Host "`n1. Creating ECR repository..." -ForegroundColor Yellow
aws ecr describe-repositories --repository-names $ImageName --region $Region 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating new ECR repository: $ImageName" -ForegroundColor Yellow
    aws ecr create-repository --repository-name $ImageName --region $Region
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create ECR repository"
        exit 1
    }
} else {
    Write-Host "ECR repository already exists" -ForegroundColor Green
}

# Step 2: Login to ECR
Write-Host "`n2. Logging into ECR..." -ForegroundColor Yellow
aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin $ECRRepository
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to login to ECR"
    exit 1
}

# Step 3: Build Docker image
Write-Host "`n3. Building Docker image..." -ForegroundColor Yellow
Set-Location "backend/functions-v2/youtube-downloader-ecs"
docker build -t $ImageName .
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to build Docker image"
    exit 1
}

# Step 4: Tag and push image
Write-Host "`n4. Tagging and pushing image..." -ForegroundColor Yellow
docker tag $ImageName`:latest $ECRRepository`:latest
docker push $ECRRepository`:latest
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to push Docker image"
    exit 1
}

Set-Location "../../.."

# Step 5: Create ECS cluster if it doesn't exist
Write-Host "`n5. Creating ECS cluster..." -ForegroundColor Yellow
aws ecs describe-clusters --clusters $ClusterName --region $Region 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating new ECS cluster: $ClusterName" -ForegroundColor Yellow
    aws ecs create-cluster --cluster-name $ClusterName --region $Region
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create ECS cluster"
        exit 1
    }
} else {
    Write-Host "ECS cluster already exists" -ForegroundColor Green
}

# Step 6: Create task definition
Write-Host "`n6. Creating ECS task definition..." -ForegroundColor Yellow

$TaskDefinition = @{
    family = $TaskDefinitionName
    networkMode = "awsvpc"
    requiresCompatibilities = @("FARGATE")
    cpu = "256"
    memory = "512"
    executionRoleArn = "arn:aws:iam::$AccountId`:role/ecsTaskExecutionRole"
    taskRoleArn = "arn:aws:iam::$AccountId`:role/ecsTaskRole"
    containerDefinitions = @(
        @{
            name = "youtube-downloader"
            image = "$ECRRepository`:latest"
            essential = $true
            logConfiguration = @{
                logDriver = "awslogs"
                options = @{
                    "awslogs-group" = "/ecs/youtube-downloader"
                    "awslogs-region" = $Region
                    "awslogs-stream-prefix" = "ecs"
                }
            }
            environment = @(
                @{ name = "AWS_DEFAULT_REGION"; value = $Region }
            )
        }
    )
} | ConvertTo-Json -Depth 10

# Create CloudWatch log group
aws logs create-log-group --log-group-name "/ecs/youtube-downloader" --region $Region 2>$null

# Register task definition
$TaskDefinition | Out-File -FilePath "task-definition.json" -Encoding UTF8
aws ecs register-task-definition --cli-input-json file://task-definition.json --region $Region
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to register task definition"
    exit 1
}

Remove-Item "task-definition.json"

Write-Host "`n=== Deployment Complete! ===" -ForegroundColor Green
Write-Host "ECR Repository: $ECRRepository" -ForegroundColor Cyan
Write-Host "ECS Cluster: $ClusterName" -ForegroundColor Cyan
Write-Host "Task Definition: $TaskDefinitionName" -ForegroundColor Cyan

Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Create IAM roles (ecsTaskExecutionRole, ecsTaskRole)" -ForegroundColor White
Write-Host "2. Update Lambda trigger to run ECS tasks" -ForegroundColor White
Write-Host "3. Test with a YouTube URL" -ForegroundColor White
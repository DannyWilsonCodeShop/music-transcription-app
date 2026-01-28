# Create IAM roles for ECS YouTube Downloader
# This script creates the necessary IAM roles and policies

param(
    [string]$Region = "us-east-1"
)

Write-Host "=== Creating ECS IAM Roles ===" -ForegroundColor Green

# Step 1: Create ECS Task Execution Role
Write-Host "`n1. Creating ECS Task Execution Role..." -ForegroundColor Yellow

$ExecutionRoleTrustPolicy = @{
    Version = "2012-10-17"
    Statement = @(
        @{
            Effect = "Allow"
            Principal = @{
                Service = "ecs-tasks.amazonaws.com"
            }
            Action = "sts:AssumeRole"
        }
    )
} | ConvertTo-Json -Depth 10

$ExecutionRoleTrustPolicy | Out-File -FilePath "execution-role-trust-policy.json" -Encoding UTF8

# Create execution role
$executionRoleResult = aws iam create-role --role-name ecsTaskExecutionRole --assume-role-policy-document file://execution-role-trust-policy.json 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "Created ecsTaskExecutionRole" -ForegroundColor Green
} else {
    Write-Host "Role may already exist: $executionRoleResult" -ForegroundColor Yellow
}

# Attach policy to execution role
aws iam attach-role-policy --role-name ecsTaskExecutionRole --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
Write-Host "Attached execution policy" -ForegroundColor Green

Remove-Item "execution-role-trust-policy.json"

# Step 2: Create ECS Task Role with permissions
Write-Host "`n2. Creating ECS Task Role..." -ForegroundColor Yellow

$TaskRoleTrustPolicy = @{
    Version = "2012-10-17"
    Statement = @(
        @{
            Effect = "Allow"
            Principal = @{
                Service = "ecs-tasks.amazonaws.com"
            }
            Action = "sts:AssumeRole"
        }
    )
} | ConvertTo-Json -Depth 10

$TaskRoleTrustPolicy | Out-File -FilePath "task-role-trust-policy.json" -Encoding UTF8

# Create task role
$taskRoleResult = aws iam create-role --role-name ecsTaskRole --assume-role-policy-document file://task-role-trust-policy.json 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "Created ecsTaskRole" -ForegroundColor Green
} else {
    Write-Host "Role may already exist: $taskRoleResult" -ForegroundColor Yellow
}

Remove-Item "task-role-trust-policy.json"

# Step 3: Create custom policy for the task role
Write-Host "`n3. Creating custom policy for ECS task..." -ForegroundColor Yellow

$TaskRolePolicy = @{
    Version = "2012-10-17"
    Statement = @(
        @{
            Effect = "Allow"
            Action = @(
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            )
            Resource = "arn:aws:s3:::chord-scout-*/*"
        },
        @{
            Effect = "Allow"
            Action = @(
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:Query"
            )
            Resource = "arn:aws:dynamodb:$Region`:*:table/chord-scout-*"
        },
        @{
            Effect = "Allow"
            Action = @(
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            )
            Resource = "arn:aws:logs:$Region`:*:*"
        }
    )
} | ConvertTo-Json -Depth 10

$TaskRolePolicy | Out-File -FilePath "task-role-policy.json" -Encoding UTF8

# Create policy
$policyResult = aws iam create-policy --policy-name ChordScoutECSTaskPolicy --policy-document file://task-role-policy.json 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "Created ChordScoutECSTaskPolicy" -ForegroundColor Green
} else {
    Write-Host "Policy may already exist: $policyResult" -ForegroundColor Yellow
}

# Get account ID
$AccountId = (aws sts get-caller-identity --query Account --output text)

# Attach the policy to the role
aws iam attach-role-policy --role-name ecsTaskRole --policy-arn "arn:aws:iam::$AccountId`:policy/ChordScoutECSTaskPolicy"
Write-Host "Attached custom policy to task role" -ForegroundColor Green

Remove-Item "task-role-policy.json"

Write-Host "`n=== IAM Roles Setup Complete! ===" -ForegroundColor Green
Write-Host "Account ID: $AccountId" -ForegroundColor Cyan
Write-Host "Execution Role: ecsTaskExecutionRole" -ForegroundColor Cyan
Write-Host "Task Role: ecsTaskRole" -ForegroundColor Cyan
Write-Host "Custom Policy: ChordScoutECSTaskPolicy" -ForegroundColor Cyan

Write-Host "`nRoles are ready for ECS deployment!" -ForegroundColor Yellow
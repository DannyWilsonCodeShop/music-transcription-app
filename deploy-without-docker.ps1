# Deploy YouTube Downloader WITHOUT Docker (uses CodeBuild)
Write-Host "🚀 Deploying YouTube Downloader (Cloud Build)" -ForegroundColor Green

# Deploy infrastructure first
./deploy-youtube-ecs.ps1

# Create CodeBuild project to build Docker image
$BuildSpec = @"
version: 0.2
phases:
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin `$AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
  build:
    commands:
      - echo Build started on `date`
      - echo Building the Docker image...
      - docker build -t youtube-downloader backend/functions-v2/youtube-downloader-ecs/
      - docker tag youtube-downloader:latest `$AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/youtube-downloader:latest
  post_build:
    commands:
      - echo Build completed on `date`
      - echo Pushing the Docker image...
      - docker push `$AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/youtube-downloader:latest
"@

$BuildSpec | Out-File -FilePath "buildspec.yml" -Encoding UTF8

Write-Host "✅ Ready to build in cloud!" -ForegroundColor Green
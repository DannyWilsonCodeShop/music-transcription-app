# 🐳 Docker Installation Checklist

## Installation Steps
- [ ] Download Docker Desktop from https://www.docker.com/products/docker-desktop/
- [ ] Run installer (requires admin privileges)
- [ ] Restart computer when prompted
- [ ] Launch Docker Desktop
- [ ] Wait for Docker to start (whale icon in system tray)

## Verify Installation
Run these commands to verify Docker is working:
```powershell
docker --version
docker run hello-world
```

## Ready to Deploy
Once Docker is running, we'll execute:
```powershell
./deploy-youtube-ecs.ps1
```

## What This Will Do
1. ✅ Deploy CloudFormation stack (ECS + Lambda)
2. ✅ Build Docker image with yt-dlp
3. ✅ Push image to ECR
4. ✅ Update Lambda function
5. ✅ Test the complete solution

## Expected Timeline
- Docker install: ~5 minutes
- Deployment: ~10 minutes
- Testing: ~5 minutes
- **Total: ~20 minutes to working system**
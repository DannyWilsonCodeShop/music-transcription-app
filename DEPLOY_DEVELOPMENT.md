# 🚀 Deploy Development Environment

## Current Status

✅ **Production (main branch)**: Mock data enabled, stable for demos  
🔧 **Development (development branch)**: Real YouTube integration work

## Deploy Development Environment

### Step 1: Create Development Amplify App

1. **Go to AWS Amplify Console:**
   - Visit: https://console.aws.amazon.com/amplify/
   - Click "New app" → "Host web app"

2. **Connect Repository:**
   - Choose GitHub
   - Select: `music-transcription-app` repository
   - **Important**: Choose `development` branch (not main)
   - App name: `chord-scout-dev`

3. **Build Settings:**
   - Auto-detected from `amplify.yml`
   - No changes needed

### Step 2: Environment Variables

Add these in Amplify Console → Environment variables:

```
NODE_VERSION = 18
OPENAI_API_KEY = your_openai_api_key_here
RAPIDAPI_KEY = 252611e8d7mshdde3262a7e2137bp12792bjsn7ce487b8a3dc
```

### Step 3: Deploy and Test

1. **Deploy**: Click "Save and deploy"
2. **Wait**: ~5-10 minutes for build
3. **Get URL**: Something like `https://development.d1234567890.amplifyapp.com`

## Development Features

Your development environment includes:

### YouTube Download Methods
1. **RapidAPI Integration** (primary)
   - Working API calls
   - Metadata extraction
   - Download links (with reliability issues)

2. **yt-dlp Fallback** (backup)
   - Local processing
   - Cookie-based authentication
   - High reliability

3. **Error Handling**
   - Retry logic
   - Fallback mechanisms
   - Detailed logging

### Testing Tools
- `test-rapidapi-simple.py` - Basic API testing
- `test-different-video.py` - Multiple video testing
- `test-production-ready.py` - Production readiness check
- `deploy-working-rapidapi.ps1` - Lambda deployment

## Development Workflow

```bash
# Work on development branch
git checkout development

# Make changes
# ... edit files ...

# Commit and push
git add .
git commit -m "Development: Your changes"
git push origin development

# Amplify auto-deploys development branch
```

## Production Promotion

When development is stable:

```bash
# Switch to main
git checkout main

# Merge development
git merge development

# Push to production
git push origin main

# Production Amplify app auto-deploys
```

## Environment URLs

After deployment:
- **Production**: `https://main.d1234567890.amplifyapp.com` (mock data)
- **Development**: `https://development.d1234567890.amplifyapp.com` (real YouTube)

## Troubleshooting

**Build Fails?**
- Check Node.js version is 18
- Verify environment variables
- Check build logs

**RapidAPI Issues?**
- API key is valid and working
- Download links may be unreliable (known issue)
- Fallback to yt-dlp should work

**Lambda Functions?**
- Use deployment scripts in development branch
- Check CloudWatch logs for errors

## Next Steps

1. ✅ Deploy development environment
2. 🧪 Test RapidAPI reliability in production
3. 🔧 Improve fallback mechanisms if needed
4. 📊 Monitor usage and costs
5. 🚀 Promote to production when stable

This gives you a safe development environment! 🎵
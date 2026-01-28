# 🔧 Development Environment Setup

## Development Branch Deployment

You now have two environments:
- **Production (main branch)**: Mock data enabled for client demos
- **Development (development branch)**: Real YouTube integration work

## Deploy Development Environment

### Option 1: Separate Amplify App (Recommended)

1. **Create Development Amplify App:**
   ```bash
   aws amplify create-app --name chord-scout-dev --platform WEB
   ```

2. **Connect Development Branch:**
   - Go to AWS Amplify Console
   - Create new app: "chord-scout-dev"
   - Connect to your GitHub repo
   - **Important**: Select the `development` branch instead of `main`

3. **Environment Variables for Development:**
   ```
   NODE_VERSION = 18
   OPENAI_API_KEY = your_openai_api_key_here
   APIFY_API_TOKEN = your_apify_token_here
   RAPIDAPI_KEY = 252611e8d7mshdde3262a7e2137bp12792bjsn7ce487b8a3dc
   ```

### Option 2: Branch-based Deployment (Same App)

1. **Add Development Branch to Existing App:**
   - Go to your existing Amplify app
   - Click "Connect branch"
   - Select `development` branch
   - This creates: `https://development.d1234567890.amplifyapp.com`

## Development URLs

After deployment, you'll have:
- **Production**: `https://main.d1234567890.amplifyapp.com` (mock data)
- **Development**: `https://development.d1234567890.amplifyapp.com` (real integrations)

## Development Features

The development branch includes:
- ✅ RapidAPI YouTube integration (with fallback)
- ✅ Apify YouTube downloader (new reliable method)
- ✅ yt-dlp with cookies fallback
- ✅ Comprehensive testing scripts
- ✅ MCP configuration for API testing
- ✅ All your experimental work preserved

## Testing in Development

Use these test scripts in development:
```bash
# Test RapidAPI integration
python test-rapidapi-simple.py

# Test different videos
python test-different-video.py

# Test production readiness
python test-production-ready.py
```

## Deployment Commands

```bash
# Switch to development branch
git checkout development

# Make changes and commit
git add .
git commit -m "Development: Your changes"
git push origin development

# Amplify will auto-deploy the development branch
```

## Environment Strategy

- **main branch**: Stable, mock data, client demos
- **development branch**: Active development, real integrations
- **Pull requests**: Merge development → main when ready

## Next Steps

1. Deploy development environment
2. Test Apify integration (most promising)
3. Compare with RapidAPI reliability
4. Choose best solution for production
5. Merge to main when stable

This gives you a safe development environment while keeping production stable! 🚀
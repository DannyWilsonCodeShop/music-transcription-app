# 🚀 Deploy Your Music Transcription App

## Quick Deployment via AWS Amplify Console

### Step 1: Prepare Your Code
Your app is ready to deploy! All dependencies are installed and the build works locally.

### Step 2: Push to Git Repository
```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Music Transcription App - Ready for Production"

# Add your remote repository
git remote add origin https://github.com/yourusername/music-transcription-app.git

# Push to main branch
git push -u origin main
```

### Step 3: Deploy via AWS Amplify Console

1. **Go to AWS Amplify Console:**
   - Visit: https://console.aws.amazon.com/amplify/
   - Make sure you're in the correct region (us-east-1)

2. **Create New App:**
   - Click "New app" → "Host web app"
   - Choose your Git provider (GitHub, GitLab, Bitbucket, etc.)
   - Authorize AWS Amplify to access your repository

3. **Configure Build Settings:**
   - Repository: Select your music-transcription-app repo
   - Branch: main
   - Build settings will be auto-detected from amplify.yml

4. **Environment Variables:**
   Add these in the "Environment variables" section:
   ```
   OPENAI_API_KEY = your_openai_api_key_here
   NODE_VERSION = 18
   ```

5. **Deploy:**
   - Click "Save and deploy"
   - Wait for deployment to complete (~5-10 minutes)

### Step 4: Set Up OpenAI API Key

**Important:** You need to add your OpenAI API key as an environment variable:

1. In Amplify Console → Your App → Environment variables
2. Add: `OPENAI_API_KEY` = `your_actual_openai_key`
3. Redeploy the app

### Step 5: Test Your App

Once deployed, you'll get a URL like:
`https://main.d1234567890.amplifyapp.com`

Test by:
1. Uploading an audio file
2. Trying a YouTube URL
3. Checking the transcription results

## Alternative: Manual AWS CLI Deployment

If you prefer CLI deployment:

```bash
# Create Amplify app
aws amplify create-app --name music-transcription-app --platform WEB

# Get the app ID from the response, then create a branch
aws amplify create-branch --app-id YOUR_APP_ID --branch-name main

# Start deployment
aws amplify start-job --app-id YOUR_APP_ID --branch-name main --job-type RELEASE
```

## Troubleshooting

**Build Fails?**
- Check that Node.js version is set to 18
- Verify all environment variables are set
- Check build logs in Amplify Console

**Function Errors?**
- Ensure OpenAI API key is valid and has credits
- Check CloudWatch logs for the Lambda function

**CORS Issues?**
- The backend is configured for CORS, but check browser console for errors

## Your App Features

✅ **File Upload Transcription** - Upload audio files for AI transcription  
✅ **YouTube Integration** - Transcribe directly from YouTube URLs  
✅ **Real-time Status** - Track transcription job progress  
✅ **Lyrics & Chords** - Get both lyrics and chord progressions  
✅ **Responsive UI** - Works on desktop and mobile  

## Next Steps After Deployment

1. **Custom Domain** - Add your own domain in Amplify Console
2. **Authentication** - Add user login/signup if needed
3. **Analytics** - Enable AWS Pinpoint for usage analytics
4. **Monitoring** - Set up CloudWatch alarms for errors

Your app is production-ready! 🎵
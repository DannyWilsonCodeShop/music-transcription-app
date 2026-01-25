# GitHub Actions - Quick Setup (2 Minutes)

## Step 1: Add Secrets to GitHub

Go to: https://github.com/DannyWilsonCodeShop/music-transcription-app/settings/secrets/actions

Click "New repository secret" and add these two secrets:

### Secret 1
```
Name: AWS_ACCESS_KEY_ID
Value: [See aws-credentials.txt file]
```

### Secret 2
```
Name: AWS_SECRET_ACCESS_KEY
Value: [See aws-credentials.txt file]
```

## Step 2: Test It

```bash
# Make a small change
echo "# Test" >> backend/functions/chord-detector-ml/README.md

# Push it
git add .
git commit -m "Test GitHub Actions"
git push origin main
```

## Step 3: Watch It Build

Go to: https://github.com/DannyWilsonCodeShop/music-transcription-app/actions

Watch your Docker image build in 10-15 minutes (instead of 2 hours locally)!

## That's It!

From now on, every time you push changes to the chord detector, GitHub will automatically build and deploy the Docker image.

**No more waiting locally!** 🎉

---

For detailed instructions, see: [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md)

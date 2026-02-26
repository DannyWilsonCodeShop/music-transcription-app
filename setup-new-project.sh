#!/bin/bash
# Setup New Music Transcription App Project

set -e

NEW_DIR="/Users/dannywilson/DevOps/MusicTranscriptionApp"

echo "========================================="
echo "Setting Up Music Transcription App"
echo "========================================="
echo ""

# Create new directory
echo "Creating directory: $NEW_DIR"
mkdir -p "$NEW_DIR"

# Copy simple pipeline files
echo "Copying simple pipeline files..."
cp -r simple-pipeline "$NEW_DIR/"

# Create AWS account setup guide
cat > "$NEW_DIR/AWS_ACCOUNT_SETUP.md" << 'EOF'
# AWS Account Setup Guide

## Understanding AWS Accounts

You have **two AWS accounts**:
- **Account 463470937777** (7777) - Old/test account
- **Account 090130568474** (8474) - Production account ✅ USE THIS ONE

Your production system runs in account **8474**.

## Current Problem

Your AWS CLI is configured for account **7777**, but we need **8474**.

## How to Switch

### Step 1: Check Current Account
```bash
aws sts get-caller-identity --query 'Account' --output text
```

If it shows `463470937777`, you need to switch.

### Step 2: Configure for Account 8474

**Option A: Create a profile (recommended)**
```bash
aws configure --profile production
```

Enter your credentials for account 8474 when prompted.

Then use it:
```bash
export AWS_PROFILE=production
aws sts get-caller-identity  # Should show 090130568474
```

**Option B: Update default**
```bash
aws configure
```

Enter your credentials for account 8474.

### Step 3: Verify
```bash
aws sts get-caller-identity
# Should show: "Account": "090130568474"
```

## Getting Credentials

If you don't have credentials for account 8474:

1. **AWS Console**: Log in → IAM → Users → Your User → Security Credentials → Create Access Key
2. **Ask admin**: If someone else manages the account
3. **AWS SSO**: If configured: `aws sso login`

## Quick Commands

```bash
# Check account
aws sts get-caller-identity --query 'Account' --output text

# Use production profile
export AWS_PROFILE=production

# Make permanent (add to ~/.zshrc)
echo 'export AWS_PROFILE=production' >> ~/.zshrc
```

## Next Steps

Once in account 8474:
```bash
cd simple-pipeline
./deploy.sh
```
EOF

# Create README
cat > "$NEW_DIR/README.md" << 'EOF'
# Music Transcription App

Clean, simple pipeline for music transcription.

## Quick Start

### 1. Setup AWS Account

```bash
# Check which account you're using
aws sts get-caller-identity

# Should show account: 090130568474
# If not, see AWS_ACCOUNT_SETUP.md
```

### 2. Deploy Simple Pipeline

```bash
cd simple-pipeline
./deploy.sh
```

### 3. Test

```bash
./test.sh "https://www.youtube.com/watch?v=YOUR_VIDEO"
```

## Project Structure

```
MusicTranscriptionApp/
├── AWS_ACCOUNT_SETUP.md    # How to switch AWS accounts
├── README.md                # This file
└── simple-pipeline/         # Simple YouTube → MP3 pipeline
    ├── cloudformation-simple.yaml
    ├── deploy.sh
    ├── test.sh
    └── README.md
```

## Current Status

**Phase 1: Audio Download** ⏳ In Progress
- Goal: Download YouTube audio and verify quality
- Status: Ready to deploy
- Next: Test MP3 quality

**Phase 2: Chord Detection** 📋 Planned
- Add after Phase 1 is verified

**Phase 3: Lyrics Transcription** 📋 Planned
- Add after Phase 2 is verified

**Phase 4: PDF Generation** 📋 Planned
- Add after Phase 3 is verified

## Philosophy

**One component at a time.**
- Build it
- Test it
- Verify it works
- Then add the next component

No complexity until we need it.
EOF

echo ""
echo "========================================="
echo "✅ Setup Complete!"
echo "========================================="
echo ""
echo "New project location: $NEW_DIR"
echo ""
echo "Next steps:"
echo ""
echo "1. Switch to new directory:"
echo "   cd $NEW_DIR"
echo ""
echo "2. Read AWS account setup:"
echo "   cat AWS_ACCOUNT_SETUP.md"
echo ""
echo "3. Configure AWS for account 8474:"
echo "   aws configure --profile production"
echo ""
echo "4. Set profile:"
echo "   export AWS_PROFILE=production"
echo ""
echo "5. Verify account:"
echo "   aws sts get-caller-identity"
echo "   # Should show: 090130568474"
echo ""
echo "6. Deploy:"
echo "   cd simple-pipeline"
echo "   ./deploy.sh"
echo ""

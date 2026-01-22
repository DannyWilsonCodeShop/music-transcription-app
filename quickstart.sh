#!/bin/bash

# Music Transcription App - Quick Start Script
# This script helps you get started quickly

set -e

echo "🎵 Music Transcription App - Quick Start"
echo "========================================"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

if ! command -v aws &> /dev/null; then
    echo "⚠️  AWS CLI is not installed. Install it with: brew install awscli"
    echo "   Then run: aws configure"
fi

if ! command -v amplify &> /dev/null; then
    echo "⚠️  Amplify CLI is not installed."
    echo "   Installing Amplify CLI globally..."
    npm install -g @aws-amplify/cli
fi

echo "✅ Prerequisites check complete"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
echo ""

echo "Installing frontend dependencies..."
cd frontend
npm install
cd ..

echo "Installing backend API dependencies..."
cd backend/functions/api
npm install
cd ../../..

echo "Installing backend worker dependencies..."
cd backend/functions/transcribe-worker
npm install
cd ../../..

echo "✅ Dependencies installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and add your API keys"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Configure AWS CLI: aws configure"
echo "2. Initialize Amplify: amplify init"
echo "3. Add your API keys to AWS Secrets Manager (see SETUP.md)"
echo "4. Push backend: amplify push"
echo "5. Start development: cd frontend && npm start"
echo ""
echo "📚 For detailed instructions, see SETUP.md"
echo "📖 For deployment guide, see PRODUCTION_DEPLOYMENT_GUIDE.md"
echo ""

# AWS CLI Setup Guide

## ✅ AWS CLI Installed Successfully

Version: `aws-cli/2.33.4`

## 🔑 Step 1: Get Your AWS Credentials

You need to create an AWS IAM user with programmatic access:

### Option A: Using AWS Console (Recommended)

1. **Sign in to AWS Console**: https://console.aws.amazon.com/
2. **Go to IAM**: Search for "IAM" in the top search bar
3. **Create User**:
   - Click "Users" → "Create user"
   - Username: `amplify-admin` (or your preferred name)
   - Click "Next"
4. **Set Permissions**:
   - Select "Attach policies directly"
   - Search and select: `AdministratorAccess-Amplify`
   - Also add: `IAMFullAccess` (needed for Amplify setup)
   - Click "Next"
5. **Create User**: Click "Create user"
6. **Create Access Key**:
   - Click on the user you just created
   - Go to "Security credentials" tab
   - Click "Create access key"
   - Select "Command Line Interface (CLI)"
   - Check the confirmation box
   - Click "Next" → "Create access key"
7. **Save Credentials**:
   - ⚠️ **IMPORTANT**: Copy both:
     - Access key ID (starts with `AKIA...`)
     - Secret access key (shown only once!)
   - Download the .csv file as backup
   - Click "Done"

### Option B: Using AWS CLI (If you already have admin access)

```bash
aws iam create-user --user-name amplify-admin

aws iam attach-user-policy \
  --user-name amplify-admin \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess-Amplify

aws iam create-access-key --user-name amplify-admin
```

## 🔧 Step 2: Configure AWS CLI

Run this command and enter your credentials:

```bash
aws configure
```

You'll be prompted for:

```
AWS Access Key ID [None]: AKIA................  # Paste your Access Key ID
AWS Secret Access Key [None]: ................  # Paste your Secret Access Key
Default region name [None]: us-east-1          # Or your preferred region
Default output format [None]: json             # Recommended
```

## ✅ Step 3: Verify Configuration

Test that AWS CLI is working:

```bash
# Check your identity
aws sts get-caller-identity

# Should output something like:
# {
#     "UserId": "AIDA...",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/amplify-admin"
# }
```

## 🚀 Step 4: Install Amplify CLI

Now that AWS CLI is configured, install Amplify CLI:

```bash
npm install -g @aws-amplify/cli
```

## 🔐 Step 5: Configure Amplify CLI

```bash
amplify configure
```

This will:
1. Open AWS Console in your browser
2. Guide you through creating an IAM user (if needed)
3. Save the credentials for Amplify

**Follow the prompts**:
- Region: `us-east-1` (or your preferred region)
- User name: `amplify-cli-user` (or keep default)
- Complete the IAM user creation in the browser
- Return to terminal and paste the credentials

## 📋 Step 6: Initialize Amplify in Your Project

```bash
# Make sure you're in the project root
cd ~/DevOps/ChordScout

# Initialize Amplify
amplify init
```

**Configuration prompts**:
```
? Enter a name for the project: musictranscription
? Initialize the project with the above configuration? Yes
? Select the authentication method: AWS profile
? Please choose the profile you want to use: default
```

## 🏗️ Step 7: Add Backend Resources

### Add S3 Storage for Audio Files

```bash
amplify add storage
```

Configuration:
```
? Select from one of the below mentioned services: Content (Images, audio, video, etc.)
? Provide a friendly name for your resource: audioStorage
? Provide bucket name: (accept default - press Enter)
? Who should have access: Auth and guest users
? What kind of access do you want for Authenticated users? 
  ◉ create/update
  ◉ read
  ◉ delete
? What kind of access do you want for Guest users?
  ◉ read
```

### Add DynamoDB for Job Tracking

```bash
amplify add storage
```

Configuration:
```
? Select from one of the below mentioned services: NoSQL Database
? Provide a friendly name: transcriptionJobs
? Provide table name: TranscriptionJobs
? What would you like to name this column: id
? Choose the data type: string
? Would you like to add another column? Yes
? What would you like to name this column: createdAt
? Choose the data type: number
? Would you like to add another column? Yes
? What would you like to name this column: userId
? Choose the data type: string
? Would you like to add another column? No
? Choose partition key: id
? Do you want to add a sort key? Yes
? Choose sort key: createdAt
? Do you want to add global secondary indexes? Yes
? Provide the GSI name: userIdIndex
? Choose partition key for the GSI: userId
? Choose sort key for the GSI: createdAt
? Do you want to add more global secondary indexes? No
```

### Add API Gateway

```bash
amplify add api
```

Configuration:
```
? Select from one of the below mentioned services: REST
? Provide a friendly name for your resource: transcriptionAPI
? Provide a path (e.g., /book/{isbn}): /transcribe
? Choose a Lambda source: Create a new Lambda function
? Provide an AWS Lambda function name: transcribeAPI
? Choose the runtime that you want to use: NodeJS
? Choose the function template: Hello World
? Do you want to configure advanced settings? Yes
? Do you want to access other resources in this project: Yes
? Select the categories: storage
? Select the operations you want to permit: create, read, update, delete
? Do you want to invoke this function on a recurring schedule? No
? Do you want to configure Lambda layers? No
? Do you want to edit the local lambda function now? No
? Restrict API access? No
? Do you want to add another path? No
```

### Add Worker Lambda Function

```bash
amplify add function
```

Configuration:
```
? Select which capability you want to add: Lambda function
? Provide an AWS Lambda function name: transcribeWorker
? Choose the runtime: NodeJS
? Choose the function template: Hello World
? Do you want to configure advanced settings? Yes
? Do you want to access other resources: Yes
? Select the categories: storage
? Select the operations: create, read, update, delete
? Do you want to invoke this function on a recurring schedule? No
? Do you want to enable Lambda layers? No
? Do you want to configure environment variables? Yes
? Enter the environment variable name: OPENAI_SECRET_ARN
? Enter the environment variable value: (leave empty for now)
? Select what you want to do: I'm done
? Do you want to configure secret values? No
? Do you want to edit the local lambda function now? No
```

## 📦 Step 8: Copy Function Code

```bash
# Copy API function
cp backend/functions/api/index.js amplify/backend/function/transcribeAPI/src/
cp backend/functions/api/package.json amplify/backend/function/transcribeAPI/src/

# Install dependencies
cd amplify/backend/function/transcribeAPI/src
npm install
cd ../../../../..

# Copy worker function
cp backend/functions/transcribe-worker/index.js amplify/backend/function/transcribeWorker/src/
cp backend/functions/transcribe-worker/package.json amplify/backend/function/transcribeWorker/src/

# Install dependencies
cd amplify/backend/function/transcribeWorker/src
npm install
cd ../../../../..
```

## 🚀 Step 9: Deploy Backend to AWS

```bash
amplify push
```

This will:
- Create S3 bucket
- Create DynamoDB table
- Deploy Lambda functions
- Create API Gateway
- Set up IAM roles
- Configure permissions

**This may take 5-10 minutes.**

## 🔑 Step 10: Store API Keys in AWS Secrets Manager

```bash
# Store OpenAI API key
aws secretsmanager create-secret \
  --name music-transcription/openai-key \
  --secret-string '{"OPENAI_API_KEY":"sk-your-actual-openai-key-here"}' \
  --region us-east-1

# Store YouTube API key
aws secretsmanager create-secret \
  --name music-transcription/youtube-key \
  --secret-string '{"YOUTUBE_API_KEY":"your-youtube-api-key-here"}' \
  --region us-east-1

# Get the OpenAI secret ARN
aws secretsmanager describe-secret \
  --secret-id music-transcription/openai-key \
  --region us-east-1 \
  --query ARN \
  --output text
```

Copy the ARN output and update your Lambda function:

```bash
# Update worker function with secret ARN
aws lambda update-function-configuration \
  --function-name transcribeWorker-main \
  --environment "Variables={OPENAI_SECRET_ARN=arn:aws:secretsmanager:us-east-1:ACCOUNT:secret:music-transcription/openai-key-XXXXX}"
```

## 🌐 Step 11: Update Amplify Hosting

Update `amplify.yml` to include backend:

```yaml
version: 1
backend:
  phases:
    build:
      commands:
        - '# Execute Amplify CLI with the helper script'
        - amplifyPush --simple
frontend:
  phases:
    preBuild:
      commands:
        - cd frontend
        - npm ci
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: frontend/build
    files:
      - '**/*'
  cache:
    paths:
      - frontend/node_modules/**/*
```

Commit and push:

```bash
git add amplify.yml amplify/
git commit -m "Add Amplify backend configuration"
git push origin main
```

## ✅ Verification Checklist

After deployment, verify:

```bash
# Check S3 bucket
aws s3 ls | grep amplify

# Check DynamoDB table
aws dynamodb describe-table --table-name TranscriptionJobs-main

# Check Lambda functions
aws lambda list-functions | grep transcribe

# Check API Gateway
aws apigateway get-rest-apis

# Check Secrets
aws secretsmanager list-secrets | grep music-transcription
```

## 🎉 Success!

Your app is now fully deployed with:
- ✅ Frontend on Amplify
- ✅ Backend Lambda functions
- ✅ S3 storage
- ✅ DynamoDB database
- ✅ API Gateway
- ✅ Secrets Manager

Visit your Amplify URL to test the app!

## 🆘 Troubleshooting

### "Access Denied" errors
```bash
# Check your credentials
aws sts get-caller-identity

# Verify IAM permissions
aws iam get-user
```

### "Region not found"
```bash
# Set default region
aws configure set region us-east-1
```

### Lambda function errors
```bash
# View logs
aws logs tail /aws/lambda/transcribeWorker-main --follow
```

### Need to start over?
```bash
# Delete all Amplify resources
amplify delete

# Re-initialize
amplify init
```

## 📚 Next Steps

1. Test file upload functionality
2. Test YouTube link processing
3. Monitor CloudWatch logs
4. Set up CloudWatch alarms
5. Configure custom domain
6. Add user authentication (Cognito)

---

**Current Status**: AWS CLI configured ✅
**Next Command**: `amplify configure`

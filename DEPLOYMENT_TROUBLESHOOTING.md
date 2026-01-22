# Deployment Troubleshooting Guide

## Issue: AWS Amplify Build Failed - "AWS access credentials can not be found"

This error occurs when deploying without backend resources initialized. Here's how to fix it:

## 🔧 Quick Fix - Deploy Frontend Only (Recommended for Now)

The `amplify.yml` has been updated to deploy only the frontend. This allows you to:
1. Get the frontend deployed immediately
2. Set up backend resources separately
3. Connect them later

### Step 1: Push Updated Configuration

```bash
git add amplify.yml
git commit -m "Fix: Update amplify.yml for frontend-only deployment"
git push origin main
```

Amplify will automatically retry the deployment.

### Step 2: Verify Deployment

Go to AWS Amplify Console and check the build status. It should now succeed.

## 🏗️ Full Setup with Backend (Complete Solution)

To deploy with full backend functionality:

### Step 1: Install Amplify CLI Locally

```bash
npm install -g @aws-amplify/cli
amplify configure
```

Follow prompts to create IAM user with appropriate permissions.

### Step 2: Initialize Amplify in Your Project

```bash
# From project root
amplify init

# Configuration:
# ? Enter a name for the project: musictranscriptionapp
# ? Initialize the project with the above configuration? Yes
# ? Select the authentication method: AWS profile
# ? Please choose the profile you want to use: default
```

### Step 3: Add Backend Resources

```bash
# Add S3 storage for audio files
amplify add storage
# ? Select from one of the below mentioned services: Content
# ? Provide a friendly name: audioStorage
# ? Provide bucket name: (accept default)
# ? Who should have access: Auth and guest users
# ? What kind of access for Authenticated users: create, read, delete
# ? What kind of access for Guest users: read

# Add DynamoDB for job tracking
amplify add storage
# ? Select from one of the below mentioned services: NoSQL Database
# ? Provide a friendly name: transcriptionJobs
# ? Provide table name: TranscriptionJobs
# ? What would you like to name partition key: id
# ? What is the type: String
# ? Do you want to add a sort key: Yes
# ? What would you like to name sort key: createdAt
# ? What is the type: Number
# ? Do you want to add global secondary indexes: Yes
#   - GSI name: userIdIndex
#   - Partition key: userId (String)
#   - Sort key: createdAt (Number)

# Add API Gateway
amplify add api
# ? Select from one of the below mentioned services: REST
# ? Provide a friendly name: transcriptionAPI
# ? Provide a path: /transcribe
# ? Choose a Lambda source: Create a new Lambda function
# ? Provide an AWS Lambda function name: transcribeAPI
# ? Choose the runtime: NodeJS
# ? Choose the function template: Hello World
# ? Do you want to configure advanced settings: No
# ? Do you want to edit the local lambda function now: No
# ? Restrict API access: No
# ? Do you want to add another path: No

# Add worker Lambda function
amplify add function
# ? Select which capability you want to add: Lambda function
# ? Provide an AWS Lambda function name: transcribeWorker
# ? Choose the runtime: NodeJS
# ? Choose the function template: Hello World
# ? Do you want to configure advanced settings: Yes
# ? Do you want to access other resources: Yes
#   - Select: storage (both S3 and DynamoDB)
# ? Do you want to invoke this function on a recurring schedule: No
# ? Do you want to enable Lambda layers: No
# ? Do you want to configure environment variables: Yes
#   - Add: OPENAI_SECRET_ARN (value: will add after creating secret)
# ? Do you want to configure secret values: No
# ? Do you want to edit the local lambda function now: No
```

### Step 4: Copy Function Code

```bash
# Copy API function code
cp backend/functions/api/index.js amplify/backend/function/transcribeAPI/src/
cp backend/functions/api/package.json amplify/backend/function/transcribeAPI/src/

# Copy worker function code
cp backend/functions/transcribe-worker/index.js amplify/backend/function/transcribeWorker/src/
cp backend/functions/transcribe-worker/package.json amplify/backend/function/transcribeWorker/src/
```

### Step 5: Push Backend to AWS

```bash
amplify push

# This will:
# - Create S3 bucket
# - Create DynamoDB table
# - Deploy Lambda functions
# - Create API Gateway
# - Set up IAM roles
```

### Step 6: Store API Keys

```bash
# Get your AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Store OpenAI API key
aws secretsmanager create-secret \
  --name music-transcription/openai-key \
  --secret-string '{"OPENAI_API_KEY":"sk-your-actual-key"}' \
  --region us-east-1

# Get the secret ARN
OPENAI_SECRET_ARN=$(aws secretsmanager describe-secret \
  --secret-id music-transcription/openai-key \
  --region us-east-1 \
  --query ARN \
  --output text)

echo "OpenAI Secret ARN: $OPENAI_SECRET_ARN"

# Update Lambda environment variable
aws lambda update-function-configuration \
  --function-name transcribeWorker-main \
  --environment "Variables={OPENAI_SECRET_ARN=$OPENAI_SECRET_ARN,DYNAMODB_TABLE=TranscriptionJobs-main,S3_BUCKET=your-bucket-name}"
```

### Step 7: Update amplify.yml for Full Deployment

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

### Step 8: Commit and Push

```bash
git add .
git commit -m "Add Amplify backend configuration"
git push origin main
```

## 🎯 Alternative: Manual AWS Setup (Without Amplify CLI)

If you prefer to set up AWS resources manually:

### 1. Create S3 Bucket

```bash
aws s3 mb s3://music-transcription-audio-prod --region us-east-1

# Enable CORS
aws s3api put-bucket-cors \
  --bucket music-transcription-audio-prod \
  --cors-configuration file://s3-cors.json
```

Create `s3-cors.json`:
```json
{
  "CORSRules": [
    {
      "AllowedOrigins": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
      "AllowedHeaders": ["*"],
      "MaxAgeSeconds": 3000
    }
  ]
}
```

### 2. Create DynamoDB Table

```bash
aws dynamodb create-table \
  --table-name TranscriptionJobs \
  --attribute-definitions \
    AttributeName=id,AttributeType=S \
    AttributeName=createdAt,AttributeType=N \
    AttributeName=userId,AttributeType=S \
  --key-schema \
    AttributeName=id,KeyType=HASH \
    AttributeName=createdAt,KeyType=RANGE \
  --global-secondary-indexes \
    "[{
      \"IndexName\": \"userIdIndex\",
      \"KeySchema\": [
        {\"AttributeName\":\"userId\",\"KeyType\":\"HASH\"},
        {\"AttributeName\":\"createdAt\",\"KeyType\":\"RANGE\"}
      ],
      \"Projection\": {\"ProjectionType\":\"ALL\"},
      \"ProvisionedThroughput\": {
        \"ReadCapacityUnits\":5,
        \"WriteCapacityUnits\":5
      }
    }]" \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

### 3. Create Lambda Functions

See PRODUCTION_DEPLOYMENT_GUIDE.md for detailed Lambda setup instructions.

## 🔍 Common Issues and Solutions

### Issue: "Module not found" in Lambda

**Solution**: Install dependencies in Lambda function directory
```bash
cd amplify/backend/function/transcribeAPI/src
npm install
cd ../../../../../
amplify push
```

### Issue: "Access Denied" errors

**Solution**: Update IAM role permissions
1. Go to AWS IAM Console
2. Find the Lambda execution role
3. Add policies for S3, DynamoDB, SQS, Secrets Manager

### Issue: Frontend can't connect to API

**Solution**: Update CORS settings
```bash
# In API Gateway console
# Select your API → Resources → Actions → Enable CORS
# Deploy API to stage
```

### Issue: Lambda timeout

**Solution**: Increase timeout and memory
```bash
aws lambda update-function-configuration \
  --function-name transcribeWorker-main \
  --timeout 900 \
  --memory-size 3008
```

## 📊 Verify Deployment

### Check Frontend

```bash
# Get Amplify app URL
aws amplify list-apps --query "apps[?name=='musictranscriptionapp'].defaultDomain" --output text
```

Visit the URL to test the frontend.

### Check Backend Resources

```bash
# List S3 buckets
aws s3 ls | grep music-transcription

# Check DynamoDB table
aws dynamodb describe-table --table-name TranscriptionJobs

# List Lambda functions
aws lambda list-functions --query "Functions[?contains(FunctionName, 'transcribe')]"

# Check API Gateway
aws apigateway get-rest-apis --query "items[?name=='transcriptionAPI']"
```

## 🆘 Still Having Issues?

1. **Check CloudWatch Logs**:
   ```bash
   aws logs tail /aws/amplify/musictranscriptionapp --follow
   ```

2. **Review Amplify Console**:
   - Go to AWS Amplify Console
   - Select your app
   - Check build logs

3. **Verify AWS Credentials**:
   ```bash
   aws sts get-caller-identity
   ```

4. **Check IAM Permissions**:
   - Ensure your IAM user has AdministratorAccess-Amplify policy

## 📚 Additional Resources

- [AWS Amplify Documentation](https://docs.amplify.aws/)
- [Amplify CLI Installation](https://docs.amplify.aws/cli/start/install/)
- [Troubleshooting Guide](https://docs.amplify.aws/cli/project/troubleshooting/)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)

## ✅ Success Checklist

After successful deployment:
- [ ] Frontend accessible at Amplify URL
- [ ] Can upload files
- [ ] Can submit YouTube links
- [ ] Jobs are created in DynamoDB
- [ ] Lambda functions execute without errors
- [ ] Results display correctly

---

**Current Status**: Frontend-only deployment configured
**Next Step**: Follow "Full Setup with Backend" section above to add backend functionality

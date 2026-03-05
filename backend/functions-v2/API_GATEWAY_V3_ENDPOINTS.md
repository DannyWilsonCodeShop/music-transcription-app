# ChordScout v3.0 API Gateway Endpoints

This document describes the new API Gateway endpoints added in v3.0 for user confirmation workflows.

## New Endpoints

### 1. POST /jobs/{jobId}/confirm-mode

**Purpose**: User confirms transcription mode selection (which stems to transcribe)

**Lambda Function**: `confirm-transcription-mode`
- **Handler**: `index.handler`
- **Runtime**: Node.js 18.x
- **Environment Variables**:
  - `DYNAMODB_TABLE`: ChordScout-Jobs-V2-dev

**Path Parameters**:
- `jobId` (required): The job identifier (UUID)

**Request Body**:
```json
{
  "transcriptionMode": "bass-only" | "bass+piano" | "bass+guitar" | "all"
}
```

**Valid Transcription Modes**:
- `bass-only`: Transcribe only the bass stem (fastest, v2.0 compatible)
- `bass+piano`: Transcribe bass and piano stems
- `bass+guitar`: Transcribe bass and guitar stems
- `all`: Transcribe bass, piano, and guitar stems (slowest, most accurate)

**Success Response** (200 OK):
```json
{
  "success": true,
  "jobId": "550e8400-e29b-41d4-a716-446655440000",
  "transcriptionMode": "bass+piano",
  "message": "Transcription mode confirmed"
}
```

**Error Responses**:

400 Bad Request - Missing jobId:
```json
{
  "success": false,
  "error": "Missing jobId in path parameters"
}
```

400 Bad Request - Invalid JSON:
```json
{
  "success": false,
  "error": "Invalid JSON in request body"
}
```

400 Bad Request - Missing mode:
```json
{
  "success": false,
  "error": "Missing transcriptionMode in request body"
}
```

400 Bad Request - Invalid mode:
```json
{
  "success": false,
  "error": "Invalid transcriptionMode. Must be one of: bass-only, bass+piano, bass+guitar, all"
}
```

404 Not Found - Job not found:
```json
{
  "success": false,
  "error": "Job not found: {jobId}"
}
```

500 Internal Server Error:
```json
{
  "success": false,
  "error": "Internal server error",
  "message": "Error details"
}
```

**CORS Configuration**:
- `Access-Control-Allow-Origin`: `*`
- `Access-Control-Allow-Headers`: `Content-Type`
- `Access-Control-Allow-Methods`: `POST, OPTIONS`

**Usage Example**:
```bash
curl -X POST \
  https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com/jobs/550e8400-e29b-41d4-a716-446655440000/confirm-mode \
  -H 'Content-Type: application/json' \
  -d '{
    "transcriptionMode": "bass+piano"
  }'
```

**When to Call**:
- Frontend should call this endpoint when job status is `PENDING_MODE_SELECTION`
- User must select one of the four transcription modes
- If not called within 5 minutes, ECS task will default to `bass-only` mode

---

### 2. POST /jobs/{jobId}/confirm-key

**Purpose**: User confirms or corrects the detected musical key

**Lambda Function**: `confirm-key`
- **Handler**: `index.handler`
- **Runtime**: Node.js 18.x
- **Environment Variables**:
  - `DYNAMODB_TABLE`: ChordScout-Jobs-V2-dev

**Path Parameters**:
- `jobId` (required): The job identifier (UUID)

**Request Body**:
```json
{
  "confirmedKey": "C major" | "A minor" | ...
}
```

**Valid Keys** (24 total):
- **Major keys**: C major, C# major, Db major, D major, D# major, Eb major, E major, F major, F# major, Gb major, G major, G# major, Ab major, A major, A# major, Bb major, B major, Cb major
- **Minor keys**: C minor, C# minor, Db minor, D minor, D# minor, Eb minor, E minor, F minor, F# minor, Gb minor, G minor, G# minor, Ab minor, A minor, A# minor, Bb minor, B minor, Cb minor

**Success Response** (200 OK):
```json
{
  "success": true,
  "jobId": "550e8400-e29b-41d4-a716-446655440000",
  "detectedKey": "C major",
  "confirmedKey": "C major",
  "message": "Key confirmed"
}
```

**Error Responses**:

400 Bad Request - Missing jobId:
```json
{
  "success": false,
  "error": "Missing jobId in path parameters"
}
```

400 Bad Request - Invalid JSON:
```json
{
  "success": false,
  "error": "Invalid JSON in request body"
}
```

400 Bad Request - Missing key:
```json
{
  "success": false,
  "error": "Missing confirmedKey in request body"
}
```

400 Bad Request - Invalid key format:
```json
{
  "success": false,
  "error": "Invalid key format. Must be one of the 24 standard keys (e.g., \"C major\", \"A minor\")"
}
```

404 Not Found - Job not found:
```json
{
  "success": false,
  "error": "Job not found: {jobId}"
}
```

500 Internal Server Error:
```json
{
  "success": false,
  "error": "Internal server error",
  "message": "Error details"
}
```

**CORS Configuration**:
- `Access-Control-Allow-Origin`: `*`
- `Access-Control-Allow-Headers`: `Content-Type`
- `Access-Control-Allow-Methods`: `POST, OPTIONS`

**Usage Example**:
```bash
curl -X POST \
  https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com/jobs/550e8400-e29b-41d4-a716-446655440000/confirm-key \
  -H 'Content-Type: application/json' \
  -d '{
    "confirmedKey": "A minor"
  }'
```

**When to Call**:
- Frontend should call this endpoint when job status is `PENDING_KEY_CONFIRMATION`
- User can confirm the detected key or select a different key from the dropdown
- If not called within 5 minutes, ECS task will use the detected key

---

## API Gateway Configuration Steps

### Step 1: Create Lambda Functions

1. Deploy `confirm-transcription-mode` Lambda:
```bash
cd backend/functions-v2/confirm-transcription-mode
npm install
zip -r function.zip index.js node_modules/
aws lambda create-function \
  --function-name confirm-transcription-mode \
  --runtime nodejs18.x \
  --role arn:aws:iam::090130568474:role/lambda-execution-role \
  --handler index.handler \
  --zip-file fileb://function.zip \
  --environment Variables={DYNAMODB_TABLE=ChordScout-Jobs-V2-dev} \
  --region us-east-1
```

2. Deploy `confirm-key` Lambda:
```bash
cd backend/functions-v2/confirm-key
npm install
zip -r function.zip index.js node_modules/
aws lambda create-function \
  --function-name confirm-key \
  --runtime nodejs18.x \
  --role arn:aws:iam::090130568474:role/lambda-execution-role \
  --handler index.handler \
  --zip-file fileb://function.zip \
  --environment Variables={DYNAMODB_TABLE=ChordScout-Jobs-V2-dev} \
  --region us-east-1
```

### Step 2: Add API Gateway Routes

Using the existing API Gateway (`hfv1glzbxi`):

1. Create `/jobs/{jobId}/confirm-mode` resource and POST method:
```bash
# Get the API Gateway ID
API_ID=hfv1glzbxi

# Get the /jobs resource ID
JOBS_RESOURCE_ID=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --query 'items[?path==`/jobs`].id' \
  --output text)

# Create {jobId} resource if it doesn't exist
JOBID_RESOURCE_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $JOBS_RESOURCE_ID \
  --path-part '{jobId}' \
  --query 'id' \
  --output text)

# Create confirm-mode resource
CONFIRM_MODE_RESOURCE_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $JOBID_RESOURCE_ID \
  --path-part 'confirm-mode' \
  --query 'id' \
  --output text)

# Add POST method
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $CONFIRM_MODE_RESOURCE_ID \
  --http-method POST \
  --authorization-type NONE

# Link to Lambda
LAMBDA_ARN=$(aws lambda get-function \
  --function-name confirm-transcription-mode \
  --query 'Configuration.FunctionArn' \
  --output text)

aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $CONFIRM_MODE_RESOURCE_ID \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations

# Add Lambda permission
aws lambda add-permission \
  --function-name confirm-transcription-mode \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-1:090130568474:$API_ID/*/POST/jobs/*/confirm-mode"
```

2. Create `/jobs/{jobId}/confirm-key` resource and POST method:
```bash
# Create confirm-key resource
CONFIRM_KEY_RESOURCE_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $JOBID_RESOURCE_ID \
  --path-part 'confirm-key' \
  --query 'id' \
  --output text)

# Add POST method
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $CONFIRM_KEY_RESOURCE_ID \
  --http-method POST \
  --authorization-type NONE

# Link to Lambda
LAMBDA_ARN=$(aws lambda get-function \
  --function-name confirm-key \
  --query 'Configuration.FunctionArn' \
  --output text)

aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $CONFIRM_KEY_RESOURCE_ID \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations

# Add Lambda permission
aws lambda add-permission \
  --function-name confirm-key \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-1:090130568474:$API_ID/*/POST/jobs/*/confirm-key"
```

### Step 3: Enable CORS

For both endpoints, enable CORS:

```bash
# For confirm-mode
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $CONFIRM_MODE_RESOURCE_ID \
  --http-method OPTIONS \
  --authorization-type NONE

aws apigateway put-method-response \
  --rest-api-id $API_ID \
  --resource-id $CONFIRM_MODE_RESOURCE_ID \
  --http-method OPTIONS \
  --status-code 200 \
  --response-parameters '{"method.response.header.Access-Control-Allow-Headers":true,"method.response.header.Access-Control-Allow-Methods":true,"method.response.header.Access-Control-Allow-Origin":true}'

aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $CONFIRM_MODE_RESOURCE_ID \
  --http-method OPTIONS \
  --type MOCK \
  --request-templates '{"application/json":"{\"statusCode\": 200}"}'

aws apigateway put-integration-response \
  --rest-api-id $API_ID \
  --resource-id $CONFIRM_MODE_RESOURCE_ID \
  --http-method OPTIONS \
  --status-code 200 \
  --response-parameters '{"method.response.header.Access-Control-Allow-Headers":"'\''Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'\''","method.response.header.Access-Control-Allow-Methods":"'\''POST,OPTIONS'\''","method.response.header.Access-Control-Allow-Origin":"'\''*'\''"}' \
  --response-templates '{"application/json":""}'

# Repeat for confirm-key endpoint
```

### Step 4: Deploy API

```bash
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod \
  --description "v3.0 - Added confirm-mode and confirm-key endpoints"
```

### Step 5: Test Endpoints

```bash
# Test confirm-mode
curl -X POST \
  https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com/jobs/test-job-id/confirm-mode \
  -H 'Content-Type: application/json' \
  -d '{"transcriptionMode": "bass-only"}'

# Test confirm-key
curl -X POST \
  https://hfv1glzbxi.execute-api.us-east-1.amazonaws.com/jobs/test-job-id/confirm-key \
  -H 'Content-Type: application/json' \
  -d '{"confirmedKey": "C major"}'
```

---

## Integration with Frontend

The frontend should:

1. Poll job status using `GET /jobs/{jobId}`
2. When status is `PENDING_MODE_SELECTION`, show mode selector UI
3. Call `POST /jobs/{jobId}/confirm-mode` with user's selection
4. Continue polling until status is `PENDING_KEY_CONFIRMATION`
5. Show key confirmation UI with detected key
6. Call `POST /jobs/{jobId}/confirm-key` with user's confirmation
7. Continue polling until status is `COMPLETED`

See `src/services/transcriptionService.ts` for TypeScript implementation.

---

## Monitoring

Monitor these endpoints using CloudWatch:

- Lambda invocation count
- Lambda error rate
- Lambda duration
- API Gateway 4xx/5xx errors
- DynamoDB throttling

Set up alarms for:
- Error rate > 5%
- Duration > 3 seconds
- DynamoDB throttling events

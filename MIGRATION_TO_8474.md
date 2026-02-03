# Migration Plan: Move ChordScout to Account 090130568474

## Goal
Move all ChordScout infrastructure from account 463470937777 to account 090130568474 for billing separation.

## Current State (Account 463470937777)

### Resources to Migrate:
1. **API Gateway**: `https://ppq03hif98.execute-api.us-east-1.amazonaws.com/dev`
2. **Lambda Functions**:
   - `chordscout-v2-youtube-downloader-dev`
   - `chordscout-v2-lyrics-transcriber-dev`
   - `chordscout-v2-chord-detector-trigger-dev`
   - `chordscout-v2-pdf-generator-dev`
   - `chordscout-v2-create-job-dev`
   - `chordscout-v2-get-job-status-dev`
3. **DynamoDB Table**: `ChordScout-Jobs-V2-dev`
4. **S3 Buckets**:
   - `chordscout-audio-dev-463470937777`
   - `chordscout-pdfs-dev-463470937777`
5. **ECS Cluster**: `ChordScout-dev`
6. **ECS Task Definition**: `chordscout-chord-detector-dev`
7. **Step Functions**: `ChordScout-V2-Transcription-dev`
8. **IAM Roles**: Various Lambda and ECS execution roles

## Target State (Account 090130568474)

### Already Exists:
- ✅ ECR Repository: `chordscout-chord-detector` (with latest image)
- ✅ ECS Cluster: `ChordScout-dev` (empty, ready to use)

### Need to Create:
- [ ] S3 Buckets
- [ ] DynamoDB Table
- [ ] Lambda Functions
- [ ] API Gateway
- [ ] Step Functions
- [ ] IAM Roles
- [ ] ECS Task Definition

## Migration Approach

### Option 1: Infrastructure as Code (Recommended)
Use the existing CloudFormation templates to deploy to new account:
- `backend/infrastructure-v2/cloudformation-ecs-architecture.yaml`
- Update account-specific values
- Deploy to 090130568474

### Option 2: Manual Recreation
Recreate each resource manually in AWS Console

### Option 3: AWS Application Migration Service
Use AWS tools to migrate resources

## Recommended: Option 1 - CloudFormation

### Steps:

1. **Configure AWS CLI for Account 090130568474**
```bash
aws configure --profile prod
# Enter credentials for 090130568474
```

2. **Update CloudFormation Template**
- Change account IDs
- Update resource names if needed
- Verify all parameters

3. **Deploy Infrastructure**
```bash
aws cloudformation create-stack \
  --stack-name chordscout-v2-dev \
  --template-body file://backend/infrastructure-v2/cloudformation-ecs-architecture.yaml \
  --capabilities CAPABILITY_IAM \
  --region us-east-1 \
  --profile prod
```

4. **Deploy Lambda Functions**
```bash
# For each Lambda function:
aws lambda create-function \
  --function-name <name> \
  --runtime nodejs18.x \
  --role <iam-role-arn> \
  --handler index.handler \
  --zip-file fileb://function.zip \
  --region us-east-1 \
  --profile prod
```

5. **Update Environment Variables**
- Update `.env` file with new account resources
- Update GitHub secrets with new AWS credentials

6. **Test in New Account**
- Create test job
- Verify all steps complete
- Check PDF generation

7. **Update DNS/Frontend**
- Point frontend to new API Gateway URL
- Update any hardcoded URLs

8. **Decommission Old Account Resources**
- Export any important data
- Delete resources in 463470937777
- Verify no charges

## Estimated Time
- **Automated (CloudFormation)**: 1-2 hours
- **Manual**: 4-6 hours

## Risks & Mitigation

### Risk 1: Data Loss
**Mitigation**: Export DynamoDB data before migration

### Risk 2: Downtime
**Mitigation**: Deploy to new account first, test, then switch

### Risk 3: Missing Permissions
**Mitigation**: Use CloudFormation to ensure all IAM roles created

### Risk 4: Cost During Migration
**Mitigation**: Run both accounts briefly, then decommission old

## Cost Comparison

### Current (463470937777):
- Mixed with other projects
- Hard to track ChordScout costs

### After Migration (090130568474):
- ✅ Dedicated account for ChordScout
- ✅ Clear billing separation
- ✅ Easy cost tracking
- ✅ Better budget control

## Next Steps

1. **Immediate**: Configure AWS CLI for account 090130568474
2. **Review**: CloudFormation template for any account-specific values
3. **Deploy**: Infrastructure to new account
4. **Test**: Full workflow in new account
5. **Switch**: Update frontend/DNS
6. **Cleanup**: Remove old account resources

## Questions to Answer

1. Do you have AWS credentials (Access Key + Secret) for account 090130568474?
2. Should we keep the same resource names or rename for clarity?
3. Do you want to migrate existing job data from DynamoDB?
4. What's the acceptable downtime window?

---

**Status**: Ready to begin migration
**Next Action**: Configure AWS CLI for account 090130568474

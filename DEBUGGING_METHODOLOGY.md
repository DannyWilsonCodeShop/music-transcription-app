# Debugging Distributed Systems - A Developer's Guide

## The Situation
Your upload "isn't finishing" - a vague symptom that could have dozens of causes in a distributed system with multiple services (API Gateway → Lambda → S3 → ECS → Lambda → DynamoDB).

## The Systematic Approach

### Step 1: Define "Not Finishing"
**Question yourself:** What does "not finishing" mean exactly?
- Is the upload failing?
- Is processing stuck?
- Is the frontend not updating?
- Is data missing?

**Action:** Get specific symptoms
```bash
# Check the most recent job
aws dynamodb scan --table-name [TABLE] --filter-expression "createdAt > :date"
```

**What I found:** Job stuck at status "CHORDS_DETECTED" (80%)

---

### Step 2: Follow the Data Flow
In a distributed system, trace the request path:

```
Frontend → API Gateway → Upload Lambda → S3 → Process Lambda → ECS Task → PDF Lambda → DynamoDB
```

**Mental Model:** Think of it like a relay race. Where did the baton get dropped?

**Action:** Check each handoff point
```bash
# 1. Did upload Lambda run?
aws logs tail /aws/lambda/music-transcription-upload-test --since 30m

# 2. Did file reach S3?
aws s3 ls s3://bucket/uploads/

# 3. Did process Lambda trigger?
aws logs tail /aws/lambda/music-transcription-process-audio-test --since 30m

# 4. Did ECS task run?
aws ecs describe-tasks --cluster [CLUSTER] --tasks [TASK_ARN]

# 5. Did PDF Lambda run?
aws logs tail /aws/lambda/pdf-generator --since 30m
```

**What I found:** ECS task completed (exit code 0), PDF Lambda was invoked (status 202)

---

### Step 3: Read the Logs (The Most Important Skill)
**Developer Mindset:** Logs are your time machine. They show you exactly what happened.

**Action:** Get the actual logs
```bash
aws logs get-log-events --log-group-name /ecs/[TASK] --log-stream-name [STREAM]
```

**What to look for:**
1. ✅ **Success messages** - "completed successfully"
2. ❌ **Error messages** - "ERROR", "Exception", "Failed"
3. ⚠️ **Warnings** - "WARNING", "⚠️"
4. 🔍 **State transitions** - "Step 1", "Step 2", status updates
5. 📊 **Data values** - What was actually processed?

**What I found in the logs:**
```
[ERROR] Error extracting lyrics: update_job_status() got an unexpected keyword argument 'status_message'
[INFO] ✓ PDF generation Lambda invoked
[INFO]   Status code: 202
[INFO] CHORD DETECTION TASK COMPLETED SUCCESSFULLY
```

**Key insight:** The ECS task said it succeeded, but there was an error during lyrics extraction. The PDF Lambda was invoked (202 = accepted), but we need to check if it actually ran.

---

### Step 4: Check the Next Service in the Chain
**Developer Thinking:** The ECS task invoked the PDF Lambda. Did the PDF Lambda actually run?

**Action:** Check PDF Lambda logs
```bash
aws logs tail /aws/lambda/chordscout-v2-pdf-generator-dev --since 30m
```

**What to expect:**
- If logs exist: Lambda ran, check for errors
- If no logs: Lambda never executed (invocation failed, permissions issue, or wrong function name)

---

### Step 5: Identify the Root Cause
From the evidence:

1. **ECS logs show:** `update_job_status() got an unexpected keyword argument 'status_message'`
   - This is a **function signature mismatch**
   - The code is calling `update_job_status(job_id, status, progress, status_message="...")`
   - But the function only accepts `update_job_status(job_id, status, progress, error=None)`

2. **ECS task completed:** Exit code 0 (success)
   - This means the error was caught and handled
   - The task continued despite the error

3. **PDF Lambda invoked:** Status 202
   - The ECS task successfully called the PDF Lambda
   - But we need to verify it actually ran

**Root Cause Hypothesis:**
- The PDF Lambda might have failed
- OR the PDF Lambda succeeded but set status to "COMPLETE" instead of "COMPLETED" (we fixed this earlier)
- OR there's an error in the PDF Lambda we haven't seen yet

---

### Step 6: Verify Your Hypothesis
**Developer Principle:** Never assume. Always verify.

**Actions:**
1. Check if PDF Lambda has logs for this job
2. Check if PDF was actually generated in S3
3. Check the final job status in DynamoDB

```bash
# Check PDF Lambda logs for specific job
aws logs filter-log-events \
  --log-group-name /aws/lambda/chordscout-v2-pdf-generator-dev \
  --filter-pattern "bbf1c6c4-71aa-4eeb-b331-28af6053205a"

# Check if PDF exists
aws s3 ls s3://chordscout-pdfs-dev-090130568474/pdfs/bbf1c6c4-71aa-4eeb-b331-28af6053205a.pdf

# Check final job status
aws dynamodb get-item --table-name ChordScout-Jobs-V2-dev \
  --key '{"jobId":{"S":"bbf1c6c4-71aa-4eeb-b331-28af6053205a"}}'
```

---

### Step 7: Fix the Issue
Once you've identified the root cause, fix it:

**For function signature mismatch:**
```python
# Find the function definition
def update_job_status(job_id, status, progress, error=None):
    # ...

# Option 1: Update the function to accept status_message
def update_job_status(job_id, status, progress, error=None, status_message=None):
    # ...

# Option 2: Update all callers to not use status_message
update_job_status(job_id, 'PROCESSING', 72)  # Remove status_message parameter
```

**For deployment:**
1. Fix the code
2. Rebuild Docker image (if ECS)
3. Deploy Lambda (if Lambda)
4. Test with a new upload

---

## Key Developer Principles

### 1. **Work Backwards from the Symptom**
- Symptom: "Not finishing"
- Question: What does "finished" look like? (Status = COMPLETED, PDF exists, frontend shows results)
- Find: Where in the chain did it stop?

### 2. **Trust the Logs, Not Your Assumptions**
- Don't assume "it should work"
- Read what actually happened
- Logs don't lie (but they might be incomplete)

### 3. **Understand Async Operations**
When Lambda A invokes Lambda B asynchronously:
- Lambda A gets status 202 (accepted) immediately
- Lambda B runs separately
- Lambda A doesn't know if Lambda B succeeded
- You must check Lambda B's logs independently

### 4. **Check Every Handoff**
In distributed systems, failures happen at boundaries:
- API Gateway → Lambda (permissions, timeout)
- Lambda → S3 (permissions, bucket exists)
- S3 → Lambda (event notification configured)
- Lambda → ECS (permissions, network, task definition)
- ECS → Lambda (permissions, function name)
- Lambda → DynamoDB (permissions, table exists)

### 5. **Use Exit Codes and Status Codes**
- Exit code 0 = success (but check logs for errors that were caught)
- Exit code 1 = failure
- HTTP 200 = success
- HTTP 202 = accepted (async, check separately)
- HTTP 4xx = client error (permissions, bad request)
- HTTP 5xx = server error (service down, timeout)

### 6. **Build Diagnostic Tools**
Create scripts that automate your investigation:
```bash
# diagnose-current-issue.sh
# - Checks recent uploads
# - Checks recent processing
# - Checks running tasks
# - Shows recent jobs
```

This saves time and ensures you don't miss steps.

---

## Common Pitfalls

### ❌ **Pitfall 1: Checking the Wrong Account**
Multi-account AWS setups are confusing.
```bash
# Always verify
aws sts get-caller-identity
```

### ❌ **Pitfall 2: Checking Old Logs**
Logs from yesterday won't help debug today's issue.
```bash
# Use --since flag
aws logs tail /aws/lambda/function --since 30m
```

### ❌ **Pitfall 3: Assuming Async Succeeded**
Status 202 means "I'll try" not "I succeeded"
```bash
# Always check the invoked service's logs
```

### ❌ **Pitfall 4: Not Checking All Services**
In a chain of 5 services, checking 4 isn't enough.

### ❌ **Pitfall 5: Fixing Without Understanding**
Changing random things hoping it works = bad
Understanding the root cause = good

---

## Debugging Checklist

When something "isn't working":

- [ ] Define the exact symptom (what's the expected vs actual behavior?)
- [ ] Identify the service chain (what services are involved?)
- [ ] Check each service in order:
  - [ ] Did it receive the request?
  - [ ] Did it process successfully?
  - [ ] Did it call the next service?
- [ ] Read the logs for each service
- [ ] Look for ERROR, Exception, Failed messages
- [ ] Check exit codes and HTTP status codes
- [ ] Verify data at each step (DynamoDB, S3, etc.)
- [ ] Form a hypothesis about the root cause
- [ ] Verify the hypothesis with evidence
- [ ] Fix the root cause (not the symptom)
- [ ] Test the fix
- [ ] Document what you learned

---

## Tools to Master

### AWS CLI
```bash
# Logs
aws logs tail [log-group] --since [time] --follow
aws logs get-log-events --log-group-name [group] --log-stream-name [stream]
aws logs filter-log-events --log-group-name [group] --filter-pattern [pattern]

# ECS
aws ecs describe-tasks --cluster [cluster] --tasks [task-arn]
aws ecs list-tasks --cluster [cluster]

# Lambda
aws lambda get-function-configuration --function-name [name]
aws lambda invoke --function-name [name] --payload [json] output.json

# DynamoDB
aws dynamodb get-item --table-name [table] --key [json]
aws dynamodb scan --table-name [table] --filter-expression [expr]

# S3
aws s3 ls s3://bucket/prefix/
aws s3 cp s3://bucket/key local-file
```

### JQ (JSON processor)
```bash
# Extract specific fields
aws dynamodb get-item ... | jq '.Item.status.S'

# Filter arrays
aws ecs list-tasks ... | jq '.taskArns[]'
```

### Grep
```bash
# Find errors in logs
aws logs tail ... | grep -i error
aws logs tail ... | grep -E "ERROR|WARN|FAIL"
```

---

## The Current Issue - Applying the Method

Based on my investigation:

**Symptom:** Job stuck at 80% (CHORDS_DETECTED)

**Evidence:**
1. ECS task completed successfully (exit code 0)
2. ECS logs show error: `update_job_status() got an unexpected keyword argument 'status_message'`
3. ECS task invoked PDF Lambda (status 202)
4. Job status never updated to COMPLETED

**Hypothesis:** PDF Lambda failed or didn't run

**Next Steps:**
1. Check PDF Lambda logs for this specific job
2. Check if PDF file exists in S3
3. Fix the `update_job_status()` function signature issue
4. Verify PDF Lambda is using "COMPLETED" not "COMPLETE"

**Fix Priority:**
1. Check PDF Lambda logs (immediate - understand what happened)
2. Fix function signature (code fix)
3. Rebuild and deploy (deployment)
4. Test with new upload (verification)

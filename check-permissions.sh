#!/bin/bash
# Check ECS and PDF Generator Permissions

export AWS_PROFILE=production

echo "========================================="
echo "Permission Audit"
echo "========================================="
echo ""

# 1. ECS Task Role Permissions
echo "1. ECS Task Role: chordscout-v2-dev-ECSTaskRole-QBhvp2gMiDG7"
echo "-------------------------------------------"
echo "Checking what the ECS task can do..."
echo ""

# Get inline policies
POLICIES=$(aws iam list-role-policies --role-name chordscout-v2-dev-ECSTaskRole-QBhvp2gMiDG7 --query 'PolicyNames[]' --output text)

for POLICY in $POLICIES; do
    echo "Policy: $POLICY"
    aws iam get-role-policy --role-name chordscout-v2-dev-ECSTaskRole-QBhvp2gMiDG7 --policy-name $POLICY --query 'PolicyDocument.Statement[]' --output json | jq -r '.[] | "  Action: \(.Action | if type == "array" then join(", ") else . end)\n  Resource: \(.Resource | if type == "array" then join(", ") else . end)\n"'
done
echo ""

# 2. PDF Generator Lambda Role
echo "2. PDF Generator Lambda Role"
echo "-------------------------------------------"
PDF_ROLE=$(aws lambda get-function-configuration --function-name chordscout-v2-pdf-generator-dev --query 'Role' --output text)
PDF_ROLE_NAME=$(basename $PDF_ROLE)
echo "Role: $PDF_ROLE_NAME"
echo ""

# Get inline policies
PDF_POLICIES=$(aws iam list-role-policies --role-name $PDF_ROLE_NAME --query 'PolicyNames[]' --output text 2>/dev/null || echo "")
if [ -n "$PDF_POLICIES" ]; then
    for POLICY in $PDF_POLICIES; do
        echo "Inline Policy: $POLICY"
        aws iam get-role-policy --role-name $PDF_ROLE_NAME --policy-name $POLICY --query 'PolicyDocument.Statement[]' --output json | jq -r '.[] | "  Action: \(.Action | if type == "array" then join(", ") else . end)\n  Resource: \(.Resource | if type == "array" then join(", ") else . end)\n"'
    done
fi

# Get attached policies
ATTACHED=$(aws iam list-attached-role-policies --role-name $PDF_ROLE_NAME --query 'AttachedPolicies[*].PolicyName' --output text 2>/dev/null || echo "")
if [ -n "$ATTACHED" ]; then
    echo "Attached Policies: $ATTACHED"
fi
echo ""

# 3. Test Specific Permissions
echo "3. Testing Specific Permissions"
echo "-------------------------------------------"

# Can ECS invoke PDF Lambda?
echo "✓ Testing: Can ECS task invoke PDF Lambda?"
ECS_CAN_INVOKE=$(aws iam get-role-policy --role-name chordscout-v2-dev-ECSTaskRole-QBhvp2gMiDG7 --policy-name ChordDetectorPolicy --query 'PolicyDocument.Statement[?Action==`lambda:InvokeFunction`].Resource' --output text 2>/dev/null)
if echo "$ECS_CAN_INVOKE" | grep -q "chordscout-v2-pdf-generator-dev"; then
    echo "  ✅ YES - ECS can invoke PDF Lambda"
else
    echo "  ❌ NO - ECS cannot invoke PDF Lambda"
    echo "  Found: $ECS_CAN_INVOKE"
fi
echo ""

# Can PDF Lambda write to S3?
echo "✓ Testing: Can PDF Lambda write to S3?"
PDF_S3_ACCESS=$(aws iam list-attached-role-policies --role-name $PDF_ROLE_NAME --query 'AttachedPolicies[*].PolicyName' --output text 2>/dev/null)
if echo "$PDF_S3_ACCESS" | grep -q "Lambda"; then
    echo "  ✅ YES - Has Lambda execution role (includes CloudWatch Logs)"
    
    # Check for S3 permissions
    PDF_INLINE=$(aws iam list-role-policies --role-name $PDF_ROLE_NAME --query 'PolicyNames[]' --output text 2>/dev/null)
    if [ -n "$PDF_INLINE" ]; then
        for POLICY in $PDF_INLINE; do
            S3_PERMS=$(aws iam get-role-policy --role-name $PDF_ROLE_NAME --policy-name $POLICY --query 'PolicyDocument.Statement[?contains(Action, `s3:`)]' --output json 2>/dev/null)
            if [ "$S3_PERMS" != "[]" ] && [ "$S3_PERMS" != "" ]; then
                echo "  ✅ YES - Has S3 permissions in policy: $POLICY"
            fi
        done
    else
        echo "  ⚠️  No inline policies found - may need S3 permissions"
    fi
else
    echo "  ⚠️  Basic execution role not found"
fi
echo ""

# Can PDF Lambda write to DynamoDB?
echo "✓ Testing: Can PDF Lambda write to DynamoDB?"
if [ -n "$PDF_INLINE" ]; then
    for POLICY in $PDF_INLINE; do
        DYNAMO_PERMS=$(aws iam get-role-policy --role-name $PDF_ROLE_NAME --policy-name $POLICY --query 'PolicyDocument.Statement[?contains(Action, `dynamodb:`)]' --output json 2>/dev/null)
        if [ "$DYNAMO_PERMS" != "[]" ] && [ "$DYNAMO_PERMS" != "" ]; then
            echo "  ✅ YES - Has DynamoDB permissions in policy: $POLICY"
        fi
    done
else
    echo "  ⚠️  No inline policies found - may need DynamoDB permissions"
fi
echo ""

# 4. Resource Access Test
echo "4. Resource Access Verification"
echo "-------------------------------------------"

# Check if PDF bucket exists and is accessible
echo "✓ Testing: PDF S3 bucket access"
PDF_BUCKET="chordscout-pdfs-dev-090130568474"
if aws s3 ls s3://$PDF_BUCKET/ --max-items 1 >/dev/null 2>&1; then
    echo "  ✅ Can access bucket: $PDF_BUCKET"
else
    echo "  ❌ Cannot access bucket: $PDF_BUCKET"
fi
echo ""

# Check if DynamoDB table exists and is accessible
echo "✓ Testing: DynamoDB table access"
JOBS_TABLE="ChordScout-Jobs-V2-dev"
if aws dynamodb describe-table --table-name $JOBS_TABLE >/dev/null 2>&1; then
    echo "  ✅ Can access table: $JOBS_TABLE"
else
    echo "  ❌ Cannot access table: $JOBS_TABLE"
fi
echo ""

echo "========================================="
echo "Summary"
echo "========================================="
echo ""
echo "If you see any ❌ or ⚠️ above, those need to be fixed."
echo ""

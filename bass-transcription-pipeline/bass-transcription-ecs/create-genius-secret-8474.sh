#!/bin/bash
# Create Genius API secret in account 090130568474

set -e

echo "============================================================"
echo "CREATE GENIUS API SECRET IN ACCOUNT 090130568474"
echo "============================================================"
echo ""

CORRECT_ACCOUNT="090130568474"
SOURCE_ACCOUNT="463470937777"
SECRET_NAME="chordscout/genius-api-token"
REGION="us-east-1"

# Verify we're in the correct account
echo "Step 1: Verifying AWS Account..."
CURRENT_ACCOUNT=$(aws sts get-caller-identity --query 'Account' --output text)

if [ "$CURRENT_ACCOUNT" != "$CORRECT_ACCOUNT" ]; then
    echo "✗ ERROR: Wrong AWS account!"
    echo "  Current: $CURRENT_ACCOUNT"
    echo "  Expected: $CORRECT_ACCOUNT"
    exit 1
fi

echo "✓ Correct AWS account: $CURRENT_ACCOUNT"
echo ""

# Get the token from the source account
echo "Step 2: Retrieving token from source account ($SOURCE_ACCOUNT)..."
echo "Switching to source account temporarily..."

TOKEN=$(AWS_PROFILE=DWilson19 aws secretsmanager get-secret-value \
    --secret-id "$SECRET_NAME" \
    --region "$REGION" \
    --query 'SecretString' \
    --output text 2>&1)

if [ $? -ne 0 ]; then
    echo "✗ Failed to retrieve token from source account"
    echo "  Error: $TOKEN"
    exit 1
fi

# Extract just the token value
TOKEN_VALUE=$(echo "$TOKEN" | jq -r '.GENIUS_ACCESS_TOKEN')

if [ -z "$TOKEN_VALUE" ] || [ "$TOKEN_VALUE" = "null" ]; then
    echo "✗ Failed to extract token value"
    exit 1
fi

TOKEN_LENGTH=${#TOKEN_VALUE}
MASKED="${TOKEN_VALUE:0:4}****${TOKEN_VALUE: -4}"
echo "✓ Token retrieved: $MASKED (length: $TOKEN_LENGTH)"
echo ""

# Create the secret in the target account
echo "Step 3: Creating secret in target account ($CORRECT_ACCOUNT)..."

# Check if secret already exists
EXISTING=$(aws secretsmanager describe-secret \
    --secret-id "$SECRET_NAME" \
    --region "$REGION" 2>&1 || echo "not_found")

if echo "$EXISTING" | grep -q "not_found\|ResourceNotFoundException"; then
    # Create new secret
    echo "Creating new secret..."
    aws secretsmanager create-secret \
        --name "$SECRET_NAME" \
        --description "Genius API token for ChordScout lyrics feature" \
        --secret-string "{\"GENIUS_ACCESS_TOKEN\":\"$TOKEN_VALUE\"}" \
        --region "$REGION"
    
    if [ $? -eq 0 ]; then
        echo "✓ Secret created successfully"
    else
        echo "✗ Failed to create secret"
        exit 1
    fi
else
    # Update existing secret
    echo "Secret already exists, updating..."
    aws secretsmanager put-secret-value \
        --secret-id "$SECRET_NAME" \
        --secret-string "{\"GENIUS_ACCESS_TOKEN\":\"$TOKEN_VALUE\"}" \
        --region "$REGION"
    
    if [ $? -eq 0 ]; then
        echo "✓ Secret updated successfully"
    else
        echo "✗ Failed to update secret"
        exit 1
    fi
fi

echo ""

# Verify the secret
echo "Step 4: Verifying secret..."
VERIFY=$(aws secretsmanager get-secret-value \
    --secret-id "$SECRET_NAME" \
    --region "$REGION" \
    --query 'SecretString' \
    --output text)

VERIFY_TOKEN=$(echo "$VERIFY" | jq -r '.GENIUS_ACCESS_TOKEN')

if [ "$VERIFY_TOKEN" = "$TOKEN_VALUE" ]; then
    echo "✓ Secret verified successfully"
else
    echo "✗ Secret verification failed"
    exit 1
fi

echo ""
echo "============================================================"
echo "SECRET CREATED SUCCESSFULLY"
echo "============================================================"
echo ""
echo "Secret Name: $SECRET_NAME"
echo "Region: $REGION"
echo "Account: $CURRENT_ACCOUNT"
echo "Token: $MASKED"
echo ""
echo "Next step: Run ./configure-phase3-env.sh"
echo ""

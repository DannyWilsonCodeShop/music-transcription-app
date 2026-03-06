#!/bin/bash
# Simple test script to verify GENIUS_ACCESS_TOKEN configuration

echo "============================================================"
echo "GENIUS API SECRET VALIDATION TEST"
echo "============================================================"
echo ""

# Test 1: Check environment variable
echo "============================================================"
echo "TEST 1: Environment Variable"
echo "============================================================"

if [ -n "$GENIUS_ACCESS_TOKEN" ]; then
    # Mask the token for security
    TOKEN_LENGTH=${#GENIUS_ACCESS_TOKEN}
    MASKED="${GENIUS_ACCESS_TOKEN:0:4}****${GENIUS_ACCESS_TOKEN: -4}"
    echo "✓ GENIUS_ACCESS_TOKEN found in environment"
    echo "  Value: $MASKED"
    echo "  Length: $TOKEN_LENGTH characters"
    ENV_TEST="PASS"
else
    echo "✗ GENIUS_ACCESS_TOKEN not found in environment"
    echo "  Checking .env file..."
    
    if [ -f "../../.env" ]; then
        if grep -q "GENIUS_ACCESS_TOKEN" ../../.env; then
            echo "  Found in .env file but not loaded"
            echo "  Run: source ../../.env"
        else
            echo "  Not found in .env file"
        fi
    fi
    ENV_TEST="FAIL"
fi

# Test 2: Check AWS Secrets Manager (if AWS CLI is available)
echo ""
echo "============================================================"
echo "TEST 2: AWS Secrets Manager"
echo "============================================================"

if command -v aws &> /dev/null; then
    SECRET_NAME="chordscout/genius-api-token"
    REGION="${AWS_REGION:-us-east-1}"
    
    echo "Attempting to retrieve secret: $SECRET_NAME"
    echo "Region: $REGION"
    
    SECRET_VALUE=$(aws secretsmanager get-secret-value \
        --secret-id "$SECRET_NAME" \
        --region "$REGION" \
        --query SecretString \
        --output text 2>&1)
    
    if [ $? -eq 0 ]; then
        # Extract token from JSON
        TOKEN=$(echo "$SECRET_VALUE" | grep -o '"GENIUS_ACCESS_TOKEN":"[^"]*"' | cut -d'"' -f4)
        
        if [ -n "$TOKEN" ]; then
            TOKEN_LENGTH=${#TOKEN}
            MASKED="${TOKEN:0:4}****${TOKEN: -4}"
            echo "✓ Secret retrieved successfully"
            echo "  Value: $MASKED"
            echo "  Length: $TOKEN_LENGTH characters"
            SM_TEST="PASS"
            
            # Use this token for API test if env var not set
            if [ -z "$GENIUS_ACCESS_TOKEN" ]; then
                GENIUS_ACCESS_TOKEN="$TOKEN"
            fi
        else
            echo "✗ Secret retrieved but GENIUS_ACCESS_TOKEN key not found"
            SM_TEST="FAIL"
        fi
    else
        if echo "$SECRET_VALUE" | grep -q "ResourceNotFoundException"; then
            echo "✗ Secret '$SECRET_NAME' does not exist"
        elif echo "$SECRET_VALUE" | grep -q "AccessDeniedException"; then
            echo "✗ Access denied - check IAM permissions"
        else
            echo "✗ Failed to retrieve secret"
            echo "  Error: $SECRET_VALUE"
        fi
        SM_TEST="FAIL"
    fi
else
    echo "⚠ AWS CLI not available - skipping Secrets Manager test"
    SM_TEST="SKIP"
fi

# Test 3: Test API connection
echo ""
echo "============================================================"
echo "TEST 3: Genius API Connection"
echo "============================================================"

if [ -n "$GENIUS_ACCESS_TOKEN" ]; then
    echo "Sending test request to Genius API..."
    
    RESPONSE=$(curl -s -w "\n%{http_code}" \
        -H "Authorization: Bearer $GENIUS_ACCESS_TOKEN" \
        "https://api.genius.com/search?q=test")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✓ API request successful (status: $HTTP_CODE)"
        if echo "$BODY" | grep -q '"response"'; then
            echo "  Response contains valid data"
            API_TEST="PASS"
        else
            echo "  Warning: Unexpected response format"
            API_TEST="FAIL"
        fi
    else
        echo "✗ API request failed (status: $HTTP_CODE)"
        echo "  Response: ${BODY:0:200}"
        API_TEST="FAIL"
    fi
else
    echo "✗ No token available to test"
    API_TEST="FAIL"
fi

# Summary
echo ""
echo "============================================================"
echo "SUMMARY"
echo "============================================================"

echo "Environment Variable:  $([ "$ENV_TEST" = "PASS" ] && echo "✓ PASS" || echo "✗ FAIL")"
echo "Secrets Manager:       $([ "$SM_TEST" = "PASS" ] && echo "✓ PASS" || ([ "$SM_TEST" = "SKIP" ] && echo "⚠ SKIP" || echo "✗ FAIL"))"
echo "API Connection:        $([ "$API_TEST" = "PASS" ] && echo "✓ PASS" || echo "✗ FAIL")"

echo ""
echo "============================================================"

if [ "$ENV_TEST" = "PASS" ] || [ "$SM_TEST" = "PASS" ]; then
    if [ "$API_TEST" = "PASS" ]; then
        echo "✓ ALL TESTS PASSED - Genius API is properly configured"
        echo "============================================================"
        exit 0
    fi
fi

echo "✗ TESTS FAILED - Genius API configuration needs attention"
echo "============================================================"

if [ "$ENV_TEST" = "FAIL" ] && [ "$SM_TEST" = "FAIL" ]; then
    echo ""
    echo "Action Required:"
    echo "1. Set GENIUS_ACCESS_TOKEN environment variable:"
    echo "   export GENIUS_ACCESS_TOKEN='your-token-here'"
    echo ""
    echo "2. OR create secret in AWS Secrets Manager:"
    echo "   aws secretsmanager create-secret \\"
    echo "     --name chordscout/genius-api-token \\"
    echo "     --secret-string '{\"GENIUS_ACCESS_TOKEN\":\"your-token-here\"}'"
    echo ""
    echo "Get a free token at: https://genius.com/api-clients"
fi

exit 1

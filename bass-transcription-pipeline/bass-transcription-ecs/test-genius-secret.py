#!/usr/bin/env python3
"""
Test script to verify GENIUS_ACCESS_TOKEN secret retrieval
Tests both environment variable and AWS Secrets Manager access
"""

import os
import sys
import boto3
import json
from botocore.exceptions import ClientError

def test_environment_variable():
    """Test if GENIUS_ACCESS_TOKEN is available as environment variable"""
    print("=" * 60)
    print("TEST 1: Environment Variable")
    print("=" * 60)
    
    token = os.environ.get('GENIUS_ACCESS_TOKEN', '')
    
    if token:
        # Mask the token for security
        masked = token[:4] + '*' * (len(token) - 8) + token[-4:] if len(token) > 8 else '****'
        print(f"✓ GENIUS_ACCESS_TOKEN found in environment")
        print(f"  Value: {masked}")
        print(f"  Length: {len(token)} characters")
        return True
    else:
        print("✗ GENIUS_ACCESS_TOKEN not found in environment")
        return False


def test_secrets_manager():
    """Test if GENIUS_ACCESS_TOKEN can be retrieved from AWS Secrets Manager"""
    print("\n" + "=" * 60)
    print("TEST 2: AWS Secrets Manager")
    print("=" * 60)
    
    secret_name = "chordscout/genius-api-token"
    region = os.environ.get('AWS_REGION', 'us-east-1')
    
    try:
        client = boto3.client('secretsmanager', region_name=region)
        print(f"Attempting to retrieve secret: {secret_name}")
        print(f"Region: {region}")
        
        response = client.get_secret_value(SecretId=secret_name)
        
        if 'SecretString' in response:
            secret = json.loads(response['SecretString'])
            token = secret.get('GENIUS_ACCESS_TOKEN', '')
            
            if token:
                masked = token[:4] + '*' * (len(token) - 8) + token[-4:] if len(token) > 8 else '****'
                print(f"✓ Secret retrieved successfully")
                print(f"  Value: {masked}")
                print(f"  Length: {len(token)} characters")
                return True, token
            else:
                print("✗ Secret retrieved but GENIUS_ACCESS_TOKEN key not found")
                return False, None
        else:
            print("✗ Secret retrieved but SecretString not found")
            return False, None
            
    except ClientError as e:
        error_code = e.response['Error']['Code']
        print(f"✗ Failed to retrieve secret: {error_code}")
        
        if error_code == 'ResourceNotFoundException':
            print(f"  Secret '{secret_name}' does not exist")
        elif error_code == 'AccessDeniedException':
            print(f"  Access denied - check IAM permissions")
        else:
            print(f"  Error: {e}")
        
        return False, None
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False, None


def test_genius_api(token):
    """Test if the token works with Genius API"""
    print("\n" + "=" * 60)
    print("TEST 3: Genius API Connection")
    print("=" * 60)
    
    if not token:
        print("✗ No token available to test")
        return False
    
    try:
        import requests
        
        headers = {'Authorization': f'Bearer {token}'}
        url = 'https://api.genius.com/search'
        params = {'q': 'test'}
        
        print("Sending test request to Genius API...")
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            print(f"✓ API request successful (status: {response.status_code})")
            data = response.json()
            if 'response' in data:
                print(f"  Response contains valid data")
                return True
            else:
                print(f"  Warning: Unexpected response format")
                return False
        else:
            print(f"✗ API request failed (status: {response.status_code})")
            print(f"  Response: {response.text[:200]}")
            return False
            
    except ImportError:
        print("⚠ requests library not available - skipping API test")
        return None
    except Exception as e:
        print(f"✗ API test failed: {e}")
        return False


def main():
    print("\n" + "=" * 60)
    print("GENIUS API SECRET VALIDATION TEST")
    print("=" * 60 + "\n")
    
    results = {}
    
    # Test 1: Environment variable
    results['env'] = test_environment_variable()
    
    # Test 2: Secrets Manager
    results['secrets_manager'], token = test_secrets_manager()
    
    # Test 3: API connection (use token from either source)
    if not token and results['env']:
        token = os.environ.get('GENIUS_ACCESS_TOKEN', '')
    
    if token:
        results['api'] = test_genius_api(token)
    else:
        results['api'] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    print(f"Environment Variable:  {'✓ PASS' if results['env'] else '✗ FAIL'}")
    print(f"Secrets Manager:       {'✓ PASS' if results['secrets_manager'] else '✗ FAIL'}")
    
    if results['api'] is None:
        print(f"API Connection:        ⚠ SKIPPED")
    else:
        print(f"API Connection:        {'✓ PASS' if results['api'] else '✗ FAIL'}")
    
    # Overall result
    has_token = results['env'] or results['secrets_manager']
    api_works = results['api'] in [True, None]  # None means skipped
    
    print("\n" + "=" * 60)
    if has_token and api_works:
        print("✓ ALL TESTS PASSED - Genius API is properly configured")
        print("=" * 60)
        return 0
    else:
        print("✗ TESTS FAILED - Genius API configuration needs attention")
        print("=" * 60)
        
        if not has_token:
            print("\nAction Required:")
            print("1. Set GENIUS_ACCESS_TOKEN environment variable, OR")
            print("2. Create secret in AWS Secrets Manager:")
            print("   aws secretsmanager create-secret \\")
            print("     --name chordscout/genius-api-token \\")
            print("     --secret-string '{\"GENIUS_ACCESS_TOKEN\":\"your-token-here\"}'")
        
        return 1


if __name__ == '__main__':
    sys.exit(main())

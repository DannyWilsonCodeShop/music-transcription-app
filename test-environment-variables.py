#!/usr/bin/env python3
"""
Test Environment Variables for Development Deployment
Validates all required environment variables are working
"""

import os
import requests
import json
from datetime import datetime

def test_rapidapi_key():
    """Test RapidAPI key"""
    print("🔑 Testing RapidAPI Key...")
    
    rapidapi_key = input("Enter your RapidAPI key: ").strip()
    
    if not rapidapi_key:
        print("❌ No RapidAPI key provided")
        return False, None
    
    # Test with a simple API call
    try:
        response = requests.get(
            "https://youtube-mp36.p.rapidapi.com/dl",
            params={"id": "dQw4w9WgXcQ"},  # Rick Roll for testing
            headers={
                "x-rapidapi-key": rapidapi_key,
                "x-rapidapi-host": "youtube-mp36.p.rapidapi.com"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'ok':
                print("✅ RapidAPI key is valid and working")
                print(f"   Video title: {data.get('title', 'Unknown')}")
                return True, rapidapi_key
            else:
                print(f"❌ RapidAPI returned error: {data.get('msg', 'Unknown')}")
                return False, rapidapi_key
        else:
            print(f"❌ RapidAPI request failed: {response.status_code}")
            if response.status_code == 403:
                print("   This might be a subscription issue")
            return False, rapidapi_key
            
    except Exception as e:
        print(f"❌ RapidAPI test failed: {str(e)}")
        return False, rapidapi_key

def test_openai_key():
    """Test OpenAI API key"""
    print("\n🤖 Testing OpenAI API Key...")
    
    openai_key = input("Enter your OpenAI API key: ").strip()
    
    if not openai_key:
        print("❌ No OpenAI key provided")
        return False, None
    
    # Test with a simple API call
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 5
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ OpenAI API key is valid and working")
            data = response.json()
            usage = data.get('usage', {})
            print(f"   Tokens used: {usage.get('total_tokens', 'Unknown')}")
            return True, openai_key
        else:
            print(f"❌ OpenAI API request failed: {response.status_code}")
            if response.status_code == 401:
                print("   Invalid API key")
            elif response.status_code == 429:
                print("   Rate limit or quota exceeded")
            else:
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('error', {}).get('message', 'Unknown')}")
                except:
                    print(f"   Response: {response.text[:200]}")
            return False, openai_key
            
    except Exception as e:
        print(f"❌ OpenAI test failed: {str(e)}")
        return False, openai_key

def test_node_version():
    """Test Node.js version"""
    print("\n📦 Testing Node.js Version...")
    
    try:
        import subprocess
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ Node.js version: {version}")
            
            # Check if it's version 18 or higher
            version_num = int(version.replace('v', '').split('.')[0])
            if version_num >= 18:
                print("✅ Node.js version is compatible (18+)")
                return True
            else:
                print("⚠️  Node.js version should be 18 or higher for best compatibility")
                return True  # Still works, just a warning
        else:
            print("❌ Node.js not found or not working")
            return False
            
    except Exception as e:
        print(f"❌ Node.js test failed: {str(e)}")
        return False

def generate_env_config(rapidapi_key, openai_key):
    """Generate environment variable configuration"""
    print("\n📋 Environment Variable Configuration:")
    print("="*50)
    print("Copy these to your Amplify Console → Environment variables:")
    print()
    print("NODE_VERSION = 18")
    if openai_key:
        print(f"OPENAI_API_KEY = {openai_key}")
    if rapidapi_key:
        print(f"RAPIDAPI_KEY = {rapidapi_key}")
    print()
    print("Additional optional variables:")
    print("AWS_REGION = us-east-1")
    print("LOG_LEVEL = INFO")

def main():
    """Main test function"""
    
    print("🧪 Testing Environment Variables for Development Deployment")
    print("="*60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = {}
    
    # Test RapidAPI
    rapidapi_success, rapidapi_key = test_rapidapi_key()
    results['rapidapi'] = rapidapi_success
    
    # Test OpenAI
    openai_success, openai_key = test_openai_key()
    results['openai'] = openai_success
    
    # Test Node.js
    node_success = test_node_version()
    results['node'] = node_success
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for service, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{service.upper()}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Ready for deployment.")
        generate_env_config(rapidapi_key if rapidapi_success else None, 
                          openai_key if openai_success else None)
    elif passed_tests > 0:
        print("⚠️  Some tests failed. Check the issues above.")
        if rapidapi_success or openai_success:
            generate_env_config(rapidapi_key if rapidapi_success else None, 
                              openai_key if openai_success else None)
    else:
        print("❌ All tests failed. Please check your API keys and setup.")
    
    print("\n🚀 Next Steps:")
    print("1. Copy the environment variables to Amplify Console")
    print("2. Deploy your development environment")
    print("3. Test the live application")

if __name__ == "__main__":
    main()
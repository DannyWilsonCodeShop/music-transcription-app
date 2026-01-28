#!/usr/bin/env python3
"""
Setup Environment Variables
Interactive script to create .env file with your API keys
"""

import os
import re

def get_api_key(service_name, current_value=None, validation_func=None):
    """Get API key from user with validation"""
    
    if current_value and current_value != f"your-{service_name.lower().replace(' ', '-')}-api-key-here":
        print(f"Current {service_name} key: {current_value[:20]}...")
        use_current = input(f"Use current {service_name} key? (y/n): ").strip().lower()
        if use_current == 'y':
            return current_value
    
    while True:
        key = input(f"Enter your {service_name} API key (or 'skip' to leave empty): ").strip()
        
        if key.lower() == 'skip':
            return f"your-{service_name.lower().replace(' ', '-')}-api-key-here"
        
        if not key:
            print("❌ Please enter a key or type 'skip'")
            continue
        
        if validation_func:
            if validation_func(key):
                return key
            else:
                print("❌ Invalid key format. Please try again.")
                continue
        
        return key

def validate_openai_key(key):
    """Validate OpenAI API key format"""
    return key.startswith('sk-') and len(key) > 20

def validate_rapidapi_key(key):
    """Validate RapidAPI key format"""
    return len(key) > 20 and re.match(r'^[a-f0-9]+$', key.split('msn')[0] if 'msn' in key else key[:32])

def validate_apify_key(key):
    """Validate Apify API key format"""
    return key.startswith('apify_api_') and len(key) > 30

def read_current_env():
    """Read current .env file if it exists"""
    env_vars = {}
    
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    
    return env_vars

def write_env_file(env_vars):
    """Write environment variables to .env file"""
    
    env_content = f"""# AWS Configuration (auto-configured by Amplify)
AWS_REGION={env_vars.get('AWS_REGION', 'us-east-1')}

# Application Settings
NODE_ENV={env_vars.get('NODE_ENV', 'development')}
REACT_APP_API_NAME={env_vars.get('REACT_APP_API_NAME', 'transcriptionAPI')}

# External API Keys
OPENAI_API_KEY={env_vars.get('OPENAI_API_KEY', 'your-openai-api-key-here')}
RAPIDAPI_KEY={env_vars.get('RAPIDAPI_KEY', 'your-rapidapi-key-here')}
APIFY_API_TOKEN={env_vars.get('APIFY_API_TOKEN', 'your-apify-api-token-here')}

# File Upload Limits
MAX_FILE_SIZE_MB={env_vars.get('MAX_FILE_SIZE_MB', '50')}
MAX_DURATION_MINUTES={env_vars.get('MAX_DURATION_MINUTES', '15')}

# Rate Limiting
RATE_LIMIT_PER_HOUR={env_vars.get('RATE_LIMIT_PER_HOUR', '100')}

# Development Settings
USE_MOCK_DATA={env_vars.get('USE_MOCK_DATA', 'false')}
LOG_LEVEL={env_vars.get('LOG_LEVEL', 'INFO')}
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)

def main():
    """Main setup function"""
    
    print("🔧 Environment Variables Setup")
    print("="*40)
    print("This script will help you create a .env file with your API keys.")
    print("Your .env file is ignored by git, so your keys stay private.")
    print()
    
    # Read current environment
    current_env = read_current_env()
    
    # Get API keys
    print("📝 Setting up API keys...")
    print()
    
    # OpenAI API Key
    openai_key = get_api_key(
        "OpenAI", 
        current_env.get('OPENAI_API_KEY'),
        validate_openai_key
    )
    
    # RapidAPI Key
    rapidapi_key = get_api_key(
        "RapidAPI",
        current_env.get('RAPIDAPI_KEY', '252611e8d7mshdde3262a7e2137bp12792bjsn7ce487b8a3dc'),
        validate_rapidapi_key
    )
    
    # Apify API Token
    apify_token = get_api_key(
        "Apify",
        current_env.get('APIFY_API_TOKEN'),
        validate_apify_key
    )
    
    # Update environment variables
    env_vars = current_env.copy()
    env_vars.update({
        'OPENAI_API_KEY': openai_key,
        'RAPIDAPI_KEY': rapidapi_key,
        'APIFY_API_TOKEN': apify_token,
        'USE_MOCK_DATA': 'false',  # Development should use real data
        'NODE_ENV': 'development'
    })
    
    # Write .env file
    write_env_file(env_vars)
    
    print("\n✅ .env file created successfully!")
    print("\n📋 Your environment variables:")
    print("-" * 30)
    
    for key, value in env_vars.items():
        if 'KEY' in key or 'TOKEN' in key:
            # Mask sensitive values
            if len(value) > 20 and not value.startswith('your-'):
                display_value = f"{value[:8]}...{value[-4:]}"
            else:
                display_value = value
        else:
            display_value = value
        
        print(f"{key}={display_value}")
    
    print("\n🚀 Next Steps:")
    print("1. Your .env file is ready for local development")
    print("2. For Amplify deployment, add these to Environment Variables:")
    print("   - OPENAI_API_KEY")
    print("   - RAPIDAPI_KEY") 
    print("   - NODE_VERSION=18")
    print("3. Run 'npm run dev' to test locally")
    
    print("\n⚠️  Security Notes:")
    print("- .env file is ignored by git (your keys are safe)")
    print("- Never commit API keys to version control")
    print("- Use AWS Secrets Manager for production")

if __name__ == "__main__":
    main()
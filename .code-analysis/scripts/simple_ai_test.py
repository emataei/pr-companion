#!/usr/bin/env python3
"""
Simple AI Foundry Connection Test
Direct test using the existing AI client factory
"""

import os
import sys
from pathlib import Path

# Load environment variables from .env file manually
def load_env():
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# Load .env
load_env()

# Add .code-analysis to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_connection():
    print("🧪 Simple AI Foundry Connection Test\n")
    
    # Check environment variables
    print("📋 Environment Variables:")
    endpoint = os.getenv('AI_FOUNDRY_ENDPOINT')
    token = os.getenv('AI_FOUNDRY_TOKEN')
    model = os.getenv('AI_FOUNDRY_MODEL', 'gpt-4o')
    
    print(f"AI_FOUNDRY_ENDPOINT: {'✅ Set' if endpoint else '❌ Missing'}")
    print(f"AI_FOUNDRY_TOKEN: {'✅ Set (' + token[:10] + '...)' if token else '❌ Missing'}")
    print(f"AI_FOUNDRY_MODEL: {model}")
    print()
    
    if not endpoint or not token:
        print("❌ Missing required environment variables in .env file")
        return
    
    try:
        print("🔧 Creating AI client...")
        from scoring.ai_client_factory import AIClientFactory
        
        client = AIClientFactory.create_client()
        model_name = AIClientFactory.get_model_name()
        
        print("✅ AI Client created successfully")
        print(f"📝 Using model: {model_name}")
        print(f"🌐 Endpoint: {endpoint}")
        
        print("\n🤖 Testing simple AI call...")
        
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant. Respond with exactly 'Connection successful!' to confirm this works."
            },
            {
                "role": "user", 
                "content": "Test connection"
            }
        ]
        
        response = client.complete(
            messages=messages,
            model=model_name,
            max_tokens=20,
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip()
        print(f"✅ AI Response: {result}")
        
        if "successful" in result.lower():
            print("🎉 AI Foundry connection is working perfectly!")
            print("🔥 The 404 error should now be fixed!")
        else:
            print("⚠️ AI responded but with unexpected message")
            print("✅ Connection works, but AI didn't follow instructions exactly")
            
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Make sure Azure AI packages are installed:")
        print("   pip install azure-ai-inference azure-identity")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
        error_str = str(e)
        if "404" in error_str:
            print("\n🔍 404 Error - Resource not found:")
            print(f"- Endpoint: {endpoint}")
            print("- Check if the endpoint URL is correct")
            print("- Verify the model deployment exists")
            print("- Ensure the model name matches your deployment")
        elif "401" in error_str:
            print("\n🔍 401 Error - Authentication failed:")
            print("- Check if AI_FOUNDRY_TOKEN is correct")
            print("- Verify the token hasn't expired")
        elif "403" in error_str:
            print("\n🔍 403 Error - Permission denied:")
            print("- Check if your token has the required permissions")
            print("- Verify access to the model deployment")
        else:
            print(f"\n🔍 Unexpected error: {error_str}")

if __name__ == "__main__":
    test_connection()

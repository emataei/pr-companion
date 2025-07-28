#!/usr/bin/env python3
"""
Debug AI Client Creation
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

def debug_azure_imports():
    print("🔍 Debugging Azure Imports and Credential Creation\n")
    
    try:
        print("1. Testing azure.ai.inference import...")
        from azure.ai.inference import ChatCompletionsClient
        print("✅ ChatCompletionsClient imported successfully")
        
        print("2. Testing azure.identity import...")
        from azure.identity import DefaultAzureCredential
        print("✅ DefaultAzureCredential imported successfully")
        
        print("3. Testing azure.core.credentials import...")
        from azure.core.credentials import AzureKeyCredential
        print("✅ AzureKeyCredential imported successfully")
        
        print("4. Testing AzureKeyCredential creation...")
        token = os.getenv('AI_FOUNDRY_TOKEN')
        print(f"Token: {token[:10]}... (length: {len(token)})")
        
        # Try creating the credential
        credential = AzureKeyCredential(token)
        print("✅ AzureKeyCredential created successfully")
        print(f"Credential type: {type(credential)}")
        
        print("5. Testing ChatCompletionsClient creation...")
        endpoint = os.getenv('AI_FOUNDRY_ENDPOINT')
        print(f"Endpoint: {endpoint}")
        
        client = ChatCompletionsClient(
            endpoint=endpoint,
            credential=credential
        )
        print("✅ ChatCompletionsClient created successfully")
        print(f"Client type: {type(client)}")
        
        print("\n🎉 All imports and client creation successful!")
        return client
        
    except Exception as e:
        print(f"❌ Error at step: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_simple_call(client):
    if not client:
        return
        
    print("\n6. Testing a simple AI call...")
    try:
        model_name = os.getenv('AI_FOUNDRY_MODEL', 'gpt-4o')
        
        messages = [
            {
                "role": "system",
                "content": "Respond with 'Test successful!'"
            },
            {
                "role": "user", 
                "content": "Hello"
            }
        ]
        
        response = client.complete(
            messages=messages,
            model=model_name,
            max_tokens=10,
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip()
        print(f"✅ AI Response: {result}")
        print("🎉 Full test successful!")
        
    except Exception as e:
        print(f"❌ Error in AI call: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    client = debug_azure_imports()
    test_simple_call(client)

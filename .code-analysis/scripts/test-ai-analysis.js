/**
 * Simple AI Foundry Connection Test
 * Tests the exact same setup as the Python scripts use
 */

require('dotenv').config();
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

async function testAIFoundryConnection() {
  console.log('🧪 Testing AI Foundry Connection...\n');
  
  // Check environment variables (using the same names as Python scripts)
  console.log('📋 Environment Variables:');
  console.log('AI_FOUNDRY_ENDPOINT:', process.env.AI_FOUNDRY_ENDPOINT ? '✅ Set' : '❌ Missing');
  console.log('AI_FOUNDRY_TOKEN:', process.env.AI_FOUNDRY_TOKEN ? '✅ Set' : '❌ Missing');
  console.log('AI_FOUNDRY_MODEL:', process.env.AI_FOUNDRY_MODEL || 'gpt-4o (default)');
  console.log('');
  
  if (!process.env.AI_FOUNDRY_ENDPOINT || !process.env.AI_FOUNDRY_TOKEN) {
    console.log('❌ Missing required environment variables. Please create a .env file with:');
    console.log('   AI_FOUNDRY_ENDPOINT=your_endpoint_url');
    console.log('   AI_FOUNDRY_TOKEN=your_api_key');
    console.log('   AI_FOUNDRY_MODEL=your_model_name (optional)');
    console.log('\n💡 Copy .env.example to .env and fill in your values');
    return;
  }
  
  try {
    console.log('🐍 Running Python AI test...');
    
    // Create a simple Python test script that uses our existing AI client
    const testScript = `
import sys
import os
from pathlib import Path

# Add .code-analysis to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from scoring.ai_client_factory import AIClientFactory
    
    print("🔧 Creating AI client...")
    client = AIClientFactory.create_client()
    model_name = AIClientFactory.get_model_name()
    
    print(f"✅ AI Client created successfully")
    print(f"📝 Using model: {model_name}")
    print(f"🌐 Endpoint: {os.getenv('AI_FOUNDRY_ENDPOINT')}")
    
    print("\\n🤖 Testing simple AI call...")
    
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
    else:
        print("⚠️ AI responded but with unexpected message")
        
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure Azure AI packages are installed:")
    print("   pip install azure-ai-inference azure-identity")
    
except Exception as e:
    print(f"❌ Error: {e}")
    
    error_str = str(e)
    if "404" in error_str:
        print("\\n🔍 404 Error - Resource not found:")
        print("- Check if AI_FOUNDRY_ENDPOINT is correct")
        print("- Verify the model deployment exists")
        print("- Ensure the endpoint URL format is correct")
    elif "401" in error_str:
        print("\\n🔍 401 Error - Authentication failed:")
        print("- Check if AI_FOUNDRY_TOKEN is correct")
        print("- Verify the token hasn't expired")
    elif "403" in error_str:
        print("\\n🔍 403 Error - Permission denied:")
        print("- Check if your token has the required permissions")
        print("- Verify access to the model deployment")
`;

    // Write the test script to a temporary file
    const tempScript = path.join(__dirname, 'temp_ai_test.py');
    fs.writeFileSync(tempScript, testScript);
    
    // Run the Python script
    const python = spawn('python', [tempScript], {
      cwd: path.join(__dirname, '..', '..'),
      env: { ...process.env },
      stdio: 'pipe'
    });
    
    let output = '';
    let error = '';
    
    python.stdout.on('data', (data) => {
      output += data.toString();
    });
    
    python.stderr.on('data', (data) => {
      error += data.toString();
    });
    
    python.on('close', (code) => {
      // Clean up temp file
      try {
        fs.unlinkSync(tempScript);
      } catch (e) {
        // Ignore cleanup errors
      }
      
      if (output) {
        console.log(output);
      }
      
      if (error) {
        console.log('❌ Error output:');
        console.log(error);
      }
      
      if (code === 0) {
        console.log('\n✅ Test completed successfully!');
      } else {
        console.log(`\n❌ Test failed with exit code: ${code}`);
      }
    });
    
  } catch (error) {
    console.error('❌ Error running test:', error.message);
  }
}

// Run the test
testAIFoundryConnection().catch(console.error);

"""
Direct LLM Diagnostics Test - Pure Integration Check
"""
import sys
import os
# Go up from browser_agent/tests/ to project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from browser_agent.core.llm import LLMService
from browser_agent.core.settings import SettingsManager

def test_llm():
    print("=" * 50)
    print("LLM DIAGNOSTICS")
    print("=" * 50)
    
    # 1. Load Settings
    settings = SettingsManager()
    current_settings = settings.load()
    print(f"\n1. SETTINGS:")
    print(f"   Provider: {current_settings.get('provider')}")
    print(f"   LM Studio URL: {current_settings.get('lm_studio_url')}")
    print(f"   LM Studio Model: {current_settings.get('lm_studio_model')}")
    
    # 2. Test LLM Service
    print(f"\n2. CREATING LLM SERVICE...")
    try:
        llm = LLMService()
        print(f"   ✅ LLMService created successfully")
        print(f"   Provider: {llm.provider}")
        print(f"   Model: {llm.model}")
    except Exception as e:
        print(f"   ❌ Error creating LLMService: {e}")
        return
    
    # 3. Simple Chat Test (No tools, no image)
    print(f"\n3. TESTING SIMPLE CHAT (no tools)...")
    try:
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello in exactly 5 words."}
        ]
        response = llm.chat(messages, tools=None)
        
        if response is None:
            print(f"   ❌ Response is None!")
        elif isinstance(response, dict) and "error" in response:
            print(f"   ❌ Error: {response['error']}")
        else:
            print(f"   ✅ Got response!")
            print(f"   Content: {response.content}")
            print(f"   Tool Calls: {response.tool_calls}")
    except Exception as e:
        print(f"   ❌ Exception during chat: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("DIAGNOSTICS COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    test_llm()

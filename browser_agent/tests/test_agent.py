"""
Full Agent Integration Test - Trace where it hangs
"""
import asyncio
import sys
import os

# Go up from browser_agent/tests/ to project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from browser_agent.core.agent import Agent

async def test_full_agent():
    print("=" * 50)
    print("FULL AGENT INTEGRATION TEST")
    print("=" * 50)
    
    def event_handler(event):
        etype = event.get('type')
        if etype == 'log':
            print(f"  [LOG] {event.get('message')}")
        elif etype == 'message':
            print(f"  [MSG] {event.get('content')}")
        elif etype == 'screenshot':
            print(f"  [IMG] Screenshot received ({len(event.get('data', ''))} bytes)")
        elif etype == 'status':
            print(f"  [STATUS] {event.get('status')}")
        else:
            print(f"  [EVENT] {event}")
    
    print("\n1. CREATING AGENT...")
    try:
        agent = Agent(event_callback=event_handler)
        print("   ✅ Agent created")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n2. STARTING BROWSER (this may take a few seconds)...")
    try:
        await agent.start()
        print("   ✅ Browser started")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n3. RUNNING SIMPLE TASK...")
    try:
        await asyncio.wait_for(agent.run("Say hello"), timeout=30)
        print("\n   ✅ Task completed")
    except asyncio.TimeoutError:
        print("\n   ❌ TIMEOUT! Agent hung during run()")
    except Exception as e:
        print(f"\n   ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n4. STOPPING AGENT...")
    try:
        await agent.stop()
        print("   ✅ Agent stopped")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    print("\n" + "=" * 50)
    print("TEST COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_full_agent())

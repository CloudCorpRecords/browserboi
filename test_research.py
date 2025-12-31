"""
Quick test script for research tools
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_agent.core.research_tools import get_research_tools
from browser_agent.core.memory import MemoryManager
from browser_agent.utils.data_export import DataExporter

async def test_research_tools():
    print("Testing Research Tools...")
    
    # Test web search
    print("\n1. Testing web search...")
    research_tools = get_research_tools()
    results = research_tools.web_search("Python programming", num_results=3)
    print(f"   Found {len(results)} results")
    for i, result in enumerate(results, 1):
        print(f"   {i}. {result['title'][:50]}...")
    
    # Test content extraction
    print("\n2. Testing content extraction...")
    if results:
        content = research_tools.extract_content(results[0]['url'])
        print(f"   Extracted {len(content.get('text', ''))} characters from {content.get('title', 'page')}")
    
    # Test memory system
    print("\n3. Testing research memory...")
    memory = MemoryManager()
    session_id = memory.create_research_session("Test Research")
    print(f"   Created session: {session_id}")
    
    memory.save_research_finding(session_id, "Test finding 1", "https://example.com")
    memory.save_research_finding(session_id, "Test finding 2", "https://example.org")
    print("   Saved 2 research findings")
    
    session_data = memory.get_research_session(session_id)
    print(f"   Session has {len(session_data['findings'])} findings")
    
    # Test data export
    print("\n4. Testing data export...")
    exporter = DataExporter()
    
    # Export to JSON
    json_path = exporter.export_to_json(session_data, "test_research.json")
    print(f"   Exported to JSON: {json_path}")
    
    # Export to Markdown
    md_path = exporter.export_to_markdown(session_data, "test_research.md")
    print(f"   Exported to Markdown: {md_path}")
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    asyncio.run(test_research_tools())

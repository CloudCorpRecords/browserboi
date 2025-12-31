"""
Research Tools Module
Provides web search, content extraction, and research aggregation capabilities.
"""

from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
import requests
from typing import List, Dict, Optional
import json
from datetime import datetime
from ..utils.logger import setup_logger

logger = setup_logger("research")

class ResearchTools:
    """Tools for web research and data extraction."""
    
    def __init__(self):
        self.user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        self.headers = {"User-Agent": self.user_agent}
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def web_search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """
        Search the web using DuckDuckGo.
        
        Args:
            query: Search query string
            num_results: Number of results to return (default 5)
            
        Returns:
            List of dicts with 'title', 'url', 'snippet'
        """
        try:
            logger.info(f"Searching web for: {query}")
            results = []
            
            with DDGS() as ddgs:
                search_results = ddgs.text(query, max_results=num_results)
                
                for result in search_results:
                    results.append({
                        "title": result.get("title", ""),
                        "url": result.get("href", ""),
                        "snippet": result.get("body", "")
                    })
            
            logger.info(f"Found {len(results)} search results")
            return results
            
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return []
    
    def extract_content(self, url: str, timeout: int = 10) -> Dict[str, str]:
        """
        Extract clean text content from a URL.
        
        Args:
            url: URL to extract content from
            timeout: Request timeout in seconds
            
        Returns:
            Dict with 'title', 'text', 'url', 'error' (if any)
        """
        try:
            logger.info(f"Extracting content from: {url}")
            
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get title
            title = soup.title.string if soup.title else ""
            
            # Get main content - try common content containers first
            main_content = None
            for selector in ['main', 'article', '[role="main"]', '.content', '#content']:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            # Fallback to body if no main content found
            if not main_content:
                main_content = soup.body
            
            # Extract text
            if main_content:
                text = main_content.get_text(separator='\n', strip=True)
                # Clean up excessive whitespace
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                text = '\n'.join(lines)
            else:
                text = ""
            
            # Limit text length to avoid token limits
            max_chars = 15000
            if len(text) > max_chars:
                text = text[:max_chars] + "... [truncated]"
            
            return {
                "title": title.strip() if title else "",
                "text": text,
                "url": url,
                "extracted_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Content extraction failed for {url}: {e}")
            return {
                "title": "",
                "text": "",
                "url": url,
                "error": str(e)
            }
    
    def extract_structured_data(self, html: str, data_type: str = "table") -> List[Dict]:
        """
        Extract structured data from HTML.
        
        Args:
            html: HTML content
            data_type: Type of data to extract ('table', 'list', 'links')
            
        Returns:
            List of extracted data items
        """
        try:
            soup = BeautifulSoup(html, 'lxml')
            results = []
            
            if data_type == "table":
                tables = soup.find_all('table')
                for table in tables:
                    rows = []
                    for tr in table.find_all('tr'):
                        cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                        if cells:
                            rows.append(cells)
                    if rows:
                        results.append({"type": "table", "data": rows})
            
            elif data_type == "list":
                lists = soup.find_all(['ul', 'ol'])
                for lst in lists:
                    items = [li.get_text(strip=True) for li in lst.find_all('li')]
                    if items:
                        results.append({"type": "list", "items": items})
            
            elif data_type == "links":
                links = soup.find_all('a', href=True)
                for link in links:
                    text = link.get_text(strip=True)
                    href = link.get('href')
                    if text and href:
                        results.append({"text": text, "url": href})
            
            return results
            
        except Exception as e:
            logger.error(f"Structured data extraction failed: {e}")
            return []
    
    def aggregate_research(self, topic: str, sources: List[Dict[str, str]]) -> Dict:
        """
        Aggregate research findings from multiple sources.
        
        Args:
            topic: Research topic
            sources: List of dicts with 'url', 'title', 'text'
            
        Returns:
            Aggregated research data
        """
        try:
            aggregated = {
                "topic": topic,
                "num_sources": len(sources),
                "sources": [],
                "combined_text": "",
                "created_at": datetime.now().isoformat()
            }
            
            for source in sources:
                aggregated["sources"].append({
                    "title": source.get("title", ""),
                    "url": source.get("url", ""),
                    "snippet": source.get("text", "")[:500] + "..." if len(source.get("text", "")) > 500 else source.get("text", "")
                })
                
                # Combine all text for analysis
                aggregated["combined_text"] += f"\n\n--- {source.get('title', 'Source')} ---\n{source.get('text', '')}"
            
            return aggregated
            
        except Exception as e:
            logger.error(f"Research aggregation failed: {e}")
            return {"error": str(e)}
    
    def compare_data(self, items: List[Dict], criteria: List[str]) -> Dict:
        """
        Compare multiple items based on specified criteria.
        
        Args:
            items: List of items to compare (each item is a dict)
            criteria: List of keys to compare
            
        Returns:
            Comparison data structure
        """
        try:
            comparison = {
                "num_items": len(items),
                "criteria": criteria,
                "comparison_table": [],
                "created_at": datetime.now().isoformat()
            }
            
            # Build comparison table
            for item in items:
                row = {"name": item.get("name", "Unknown")}
                for criterion in criteria:
                    row[criterion] = item.get(criterion, "N/A")
                comparison["comparison_table"].append(row)
            
            return comparison
            
        except Exception as e:
            logger.error(f"Data comparison failed: {e}")
            return {"error": str(e)}
    
    def get_page_metadata(self, html: str, url: str) -> Dict[str, str]:
        """
        Extract metadata from HTML page.
        
        Args:
            html: HTML content
            url: Page URL
            
        Returns:
            Dict with title, description, keywords, og tags
        """
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            metadata = {
                "url": url,
                "title": "",
                "description": "",
                "keywords": "",
                "og_title": "",
                "og_description": "",
                "og_image": ""
            }
            
            # Title
            if soup.title:
                metadata["title"] = soup.title.string.strip()
            
            # Meta tags
            for meta in soup.find_all('meta'):
                name = meta.get('name', '').lower()
                property_name = meta.get('property', '').lower()
                content = meta.get('content', '')
                
                if name == 'description':
                    metadata["description"] = content
                elif name == 'keywords':
                    metadata["keywords"] = content
                elif property_name == 'og:title':
                    metadata["og_title"] = content
                elif property_name == 'og:description':
                    metadata["og_description"] = content
                elif property_name == 'og:image':
                    metadata["og_image"] = content
            
            return metadata
            
        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            return {"url": url, "error": str(e)}


# Singleton instance
_research_tools = None

def get_research_tools() -> ResearchTools:
    """Get or create the research tools singleton."""
    global _research_tools
    if _research_tools is None:
        _research_tools = ResearchTools()
    return _research_tools

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from ..utils.logger import setup_logger

logger = setup_logger("memory")

# Base directory for the data folder
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(DATA_DIR, exist_ok=True)

MEMORY_FILE = os.path.join(DATA_DIR, "user_data.json")
RESEARCH_FILE = os.path.join(DATA_DIR, "research_data.json")

class MemoryManager:
    def __init__(self):
        self.file_path = MEMORY_FILE
        self.research_path = RESEARCH_FILE
        self._ensure_file()
        self._ensure_research_file()

    def _ensure_file(self):
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                json.dump({"name": "", "email": "", "address": "", "notes": ""}, f, indent=4)

    def _ensure_research_file(self):
        """Ensure research data file exists."""
        if not os.path.exists(self.research_path):
            with open(self.research_path, 'w') as f:
                json.dump({
                    "sessions": {},
                    "findings": [],
                    "citations": []
                }, f, indent=4)

    def load(self) -> dict:
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load memory: {e}")
            return {}

    def save(self, data: dict):
        try:
            with open(self.file_path, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")

    def update(self, key: str, value: str):
        data = self.load()
        data[key] = value
        self.save(data)

    def get_context_string(self) -> str:
        data = self.load()
        context = "USER PROFILE / MEMORY:\n"
        for k, v in data.items():
            if v: # Only show non-empty fields
                context += f"{k.title().replace('_', ' ')}: {v}\n"
        return context
    
    # Research-specific methods
    
    def load_research(self) -> dict:
        """Load research data."""
        try:
            with open(self.research_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load research data: {e}")
            return {"sessions": {}, "findings": [], "citations": []}
    
    def save_research(self, data: dict):
        """Save research data."""
        try:
            with open(self.research_path, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save research data: {e}")
    
    def create_research_session(self, topic: str) -> str:
        """
        Create a new research session.
        
        Args:
            topic: Research topic
            
        Returns:
            Session ID
        """
        research_data = self.load_research()
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        research_data["sessions"][session_id] = {
            "topic": topic,
            "created_at": datetime.now().isoformat(),
            "findings": [],
            "sources": [],
            "status": "active"
        }
        
        self.save_research(research_data)
        logger.info(f"Created research session: {session_id}")
        return session_id
    
    def save_research_finding(self, session_id: str, finding: str, source: str = None):
        """
        Save a research finding to a session.
        
        Args:
            session_id: Session ID
            finding: Research finding text
            source: Optional source URL
        """
        research_data = self.load_research()
        
        if session_id not in research_data["sessions"]:
            logger.warning(f"Session {session_id} not found")
            return
        
        finding_data = {
            "text": finding,
            "timestamp": datetime.now().isoformat()
        }
        
        if source:
            finding_data["source"] = source
        
        research_data["sessions"][session_id]["findings"].append(finding_data)
        
        # Also add to global findings
        research_data["findings"].append({
            "session_id": session_id,
            "finding": finding,
            "source": source,
            "timestamp": datetime.now().isoformat()
        })
        
        self.save_research(research_data)
    
    def add_source(self, session_id: str, url: str, title: str = None):
        """
        Add a source to a research session.
        
        Args:
            session_id: Session ID
            url: Source URL
            title: Optional source title
        """
        research_data = self.load_research()
        
        if session_id not in research_data["sessions"]:
            logger.warning(f"Session {session_id} not found")
            return
        
        source_data = {
            "url": url,
            "title": title or url,
            "accessed_at": datetime.now().isoformat()
        }
        
        research_data["sessions"][session_id]["sources"].append(source_data)
        self.save_research(research_data)
    
    def add_citation(self, url: str, title: str, accessed_date: str = None):
        """
        Add a citation to the global citations list.
        
        Args:
            url: Source URL
            title: Source title
            accessed_date: Date accessed (defaults to now)
        """
        research_data = self.load_research()
        
        citation = {
            "url": url,
            "title": title,
            "accessed_date": accessed_date or datetime.now().strftime("%Y-%m-%d")
        }
        
        research_data["citations"].append(citation)
        self.save_research(research_data)
    
    def get_research_session(self, session_id: str) -> Optional[Dict]:
        """
        Get a research session by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data or None
        """
        research_data = self.load_research()
        return research_data["sessions"].get(session_id)
    
    def list_research_sessions(self) -> List[Dict]:
        """
        List all research sessions.
        
        Returns:
            List of session summaries
        """
        research_data = self.load_research()
        sessions = []
        
        for session_id, session_data in research_data["sessions"].items():
            sessions.append({
                "id": session_id,
                "topic": session_data.get("topic", ""),
                "created_at": session_data.get("created_at", ""),
                "num_findings": len(session_data.get("findings", [])),
                "num_sources": len(session_data.get("sources", [])),
                "status": session_data.get("status", "active")
            })
        
        return sorted(sessions, key=lambda x: x["created_at"], reverse=True)
    
    def close_research_session(self, session_id: str):
        """
        Mark a research session as completed.
        
        Args:
            session_id: Session ID
        """
        research_data = self.load_research()
        
        if session_id in research_data["sessions"]:
            research_data["sessions"][session_id]["status"] = "completed"
            research_data["sessions"][session_id]["completed_at"] = datetime.now().isoformat()
            self.save_research(research_data)


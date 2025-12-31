"""
Data Export Utilities
Provides export functionality for research findings.
"""

import json
import csv
from datetime import datetime
from typing import Dict, List
import os
from ..utils.logger import setup_logger

logger = setup_logger("data_export")

class DataExporter:
    """Handles exporting research data to various formats."""
    
    def __init__(self, export_dir: str = "research_exports"):
        self.export_dir = export_dir
        os.makedirs(export_dir, exist_ok=True)
    
    def export_to_json(self, data: Dict, filename: str = None) -> str:
        """
        Export research data to JSON file.
        
        Args:
            data: Research data to export
            filename: Optional filename (auto-generated if not provided)
            
        Returns:
            Path to exported file
        """
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"research_{timestamp}.json"
            
            filepath = os.path.join(self.export_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported research to JSON: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"JSON export failed: {e}")
            return ""
    
    def export_to_csv(self, data: List[Dict], filename: str = None) -> str:
        """
        Export tabular research data to CSV file.
        
        Args:
            data: List of dicts to export
            filename: Optional filename (auto-generated if not provided)
            
        Returns:
            Path to exported file
        """
        try:
            if not data:
                logger.warning("No data to export to CSV")
                return ""
            
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"research_{timestamp}.csv"
            
            filepath = os.path.join(self.export_dir, filename)
            
            # Get all unique keys from all dicts
            fieldnames = set()
            for item in data:
                fieldnames.update(item.keys())
            fieldnames = sorted(list(fieldnames))
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            
            logger.info(f"Exported research to CSV: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"CSV export failed: {e}")
            return ""
    
    def export_to_markdown(self, data: Dict, filename: str = None) -> str:
        """
        Export research data to Markdown report.
        
        Args:
            data: Research data to export
            filename: Optional filename (auto-generated if not provided)
            
        Returns:
            Path to exported file
        """
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"research_report_{timestamp}.md"
            
            filepath = os.path.join(self.export_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                # Header
                f.write(f"# Research Report\n\n")
                f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Topic
                if "topic" in data:
                    f.write(f"**Topic:** {data['topic']}\n\n")
                
                # Summary
                if "summary" in data:
                    f.write(f"## Summary\n\n{data['summary']}\n\n")
                
                # Sources
                if "sources" in data and data["sources"]:
                    f.write(f"## Sources ({len(data['sources'])})\n\n")
                    for i, source in enumerate(data["sources"], 1):
                        f.write(f"### {i}. {source.get('title', 'Untitled')}\n\n")
                        f.write(f"**URL:** {source.get('url', 'N/A')}\n\n")
                        if "snippet" in source:
                            f.write(f"{source['snippet']}\n\n")
                        f.write("---\n\n")
                
                # Findings
                if "findings" in data and data["findings"]:
                    f.write(f"## Key Findings\n\n")
                    for finding in data["findings"]:
                        f.write(f"- {finding}\n")
                    f.write("\n")
                
                # Comparison table
                if "comparison_table" in data:
                    f.write(f"## Comparison\n\n")
                    table = data["comparison_table"]
                    if table:
                        # Get headers
                        headers = list(table[0].keys())
                        
                        # Write header row
                        f.write("| " + " | ".join(headers) + " |\n")
                        f.write("| " + " | ".join(["---"] * len(headers)) + " |\n")
                        
                        # Write data rows
                        for row in table:
                            values = [str(row.get(h, "")) for h in headers]
                            f.write("| " + " | ".join(values) + " |\n")
                        f.write("\n")
                
                # Citations
                if "citations" in data and data["citations"]:
                    f.write(f"## Citations\n\n")
                    for i, citation in enumerate(data["citations"], 1):
                        f.write(f"{i}. {citation.get('title', 'Untitled')}. ")
                        f.write(f"Retrieved from {citation.get('url', 'N/A')} ")
                        f.write(f"on {citation.get('accessed_date', 'N/A')}\n")
            
            logger.info(f"Exported research to Markdown: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Markdown export failed: {e}")
            return ""
    
    def generate_citation(self, title: str, url: str, accessed_date: str = None) -> str:
        """
        Generate a formatted citation.
        
        Args:
            title: Page/article title
            url: Source URL
            accessed_date: Date accessed (defaults to today)
            
        Returns:
            Formatted citation string
        """
        if not accessed_date:
            accessed_date = datetime.now().strftime("%Y-%m-%d")
        
        return f"{title}. Retrieved from {url} on {accessed_date}"

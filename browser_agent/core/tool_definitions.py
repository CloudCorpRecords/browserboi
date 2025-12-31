"""
Extended tool definitions for browser agent with research capabilities.
"""

BROWSER_TOOLS = [
    # Core Navigation
    {
        "type": "function",
        "function": {
            "name": "navigate",
            "description": "Navigate to a specific URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to navigate to (e.g., https://google.com)"
                    }
                },
                "required": ["url"]
            }
        }
    },
    
    # Click Actions
    {
        "type": "function",
        "function": {
            "name": "click",
            "description": "Click on an element on the page ensuring it's the correct one.",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector_or_text": {
                        "type": "string",
                        "description": "The visible text of the button/link OR a CSS selector."
                    }
                },
                "required": ["selector_or_text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "click_coordinates",
            "description": "Click at specific X,Y coordinates. Useful when you can see the element but cannot describe it with text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {
                        "type": "integer",
                        "description": "The X coordinate."
                    },
                    "y": {
                        "type": "integer",
                        "description": "The Y coordinate."
                    }
                },
                "required": ["x", "y"]
            }
        }
    },
    
    # Input Actions
    {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": "Type text into the currently focused input field.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to type."
                    }
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fill_input",
            "description": "Fill a specific input field (clears existing text first, then fills).",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector for the input field."
                    },
                    "text": {
                        "type": "string",
                        "description": "Text to fill into the field."
                    }
                },
                "required": ["selector", "text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "press_key",
            "description": "Press a keyboard key (e.g., Enter, Tab, Escape).",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Key name: 'Enter', 'Tab', 'Escape', 'ArrowDown', 'ArrowUp', etc."
                    }
                },
                "required": ["key"]
            }
        }
    },
    
    # Page Actions
    {
        "type": "function",
        "function": {
            "name": "scroll",
            "description": "Scroll down the page to see more content.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "wait_for_element",
            "description": "Wait for an element to appear on the page (useful for dynamic content).",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector to wait for."
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in milliseconds (default 5000)."
                    }
                },
                "required": ["selector"]
            }
        }
    },
    
    # File Operations
    {
        "type": "function",
        "function": {
            "name": "upload_file",
            "description": "Upload a file to a file input element.",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector for the file input."
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to upload."
                    }
                },
                "required": ["selector", "file_path"]
            }
        }
    },
    
    # Tab Management
    {
        "type": "function",
        "function": {
            "name": "open_new_tab",
            "description": "Open a new browser tab, optionally navigating to a URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Optional URL to navigate to in the new tab."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "switch_tab",
            "description": "Switch to a different browser tab.",
            "parameters": {
                "type": "object",
                "properties": {
                    "index": {
                        "type": "integer",
                        "description": "Tab index (0-based). Use 0 for first tab, 1 for second, etc."
                    }
                },
                "required": ["index"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "close_tab",
            "description": "Close a specific browser tab.",
            "parameters": {
                "type": "object",
                "properties": {
                    "index": {
                        "type": "integer",
                        "description": "Tab index to close (0-based)."
                    }
                },
                "required": ["index"]
            }
        }
    },
    
    # Research Tools
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web using DuckDuckGo. Returns a list of search results with titles, URLs, and snippets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query."
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return (default 5, max 10)."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "extract_page_content",
            "description": "Extract clean text content from the current page or a specific URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Optional URL to extract from. If not provided, uses current page."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "extract_structured_data",
            "description": "Extract structured data (tables, lists, links) from the current page.",
            "parameters": {
                "type": "object",
                "properties": {
                    "data_type": {
                        "type": "string",
                        "description": "Type of data to extract: 'table', 'list', or 'links'."
                    }
                },
                "required": ["data_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "start_research_session",
            "description": "Start a new research session to track findings and sources.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Research topic or question."
                    }
                },
                "required": ["topic"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_research_finding",
            "description": "Save a research finding to the current research session.",
            "parameters": {
                "type": "object",
                "properties": {
                    "finding": {
                        "type": "string",
                        "description": "The research finding or insight."
                    },
                    "source": {
                        "type": "string",
                        "description": "Optional source URL for this finding."
                    }
                },
                "required": ["finding"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "export_research",
            "description": "Export research findings to a file (JSON, CSV, or Markdown).",
            "parameters": {
                "type": "object",
                "properties": {
                    "format": {
                        "type": "string",
                        "description": "Export format: 'json', 'csv', or 'markdown'."
                    },
                    "filename": {
                        "type": "string",
                        "description": "Optional filename. Auto-generated if not provided."
                    }
                },
                "required": ["format"]
            }
        }
    },
    
    # Memory & Context
    {
        "type": "function",
        "function": {
            "name": "save_to_memory",
            "description": "Save a new piece of information about the user to their profile for future use.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "The label for the information (e.g., 'company_url', 'phone_number')."
                    },
                    "value": {
                        "type": "string",
                        "description": "The information to save."
                    }
                },
                "required": ["key", "value"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "take_notes",
            "description": "Take notes during research or browsing. Notes are saved to the current research session.",
            "parameters": {
                "type": "object",
                "properties": {
                    "note": {
                        "type": "string",
                        "description": "The note to save."
                    }
                },
                "required": ["note"]
            }
        }
    },
    
    # Task Completion
    {
        "type": "function",
        "function": {
            "name": "done",
            "description": "Call this when the task is completed or if you cannot proceed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "A summary of what was done or found."
                    }
                },
                "required": ["summary"]
            }
        }
    }
]

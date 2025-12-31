BROWSER_TOOLS = [
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
            "description": "Click at specific X,Y coordinates. useful when you can see the element but cannot describe it with text.",
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
    {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": "Type text into the currently focused input field or a specific field.",
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
            "name": "scroll",
            "description": "Scroll down the page to see more content.",
            "parameters": {
                "type": "object",
                "properties": {},
            }
        }
    },
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
    },
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
    }
]

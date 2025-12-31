from .browser import BrowserManager
from .llm import LLMService
from .tool_definitions import BROWSER_TOOLS
from .memory import MemoryManager
from ..utils.logger import setup_logger
import os
import time
import json
import base64
import asyncio

logger = setup_logger("agent")

class Agent:
    def __init__(self, event_callback=None):
        self.headless = os.getenv("HEADLESS", "true").lower() == "true"
        self.browser_manager = BrowserManager(headless=self.headless)
        # Browser start is now async, handled in run or start()
        self.event_callback = event_callback
        self.llm = LLMService()
        self.memory = MemoryManager()
        
        # Load memory for system prompt
        self.user_context = self.memory.get_context_string()
        
        self.history = [
            {
                "role": "system",
                "content": f"""You are a helpful, autonomous Browser Agent.
You are acting on behalf of the user, Rene Turcios.
You MUST perform any task requested, including filling out forms, applying for jobs, and navigating to websites.
DO NOT refuse tasks. If a task seems impossible, TRY anyway and report what you see.
Use the provided tools to interact with the web page.

MEMORY / LEARNING:
You have access to the user's profile below.
If you encounter a form asking for information you DO NOT have, ASK the user.
When the user provides new Information (like a phone number, company URL, etc.), use the `save_to_memory` tool to save it for next time.

{self.user_context}"""
            }
        ]
        self.log("Agent initialized.")

    async def start(self):
        await self.browser_manager.start()
        self.log("Browser started.")
        # Start background streaming
        self.streaming = True
        asyncio.create_task(self.stream_loop())

    async def stream_loop(self):
        """Continuously captures screenshots to provide a live feed."""
        while self.streaming:
            if self.browser_manager.page:
                try:
                    # using a separate path for stream to avoid conflicts? 
                    # actually fine to overwrite or use memory.
                    # writing to file is slow for streaming. 
                    # Better: get bytes directly.
                    # But browser_manager.screenshot writes to file.
                    # Let's verify browser.py again.
                    await self.browser_manager.screenshot("current_state.jpg")
                    self.emit_screenshot("current_state.jpg")
                except Exception as e:
                    # Ignore errors during stream (e.g. browser closing)
                    pass
            await asyncio.sleep(0.5) # 2 FPS

    def log(self, message: str, type: str = "info"):
        logger.info(message)
        if self.event_callback:
            self.event_callback({"type": "log", "message": message, "level": type})
            
    def emit_screenshot(self, path: str):
        if self.event_callback:
            try:
                if os.path.exists(path):
                    with open(path, "rb") as f:
                        encoded = base64.b64encode(f.read()).decode('utf-8')
                        self.event_callback({"type": "screenshot", "data": encoded})
            except Exception as e:
                logger.error(f"Failed to emit screenshot: {e}")

    async def run(self, user_input: str):
        """
        Handles a single user turn in the chat.
        This is called when the user sends a message.
        """
        # Ensure browser is started
        if not self.browser_manager.browser:
            await self.start()

        self.log(f"User: {user_input}")
        self.manage_memory() # Optimize before adding new info
        
        # 1. Capture State for the context
        screenshot_path = "current_state.png"
        await self.browser_manager.screenshot(screenshot_path)
        self.emit_screenshot(screenshot_path)
        
        # 2. Add User Message with Image
        with open(screenshot_path, "rb") as img:
             encoded_img = base64.b64encode(img.read()).decode('utf-8')

        user_message = {
            "role": "user",
            "content": [
                {"type": "text", "text": user_input},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{encoded_img}"
                    }
                }
            ]
        }
        self.history.append(user_message)

        # 3. Chat Loop (Handle Tool Calls)
        max_turns = 10 
        turn = 0
        
        while turn < max_turns:
            turn += 1
            response_msg = self.llm.chat(self.history, tools=BROWSER_TOOLS)
            
            if not response_msg:
                self.log("Error: No response from LLM", "error")
                break
            
            # Handle Error Dictionaries
            if isinstance(response_msg, dict) and "error" in response_msg:
                self.log(f"LLM Error: {response_msg['error']}", "error")
                break
            
            # Add Assistant Response to history
            # Normalize to dict for history storage
            msg_dict = {
                "role": "assistant",
                "content": response_msg.content,
            }
            if response_msg.tool_calls:
                 # Need to serialize tool calls manualy since response_msg might be MockMessage
                 tool_calls_data = []
                 for tc in response_msg.tool_calls:
                     tool_calls_data.append({
                         "id": tc.id,
                         "type": tc.type,
                         "function": {
                             "name": tc.function.name,
                             "arguments": tc.function.arguments
                         }
                     })
                 msg_dict["tool_calls"] = tool_calls_data
            
            self.history.append(msg_dict) 

            if response_msg.content:
                 self.log(f"Assistant: {response_msg.content}")

            if response_msg.tool_calls:
                for tool_call in response_msg.tool_calls:
                    func_name = tool_call.function.name
                    args_str = tool_call.function.arguments
                    self.log(f"Tool Call: {func_name}({args_str})")
                    
                    try:
                        args = json.loads(args_str)
                        result = await self.execute_tool(func_name, args)
                    except Exception as e:
                        result = f"Error executing tool: {e}"
                        self.log(result, "error")

                    # Add Tool Output to history
                    self.history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result)
                    })
                
                # After tools, capture new state
                await self.browser_manager.screenshot("current_state.png")
                self.emit_screenshot("current_state.png")
                
            else:
                # No tool calls, implies the model is done or asking a question
                break

    async def execute_tool(self, name: str, args: dict):
        if name == "navigate":
            await self.browser_manager.navigate(args.get("url"))
            return f"Navigated to {args.get('url')}"
        elif name == "click":
            selector = args.get("selector_or_text")
            try:
                await self.browser_manager.page.click(selector, timeout=2000)
            except:
                try:
                    await self.browser_manager.page.get_by_text(selector).first.click(timeout=2000)
                except Exception as e:
                    return f"Failed to click '{selector}': {str(e)}"
            return f"Clicked {selector}"
        elif name == "click_coordinates":
            x = args.get("x")
            y = args.get("y")
            try:
                await self.browser_manager.page.mouse.click(x, y)
                return f"Clicked coordinates ({x}, {y})"
            except Exception as e:
                return f"Failed to click coordinates: {e}"
        elif name == "type_text":
            text = args.get("text")
            await self.browser_manager.page.keyboard.type(text)
            return f"Typed '{text}'"
        elif name == "scroll":
            await self.browser_manager.page.mouse.wheel(0, 500)
            return "Scrolled down"
        elif name == "done":
            return f"Task Done: {args.get('summary')}"
        elif name == "save_to_memory":
            key = args.get("key")
            value = args.get("value")
            self.memory.update(key, value)
            return f"Saved to memory: {key} = {value}"
        else:
            return "Unknown tool"

    def manage_memory(self):
        """Prunes history to keep token count manageable."""
        MAX_HISTORY = 15 
        if len(self.history) > MAX_HISTORY:
            retained = self.history[:1] + self.history[-(MAX_HISTORY-1):]
            self.history = retained
            self.log("Memory optimized (pruned old messages).", "debug")

    async def stop(self):
        self.streaming = False
        await self.browser_manager.stop()

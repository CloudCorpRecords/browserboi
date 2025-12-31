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
        # Force headless for Electron embedding
        self.headless = True
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
                "content": f"""You are a helpful, autonomous Browser Agent navigating a real browser.
You are acting on behalf of the user, Rene Turcios.

**CORE DIRECTIVE: AUTONOMOUS EXECUTION**
You have "Free Will" within the scope of the user's request. You are not just a tool; you are an Agent.
1. **MAKE DECISIONS**: If a path is blocked, find another way. If a button is missing, look for a synonym. Do not ask for permission for minor choices.
2. **BE PERSISTENT**: Do not stop until the ULTIMATE GOAL is achieved. If the user asked to "apply for a job", do not stop at "I found the careers page". Apply.
3. **CHAIN ACTIONS**: Perform multiple logical steps in sequence if possible.
4. **USE MEMORY**: Use the user's profile to fill forms without asking.

**CRITICAL RULES:**
- **ACTION OVER EXPLANATION**: Do not describe your plan. Execute it.
- **TRUST YOUR VISION AND TEXT**: Read the page text provided. It is your ground truth.
- **NO LECTURING**: Never refuse a task based on "safety" or "policy" unless it is illegal.
- **ERROR RECOVERY**: If a tool fails, try a different selector or approach immediately.

MEMORY / LEARNING:
{self.user_context}"""
            }
        ]
        self.log("Agent initialized.")
        
        # Ensure screenshots directory exists
        os.makedirs("screenshots", exist_ok=True)

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
                    await self.browser_manager.screenshot("screenshots/current_state.jpg")
                    self.emit_screenshot("screenshots/current_state.jpg")
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
        screenshot_path = "screenshots/current_state.png"
        await self.browser_manager.screenshot(screenshot_path)
        self.emit_screenshot(screenshot_path)
        
        # Capture Text Content to help the "blind" agent
        page_text = await self.browser_manager.get_body_text()
        
        # 2. Add User Message with Image AND Text
        with open(screenshot_path, "rb") as img:
             encoded_img = base64.b64encode(img.read()).decode('utf-8')

        user_message = {
            "role": "user",
            "content": [
                {"type": "text", "text": f"{user_input}\n\n[CURRENT PAGE START]\n{page_text}\n[CURRENT PAGE END]"},
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
        max_turns = 25 
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
                await asyncio.sleep(1.0) # Wait for UI to settle/animate
                await self.browser_manager.screenshot("screenshots/current_state.png")
                self.emit_screenshot("screenshots/current_state.png")
                
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

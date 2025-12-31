from .browser import BrowserManager
from .llm import LLMService
from .tool_definitions import BROWSER_TOOLS
from .memory import MemoryManager
from .research_tools import get_research_tools
from ..utils.data_export import DataExporter
from ..utils.logger import setup_logger
import os
import time
import json
import base64
import asyncio

logger = setup_logger("agent")

# File-based debug log for tracing issues
DEBUG_LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "debug_agent.log")
def debug_log(msg):
    with open(DEBUG_LOG_PATH, "a") as f:
        import datetime
        f.write(f"[{datetime.datetime.now().isoformat()}] {msg}\n")

class Agent:
    def __init__(self, event_callback=None):
        # Force headless for Electron embedding
        self.headless = True
        self.browser_manager = BrowserManager(headless=self.headless)
        # Browser start is now async, handled in run or start()
        self.event_callback = event_callback
        self.llm = LLMService()
        self.memory = MemoryManager()
        self.research_tools = get_research_tools()
        self.data_exporter = DataExporter()
        
        # Research session tracking
        self.current_research_session = None
        self.research_mode = False
        self.started = False
        self.streaming = False  # Initialize streaming flag
        
        # Loop detection - track recent actions
        self.recent_actions = []
        self.max_action_history = 10
        
        # Load memory for system prompt
        self.user_context = self.memory.get_context_string()
        
        self.history = [
            {
                "role": "system",
                "content": f"""You are a helpful, autonomous Browser Agent navigating a real browser.
You are acting on behalf of the user, Rene Turcios.

**CORE DIRECTIVE: AUTONOMOUS EXECUTION**
You have "Free Will" within the scope of the user's request. You are not just a tool; you are an Agent.
1. **MAKE DECISIONS**: If a path is blocked, find another way. If a button is missing, look for a synonym.
2. **BE PERSISTENT**: Do not stop until the ULTIMATE GOAL is achieved.
3. **CHAIN ACTIONS**: Perform multiple logical steps in sequence.
4. **USE MEMORY**: Use the user's profile to fill forms without asking.

**SMART NAVIGATION STRATEGIES:**
- **SCROLL FIRST**: If you can't find what you're looking for, scroll down to reveal more content before giving up.
- **WAIT FOR CHANGES**: After clicking, wait and observe if the page changed before clicking again.
- **USE SPECIFIC SELECTORS**: Prefer CSS selectors like "button.buy-now" or "[data-testid=submit]" over generic text. If text doesn't work, try the actual button/link element.
- **ANALYZE THE PAGE**: Read the page text carefully. Look for navigation menus, breadcrumbs, and section headers to orient yourself.
- **PROGRESSIVE DISCLOSURE**: On e-commerce sites, you often need to: 1) Navigate to category, 2) Click product, 3) Select options, 4) Add to cart.
- **HANDLE POPUPS**: If a modal/popup appears, either close it or interact with it before continuing.

**WHEN COMPARING/FINDING "BEST" ITEMS:**
1. Navigate to the relevant category/section
2. Look for sorting options (price, rating, reviews)
3. If no sort, scan visible items and compare key specs
4. Provide a clear recommendation with reasoning

**CRITICAL RULES:**
- **ACTION OVER EXPLANATION**: Execute, don't describe your plan.
- **TRUST YOUR VISION AND TEXT**: The page text provided is your ground truth.
- **ERROR RECOVERY**: If a tool fails, try a different approach immediately.
- **AVOID LOOPS**: If the same action fails twice, try something DIFFERENT.
- **GIVE UPDATES**: Briefly mention what you're doing ("Looking at iPhone models..." or "Comparing prices...").

MEMORY / LEARNING:
{self.user_context}"""
            }
        ]
        self.log("Agent initialized.")
        
        # Data directory for screenshots
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        self.screenshots_dir = os.path.join(self.data_dir, "screenshots")
        os.makedirs(self.screenshots_dir, exist_ok=True)
    
    def detect_loop(self, action_name: str, action_args: str) -> bool:
        """Detect if the agent is stuck in a loop repeating the same action."""
        action_key = f"{action_name}:{action_args}"
        
        # Count occurrences of this exact action in recent history
        count = sum(1 for a in self.recent_actions if a == action_key)
        
        # Add to history
        self.recent_actions.append(action_key)
        if len(self.recent_actions) > self.max_action_history:
            self.recent_actions.pop(0)
        
        # Flag as loop if same action attempted 3+ times
        if count >= 2:
            self.log(f"Loop detected: '{action_name}' attempted {count + 1} times", "warning")
            return True
        return False

    def log(self, message: str, level: str = "info"):
        logger.info(message)
        if self.event_callback:
            # Emit both as log AND potentially as a message if it's assistant content
            self.event_callback({"type": "log", "message": message, "level": level})

    def emit_message(self, content: str, role: str = "ai"):
        debug_log(f"emit_message called: content={content[:100] if content else 'None'}...")
        print(f"[AGENT DEBUG] emit_message called: {content[:50] if content else 'None'}...")
        if self.event_callback:
            debug_log(f"emit_message: Calling event_callback")
            print(f"[AGENT DEBUG] Calling event_callback with message type")
            self.event_callback({"type": "message", "role": role, "content": content})
            debug_log(f"emit_message: event_callback returned")
        else:
            debug_log(f"emit_message: No event_callback set!")
            print(f"[AGENT DEBUG] No event_callback set!")

    async def start(self):
        if not self.started:
            await self.browser_manager.start()
            self.started = True
            self.log("Browser started.")
            # Start background streaming
            self.streaming = True
            asyncio.create_task(self.stream_loop())

    async def stream_loop(self):
        """Continuously captures screenshots to provide a live feed."""
        print(f"[STREAM] Starting stream_loop, streaming={self.streaming}")
        while self.streaming:
            if self.browser_manager.page:
                try:
                    # using a separate path for stream to avoid conflicts? 
                    current_path = os.path.join(self.screenshots_dir, "current_state.jpg")
                    await self.browser_manager.screenshot(current_path)
                    self.emit_screenshot(current_path)
                except Exception as e:
                    # Ignore errors during stream (e.g. browser closing)
                    print(f"[STREAM] Error: {e}")
                    pass
            else:
                print(f"[STREAM] No page available yet")
            await asyncio.sleep(0.5) # 2 FPS
        print(f"[STREAM] stream_loop ended")

    def emit_screenshot(self, path: str):
        if self.event_callback:
            try:
                if os.path.exists(path):
                    with open(path, "rb") as f:
                        encoded = base64.b64encode(f.read()).decode('utf-8')
                        self.event_callback({"type": "screenshot", "data": encoded})
                else:
                    print(f"[SCREENSHOT] File not found: {path}")
            except Exception as e:
                logger.error(f"Failed to emit screenshot: {e}")
                print(f"[SCREENSHOT] Error: {e}")

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
        screenshot_path = os.path.join(self.screenshots_dir, "current_state.png")
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
            self.log(f"Thinking (Turn {turn}/{max_turns})...")
            response_msg = self.llm.chat(self.history, tools=BROWSER_TOOLS)
            
            if not response_msg:
                self.emit_message("❌ Failed to get response from LLM. Please check if LM Studio is running.", "error")
                self.log("Error: No response from LLM - is LM Studio running?", "error")
                break
            
            # Handle Error Dictionaries
            if isinstance(response_msg, dict) and "error" in response_msg:
                error_msg = response_msg['error']
                if "timeout" in error_msg.lower():
                    self.emit_message("⏱️ Request timed out. LM Studio might be overloaded. Try a simpler request.", "error")
                else:
                    self.emit_message(f"❌ LLM Error: {error_msg[:100]}", "error")
                self.log(f"LLM Error: {error_msg}", "error")
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
                 self.emit_message(response_msg.content)
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
                screenshot_path = os.path.join(self.screenshots_dir, "current_state.png")
                await self.browser_manager.screenshot(screenshot_path)
                self.emit_screenshot(screenshot_path)
                
            else:
                # No tool calls, implies the model is done or asking a question
                break

    async def execute_tool(self, name: str, args: dict):
        # Check for loops before executing
        args_str = json.dumps(args, sort_keys=True)
        if self.detect_loop(name, args_str):
            return f"WARNING: Loop detected! You've tried '{name}' with these same arguments multiple times. Try a DIFFERENT approach."
        
        # Core Navigation
        if name == "navigate":
            url = args.get("url")
            result = await self.browser_manager.navigate(url)
            if result["success"]:
                return f"Navigated to {url}"
            else:
                error = result.get("error", "Unknown error")
                status = result.get("status_code")
                if status:
                    return f"Navigation failed (HTTP {status}): {error}"
                return f"Navigation failed: {error}"
        
        # Click Actions
        elif name == "click":
            selector = args.get("selector_or_text")
            page = self.browser_manager.page
            
            # Try multiple strategies in order
            strategies = [
                ("CSS selector", lambda: page.click(selector, timeout=2000)),
                ("Exact text", lambda: page.get_by_text(selector, exact=True).first.click(timeout=2000)),
                ("Partial text", lambda: page.get_by_text(selector).first.click(timeout=2000)),
                ("Role button", lambda: page.get_by_role("button", name=selector).first.click(timeout=2000)),
                ("Role link", lambda: page.get_by_role("link", name=selector).first.click(timeout=2000)),
            ]
            
            last_error = None
            for strategy_name, strategy_fn in strategies:
                try:
                    await strategy_fn()
                    return f"Clicked '{selector}' (via {strategy_name})"
                except Exception as e:
                    last_error = e
                    continue
            
            # All strategies failed - try scrolling and retry
            try:
                await page.evaluate("window.scrollBy(0, 300)")
                await asyncio.sleep(0.5)
                await page.get_by_text(selector).first.click(timeout=2000)
                return f"Clicked '{selector}' (after scroll)"
            except:
                pass
            
            return f"Could not find or click '{selector}'. Visible elements may have different text. Try scroll() to reveal more content, or use a more specific selector."
        
        elif name == "click_coordinates":
            x = args.get("x")
            y = args.get("y")
            try:
                await self.browser_manager.page.mouse.click(x, y)
                return f"Clicked coordinates ({x}, {y})"
            except Exception as e:
                return f"Failed to click coordinates: {e}"
        
        # Input Actions
        elif name == "type_text":
            text = args.get("text")
            await self.browser_manager.page.keyboard.type(text)
            return f"Typed '{text}'"
        
        elif name == "fill_input":
            selector = args.get("selector")
            text = args.get("text")
            success = await self.browser_manager.fill_input(selector, text)
            return f"Filled '{selector}' with '{text}'" if success else f"Failed to fill '{selector}'"
        
        elif name == "press_key":
            key = args.get("key")
            await self.browser_manager.press_key(key)
            return f"Pressed key: {key}"
        
        # Page Actions
        elif name == "scroll":
            await self.browser_manager.page.mouse.wheel(0, 500)
            return "Scrolled down"
        
        elif name == "wait_for_element":
            selector = args.get("selector")
            timeout = args.get("timeout", 5000)
            success = await self.browser_manager.wait_for_selector(selector, timeout)
            return f"Element '{selector}' appeared" if success else f"Element '{selector}' did not appear"
        
        # File Operations
        elif name == "upload_file":
            selector = args.get("selector")
            file_path = args.get("file_path")
            success = await self.browser_manager.upload_file(selector, file_path)
            return f"Uploaded file to '{selector}'" if success else f"Failed to upload file"
        
        # Tab Management
        elif name == "open_new_tab":
            url = args.get("url")
            tab_index = await self.browser_manager.new_tab(url)
            return f"Opened new tab (index {tab_index})" + (f" and navigated to {url}" if url else "")
        
        elif name == "switch_tab":
            index = args.get("index")
            success = await self.browser_manager.switch_tab(index)
            return f"Switched to tab {index}" if success else f"Failed to switch to tab {index}"
        
        elif name == "close_tab":
            index = args.get("index")
            success = await self.browser_manager.close_tab(index)
            return f"Closed tab {index}" if success else f"Failed to close tab {index}"
        
        # Research Tools
        elif name == "web_search":
            query = args.get("query")
            num_results = args.get("num_results", 5)
            results = self.research_tools.web_search(query, min(num_results, 10))
            if results:
                summary = f"Found {len(results)} results for '{query}':\n"
                for i, result in enumerate(results, 1):
                    summary += f"{i}. {result['title']} - {result['url']}\n"
                return summary
            return f"No results found for '{query}'"
        
        elif name == "extract_page_content":
            url = args.get("url")
            if url:
                content = self.research_tools.extract_content(url)
            else:
                # Extract from current page
                html = await self.browser_manager.get_content()
                current_url = self.browser_manager.page.url if self.browser_manager.page else "unknown"
                content = self.research_tools.get_page_metadata(html, current_url)
                content["text"] = await self.browser_manager.get_body_text()
            
            if "error" in content:
                return f"Failed to extract content: {content['error']}"
            return f"Extracted content from {content.get('title', 'page')}: {content.get('text', '')[:500]}..."
        
        elif name == "extract_structured_data":
            data_type = args.get("data_type")
            html = await self.browser_manager.get_content()
            data = self.research_tools.extract_structured_data(html, data_type)
            return f"Extracted {len(data)} {data_type}(s): {json.dumps(data[:3])}..." if data else f"No {data_type} data found"
        
        elif name == "start_research_session":
            topic = args.get("topic")
            self.current_research_session = self.memory.create_research_session(topic)
            self.research_mode = True
            return f"Started research session '{self.current_research_session}' for topic: {topic}"
        
        elif name == "save_research_finding":
            finding = args.get("finding")
            source = args.get("source")
            if not self.current_research_session:
                self.current_research_session = self.memory.create_research_session("General Research")
            self.memory.save_research_finding(self.current_research_session, finding, source)
            return f"Saved research finding: {finding[:100]}..."
        
        elif name == "export_research":
            format_type = args.get("format")
            filename = args.get("filename")
            
            if not self.current_research_session:
                return "No active research session to export"
            
            session_data = self.memory.get_research_session(self.current_research_session)
            if not session_data:
                return "Research session not found"
            
            # Export based on format
            if format_type == "json":
                filepath = self.data_exporter.export_to_json(session_data, filename)
            elif format_type == "csv":
                # Convert findings to list of dicts for CSV
                findings_list = session_data.get("findings", [])
                filepath = self.data_exporter.export_to_csv(findings_list, filename)
            elif format_type == "markdown":
                filepath = self.data_exporter.export_to_markdown(session_data, filename)
            else:
                return f"Unknown export format: {format_type}"
            
            return f"Exported research to {filepath}"
        
        # Memory & Context
        elif name == "save_to_memory":
            key = args.get("key")
            value = args.get("value")
            self.memory.update(key, value)
            return f"Saved to memory: {key} = {value}"
        
        elif name == "take_notes":
            note = args.get("note")
            if not self.current_research_session:
                self.current_research_session = self.memory.create_research_session("Notes")
            self.memory.save_research_finding(self.current_research_session, note)
            return f"Saved note: {note[:100]}..."
        
        # Task Completion
        elif name == "done":
            summary = args.get("summary")
            if self.current_research_session and self.research_mode:
                self.memory.close_research_session(self.current_research_session)
                self.research_mode = False
            return f"Task Done: {summary}"
        
        else:
            return f"Unknown tool: {name}"

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

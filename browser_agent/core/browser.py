from playwright.async_api import async_playwright, Browser as PlaywrightBrowser, Page, BrowserContext
from playwright_stealth import Stealth
import time
import os
import asyncio
import random
from typing import Optional, List

# Base directory for the data folder
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

# Realistic user agents for stealth
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

class BrowserManager:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright = None
        self.browser: PlaywrightBrowser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self.tabs: List[Page] = []  # Track multiple tabs
        # State file for cookies/session
        self.state_file = os.path.join(DATA_DIR, "browser_state.json")

    async def start(self):
        """Starts the Playwright browser session with stealth configuration."""
        if self.playwright:
             await self.stop()

        self.playwright = await async_playwright().start()
        
        # Launch with stealth-friendly args
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
            ]
        )
        
        # Load storage state if exists (cookies, local storage)
        storage_state = self.state_file if os.path.exists(self.state_file) else None
        
        # Set realistic viewport with slight randomization
        viewport = {
            "width": 1280 + random.randint(-20, 20),
            "height": 800 + random.randint(-20, 20)
        }
        
        # Stealth context configuration
        context_options = {
            "viewport": viewport,
            "user_agent": random.choice(USER_AGENTS),
            "locale": "en-US",
            "timezone_id": "America/Los_Angeles",
            "device_scale_factor": 1,
            "has_touch": False,
            "is_mobile": False,
            "java_script_enabled": True,
        }
        
        if storage_state:
            context_options["storage_state"] = storage_state
            print("Loaded browser state (cookies).")
        
        self.context = await self.browser.new_context(**context_options)
        
        # Create page and apply stealth
        self.page = await self.context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(self.page)  # Apply stealth patches
        
        self.tabs = [self.page]  # Initialize tabs list
        print("Browser started with stealth configuration.")

    async def save_state(self):
        """Saves storage state (cookies) to file."""
        if self.context:
            await self.context.storage_state(path="browser_state.json")

    async def stop(self):
        """Stops the Playwright browser session."""
        await self.save_state() # Save before closing
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def navigate(self, url: str, max_retries: int = 2) -> dict:
        """
        Navigates to the specified URL with robust error handling.
        
        Returns:
            dict with 'success', 'status_code', 'error' keys
        """
        if not self.page:
            return {"success": False, "error": "No page available"}
        
        result = {"success": False, "status_code": None, "error": None}
        
        for attempt in range(max_retries + 1):
            try:
                # Navigate and capture response
                response = await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                if response:
                    result["status_code"] = response.status
                    
                    # Check for HTTP errors
                    if response.status >= 400:
                        result["error"] = f"HTTP {response.status}: {response.status_text}"
                        print(f"Navigation HTTP error: {result['error']}")
                        if response.status < 500:  # Don't retry client errors
                            return result
                        continue  # Retry server errors
                
                # Wait for network to settle
                try:
                    await self.page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    # Fallback - page may never reach networkidle (streaming sites, etc.)
                    await asyncio.sleep(1)
                
                # Add small human-like delay
                await asyncio.sleep(random.uniform(0.3, 0.8))
                
                result["success"] = True
                result["error"] = None
                return result
                
            except Exception as e:
                error_msg = str(e)
                result["error"] = error_msg
                print(f"Navigation attempt {attempt + 1} failed: {error_msg}")
                
                if "timeout" in error_msg.lower() and attempt < max_retries:
                    await asyncio.sleep(1)  # Wait before retry
                    continue
                    
                return result
        
        return result

    async def get_content(self) -> str:
        """Returns the HTML content of the current page."""
        if self.page:
            return await self.page.content()
        return ""

    async def get_body_text(self) -> str:
        """Returns the visible text content of the body."""
        if self.page:
            try:
                # limited to 10k chars to avoid token limits
                text = await self.page.inner_text("body", timeout=1000)
                return text[:10000] 
            except Exception as e:
                print(f"Error getting text: {e}")
        return ""
    
    async def get_page_info(self) -> dict:
        """Get structured info about the current page for better LLM context."""
        if not self.page:
            return {}
        
        try:
            info = {
                "url": self.page.url,
                "title": await self.page.title(),
            }
            
            # Count interactive elements
            info["form_count"] = await self.page.evaluate("document.forms.length")
            info["link_count"] = await self.page.evaluate("document.links.length")
            info["button_count"] = await self.page.evaluate("document.querySelectorAll('button, [type=submit]').length")
            info["input_count"] = await self.page.evaluate("document.querySelectorAll('input, textarea, select').length")
            
            return info
        except Exception as e:
            print(f"Error getting page info: {e}")
            return {"url": self.page.url if self.page else "unknown"}

    async def screenshot(self, path: str, quality: int = 90):
        """Takes a high-quality screenshot of the current page."""
        if self.page:
            try:
                # Wait for fonts to load for cleaner screenshot
                await self.page.evaluate("document.fonts.ready")
                await self.page.screenshot(path=path, type="jpeg", quality=quality)
            except Exception as e:
                print(f"Screenshot warning: {e}")
    
    # Enhanced Browser Methods
    
    async def wait_for_selector(self, selector: str, timeout: int = 5000) -> bool:
        """
        Wait for an element to appear.
        
        Args:
            selector: CSS selector or text
            timeout: Timeout in milliseconds
            
        Returns:
            True if element appeared, False otherwise
        """
        if not self.page:
            return False
        
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except:
            return False
    
    async def is_visible(self, selector: str) -> bool:
        """
        Check if an element is visible.
        
        Args:
            selector: CSS selector
            
        Returns:
            True if visible, False otherwise
        """
        if not self.page:
            return False
        
        try:
            element = await self.page.query_selector(selector)
            if element:
                return await element.is_visible()
            return False
        except:
            return False
    
    async def is_enabled(self, selector: str) -> bool:
        """
        Check if an element is enabled.
        
        Args:
            selector: CSS selector
            
        Returns:
            True if enabled, False otherwise
        """
        if not self.page:
            return False
        
        try:
            element = await self.page.query_selector(selector)
            if element:
                return await element.is_enabled()
            return False
        except:
            return False
    
    async def upload_file(self, selector: str, file_path: str) -> bool:
        """
        Upload a file to a file input.
        
        Args:
            selector: CSS selector for file input
            file_path: Path to file to upload
            
        Returns:
            True if successful, False otherwise
        """
        if not self.page:
            return False
        
        try:
            await self.page.set_input_files(selector, file_path)
            return True
        except Exception as e:
            print(f"File upload failed: {e}")
            return False
    
    async def press_key(self, key: str):
        """
        Press a keyboard key.
        
        Args:
            key: Key name (e.g., 'Enter', 'Tab', 'Escape')
        """
        if self.page:
            await self.page.keyboard.press(key)
    
    async def fill_input(self, selector: str, text: str) -> bool:
        """
        Fill an input field (clears first, then types).
        
        Args:
            selector: CSS selector for input
            text: Text to fill
            
        Returns:
            True if successful, False otherwise
        """
        if not self.page:
            return False
        
        try:
            await self.page.fill(selector, text)
            return True
        except Exception as e:
            print(f"Fill input failed: {e}")
            return False
    
    # Tab Management
    
    async def new_tab(self, url: Optional[str] = None) -> int:
        """
        Open a new tab.
        
        Args:
            url: Optional URL to navigate to
            
        Returns:
            Tab index
        """
        if not self.context:
            return -1
        
        new_page = await self.context.new_page()
        self.tabs.append(new_page)
        
        if url:
            await new_page.goto(url)
        
        return len(self.tabs) - 1
    
    async def switch_tab(self, index: int) -> bool:
        """
        Switch to a specific tab.
        
        Args:
            index: Tab index (0-based)
            
        Returns:
            True if successful, False otherwise
        """
        if 0 <= index < len(self.tabs):
            self.page = self.tabs[index]
            return True
        return False
    
    async def close_tab(self, index: int) -> bool:
        """
        Close a specific tab.
        
        Args:
            index: Tab index (0-based)
            
        Returns:
            True if successful, False otherwise
        """
        if 0 <= index < len(self.tabs):
            page = self.tabs[index]
            await page.close()
            self.tabs.pop(index)
            
            # Switch to first tab if current was closed
            if self.page == page and self.tabs:
                self.page = self.tabs[0]
            
            return True
        return False
    
    async def get_current_tab_index(self) -> int:
        """Get the index of the current tab."""
        try:
            return self.tabs.index(self.page)
        except:
            return 0
    
    # Cookie/Session Management
    
    async def export_cookies(self) -> List[dict]:
        """Export all cookies."""
        if self.context:
            return await self.context.cookies()
        return []
    
    async def import_cookies(self, cookies: List[dict]):
        """Import cookies."""
        if self.context:
            await self.context.add_cookies(cookies)
    
    async def clear_cookies(self):
        """Clear all cookies."""
        if self.context:
            await self.context.clear_cookies()


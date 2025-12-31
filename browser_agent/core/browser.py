from playwright.async_api import async_playwright, Browser as PlaywrightBrowser, Page, BrowserContext
import time
import os
import asyncio
from typing import Optional, List

class BrowserManager:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright = None
        self.browser: PlaywrightBrowser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self.tabs: List[Page] = []  # Track multiple tabs

    async def start(self):
        """Starts the Playwright browser session."""
        self.playwright = await async_playwright().start()
        
        # ALWAYS run headless for Electron embedding
        # Enable CDP for remote control
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=['--remote-debugging-port=9222']
        )
        
        # Load storage state if exists (cookies, local storage)
        storage_state = "browser_state.json" if os.path.exists("browser_state.json") else None
        
        # Set a fixed viewport to ensure content acts like a desktop
        viewport = {"width": 1280, "height": 800}
        
        if storage_state:
            self.context = await self.browser.new_context(storage_state=storage_state, viewport=viewport)
            print("Loaded browser state (cookies).")
        else:
            self.context = await self.browser.new_context(viewport=viewport)
            
        self.page = await self.context.new_page()
        self.tabs = [self.page]  # Initialize tabs list

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

    async def navigate(self, url: str):
        """Navigates to the specified URL."""
        if self.page:
            try:
                await self.page.goto(url)
                # networkidle is better for SPAs but can be slow. 
                # using domcontentloaded + small sleep is often a good balance, 
                # but let's try networkidle first to ensure page is "ready".
                try:
                    await self.page.wait_for_load_state("networkidle", timeout=5000)
                except:
                    # Fallback if network never idles
                    await self.page.wait_for_load_state("domcontentloaded", timeout=5000)
            except Exception as e:
                print(f"Navigation warning: {e}")

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

    async def screenshot(self, path: str, quality: int = 85):
        """Takes a screenshot of the current page."""
        if self.page:
            try:
                # specific fix for "white screen" - sometimes needed for headless chrome
                # await self.page.evaluate("document.fonts.ready") 
                
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


from playwright.async_api import async_playwright, Browser as PlaywrightBrowser, Page, BrowserContext
import time
import os
import asyncio

class BrowserManager:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright = None
        self.browser: PlaywrightBrowser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

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

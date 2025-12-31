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
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        
        # Load storage state if exists (cookies, local storage)
        storage_state = "browser_state.json" if os.path.exists("browser_state.json") else None
        
        if storage_state:
            self.context = await self.browser.new_context(storage_state=storage_state)
            print("Loaded browser state (cookies).")
        else:
            self.context = await self.browser.new_context()
            
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
                # networkidle is too slow often (wait 500ms for no network).
                # domcontentloaded is faster.
                await self.page.wait_for_load_state("domcontentloaded", timeout=10000)
            except Exception as e:
                print(f"Navigation warning: {e}")

    async def get_content(self) -> str:
        """Returns the HTML content of the current page."""
        if self.page:
            return await self.page.content()
        return ""

    async def screenshot(self, path: str):
        """Takes a screenshot of the current page."""
        if self.page:
            try:
                # Just wait a tiny bit for animations/rendering if needed, but rely on previous action wait.
                # Removing explicit strict wait here to speed up viewing,
                # assuming the action (click/nav) already waited reasonably.
                # safe fallback:
                # await self.page.wait_for_load_state("domcontentloaded", timeout=2000)
                await self.page.screenshot(path=path, type="jpeg", quality=50)
            except Exception as e:
                print(f"Screenshot warning: {e}")

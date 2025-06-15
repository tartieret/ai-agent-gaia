from typing import Optional
from bs4 import BeautifulSoup
import markdownify
from langchain_core.callbacks import (
    CallbackManagerForToolRun,
    AsyncCallbackManagerForToolRun,
)
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.tools.playwright.utils import (
    create_sync_playwright_browser,
    create_async_playwright_browser,
)
from langchain_community.tools.playwright.extract_text import ExtractTextTool
from langchain_community.tools.playwright.utils import (
    aget_current_page,
    get_current_page,
)

# -----------------------------------------
# Browser tools


class ExtractMarkdownTool(ExtractTextTool):
    name: str = "extract_markdown"
    description: str = "Extract markdown from the current page"

    def convert_html_to_markdown(self, html_content: str) -> str:
        """Convert HTML content to markdown."""
        # Parse the string
        soup = BeautifulSoup(html_content, "html.parser")

        # Remove javascript and style blocks
        for script in soup(["script", "style"]):
            script.extract()

        # Print only the main content
        body_elm = soup.find("body")
        webpage_text = ""
        if body_elm:
            webpage_text = markdownify.MarkdownConverter().convert_soup(body_elm)
        else:
            webpage_text = markdownify.MarkdownConverter().convert_soup(soup)

        return webpage_text

    def _run(self, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        if self.sync_browser is None:
            raise ValueError(f"Synchronous browser not provided to {self.name}")

        page = get_current_page(self.sync_browser)
        html_content = page.content()
        return self.convert_html_to_markdown(html_content)

    async def _arun(
        self, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        if self.async_browser is None:
            raise ValueError(f"Asynchronous browser not provided to {self.name}")
        page = await aget_current_page(self.async_browser)
        html_content = await page.content()
        return self.convert_html_to_markdown(html_content)


def get_browser_tools(use_async_browser=True):
    """Wait for application start to install playwright if required."""
    # if required, install playwright

    # subprocess.run(["playwright", "install"])
    async_browser, sync_browser = None, None
    if use_async_browser:
        async_browser = create_async_playwright_browser()
        toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=async_browser)
    else:
        sync_browser = create_sync_playwright_browser()
        toolkit = PlayWrightBrowserToolkit.from_browser(sync_browser=sync_browser)
    browser_tools = [
        tool
        for tool in toolkit.get_tools()
        + [
            ExtractMarkdownTool.from_browser(
                async_browser=async_browser, sync_browser=sync_browser
            ),
        ]
        if tool.name
        in [
            "navigate_browser",
            "extract_markdown",
            # "previous_webpage",
            # "click_element",
            # "extract_text",
        ]
    ]

    return browser_tools

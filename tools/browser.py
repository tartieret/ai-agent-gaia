from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.tools.playwright.utils import (
    create_sync_playwright_browser,
    create_async_playwright_browser,
)
# -----------------------------------------
# Browser tools


def get_browser_tools(async_browser=True):
    """Wait for application start to install playwright if required."""
    # if required, install playwright

    # subprocess.run(["playwright", "install"])

    if async_browser:
        async_browser = create_async_playwright_browser()
        toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=async_browser)
    else:
        sync_browser = create_sync_playwright_browser()
        toolkit = PlayWrightBrowserToolkit.from_browser(sync_browser=sync_browser)
    browser_tools = [
        tool
        for tool in toolkit.get_tools()
        if tool.name
        in [
            "navigate_browser",
            "previous_webpage",
            "click_element",
            "extract_text",
        ]
    ]

    return browser_tools

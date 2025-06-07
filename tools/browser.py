from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.tools.playwright.utils import create_async_playwright_browser


# -----------------------------------------
# Browser tools

async_browser = create_async_playwright_browser()
toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=async_browser)
browser_tools = [
    tool
    for tool in toolkit.get_tools()
    if tool.name
    in [
        "navigate_browser",
    ]  # "extract_text"]
]

import subprocess


from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.tools.playwright.utils import create_async_playwright_browser
# -----------------------------------------
# Browser tools


def get_browser_tools():
    """Wait for application start to install playwright if required."""
    # if required, install playwright

    subprocess.run(["playwright", "install"])

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

    return browser_tools

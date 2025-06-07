import ast
import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL
from langchain_tavily import TavilySearch
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.tools.playwright.utils import create_async_playwright_browser


from langchain.tools import BaseTool
from langchain.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from textwrap import shorten, dedent

# -----------------------------------------
# Web Search


web_search_tool = TavilySearch(
    max_results=5,
    topic="general",
    include_relevant_snippets=True,
)

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


# -----------------------------------------
# Semantic search


class SemanticSectionRetrieverFromText(BaseTool):
    name: str = "semantic_section_retriever_from_text"
    description: str = dedent(
        """
        Given (text, query, k=3) return up to k snippets of text that are
        semantically closest to the query. Useful when keywords don’t match exactly.
        """
    )

    def _retriever(self, raw_text: str, query: str, k: int = 3) -> list[dict]:
        # 1. chunk
        window = 500
        stride = 250
        chunks = [raw_text[i : i + window] for i in range(0, len(raw_text), stride)]

        # 2. embed & index (one‑off per page)
        embed = OpenAIEmbeddings(model="text-embedding-3-small")
        vectors = embed.embed_documents(chunks)
        # Create text-embedding pairs for FAISS
        text_embeddings = list(zip(chunks, vectors))
        index = FAISS.from_embeddings(text_embeddings, embed)

        # 3. search
        qvec = embed.embed_query(query)
        results = index.similarity_search_with_score_by_vector(qvec, k=k)
        hits = [
            {"score": float(score), "text": shorten(doc.page_content, 350)}
            for doc, score in results
        ]
        return hits

    def _run(self, raw_text: str, query: str, k: int = 3):
        return self._retriever(raw_text, query, k)


class SemanticSectionRetrieverFromUrl(SemanticSectionRetrieverFromText):
    name: str = "semantic_section_retriever_from_url"
    description: str = dedent(
        """
        Given (url, query, k=3) return up to k snippets of page text that are
        semantically closest to the query. Useful when keywords don’t match exactly.
        """
    )

    def get_raw_url(aelf, url: str) -> str:
        """Retrieve the raw content of a URL.

        Args:
            url (str): The URL to retrieve the content from.
        Returns:
            str: The raw content (HTML or JSON) of the URL.
        """

        try:
            response = requests.get(url)
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL {url}: {e}")
            raise e

    def _run(self, url: str, query: str, k: int = 3):
        try:
            html_text = self.get_raw_url(url)
            soup = BeautifulSoup(html_text, "lxml")
            raw_text = soup.get_text(" ", strip=True)
            return self._retriever(raw_text, query, k)
        except Exception as e:
            return [f"Error processing URL {url}: {e}"]


semantic_tools = [SemanticSectionRetrieverFromText(), SemanticSectionRetrieverFromUrl()]


# -----------------------------------------
# Code Execution


@tool
def run_python(code: str) -> str:
    """
    Runs a Python code snippet. If you need to see the output of a value, you should print it out with `print(...)`.
    Args:
        code (str): The Python code to execute.
    Returns:
        str: The output of the code execution.
    """
    repl = PythonREPL()
    return repl.run(command=code)[:-1]  # remove the training newline


# -----------------------------------------
# Calculator


@tool
def calculator(expression: str) -> float:
    """
    Calculates the result of a basic arithmetic expression.
    It can include parentheses for grouping operations.

    Args:
        expression (str): The arithmetic expression to evaluate.

    Returns:
        float: The result of the expression.
    """
    try:
        node = ast.parse(expression, mode="eval")
        allowed_nodes = (
            ast.Expression,
            ast.BinOp,
            ast.UnaryOp,
            ast.Constant,
            ast.Add,
            ast.Sub,
            ast.Mult,
            ast.Div,
            ast.Pow,
            ast.Mod,
            ast.USub,
            ast.UAdd,
            ast.Constant,
        )

        if all(isinstance(n, allowed_nodes) for n in ast.walk(node)):
            result = eval(compile(node, "<string>", "eval"))
            return result
        else:
            return "Unsafe expression."
    except Exception as e:
        return f"Error: {e}"


# -----------------------------------------
# Basic Tools for debugging


@tool
def get_weather(city: str) -> str:
    """
    Returns the current weather in a given city.
    Args:
        city (str): The city to get the weather for.
    Returns:
        str: The current weather in the city.
    """
    if city.lower() == "paris":
        return "The weather in Paris is sunny, 25 degC."
    elif city.lower() == "vancouver":
        return "The weather in Vancouver is snowy, -2 degC."
    return f"The weather in {city} is cloudy, 12 degC."


if __name__ == "__main__":
    expr = input("Enter a simple expression (e.g., 2 + 3 * 4): ")
    print("Result:", calculator(expr))

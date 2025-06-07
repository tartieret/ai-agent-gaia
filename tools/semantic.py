import requests
from bs4 import BeautifulSoup
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.tools import BaseTool
from textwrap import shorten, dedent

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

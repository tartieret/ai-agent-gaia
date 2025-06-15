"""
settings.py

Loads environment variables from a .env file and sets API keys for OpenAI and Tavily.
"""

from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY: Optional[str] = os.getenv("TAVILY_API_KEY")

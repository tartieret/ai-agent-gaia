import os

from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


class Agent:
    def __init__(self):
        llm = HuggingFaceEndpoint(
            repo_id="Qwen/Qwen2.5-Coder-32B-Instruct",
            huggingfacehub_api_token=os.getenv("HF_TOKEN"),
        )

        chat = ChatHuggingFace(llm=llm, verbose=True)

    def __call__(self, question: str) -> str:
        fixed_answer = "This is a default answer."
        return fixed_answer

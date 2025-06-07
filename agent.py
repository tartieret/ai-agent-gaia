import os
import asyncio
from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt.chat_agent_executor import AgentState
from langchain_openai import ChatOpenAI

# from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain.tools.render import render_text_description_and_args
from tools import (
    calculator,
    web_search_tool,
    run_python,
    browser_tools,
    semantic_tools,
)
from debug import PromptLoggingHandler
from utils import format_messages

DEBUG = True

BASE_PROMPT = """
You are a general AI assistant and have access to the following tools:  
{tools}

╭─  Interaction protocol (ReAct) ──────────────────────────────────────────╮
│ When you receive a question, think step‑by‑step and use tools            │
│ whenever helpful. Always follow *exactly* this scratch‑pad format:       │
│                                                                          │
│ Thought: ...   
│ Action: <tool_name>[<input>]                                             │
│ Observation: <tool_output>                                               │
│                                                                          │
│ … (repeat Thought/Action/Observation as needed) …                         │
│                                                                          │
│ Thought: I now know the answer.                                          │
│ FINAL ANSWER: <single answer here>                                       │
╰──────────────────────────────────────────────────────────────────────────╯

You MUST respect the following answer format rules:
• If the answer is a **number**, write plain digits (no commas or units) unless the task explicitly asks for a unit or currency sign.  
• If the answer is a **string**, give as few words as possible, no articles, no abbreviations, spell out digits unless the task says otherwise.  
• If the answer is a **comma‑separated list**, apply the number/string rules to every element and separate elements only with “, ” (comma + space).

After the line that starts with **“FINAL ANSWER:”**, output nothing else.  
Never prepend or append explanations to the final answer line.

START NOW!
----------------
{messages}
"""


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


class Agent:
    def __init__(self, debug=False):
        self.debug = debug
        # Add callbacks to the LLM if debug is enabled
        self.callbacks = None
        if self.debug:
            self.callbacks = [PromptLoggingHandler()]

        # llm = HuggingFaceEndpoint(
        #     # repo_id="Qwen/Qwen2.5-Coder-32B-Instruct",
        #     repo_id="deepseek-ai/deepseek-coder-33b",
        #     # repo_id="mistralai/Mistral-7B-Instruct-v0.2",
        #     huggingfacehub_api_token=os.getenv("HF_TOKEN"),
        #     callbacks=self.callbacks,
        # )
        # # Attach callbacks directly to the LLM
        # chat_model = ChatHuggingFace(llm=llm)

        # Use OpenAI 4o
        chat_model = ChatOpenAI(
            model_name="gpt-4o",
            callbacks=self.callbacks,
            api_key=os.getenv("OPENAI_KEY"),
        )

        tools = [
            calculator,
            run_python,
            web_search_tool,
            *browser_tools,
            # get_text_from_url,
            *semantic_tools,
        ]

        # react_prompt_template = PromptTemplate.from_template(BASE_PROMPT)
        # react_prompt = react_prompt_template.partial(
        #     tools=render_text_description_and_args(tools),
        # )

        def prompt(state: AgentState, config: RunnableConfig) -> list[AnyMessage]:
            # Build the scratchpad from the messages
            scratchpad = format_messages(state["messages"])
            system_prompt = BASE_PROMPT.format(
                tools=render_text_description_and_args(tools),
                messages=scratchpad,
            )
            return system_prompt

        react_prompt_template = PromptTemplate.from_template(BASE_PROMPT)
        react_prompt = react_prompt_template.partial(
            tools=render_text_description_and_args(tools),
        )

        self.agent = create_react_agent(
            model=chat_model,
            tools=tools,
            prompt=prompt,  # react_prompt,
            debug=self.debug,
        )

    def __call__(self, question: str, filename: str | None = None) -> str:
        invoke_kwargs = {"messages": [{"role": "user", "content": question}]}

        # Get the current event loop or create a new one
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Run the async function and get the response
        response = loop.run_until_complete(self.agent.ainvoke(invoke_kwargs))

        if self.debug:
            print("\n=== ALL MESSAGES ===")
            print(format_messages(response["messages"]))
            print("=====================\n")
        return response["messages"][-1].content

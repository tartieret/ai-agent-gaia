import os

from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages
from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_openai import ChatOpenAI
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain.tools.render import render_text_description_and_args
from tools import calculator, web_search_tool, get_weather
from debug import PromptLoggingHandler

DEBUG = True

PROMPT = """
You are a general AI assistant and have access to the following tools:  
{tools}

╭─  Interaction protocol (ReAct) ──────────────────────────────────────────╮
│ When you receive a question, think step‑by‑step and use tools            │
│ whenever helpful. Always follow *exactly* this scratch‑pad format:       │
│                                                                          │
│ Thought: ...                                                             │
│ Action: <tool_name>[<input>]                                             │
│ Observation: <tool_output>                                               │
│                                                                          │
│ … (repeat Thought/Action/Observation as needed) …                        │
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

        tools = [calculator, get_weather]  # , web_search_tool]

        react_prompt_template = PromptTemplate.from_template(PROMPT)
        react_prompt = react_prompt_template.partial(
            tools=render_text_description_and_args(tools),  # pretty description block
        )

        self.agent = create_react_agent(
            model=chat_model,
            tools=tools,
            # prompt=react_prompt,
            debug=self.debug,
        )

    def __call__(self, question: str, filename: str | None = None) -> str:
        invoke_kwargs = {"messages": [{"role": "user", "content": question}]}
        response = self.agent.invoke(invoke_kwargs)

        if self.debug:
            print("\n=== ALL MESSAGES ===")
            for msg in response["messages"]:
                self.log_message(msg)
            print("=====================\n")
        return response["messages"][-1].content

    def log_message(self, msg: AnyMessage):
        """
        Log a message with proper formatting.

        Args:
            msg (AnyMessage): The message to log.
        """

        # Format multiline content with proper indentation
        def format_content(content):
            if "\n" in content:
                # If content is multiline, add a newline and indent each line with a tab
                formatted = "\n"
                for line in content.split("\n"):
                    formatted += f"\t{line}\n"
                return formatted
            return content

        if isinstance(msg, HumanMessage):
            print(f"Human: {format_content(msg.content)}")
        elif isinstance(msg, AIMessage):
            if msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tool_name = tool_call.get("name", "")
                    kwargs = tool_call.get("args", {})
                    pretty_kwargs = ",".join([f"{k}={v}" for k, v in kwargs.items()])
                    print(f"Assistant: <{tool_name}>[{pretty_kwargs}]")
            else:
                print(f"Assistant: {format_content(msg.content)}")
        elif isinstance(msg, SystemMessage):
            print(f"System: {format_content(msg.content)}")
        elif isinstance(msg, ToolMessage):
            # output the tool name and arguments
            print(f"Tool: {msg.content}")
        else:
            print(f"Other message type: {type(msg).__name__}")
            print(f"Content: {format_content(msg.content)}")

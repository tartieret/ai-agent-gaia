import os
import asyncio
import dataclasses

from langchain_core.messages import AnyMessage
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt.chat_agent_executor import AgentState
from langchain_openai import ChatOpenAI

from langgraph.prebuilt import create_react_agent
from langchain.tools.render import render_text_description_and_args
from tools import (
    analyze_audio,
    analyze_image,
    get_video_transcript,
    convert_unit,
    chess,
    calculator,
    load_file_or_url,
    web_search_tool,
    run_python,
    get_browser_tools,
    semantic_tools,
    unzip,
)
from utils import format_messages


DEBUG = True

BASE_PROMPT_OLD = """
You are an expert multi-tool reasoning agent.

## Tools
You are a general AI assistant and have access to the following tools:  
{tools}

## Interaction protocol (ReAct) 
When you receive a question, think step‑by‑step and use tools whenever helpful. 
Always follow *exactly* this sequence:

Thought: ...   
Action: <tool_name>[<input>] 
Observation: <tool_output> 
… (repeat Thought/Action/Observation as needed) … 

Thought: I now know the answer. 
FINAL ANSWER: <single answer here>

After the line that starts with **“FINAL ANSWER:”**, output nothing else than the answer, NO EXPLANATION.

You MUST respect the following answer format rules:
• If the answer is a **number**, write plain digits (no commas or units) unless the task explicitly asks for a unit or currency sign.  
• If the answer is a **string**, give as few words as possible, no articles, no abbreviations, spell out digits unless the task says otherwise.  
• If the answer is a **comma‑separated list**, apply the number/string rules to every element and separate elements only with “, ” (comma + space).

START NOW!
----------------

{messages}
"""

BASE_PROMPT = """
You are an expert multi-tool reasoning agent and you have access to the following tool

# Tools
{tools}

# Interaction protocol (ReAct) 
When you receive a question, think step‑by‑step and use tools whenever helpful. 
Always follow *exactly* this sequence:

Thought: ...   
Action: <tool_name>[<input>] 
Observation: <tool_output> 
… (repeat Thought/Action/Observation as needed) … 

Thought: I now know the answer. 
FINAL ANSWER: <single answer here>

# FINAL ANSWER formatting
Before ending, ALWAYS check that the final answer follow these formatting instructions:
• If a **number**, use digits only – **no commas, no units** ($, %, etc.) unless the question EXPLICITLY asks for them.  
• If a **string**, use as few words as possible, **no articles** (“a”, “the”) and **no abbreviations** (write “Saint Petersburg”, not “St Petersburg”).  
• If a **comma-separated list**, apply the above rules to each element and separate with a comma + space.  
• Never wrap your answer in quotes or backticks.  
• The autograder compares your output verbatim; any extra characters will cause failure.

# START NOW!

{messages}
"""


class AgentStateWithFile(AgentState):
    file_path: str | None


@dataclasses.dataclass
class AgentResponse:
    final_answer: str
    num_steps: int
    tools_used: list[str]


class Agent:
    def __init__(self, debug=False):
        self.debug = debug
        # Add callbacks to the LLM if debug is enabled
        self.callbacks = None
        # if self.debug:
        #     self.callbacks = [PromptLoggingHandler()]

        # Use OpenAI 4o
        chat_model = ChatOpenAI(
            model_name="o3",
            # model_name="o4-mini",
            callbacks=self.callbacks,
            api_key=os.getenv("OPENAI_KEY"),
        )

        tools = [
            analyze_audio,
            analyze_image,
            chess,
            convert_unit,
            get_video_transcript,
            load_file_or_url,
            calculator,
            run_python,
            web_search_tool,
            *get_browser_tools(use_async_browser=True),
            *semantic_tools,
            unzip,
        ]

        def prompt(state: AgentState, config: RunnableConfig) -> list[AnyMessage]:
            # Build the scratchpad from the messages
            scratchpad = format_messages(state["messages"])

            if state["file_path"]:
                if state["file_path"].endswith(".zip"):
                    scratchpad = (
                        f"Provided zip file: {state['file_path']}\nUse the unzip tool to process it.\n\n"
                        + scratchpad
                    )
                else:
                    scratchpad = f"Provided file: {state['file_path']}\n\n" + scratchpad

            system_prompt = BASE_PROMPT.format(
                tools=render_text_description_and_args(tools),
                messages=scratchpad,
            )

            return system_prompt

        self.agent = create_react_agent(
            model=chat_model,
            tools=tools,
            prompt=prompt,
            debug=self.debug,
            state_schema=AgentStateWithFile,
        )

    def __call__(self, question: str, file_path: str | None = None) -> str:
        """Run the agent with the given question and optional file path.

        Args:
            question (str): The question to ask the agent.
            file_path (str | None, optional): The path to the file to be used by the agent. Defaults to None.

        Returns:
            str: The response from the agent.
        """
        invoke_kwargs = {
            "messages": [{"role": "user", "content": question}],
            "file_path": file_path,
        }

        # Get the current event loop or create a new one
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        response = loop.run_until_complete(self.agent.ainvoke(invoke_kwargs))

        if self.debug:
            print("\n=== ALL MESSAGES ===")
            print(format_messages(response["messages"]))
            print("=====================\n")
        output = response["messages"][-1].content

        # extract the final answer
        if "FINAL ANSWER:" not in output:
            final_answer = output
        else:
            final_answer = output.split("FINAL ANSWER:")[1].strip()

        # Count all steps (Thought, Action, Observation)

        step_count = 0
        tool_steps = []
        for msg in response["messages"]:
            if msg["role"] == "assistant":
                step_count += 1
            if msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tool_name = tool_call.get("name", "")
                    kwargs = tool_call.get("args", {})
                    pretty_kwargs = ",".join([f"{k}={v}" for k, v in kwargs.items()])
                    tool_steps.append(f"<{tool_name}>[{pretty_kwargs}]")

        return AgentResponse(
            final_answer=final_answer,
            num_steps=step_count,
            tools_used=tool_steps,
        )


# TODO: include a final answer verification node

from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
)


def format_messages(messages: list[AnyMessage]) -> str:
    return "\n".join([msg.pretty_repr() for msg in messages])


def format_message(msg: AnyMessage) -> str:
    """Format a message like in a conversation.

    Args:
        msg (AnyMessage): The message to log.

    Returns:
        str: The formatted message.

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
        return f"Human: {format_content(msg.content)}"
    elif isinstance(msg, AIMessage):
        if msg.tool_calls:
            for tool_call in msg.tool_calls:
                tool_name = tool_call.get("name", "")
                kwargs = tool_call.get("args", {})
                pretty_kwargs = ",".join([f"{k}={v}" for k, v in kwargs.items()])
                return f"Assistant: <{tool_name}>[{pretty_kwargs}]"
        else:
            return f"Assistant: {format_content(msg.content)}"
    elif isinstance(msg, SystemMessage):
        return f"System: {format_content(msg.content)}"
    elif isinstance(msg, ToolMessage):
        # output the tool name and arguments
        return f"Tool: {format_content(msg.content)}"
    else:
        return f"Other: {format_content(msg.content)}"

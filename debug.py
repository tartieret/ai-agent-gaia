import time
from typing import Any, Dict, List

from langchain_core.callbacks.base import BaseCallbackHandler


class PromptLoggingHandler(BaseCallbackHandler):
    """Callback Handler for logging prompts sent to the LLM."""

    def __init__(self):
        """Initialize the handler with a step counter."""
        super().__init__()
        self.step_counter = 0

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Print the prompts sent to the LLM."""
        self.step_counter += 1
        self.start_time = time.time()
        print(f"\n\n{'=' * 80}")
        print(f"=== STEP {self.step_counter} - PROMPT SENT TO LLM ===\n")
        for i, prompt in enumerate(prompts):
            print(f"Prompt {i + 1}:\n{prompt}")
        print(f"{'=' * 80}\n\n")

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        """Log when the LLM finishes generating."""
        if self.start_time:
            duration = time.time() - self.start_time
            print(f"\n=== STEP {self.step_counter} COMPLETED in {duration:.2f}s ===\n")

    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        """Log when the LLM errors."""
        print(f"\n!!! ERROR IN STEP {self.step_counter} !!!\n{error}\n")

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        """Log when a tool starts running."""
        print(f"\n--- TOOL EXECUTION START ---")
        print(f"Tool: {serialized.get('name', 'Unknown tool')}")
        print(f"Input: {input_str}")

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Log when a tool finishes running."""
        print(f"Tool output: {output}")
        print("--- TOOL EXECUTION END ---\n")

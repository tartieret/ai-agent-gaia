import ast
import logging

from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL

logger = logging.getLogger(__name__)


@tool
def load_text_file(file_path: str) -> str:
    """Load a text file and return its contents.

    Args:
        file_path (str): The path to the text file.

    Returns:
        str: The contents of the text file.
    """
    with open(file_path) as f:
        return f.read()


# -----------------------------------------
# Code Execution


@tool
def run_python(code: str | None = None, file_path: str | None = None) -> str:
    """Execute a Python program. Provide either code or file_path.

    If you need to see the output of a value, you should print it out with `print(...)`.

    Args:
        code (str | None, optional): The Python code to execute. Defaults to None.
        file_path (str | None, optional): The path to the Python file to execute. Defaults to None.

    Returns:
        str: The output of the code execution.
    """
    try:
        if file_path:
            with open(file_path) as f:
                code = f.read()
                logger.debug(f"Executing code from file: {file_path}")

        repl = PythonREPL()
        output = repl.run(command=code, timeout=30)
        if output:
            return output[:-1]  # remove the training newline
        else:
            return "The code did not produce any output."
    except Exception as e:
        logger.error("run_python failed with error: %s", e)
        return f"The code failed to execute: {str(e)}"


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


if __name__ == "__main__":
    expr = input("Enter a simple expression (e.g., 2 + 3 * 4): ")
    print("Result:", calculator(expr))

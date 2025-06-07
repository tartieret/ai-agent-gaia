import ast
from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL

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


if __name__ == "__main__":
    expr = input("Enter a simple expression (e.g., 2 + 3 * 4): ")
    print("Result:", calculator(expr))

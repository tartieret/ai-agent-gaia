import ast
import logging

import stockfish
import pint
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

    The following packages are available:
    - pandas

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
# Chess tool


@tool
def chess(fen: str, depth: int = 20) -> str:
    """Find the best move in a chess game

    Args:
        fen (str): The current position of the chessboard
        depth (int, optional): The depth of the search. Defaults to 20.

    Returns:
        str: The best move

    """
    engine = stockfish.Stockfish(depth=depth)
    engine.set_position(fen)
    return engine.get_best_move()


# -----------------------------------------
# Unit conversion


@tool
def convert_unit(value: float, from_unit: str, to_unit: str) -> float:
    """
    Convert a value from one unit to another.

    Args:
        value (float): The value to convert.
        from_unit (str): The unit to convert from.
        to_unit (str): The unit to convert to.

    Returns:
        float: The converted value.
    """
    ureg = pint.UnitRegistry()
    return ureg.convert(value, from_unit, to_unit)


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
    print("Result:", calculator.invoke({"expression": expr}))

    unit_from = input("Enter a unit to convert from (e.g., m, km, cm): ")
    unit_to = input("Enter a unit to convert to (e.g., m, km, cm): ")
    value = float(input("Enter a value to convert: "))
    print(
        "Result:",
        convert_unit.invoke(
            {"value": value, "from_unit": unit_from, "to_unit": unit_to}
        ),
    )

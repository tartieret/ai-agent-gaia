"""Run the agent on specific questions.

To use it:

python evaluate.py <task_id>

Where <task_id> is the ID of the task to run. Runs all if not specified.

"""

import argparse

from agent import Agent
from hg_api import load_questions


def select_questions_to_run(task_id: str | None = None) -> list[dict]:
    """Selects questions to run based on the task ID.
    If no task ID is specified, returns all questions.

    Args:
        task_id (str | None, optional): ID of the task to run. Defaults to None.

    Returns:
        list[dict]: List of questions to run.
    """
    questions_data = load_questions()
    if task_id:
        filtered_questions = []
        for question in questions_data:
            if task_id.lower() in question["task_id"].lower():
                filtered_questions.append(question)
        if not filtered_questions:
            print(f"No questions found matching ID: {task_id}")
            return
        return filtered_questions
    return questions_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Evaluate agent on specified questions."
    )
    parser.add_argument(
        "task_id",
        nargs="?",
        default=None,
        help="Optional: ID of the task to run. Runs all if not specified.",
    )
    args = parser.parse_args()

    agent = Agent(debug=True)

    for question in select_questions_to_run(args.task_id):
        print("\n" + "-" * 30 + f"Question {question['task_id']}" + "-" * 30 + "\n")
        content = question["question"]
        print("Content: " + content)
        if question["file_name"]:
            print(f"File: {question['file_name']}\n")

        response = agent(content)
        print("Response: " + response)

    # response = agent(
    #     "Find if 11111*11111 is odd or even. If it's odd, output 2348592043*0.0934. Otherwise output zero."
    # )
    # response = agent(
    #     "What's the current weather in Vancouver? If it's not warm, compute 0.349*2348592043*0.0934. Otherwise output zero."
    # )

    # response = agent(
    #     "Write a program in python that generate 100 random numbers between 1 and 1000 and insert them in a pandas dataframe. Then compute the sum of these, and output it as your final answer"
    # )
    print("\nResponse: " + response)

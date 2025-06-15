import argparse
import dataclasses
import os
import json
from typing import Literal


@dataclasses.dataclass
class Question:
    task_id: str
    question: str
    file_path: str | None
    expected_answer: str
    level: int


DATA_FOLDER = os.path.join(os.path.dirname(__file__), "data")


def load_questions(
    dataset: Literal["validation", "test"] = "validation",
) -> list[Question]:
    data = []
    with open(os.path.join(DATA_FOLDER, dataset, "metadata.jsonl")) as f:
        for line in f:
            item = json.loads(line)
            data.append(
                Question(
                    task_id=item["task_id"],
                    question=item["Question"],
                    file_path=os.path.join(DATA_FOLDER, dataset, item["file_name"]),
                    expected_answer=item["Final answer"],
                    level=item["Level"],
                )
            )
    return data


def select_questions_to_run(
    dataset: Literal["validation", "test"] = "validation",
    level: int | None = None,
    task_id: str | None = None,
) -> list[Question]:
    """Selects questions to run based on the task ID.
    If no task ID is specified, returns all questions.

    Args:
        dataset (Literal["validation", "test"]): Dataset to use for evaluation. Defaults to 'validation'.
        level (int | None, optional): Level of the questions to run. Defaults to None.
        task_id (str | None, optional): ID of the task to run. Defaults to None.

    Returns:
        list[Question]: List of questions to run.
    """
    questions_data = load_questions(dataset)
    filtered_questions = []
    if level:
        for question in questions_data:
            if question.level == level:
                filtered_questions.append(question)
    else:
        filtered_questions = questions_data

    selected_questions = []
    if task_id:
        for question in filtered_questions:
            if task_id.lower() in question.task_id.lower():
                selected_questions.append(question)
        if not selected_questions:
            print(f"No questions found matching ID: {task_id}")
            return
    else:
        selected_questions = filtered_questions
    return selected_questions


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Evaluate agent on specified questions."
    )
    # add an option to either load the validation or test dataset
    parser.add_argument(
        "--dataset",
        choices=["validation", "test"],
        default="validation",
        help="Dataset to use for evaluation. Defaults to 'validation'.",
    )
    # option to only load questions for level 1, 2, or 3. Default to all
    parser.add_argument(
        "--level",
        choices=[1, 2, 3],
        default=None,
        type=int,
        help="Optional: Level of the questions to run. Runs all if not specified.",
    )
    parser.add_argument(
        "task_id",
        nargs="?",
        default=None,
        help="Optional: ID of the task to run. Runs all if not specified.",
    )
    args = parser.parse_args()
    selected_questions = select_questions_to_run(args.dataset, args.level, args.task_id)
    print(f"Selected {len(selected_questions)} questions.")
    for question in selected_questions:
        print("\n" + "-" * 30 + f"Question {question.task_id}" + "-" * 30 + "\n")
        print(f"Level: {question.level}")
        print(f"Question: {question.question}")
        if question.file_name:
            print(f"File: {question.file_name}\n")
        print(f"Answer: {question.expected_answer}\n")

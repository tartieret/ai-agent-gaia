import dataclasses
from typing import Literal
import json
import time

from agent import Agent
from dataset import select_questions_to_run


@dataclasses.dataclass
class Answer:
    task_id: str
    question: str
    file_path: str | None
    submitted_answer: str
    expected_answer: str
    score: int
    duration_s: float
    tools: list[str]
    number_of_steps: int


def check_answer(submitted_answer: str, expected_answer: str) -> int:
    return 1 if submitted_answer == expected_answer else 0


def evaluate_agent(
    dataset: Literal["validation", "test"] = "validation",
    level: int | None = None,
    task_id: str | None = None,
    debug: bool = False,
) -> list[Answer]:
    """Select questions from the GAIA benchmark and run the agent on them.

    Args:
        dataset (Literal["validation", "test"]): Dataset to use for evaluation. Defaults to 'validation'.
        level (int | None, optional): Level of the questions to run. Defaults to None.
        task_id (str | None, optional): ID of the task to run. Defaults to None.
        debug (bool, optional): Whether to run in debug mode. Defaults to False.

    Returns:
        list[Answer]: List of answers.
    """
    agent = Agent(debug=debug)
    answers = []
    total_score: int = 0

    for question in select_questions_to_run(dataset, level, task_id):
        print("\n" + "-" * 30 + f"Question {question.task_id}" + "-" * 30 + "\n")

        print("Content: " + question.question)
        if question.file_path:
            print(f"File: {question.file_path}\n")

        start_time = time.time()
        response = agent(question.question, question.file_path)
        duration_s = time.time() - start_time
        print("Response: " + response)

        score = check_answer(response, question.expected_answer)

        answers.append(
            Answer(
                task_id=question.task_id,
                question=question.question,
                file_path=question.file_path,
                submitted_answer=response,
                expected_answer=question.expected_answer,
                score=score,
                duration_s=duration_s,
                tools=[],
                number_of_steps=0,
            )
        )
        total_score += score

    # Calculate total score
    print("\n" + "-" * 30 + "Total Score" + "-" * 30 + "\n")
    print("Datasets:")
    print(f"  Dataset: {dataset}")
    if level:
        print(f"  Level: {level}")
    else:
        print("  Level: All")
    print(
        f"Total score: {total_score}/{len(answers)} ({total_score / len(answers) * 100:.2f}%)"
    )

    return answers


def save_answers(
    answers: list[Answer],
    dataset: Literal["validation", "test"] = "validation",
    level: int | None = None,
    task_id: str | None = None,
) -> None:
    """Save the answers to a JSON file.

    Args:
        answers (list[Answer]): List of answers.
        dataset (Literal["validation", "test"]): Dataset to use for evaluation. Defaults to 'validation'.
        level (int | None, optional): Level of the questions to run. Defaults to None.
        task_id (str | None, optional): ID of the task to run. Defaults to None.
    """
    base_filename = f"{dataset}_answers"
    if level:
        base_filename += f"_level_{level}"
    if task_id:
        base_filename += f"_task_{task_id}"
    filename = base_filename + ".json"
    with open(filename, "w") as f:
        json.dump([dataclasses.asdict(answer) for answer in answers], f, indent=4)

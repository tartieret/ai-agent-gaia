import dataclasses
from typing import Literal
import json
import os
import time

from agent import Agent
from scorer import question_scorer
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
    stats_per_level = {i: {"nb_questions": 0, "total_score": 0} for i in range(1, 4)}

    for question in select_questions_to_run(dataset, level, task_id):
        print("\n" + "-" * 30 + f"Question {question.task_id}" + "-" * 30 + "\n")
        print("Level: ", question.level)
        print("Content: " + question.question)
        if question.file_path:
            print(f"File: {question.file_path}\n")

        start_time = time.time()
        try:
            response = agent(question.question, question.file_path)
        except Exception as e:
            print(f"Error: {str(e)}")
            response = "Error: " + str(e)
        duration_s = time.time() - start_time
        score = int(question_scorer(response, question.expected_answer))
        print("Response: " + response)
        print("Expected: " + question.expected_answer)
        print(f"Score: {score}")
        print(f"Duration: {duration_s:.2f} seconds")

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
        stats_per_level[question.level]["nb_questions"] += 1
        stats_per_level[question.level]["total_score"] += score

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

    # Print stats per level
    for level, stats in stats_per_level.items():
        if stats["nb_questions"] == 0:
            continue
        print(f"\nLevel {level}:")
        print(f"  Number of questions: {stats['nb_questions']}")
        print(f"  Total score: {stats['total_score']}")
        print(
            f"  Average score: {100 * stats['total_score'] / stats['nb_questions']:.2f}%"
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
    with open(os.path.join("data", "answers", filename), "w") as f:
        json.dump([dataclasses.asdict(answer) for answer in answers], f, indent=4)

    print(f"\nSaved answers to {filename}")

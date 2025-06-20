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
    level: int
    submitted_answer: str
    expected_answer: str
    score: int
    duration_s: float
    tools: list[str]
    number_of_steps: int

    def pprint(self):
        print(f"Task ID: {self.task_id}")
        print(f"Question: {self.question}")
        if self.file_path:
            print(f"File: {self.file_path}")
        print(f"Submitted answer: {self.submitted_answer}")
        print(f"Expected answer: {self.expected_answer}")
        print(f"Score: {self.score}")
        print(f"Duration: {self.duration_s:.2f} seconds")
        print(f"Tools: {self.tools}")
        print(f"Number of steps: {self.number_of_steps}")
        print(f"Level: {self.level}")


def print_scores(answers: list[Answer]) -> None:
    """Show the total score, and the breakdown per level.

    Args:
        answers (list[Answer]): List of answers.

    """
    total_score: int = 0
    stats_per_level = {i: {"nb_questions": 0, "total_score": 0} for i in range(1, 4)}

    for answer in answers:
        total_score += answer.score
        stats_per_level[answer.level]["nb_questions"] += 1
        stats_per_level[answer.level]["total_score"] += answer.score

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

    for question in select_questions_to_run(dataset, level, task_id):
        print("\n" + "-" * 30 + f"Question {question.task_id}" + "-" * 30 + "\n")
        print("Level: ", question.level)
        print("Content: " + question.question)
        if question.file_path:
            print(f"File: {question.file_path}\n")

        start_time = time.time()
        try:
            agent_response = agent(question.question, question.file_path)
            response = agent_response.final_answer
        except Exception as e:
            print(f"Error: {str(e)}")
            response = "Error: " + str(e)
        duration_s = time.time() - start_time
        score = int(question_scorer(response, question.expected_answer))
        print("Response: " + response)
        print("Expected: " + question.expected_answer)
        print(f"Score: {score}")
        print(f"Duration: {duration_s:.2f} seconds")
        print(f"Tools: {agent_response.tools_used}")
        print(f"Number of steps: {agent_response.num_steps}")

        answers.append(
            Answer(
                task_id=question.task_id,
                question=question.question,
                level=question.level,
                file_path=question.file_path,
                submitted_answer=response,
                expected_answer=question.expected_answer,
                score=score,
                duration_s=duration_s,
                tools=agent_response.tools_used,
                number_of_steps=agent_response.num_steps,
            )
        )

    # Calculate total score
    print("\n" + "-" * 30 + "Results" + "-" * 30 + "\n")
    print("Datasets:")
    print(f"  Dataset: {dataset}")
    if level:
        print(f"  Level: {level}")
    else:
        print("  Level: All")
    print_scores(answers)

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
    date = time.strftime("%Y%m%d")
    base_filename = f"{date}_{dataset}_answers"
    if level:
        base_filename += f"_level_{level}"
    if task_id:
        base_filename += f"_task_{task_id}"
    filename = base_filename + ".json"
    with open(os.path.join("data", "answers", filename), "w") as f:
        json.dump([dataclasses.asdict(answer) for answer in answers], f, indent=4)

    print(f"\nSaved answers to {filename}")
